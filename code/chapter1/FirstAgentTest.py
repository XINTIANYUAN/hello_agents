# 改编自 Datawhale Hello-Agents 第一章，见仓库 README 与 LICENSE.txt。
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from tavily import TavilyClient


AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action 可以直接调用工具，例如 Action: get_weather(city="北京")。
收集到所需信息后，使用 Action: Finish[最终答案] 结束。

# 重要提示:
- 每次只输出一对Thought-Action
- 工具调用必须写在同一行，从工具名开始，直接填写命名参数。不要添加 function_name= 或 Markdown 标记。
- 调用 get_attraction 时，把 get_weather 返回的天气描述原样填入 weather 参数。
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束
- 当前天气以 get_weather 返回的天气和气温为准。景点搜索摘要只用于选择景点。
- 最终答案用一到两句中文说明天气和气温，只推荐一个景点并给出理由。

请开始吧！
"""


def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    # API端点，我们请求JSON格式的数据
    url = f"https://wttr.in/{city}"

    try:
        # 发起网络请求
        response = requests.get(url, params={"format": "j1"}, timeout=15)
        # 检查响应状态码是否为200 (成功)
        response.raise_for_status()
        # 解析返回的JSON数据
        data = response.json()

        # 提取当前天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        # 格式化成自然语言返回
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError, TypeError, ValueError) as e:
        # 处理数据解析错误
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """

    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"].strip())

    # 构造景点搜索的查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # include_answer=True 会返回一个综合性的回答
        response = tavily.search(query=query, search_depth="basic", include_answer=True, timeout=20)

        # 优先使用搜索结果摘要。
        if response.get("answer"):
            return response["answer"]

        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：Tavily 搜索失败（{type(e).__name__}），请检查密钥、额度和网络。"


# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=60, max_retries=0)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content if response.choices else None
        except OpenAIError as error:
            status = getattr(error, "status_code", None)
            detail = f"HTTP {status}" if status else type(error).__name__
            raise SystemExit(f"模型请求失败（{detail}），请检查接口地址、模型 ID、密钥和额度。") from None
        if not answer:
            raise SystemExit("模型响应没有可解析的文本。请检查模型是否支持 Chat Completions。")
        print("大语言模型响应成功。")
        return answer


def main():
    # 从项目根目录读取配置，与当前工作目录无关。已有环境变量优先。
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", interpolate=False)
    config = {
        name: os.getenv(name, "").strip()
        for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL_NAME", "TAVILY_API_KEY")
    }
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise SystemExit(f"缺少配置 {', '.join(missing)}。请参照项目根目录的 .env.example。")
    base_url = urlsplit(config["OPENAI_BASE_URL"])
    if base_url.scheme not in {"http", "https"} or not base_url.hostname:
        raise SystemExit("OPENAI_BASE_URL 应填写服务提供商的 HTTP 或 HTTPS 接口根地址。")

    llm = OpenAICompatibleClient(
        model=config["MODEL_NAME"],
        api_key=config["OPENAI_API_KEY"],
        base_url=config["OPENAI_BASE_URL"],
    )

    # 初始化用户输入和历史记录
    user_prompt = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
    prompt_history = [f"用户请求: {user_prompt}"]

    print(f"用户输入: {user_prompt}\n" + "=" * 40)

    # 循环最多执行五轮
    for i in range(5):
        print(f"--- 循环 {i + 1} ---\n")

        # 3.1. 构建Prompt
        full_prompt = "\n".join(prompt_history)

        # 3.2. 调用LLM进行思考
        llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
        # 模型可能会输出多余的Thought-Action，需要截断
        match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
                print("已截断多余的 Thought-Action 对")
        print(f"模型输出:\n{llm_output}\n")
        prompt_history.append(llm_output)

        # 3.3. 解析并执行行动
        action_match = re.search(r"^[ \t]*Action:[ \t]*([^\n]+)", llm_output, re.MULTILINE)
        if not action_match:
            observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
            observation_str = f"Observation: {observation}"
            print(f"{observation_str}\n" + "=" * 40)
            prompt_history.append(observation_str)
            continue
        action_str = action_match.group(1).strip()

        # 最终答案可以有换行，工具调用仍按单行解析。
        finish_text = llm_output[action_match.start(1):].strip()
        finish_match = re.fullmatch(r"Finish\[(.+)\]", finish_text, re.DOTALL)
        if finish_match:
            print(f"任务完成，最终答案: {finish_match.group(1)}")
            return

        tool_match = re.fullmatch(r"(\w+)\((.*)\)", action_str)
        if tool_match:
            tool_name, args_str = tool_match.groups()
            kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))
            if tool_name in available_tools:
                try:
                    observation = available_tools[tool_name](**kwargs)
                except TypeError:
                    observation = f"错误：工具 '{tool_name}' 的参数不符合要求。"
            else:
                observation = f"错误：未定义的工具 '{tool_name}'"
        else:
            observation = "错误：请使用约定的工具调用或 Finish[最终答案] 格式。"

        # 3.4. 记录观察结果
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)

    raise SystemExit("达到最大循环次数，智能体未返回 Finish。")


if __name__ == "__main__":
    main()
