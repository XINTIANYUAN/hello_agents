# Task1 学习笔记 · 前言与环境配置

## 读了哪些内容

- 前言介绍了课程从智能体和语言模型基础、经典范式到多智能体实践的安排。Task1 对应的是第一次运行智能体的练习。[前言](https://github.com/datawhalechina/hello-agents/blob/main/docs/%E5%89%8D%E8%A8%80.md)
- 第一章第 1.3 节用旅行助手展示感知和行动的循环。模型提出下一步行动，Python 调用工具，把结果作为 `Observation` 加回提示，再发起下一轮模型请求。[第一章](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md)
- Extra07 提供 Python、虚拟环境、模型 API 和 Tavily 的配置步骤。[Extra07 环境配置](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md)
- Python 前置课程 Chap 0–6 可以对应到示例代码。依赖安装对应入门环境，字典用于保存工具和参数，函数封装网络请求，条件语句处理不同 Action，`for` 限制循环次数，字符串和正则表达式用于构造提示、提取参数。[Python 前置课程](https://datawhalechina.github.io/learn-python-the-smart-way-v2/Schedule/schedule/)

## 操作过程

1. 检查本机可用的 Python 版本。默认命令指向 Python 3.15.2，使用 pyenv 已安装的 Python 3.11.17 创建项目内的 `.venv`，使课程依赖与其他项目隔离。
2. 在虚拟环境里安装 `openai`、`requests`、`tavily-python` 和 `python-dotenv`，将实测的直接依赖版本写入 [requirements.txt](../../requirements.txt)。
3. 检查上游 `FirstAgentTest.py` 的配置加载，将原有占位值替换为从项目根目录加载的 `.env` 配置。将四个变量名放入 [模板](../../.env.example)，将本地配置加入 Git 忽略规则。
4. 第一次使用已有云端模型配置，请求返回 HTTP 402。启动本机已安装的 Ollama，将接口地址切换为 `http://127.0.0.1:11434/v1`，模型切换为已缓存的 `qwen3.5:4b`，并为 SDK 填入本地占位值 `ollama`。[Ollama 接口文档](https://docs.ollama.com/api/openai-compatibility)
5. 使用虚拟环境的 Python 运行第一章脚本，分别检查模型接口、天气工具和景点搜索的输出。

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python code/chapter1/FirstAgentTest.py
```

## 实际运行记录

2026 年 11 月 16 日在 macOS 和 Python 3.11.17 下复跑。模型由本机 Ollama 提供，天气与景点分别来自 wttr.in 和 Tavily 的实时请求。下表摘录终端观察结果，省略模型的行动计划原文。

| 轮次 | Action | Observation 或结束结果 |
| --- | --- | --- |
| 1 | `get_weather(city="Beijing")` | 天气工具返回 `Cloudy`、7°C。 |
| 2 | `get_attraction(city="Beijing", weather="Cloudy")` | Tavily 返回故宫博物院、中国国家博物馆等景点候选。 |
| 3 | `Finish[...]` | 模型将多云和 7°C 写入最终回答，只推荐故宫博物院。 |

复跑时依次观察到三轮 `Thought` 和 `Action`，前两轮有非错误 `Observation`，第三轮输出「任务完成，最终答案」。进程退出码为 `0`，`python -m pip check` 也通过。天气和推荐是这一次运行的结果。

## 踩坑与排查

| 问题 | 处理方式 |
| --- | --- |
| Extra07 推荐 `.env`，原始脚本使用 `YOUR_*` 占位值，并覆盖 `TAVILY_API_KEY` | 脚本读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL_NAME` 和 `TAVILY_API_KEY`。缺少配置时会列出变量名。 |
| zsh 会把未加引号的 `>` 解释成重定向 | 使用 `python -m pip install -r requirements.txt`，或为单个依赖的版本约束加引号。 |
| 云端模型请求返回 HTTP 402 | 检查服务侧额度或账单状态，也可以把模型接口换为本机 Ollama。 |
| 终端命令可以指向其他 Python 或 pip | 用项目虚拟环境的解释器运行 `python -m pip check` 和脚本，也可以直接使用 `.venv/bin/python`。 |
| 首次本地运行把景点搜索摘要里的「雨天」带入回答 | 在提示中明确当前天气以天气工具为准，景点摘要只用于选择景点。复跑保留了多云、7°C，并按用户要求给出一个景点。 |
| 模型可能在工具报错后仍输出 `Finish` | 查看两轮 `Observation` 的实际内容和动作顺序，同时确认任务完成行及进程退出码。 |
| 检查环境变量时可能在终端或截图里暴露密钥 | 使用 `git check-ignore .env` 检查忽略规则。排查配置时只检查变量名和是否已填写。 |

## 对循环的理解

天气结果既是第一轮的输出，也是第二轮景点工具的输入。把两轮行动和工具结果连起来看，才能判断推荐是否基于环境数据。模型负责提出工具调用和终止动作，Python 负责解析动作、执行已登记的工具并回填结果。对初学者来说，先弄清这两个角色，调试时就能分辨问题发生在模型回复格式、工具网络请求，还是上下文里缺少上一步结果。
