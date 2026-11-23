"""第四章共享模型客户端，兼容 Task1 的项目根目录配置。"""

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


class HelloAgentsLLM:
    def __init__(self, model=None, apiKey=None, baseUrl=None, timeout=None):
        load_dotenv(Path(__file__).resolve().parents[2] / ".env", interpolate=False)
        self.model = model or os.getenv("LLM_MODEL_ID") or os.getenv("MODEL_NAME")
        api_key = apiKey or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = baseUrl or os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        if not all((self.model, api_key, self.base_url)):
            raise ValueError("请在项目 .env 中配置模型、接口根地址和访问凭证。")
        self.client = OpenAI(
            api_key=api_key, base_url=self.base_url,
            timeout=timeout or 120, max_retries=0,
        )

    def think(self, messages, temperature=0):
        kwargs = {}
        if urlsplit(self.base_url).hostname in {"127.0.0.1", "localhost"}:
            kwargs["reasoning_effort"] = "none"
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "遵守指定格式。行动说明只用一句简短文字，直接给出结果、代码或可操作反馈。",
                }, *messages],
                temperature=temperature,
                max_tokens=1600,
                stream=False,
                **kwargs,
            )
        except OpenAIError as error:
            status = getattr(error, "status_code", None) or type(error).__name__
            raise RuntimeError(f"模型请求失败（{status}）。请检查接口、模型和网络。") from None
        content = response.choices[0].message.content if response.choices else None
        if not content or not content.strip():
            raise RuntimeError("模型未返回有效文本。")
        return content.strip()
