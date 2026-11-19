"""习题 4：采样参数和三种提示方式的小规模对照实验。"""

import json
import re
from pathlib import Path

from LocalModel import generate


def main() -> None:
    output_dir = Path(__file__).resolve().parents[2] / "docs/task3"
    sampling = []
    prompt = "给一个教 Python 的机器人起三个中文名字，只输出名字，用顿号隔开。"
    for temperature, top_p, top_k in ((0.2, 0.8, 20), (1.0, 0.95, 40)):
        for seed in (11, 22, 33):
            record = generate(prompt, {
                "temperature": temperature, "top_p": top_p, "top_k": top_k,
                "seed": seed, "num_ctx": 4096, "num_predict": 100,
            })
            sampling.append(record)
            print(f"采样 T={temperature}, top_p={top_p}, top_k={top_k}, seed={seed}")
            print(record["response"], flush=True)
    (output_dir / "sampling-results.json").write_text(json.dumps(sampling, ensure_ascii=False, indent=2) + "\n")

    task = (
        "对电商反馈做情感分类，label 必须为正面、负面、中性之一。"
        '输出一个 JSON 对象，包含 label 和一句简短判定依据 reason。\n'
    )
    strategies = {
        "Zero-shot": "",
        "Few-shot": (
            '示例：物美价廉，下次还来。 -> {"label":"正面","reason":"表达认可和复购意愿"}\n'
            '示例：商品损坏了，我很失望。 -> {"label":"负面","reason":"表达不满"}\n'
            '示例：请问订单能改地址吗？ -> {"label":"中性","reason":"提出业务问题"}\n'
        ),
        "CoT-style": "请核对情感词、否定词和转折所指向的态度，再给出一句判定依据和最终标签。\n",
    }
    samples = (
        ("物流很快，包装也完整。", "正面"),
        ("客服一直不回复，问题到现在也没解决。", "负面"),
        ("订单显示明天送达，我想查询运单号。", "中性"),
        ("并不是不满意，我很喜欢这个商品。", "正面"),
    )
    results = []
    for strategy, instruction in strategies.items():
        for text, expected in samples:
            record = generate(task + instruction + "待分类反馈：" + text, {
                "temperature": 0.2, "top_p": 0.8, "top_k": 20,
                "seed": 42, "num_ctx": 4096, "num_predict": 150,
            })
            match = re.search(r"\{.*\}", record["response"], re.DOTALL)
            try:
                parsed = json.loads(match[0]) if match else {}
            except json.JSONDecodeError:
                parsed = {}
            predicted = parsed.get("label")
            record.update(
                strategy=strategy, input=text, expected=expected,
                predicted=predicted, correct=predicted == expected,
            )
            results.append(record)
            print(f"{strategy} | {text} | 预期 {expected} | 预测 {predicted}", flush=True)
    (output_dir / "prompt-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print("实验结果已保存。")


if __name__ == "__main__":
    main()
