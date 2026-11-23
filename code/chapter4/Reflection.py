"""第四章生成、评审、优化循环，附素数函数的外部验证。"""

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from llm_client import HelloAgentsLLM
from ReAct import unique_object


INITIAL_PROMPT_TEMPLATE = """
请实现 find_primes(n: int) -> list[int]，返回1到n（含n）全部素数。
初稿先使用清楚的试除法，含 n<2 的边界处理、文档字符串和可读变量名。
只用 Python 内置能力，直接输出完整函数代码，不输出解释或调用示例。
任务补充：{task}
"""
REVIEW_ROLES = {
    "efficiency": "你是严格的算法效率评审员。检查正确性和时间复杂度，比较试除与筛法。",
    "readability": "你是注重可读性的开源项目维护者。检查命名、文档、边界处理和维护成本。",
}
REFLECT_PROMPT_TEMPLATE = """
{role}
审查 find_primes 实现。只输出一个 JSON 对象，字段 needs_revision 为布尔值，
feedback 为一段简短、具体且可执行的反馈。只有确实达到当前角色的目标时才给 false。
任务：{task}
实际函数验证：{validation}
代码：
{code}
"""
REFINE_PROMPT_TEMPLATE = """
根据评审反馈优化 find_primes，保留1到n（含n）的全部素数及n<2返回空列表的语义。
只使用 Python 内置能力。直接输出完整函数代码，含文档字符串，不输出其他文字。
任务：{task}
上一版：
{code}
评审反馈：
{feedback}
"""


def clean_code(text):
    match = re.fullmatch(r"\s*\x60\x60\x60(?:python)?\s*\n([\s\S]*?)\x60\x60\x60\s*", text)
    return match[1].strip() if match else text.strip()


def validate_prime_code(code):
    """在独立进程中检查限定纯函数及八个参考输入。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"passed": False, "error": "语法错误"}
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    allowed_calls = functions | {"range", "len", "list", "int", "float", "enumerate", "min", "max", "sum", "abs", "all", "any", "set", "tuple", "isinstance", "TypeError", "ValueError"}
    if "find_primes" not in functions:
        return {"passed": False, "error": "缺少 find_primes"}
    if any(not isinstance(node, (ast.FunctionDef, ast.Expr)) for node in tree.body):
        return {"passed": False, "error": "顶层仅允许函数和文档"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef)):
            return {"passed": False, "error": "代码超出本练习的纯函数范围"}
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return {"passed": False, "error": "不支持的标识符"}
        if isinstance(node, ast.Attribute) and node.attr not in {"append", "extend"}:
            return {"passed": False, "error": "不支持的属性访问"}
        if isinstance(node, ast.Call):
            valid_name = isinstance(node.func, ast.Name) and node.func.id in allowed_calls
            valid_method = isinstance(node.func, ast.Attribute) and node.func.attr in {"append", "extend"}
            if not (valid_name or valid_method):
                return {"passed": False, "error": "不支持的函数调用"}
    checker = """
import json
from math import isqrt
values = (-3, 0, 1, 2, 3, 10, 30, 100)
for n in values:
    expected = [x for x in range(2, n + 1) if all(x % d for d in range(2, isqrt(x) + 1))]
    assert find_primes(n) == expected, n
assert find_primes(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
print(json.dumps({"passed": True, "cases": len(values)}))
"""
    with tempfile.TemporaryDirectory(prefix="hello-agents-primes-") as directory:
        file = Path(directory) / "check.py"
        file.write_text(code + "\n" + checker)
        try:
            result = subprocess.run(
                [sys.executable, "-I", str(file)], capture_output=True, text=True, timeout=8,
            )
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "验证超时"}
        if result.returncode:
            return {"passed": False, "error": "参考输入验证失败"}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"passed": False, "error": "验证未产生有效结果"}


class Memory:
    def __init__(self):
        self.records = []

    def add_record(self, record_type, content):
        self.records.append({"type": record_type, "content": content})

    def get_last_execution(self):
        return next((record["content"] for record in reversed(self.records) if record["type"] == "execution"), None)

    def get_trajectory(self):
        return "\n".join(f"{record['type']}: {record['content']}" for record in self.records)


class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=2, reviewer_role="efficiency", initial_code=None):
        if reviewer_role not in REVIEW_ROLES:
            raise ValueError("未知评审角色")
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.reviewer_role = reviewer_role
        self.initial_code = initial_code
        self.memory = Memory()
        self.stop_reason = None

    def _get_llm_response(self, prompt):
        return self.llm_client.think([{"role": "user", "content": prompt}])

    def run(self, task):
        self.memory = Memory()
        self.stop_reason = None
        print("--- Initial Execution 初稿 ---", flush=True)
        code = self.initial_code
        if code is None:
            code = clean_code(self._get_llm_response(INITIAL_PROMPT_TEMPLATE.format(task=task)))
        self.memory.add_record("execution", code)
        print(code)
        for iteration in range(1, self.max_iterations + 1):
            validation = validate_prime_code(code)
            self.memory.add_record("validation", validation)
            print(f"Validation: {json.dumps(validation)}")
            print(f"--- Reflection 第 {iteration} 轮，角色 {self.reviewer_role} ---", flush=True)
            feedback = json.loads(self._get_llm_response(REFLECT_PROMPT_TEMPLATE.format(
                role=REVIEW_ROLES[self.reviewer_role], task=task,
                validation=validation, code=code,
            )), object_pairs_hook=unique_object)
            if (
                not isinstance(feedback, dict)
                or set(feedback) != {"needs_revision", "feedback"}
                or type(feedback["needs_revision"]) is not bool
                or not isinstance(feedback["feedback"], str)
                or not feedback["feedback"].strip()
            ):
                raise ValueError("评审未返回有效的结构化反馈")
            self.memory.add_record("reflection", feedback)
            print(f"Feedback: {json.dumps(feedback, ensure_ascii=False)}")
            if not feedback["needs_revision"] and validation["passed"]:
                self.stop_reason = "review_passed"
                break
            print("--- Refine 优化 ---", flush=True)
            code = clean_code(self._get_llm_response(REFINE_PROMPT_TEMPLATE.format(
                task=task, code=code, feedback=feedback["feedback"],
            )))
            self.memory.add_record("execution", code)
            print(code)
        final_validation = validate_prime_code(code)
        self.memory.add_record("validation", final_validation)
        if not final_validation["passed"]:
            raise RuntimeError(f"最终生成代码未通过验证：{final_validation}")
        self.stop_reason = self.stop_reason or "iteration_limit"
        print(f"Final Validation: {json.dumps(final_validation)}")
        print(f"任务完成，停止原因 {self.stop_reason}")
        return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer", choices=REVIEW_ROLES, default="efficiency")
    args = parser.parse_args()
    agent = ReflectionAgent(HelloAgentsLLM(), reviewer_role=args.reviewer)
    agent.run("编写一个Python函数，找出1到n之间所有的素数。初稿用试除法，最终优化为埃拉托斯特尼筛法。")


if __name__ == "__main__":
    main()
