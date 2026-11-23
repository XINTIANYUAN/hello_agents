"""运行一个第四章范式，保留完整日志并打印可截图的实际循环摘要。"""

import argparse
from contextlib import redirect_stdout
from datetime import datetime
import json
from pathlib import Path
import re
from time import perf_counter
from zoneinfo import ZoneInfo

from llm_client import HelloAgentsLLM
from Experiments import INITIAL_CODE
from Plan_and_solve import PlanAndSolveAgent
from ReAct import ReActAgent
from Reflection import ReflectionAgent, validate_prime_code
from tools import ToolExecutor, calculator, read_paper, search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("react", "plan", "reflection"))
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[2] / "docs/task4"
    destination.mkdir(parents=True, exist_ok=True)
    started = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    record = {"mode": args.mode, "started_at": started}
    client = HelloAgentsLLM()
    record["model"] = client.model
    begin = perf_counter()
    with (destination / f"{args.mode}-full.log").open("w") as log:
        with redirect_stdout(log):
            if args.mode == "react":
                executor = ToolExecutor()
                executor.registerTool("Search", "搜索真实网页，返回标题、链接、摘要。", search)
                executor.registerTool("ReadPaper", "输入 arxiv.org 论文URL，读取标题及作者元数据。", read_paper)
                executor.registerTool("Calculator", "输入括号和加减乘除组成的算式。", calculator)
                agent = ReActAgent(client, executor)
                question = "请搜索 ReAct 原论文，读取 arXiv 元数据，给出英文标题、第一作者英文姓名和来源链接。"
                answer = agent.run(question)
                assert any(event["action"] == "Search" and event.get("tool_success") for event in agent.events)
                assert any(event["action"] == "ReadPaper" and event.get("tool_success") for event in agent.events)
                assert "yao" in answer.lower() and "2210.03629" in answer
                record.update(question=question, answer=answer, events=agent.events)
            elif args.mode == "plan":
                agent = PlanAndSolveAgent(client)
                question = "一个水果店周一卖出了15个苹果。周二是周一的两倍，周三比周二少5个。三天总共卖出多少个苹果？"
                answer = agent.run(question)
                assert re.search(r"(?<!\d)70(?!\d)", answer)
                assert len(agent.plan) == len(agent.executor.results) and agent.plan
                record.update(question=question, answer=answer, plan=agent.plan, steps=agent.executor.results)
            else:
                agent = ReflectionAgent(client, initial_code=INITIAL_CODE)
                record["initial_source"] = "provided_trial_division_baseline"
                task = "编写函数，找出1到n之间的全部素数。初稿用试除法，最终版本要求使用埃拉托斯特尼筛法提高大n时的效率。"
                code = agent.run(task)
                validation = validate_prime_code(code)
                assert validation["passed"]
                assert sum(item["type"] == "execution" for item in agent.memory.records) >= 2
                assert any(item["type"] == "reflection" for item in agent.memory.records)
                record.update(task=task, code=code, validation=validation, records=agent.memory.records, stop_reason=agent.stop_reason)
    record["elapsed_seconds"] = round(perf_counter() - begin, 3)
    record["verified"] = True
    (destination / f"{args.mode}-result.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"Hello-Agents Task4 | {args.mode} | {started}")
    print(f"模型 {client.model}，temperature=0")
    print(f"完整日志 docs/task4/{args.mode}-full.log")
    if args.mode == "react":
        for event in record["events"]:
            print(f"\nRound {event['step']} | Thought: [已生成简短行动说明]")
            print(f"Action: {event['action']}[{event['input']}]")
            if "observation" in event:
                if event["action"] == "Search":
                    print("Observation: 已返回网页，以下节选结果链接。完整摘要见日志。")
                    for line in event["observation"].splitlines():
                        if line.startswith("https://"):
                            print(line)
                else:
                    print(f"Observation: {event['observation']}")
    elif args.mode == "plan":
        print("\nPlan:")
        for index, step in enumerate(record["plan"], 1):
            print(f"  {index}. {step}")
        print("\nSolve:")
        for index, step in enumerate(record["steps"], 1):
            print(f"  {index}. {step['result']}")
        print(f"Finish: {record['answer']}")
    else:
        execution = 0
        for item in record["records"]:
            if item["type"] == "execution":
                execution += 1
                stage = "Initial Execution（预置试除初稿）" if execution == 1 else "Refine（模型实际修订）"
                print(f"\n{stage} | 代码版本 {execution}")
                print(item["content"].splitlines()[0])
            elif item["type"] == "reflection":
                print(f"Reflection: {json.dumps(item['content'], ensure_ascii=False)}")
            elif item["type"] == "validation":
                print(f"Validation: {json.dumps(item['content'])}")
        print(f"Finish: {record['stop_reason']}")
    print(f"\nVerified: PASS | elapsed {record['elapsed_seconds']:.3f} s", flush=True)


if __name__ == "__main__":
    main()
