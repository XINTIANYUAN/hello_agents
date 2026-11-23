"""运行第四章的解析、少样本、故障恢复和评审角色对照实验。"""

import contextlib
import io
import json
import platform
import re
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from llm_client import HelloAgentsLLM
from ReAct import ReActAgent
from Reflection import ReflectionAgent, validate_prime_code
from tools import ToolExecutor, calculator


EXPRESSION = "(123+456)*789/12"
EXPECTED_VALUE = Decimal("38069.25")
CALCULATOR_QUESTION = (
    f"请必须调用 Calculator 工具计算 {EXPRESSION}，然后根据真实工具观察给出数值结果。"
)
PRIME_TASK = (
    "编写函数 find_primes(n: int) -> list[int]，返回从 1 到 n（含 n）的所有素数。"
    "n 小于 2 时返回空列表，保留完整的函数签名和文档字符串。"
)
INITIAL_CODE = '''def find_primes(n: int) -> list[int]:
    """Return all prime numbers from 1 through n, inclusive."""
    primes = []
    for number in range(2, n + 1):
        is_prime = True
        for divisor in range(2, number):
            if number % divisor == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(number)
    return primes
'''


class RecordedClient:
    """记录模型调用次数，按需先返回明确标注的人工故障。"""

    def __init__(self, client, injected_responses=()):
        self.client = client
        self.injected_responses = injected_responses
        self.calls = []

    def think(self, messages, temperature=0):
        call_index = len(self.calls)
        injected = call_index < len(self.injected_responses)
        record = {
            "source": "fault_injection" if injected else "live_model",
            "temperature": temperature,
            "success": False,
        }
        self.calls.append(record)
        started = time.monotonic()
        try:
            response = (
                self.injected_responses[call_index]
                if injected else self.client.think(messages, temperature=temperature)
            )
            record["success"] = bool(response)
            return response
        finally:
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)


def make_calculator_executor(observations):
    executor = ToolExecutor()

    def observed_calculator(expression):
        observation = calculator(expression)
        observations.append({"input": expression, "observation": observation})
        return observation

    executor.registerTool(
        "Calculator", "输入纯算术表达式，支持数字、括号和加减乘除。", observed_calculator,
    )
    return executor


def parser_comparison():
    def payload(action="Calculator", value=EXPRESSION):
        return json.dumps({"thought": "调用计算器核对结果", "action": action, "input": value}, ensure_ascii=False)

    fixtures = [
        ("valid_tool", True, f"Thought: 调用计算器\nAction: Calculator[{EXPRESSION}]", payload()),
        ("valid_finish_syntax", True, "Thought: 已取得结果\nAction: Finish[38069.25]", payload("Finish", "38069.25")),
        (
            "multiline_json_layout", True,
            f"Thought: 调用计算器\nAction: Calculator[{EXPRESSION}]",
            json.dumps(json.loads(payload()), ensure_ascii=False, indent=2),
        ),
        (
            "multiline_action_input", True,
            f"Thought: 调用计算器\nAction: Calculator[\n{EXPRESSION}\n]",
            payload(value=f"\n{EXPRESSION}\n"),
        ),
        ("missing_field", False, f"Action: Calculator[{EXPRESSION}]", json.dumps({"action": "Calculator", "input": EXPRESSION})),
        (
            "duplicate_field", False,
            f"Thought: 第一条说明\nThought: 第二条说明\nAction: Calculator[{EXPRESSION}]",
            '{"thought":"第一条说明","thought":"第二条说明","action":"Calculator","input":"' + EXPRESSION + '"}',
        ),
        (
            "trailing_action", False,
            f"Thought: 调用计算器\nAction: Calculator[{EXPRESSION}]\nAction: Finish[38069.25]",
            payload() + '\n' + payload("Finish", "38069.25"),
        ),
        (
            "trailing_prose", False,
            f"Thought: 调用计算器\nAction: Calculator[{EXPRESSION}]\n完成了。",
            payload() + '\n完成了。',
        ),
        ("unknown_tool", False, "Thought: 调用工具\nAction: Unknown[2+3]", payload("Unknown", "2+3")),
        ("empty_input", False, "Thought: 调用计算器\nAction: Calculator[]", payload(value="")),
    ]
    results = []
    for name, expected_valid, text_input, json_input in fixtures:
        for output_format, raw in (("text", text_input), ("json", json_input)):
            agent = ReActAgent(None, make_calculator_executor([]), output_format=output_format)
            result = {
                "case": name,
                "format": output_format,
                "input": raw,
                "expected_valid": expected_valid,
                "parser_accepted": False,
                "dispatch_valid": False,
            }
            try:
                thought, action = agent._parse_output(raw)
                result["parser_accepted"] = bool(thought and action)
                result["parsed_action"] = action
                match = re.fullmatch(r"(\w+)\[([\s\S]+)\]", action or "")
                if thought and match:
                    tool_name, tool_input = match.groups()
                    if tool_name == "Finish":
                        result["dispatch_valid"] = True
                    elif tool_name == "Calculator":
                        observation = calculator(tool_input)
                        result["observation"] = observation
                        result["dispatch_valid"] = not observation.startswith("错误")
            except (ValueError, TypeError):
                pass
            result["matches_expectation"] = result["dispatch_valid"] == expected_valid
            results.append(result)
    return {
        "kind": "fixed_parser_fixtures",
        "note": "固定输入对照。Finish 仅检查语法，完整 run 还要求已有成功工具观察。",
        "cases": results,
        "matching_cases": {
            output_format: sum(item["matches_expectation"] for item in results if item["format"] == output_format)
            for output_format in ("text", "json")
        },
        "cases_per_format": len(fixtures),
    }


def answer_contains_expected_value(answer):
    numbers = re.findall(r"-?\d+(?:\.\d+)?", answer.replace(",", ""))
    return any(Decimal(number) == EXPECTED_VALUE for number in numbers)


def calculator_experiment(client, *, few_shot=False, inject_failures=False):
    injected = ()
    if inject_failures:
        injected = (
            json.dumps({"thought": "人工故障注入，缺少参数", "action": "Calculator"}, ensure_ascii=False),
            json.dumps({"thought": "人工故障注入，未知工具", "action": "UnknownCalculator", "input": EXPRESSION}, ensure_ascii=False),
        )
    recorded = RecordedClient(client, injected)
    observations = []
    agent = ReActAgent(
        recorded, make_calculator_executor(observations), max_steps=6,
        output_format="json", few_shot=few_shot,
    )
    started = time.monotonic()
    result = {
        "kind": "fault_injection" if inject_failures else "live_few_shot_comparison",
        "question": CALCULATOR_QUESTION,
        "few_shot": few_shot,
        "injected_responses": list(injected),
        "expected_value": str(EXPECTED_VALUE),
    }
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            answer = agent.run(CALCULATOR_QUESTION)
        tool_confirmed = any(
            item["observation"] == calculator(EXPRESSION) for item in observations
        )
        result.update({
            "answer": answer,
            "tool_confirmed_expected_value": tool_confirmed,
            "answer_correct": answer_contains_expected_value(answer),
            "completed": True,
        })
    except Exception as error:
        result.update({"completed": False, "error_type": type(error).__name__})
    result.update({
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "calls": recorded.calls,
        "live_model_calls": sum(call["source"] == "live_model" for call in recorded.calls),
        "events": agent.events,
        "calculator_observations": observations,
    })
    if inject_failures:
        first_two_failed = len(agent.events) >= 2 and all(
            event.get("tool_success") is False for event in agent.events[:2]
        )
        result["first_two_injected_calls_rejected"] = first_two_failed
        result["recovered"] = (
            first_two_failed and result.get("completed", False)
            and result.get("tool_confirmed_expected_value", False)
            and result.get("answer_correct", False)
        )
    return result


def role_experiment(client, role):
    recorded = RecordedClient(client)
    agent = ReflectionAgent(recorded, max_iterations=2, reviewer_role=role, initial_code=INITIAL_CODE)
    started = time.monotonic()
    result = {"role": role, "task": PRIME_TASK, "initial_code": INITIAL_CODE}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = agent.run(PRIME_TASK)
            validation = validate_prime_code(code)
        result.update({"completed": True, "final_code": code, "validation": validation})
    except Exception as error:
        result.update({"completed": False, "error_type": type(error).__name__})
    result.update({
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "calls": recorded.calls,
        "stop_reason": agent.stop_reason,
        "records": agent.memory.records,
    })
    return result


def main():
    client = HelloAgentsLLM()
    destination = Path(__file__).resolve().parents[2] / "docs/task4/experiments.json"
    evidence = {
        "started_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "python_version": platform.python_version(),
        "model": client.model,
        "temperature": 0,
        "note": "单次真实模型对照。故障恢复前两条响应为人工注入，其余请求调用相同模型客户端。",
        "limitations": [
            "每个条件只运行一次，样本用于观察执行轨迹。",
            "素数验证覆盖八个参考输入，复杂度描述保留模型原文，另需算法分析或性能测量核对。",
        ],
        "parser_comparison": parser_comparison(),
        "few_shot_comparison": [],
        "reflection_role_comparison": [],
    }

    def save():
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(destination)

    save()
    for few_shot in (False, True):
        print(f"正在运行 few_shot={few_shot} 的真实计算器实验。", flush=True)
        evidence["few_shot_comparison"].append(calculator_experiment(client, few_shot=few_shot))
        save()
    print("正在运行两次明确故障注入后的真实模型恢复实验。", flush=True)
    evidence["fault_recovery"] = calculator_experiment(client, inject_failures=True)
    save()
    for role in ("efficiency", "readability"):
        print(f"正在运行 {role} 角色的真实反思实验。", flush=True)
        evidence["reflection_role_comparison"].append(role_experiment(client, role))
        save()
    evidence["finished_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    save()
    print(f"实验结果已保存到 {destination}", flush=True)


if __name__ == "__main__":
    main()
