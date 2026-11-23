"""第四章工具执行器，复用 Tavily 搜索并增加算术计算器。"""

import ast
import math
import operator
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import requests

from tavily import TavilyClient


def search(query: str) -> str:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return "错误：缺少 TAVILY_API_KEY。"
    try:
        response = TavilyClient(api_key=key).search(
            query=query, search_depth="basic", max_results=3, timeout=20,
        )
    except Exception as error:
        return f"错误：搜索失败（{type(error).__name__}）。"
    results = response.get("results", [])
    if not results:
        return "错误：搜索没有返回结果。"
    return "\n\n".join(
        f"{item.get('title', '')}\n{item.get('url', '')}\n{item.get('content', '')[:700]}"
        for item in results
    )


def read_paper(url: str) -> str:
    parts = urlsplit(url)
    match = re.fullmatch(r"/(?:abs|html|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?", parts.path)
    if parts.scheme != "https" or parts.hostname != "arxiv.org" or not match:
        return "错误：请提供 arxiv.org 的论文 abs、html 或 pdf 链接。"
    target = f"https://arxiv.org/abs/{match[1]}"

    class MetadataParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.title = ""
            self.authors = []

        def handle_starttag(self, tag, attributes):
            values = dict(attributes)
            if tag == "meta" and values.get("name") == "citation_title":
                self.title = values.get("content", "")
            if tag == "meta" and values.get("name") == "citation_author":
                self.authors.append(values.get("content", ""))

    try:
        response = requests.get(target, timeout=20)
        response.raise_for_status()
        parser = MetadataParser()
        parser.feed(response.text)
    except (requests.RequestException, ValueError):
        return "错误：读取论文元数据失败。"
    if not parser.title or not parser.authors:
        return "错误：页面未提供完整的标题和作者元数据。"
    return f"Title: {parser.title}\nAuthors: {', '.join(parser.authors)}\nFirst author: {parser.authors[0]}\nSource: {target}"


BINARY_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
}
UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculator(expression: str) -> str:
    if not expression or len(expression) > 200:
        return "错误：请提供不超过 200 字符的算术表达式。"

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            result = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
            result = BINARY_OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
            result = UNARY_OPERATORS[type(node.op)](evaluate(node.operand))
        else:
            raise ValueError("仅支持数字、括号和加减乘除。")
        if not math.isfinite(result) or abs(result) > 1e15:
            raise ValueError("计算结果超出范围。")
        return result

    try:
        tree = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > 100:
            raise ValueError("表达式过于复杂。")
        result = evaluate(tree.body)
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, RecursionError):
        return "错误：表达式无效。仅支持有限数值、括号和加减乘除，除数不能为零。"
    return str(result)


class ToolExecutor:
    def __init__(self):
        self.tools = {}

    def registerTool(self, name, description, func):
        self.tools[name] = {"description": description, "func": func}

    def getTool(self, name):
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self):
        return "\n".join(f"- {name}: {item['description']}" for name, item in self.tools.items())
