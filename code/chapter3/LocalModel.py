"""第三章本地推理，使用已有 Ollama 服务和 Python 标准库。"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from zoneinfo import ZoneInfo


ENDPOINT = "http://127.0.0.1:11434/api/chat"


def generate(prompt: str, options: dict, model: str = "qwen3:0.6b") -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "think": False,
        "stream": False,
        "options": options,
    }
    request = Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
    )
    start = perf_counter()
    with build_opener(ProxyHandler({})).open(request, timeout=180) as response:
        result = json.load(response)
    if not result.get("done") or not result.get("message", {}).get("content", "").strip():
        raise ValueError("模型未返回完整的非空回答。")
    return {
        "model": model,
        "endpoint": ENDPOINT,
        "prompt": prompt,
        "options": options,
        "response": result["message"]["content"],
        "done_reason": result.get("done_reason"),
        "prompt_tokens": result.get("prompt_eval_count"),
        "output_tokens": result.get("eval_count"),
        "elapsed_seconds": round(perf_counter() - start, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3:0.6b")
    parser.add_argument("--prompt", default="请用两句话介绍你自己，并说明语言模型可以怎样帮助学习。")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--output", type=Path, help="可选，保存本次请求设置和最终回答")
    args = parser.parse_args()
    if args.temperature < 0 or not 0 < args.top_p <= 1 or args.top_k < 1 or args.max_tokens < 1:
        parser.error("采样参数或最大输出长度超出有效范围。")
    options = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "seed": args.seed,
        "num_ctx": 4096,
        "num_predict": args.max_tokens,
    }
    print(f"运行时间 {datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')}")
    print(f"本地接口 {ENDPOINT}")
    print(f"模型 {args.model}，think=false")
    print(f"采样设置 {json.dumps(options)}")
    print(f"问题 {args.prompt}", flush=True)
    try:
        record = generate(args.prompt, options, args.model)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        raise SystemExit(f"本地推理失败（{type(error).__name__}）。请检查 Ollama 服务和模型是否已就绪。") from None
    print("\n模型回答")
    print(record["response"])
    print(f"\n完成 {record['done_reason']}，输出 {record['output_tokens']} tokens，耗时 {record['elapsed_seconds']:.3f} 秒")
    if args.output:
        args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
