# Hello-Agents 入门实践

Datawhale《从零开始构建智能体》的第一章实践。示例会查询北京当前天气，把天气作为参数交给景点搜索工具，再根据工具返回的信息给出一条旅行建议。

## 安装和运行

Extra07 的 Python 要求为 3.10 或以上。本项目在 macOS 上使用 Python 3.11.17 验证。运行需要能访问兼容 OpenAI Chat Completions 的模型接口、wttr.in 和 Tavily。

```bash
git clone https://github.com/XINTIANYUAN/hello_agents.git
cd hello_agents
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
chmod 600 .env
```

编辑项目根目录的 `.env`，填写 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL_NAME` 和 `TAVILY_API_KEY`。接口根地址通常以 `/v1` 结尾，具体路径以服务商文档为准。脚本优先使用当前进程已有的同名环境变量。Git 会忽略 `.env`，提交时请使用空白模板 `.env.example`。

如果使用本地 Ollama，请先启动服务并确认已安装 `qwen3.5:4b`。在 `.env` 中将 `OPENAI_BASE_URL` 填为 `http://127.0.0.1:11434/v1`，将 `MODEL_NAME` 填为 `qwen3.5:4b`，将 `OPENAI_API_KEY` 填为 SDK 所需的占位值 `ollama`。景点搜索仍需有效的 `TAVILY_API_KEY`。[Ollama 接口文档](https://docs.ollama.com/api/openai-compatibility)

```bash
python code/chapter1/FirstAgentTest.py
```

验收时先看 `get_weather` 的 `Observation` 是否包含天气和温度，再检查 `get_attraction` 是否收到该天气并返回景点信息。最后确认出现 `Action: Finish[...]` 和「任务完成，最终答案」。天气、景点与回答措辞会随运行时间和服务返回而变化。

## 学习记录

### Task1.1 · 第一章 初识智能体

- [学习心得](docs/task1.1/reflections.md) · [课程内容反馈](docs/task1.1/course-feedback.md)
- [操作过程、踩坑与学习笔记](docs/task1.1/learning-notes.md)
- [第一章习题解答](docs/task1.1/exercises.md) · [第 1.3 节运行截图](docs/task1.1/task1.1-run.png) · [中文操作演示](https://github.com/XINTIANYUAN/hello_agents/releases/download/v1.1/task1.1-demo.mp4)

### Task1 · 前言与环境配置

- [Task1 学习心得](docs/task1/reflections.md)
- [Task1 课程内容反馈](docs/task1/course-feedback.md)
- [Task1 操作过程、踩坑与学习笔记](docs/task1/learning-notes.md)

## 来源和许可

`code/chapter1/FirstAgentTest.py` 改编自 Datawhale Hello-Agents 贡献者的第一章示例，源版本为 `2eb1c7547018b519b85cb57acf5533f12d65bf8e`。本项目将硬编码配置改为读取环境变量，增加网络超时和本地配置检查，改进模型调用失败及 Action 格式错误时的提示，并明确工具调用语法和天气观察的用法。上游及本改编沿用 CC BY-NC-SA 4.0。[上游代码](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/code/chapter1/FirstAgentTest.py) · [许可证](LICENSE.txt)

课程材料可在线阅读。[课程仓库](https://github.com/datawhalechina/hello-agents) · [在线阅读](https://datawhalechina.github.io/hello-agents/#/) · [国内加速](https://hello-agents.datawhale.cc/) · [Extra07 环境配置](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md)
