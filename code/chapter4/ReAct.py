"""第四章 ReAct，支持课程文本协议和习题要求的 JSON 动作。"""

import argparse
import json
import re

from llm_client import HelloAgentsLLM
from tools import ToolExecutor, calculator, read_paper, search


REACT_PROMPT_TEMPLATE = """
你是一个能够调用外部工具的助手。每轮只选择一个动作。
需要外部事实时先 Search。搜索片段可能出自参考文献，查询论文标题和作者时还须 ReadPaper 读取原论文元数据。需要算术计算时先 Calculator。
工具返回结果在历史中以 Observation 给出。依据观察决定下一步。
工具失败时根据错误改正名称或参数，不要编造成功结果。
收集到实际工具观察后才使用 Finish，最终答案附必要的来源。

可用工具
{tools}

{format_instruction}
{examples}

问题
{question}

历史
{history}
"""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON 字段重复：{key}")
        result[key] = value
    return result


class ReActAgent:
    def __init__(self, llm_client, tool_executor, max_steps=6, output_format="text", few_shot=False):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.output_format = output_format
        self.few_shot = few_shot
        self.history = []
        self.events = []

    def _parse_output(self, text):
        if self.output_format == "json":
            payload = json.loads(text, object_pairs_hook=unique_object)
            if not isinstance(payload, dict) or set(payload) != {"thought", "action", "input"}:
                raise ValueError("JSON 必须且只能含 thought、action、input 三个字符串字段。")
            if not all(isinstance(value, str) and value.strip() for value in payload.values()):
                raise ValueError("三个字段都必须是非空字符串。")
            return payload["thought"], f"{payload['action']}[{payload['input']}]"
        thought = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        action = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        return thought[1].strip() if thought else None, action[1].strip() if action else None

    def run(self, question):
        self.history = []
        self.events = []
        failures = 0
        if self.output_format == "json":
            format_instruction = (
                '只输出一个 JSON 对象，字段为 thought（简短行动说明）、action（工具名或 Finish）、input（字符串参数或最终答案）。'
                '例如 {"thought":"执行计算","action":"Calculator","input":"2+3"}。'
            )
        else:
            format_instruction = (
                "只输出两行。第一行 Thought: 一句简短行动说明。"
                "第二行 Action: 工具名[字符串参数] 或 Action: Finish[最终答案]。"
            )
        examples = ""
        if self.few_shot:
            examples = (
                '示例：问题 2+3。先输出 {"thought":"需要计算","action":"Calculator","input":"2+3"}。'
                '收到 Observation: 5 后输出 {"thought":"已有结果","action":"Finish","input":"5"}。'
                "示例结束，接下来解决实际问题。"
            )
        for step in range(1, self.max_steps + 1):
            print(f"\n--- ReAct 第 {step} 轮 ---", flush=True)
            response = self.llm_client.think([{"role": "user", "content": REACT_PROMPT_TEMPLATE.format(
                tools=self.tool_executor.getAvailableTools(),
                format_instruction=format_instruction, examples=examples,
                question=question, history="\n".join(self.history) or "无",
            )}])
            try:
                thought, action = self._parse_output(response)
                match = re.fullmatch(r"(\w+)\[([\s\S]+)\]", action or "")
                if not thought or not match:
                    raise ValueError("未得到完整的 Thought 和单个 Action。")
                tool_name, tool_input = match.groups()
                if tool_name == "Finish":
                    if not any(event.get("tool_success") for event in self.events):
                        raise ValueError("结束前需要实际工具返回成功观察。")
                    print("Thought: [模型已生成行动说明]")
                    print(f"Action: Finish[{tool_input}]")
                    self.events.append({"step": step, "action": "Finish", "input": tool_input})
                    return tool_input
                tool = self.tool_executor.getTool(tool_name)
                print("Thought: [模型已生成行动说明]")
                print(f"Action: {tool_name}[{tool_input}]")
                observation = tool(tool_input) if tool else f"错误：未登记工具 {tool_name}。"
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                tool_name, tool_input = "Invalid", ""
                observation = f"错误：动作解析或选择失败。{error}"
            succeeded = not observation.startswith("错误")
            failures = 0 if succeeded else failures + 1
            self.events.append({
                "step": step, "action": tool_name, "input": tool_input,
                "observation": observation, "tool_success": succeeded,
            })
            print(f"Observation: {observation}", flush=True)
            self.history.extend([f"Action: {tool_name}[{tool_input}]", f"Observation: {observation}"])
            if failures >= 2:
                correction = (
                    "已连续两次失败。请重新核对工具列表并纠正动作。"
                    "计算器参数应为纯算术表达式，例如 (2+3)*4，"
                    "输出单个动作，使用当前协议要求的字段或格式。"
                )
                print(f"Correction: {correction}")
                self.history.append(correction)
        raise RuntimeError("达到 ReAct 最大轮次，尚未得到 Finish。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--question", default="请搜索 ReAct 原论文的 arXiv 页面，给出论文标题和第一作者，并附来源链接。")
    parser.add_argument("--few-shot", action="store_true")
    args = parser.parse_args()
    executor = ToolExecutor()
    executor.registerTool("Search", "输入检索词，返回真实网页标题、链接和摘要。", search)
    executor.registerTool("ReadPaper", "输入 arxiv.org 论文链接，读取原页面的标题和作者元数据。", read_paper)
    executor.registerTool("Calculator", "输入纯数字算式，可含括号和加减乘除，例如 (2+3)*4。", calculator)
    agent = ReActAgent(HelloAgentsLLM(), executor, output_format=args.format, few_shot=args.few_shot)
    answer = agent.run(args.question)
    print(f"\n任务完成，最终答案 {answer}")


if __name__ == "__main__":
    main()
