# Hello-Agents 入门实践

Datawhale《从零开始构建智能体》的前五章实践。第一章用模型和工具搭建旅行助手。第二章通过 ELIZA 对照规则匹配、代词转换和会话记忆。第三章部署轻量模型并比较生成参数和提示。第四章实现 ReAct、Plan-and-Solve 和 Reflection 循环。第五章在本机 n8n 搭建带知识检索、计算器和持久化记忆的学习助手。

## 第一章安装和运行

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

## 第二章运行 ELIZA

在仓库根目录使用已有的虚拟环境或本地 Python 3.10 及以上版本。两个示例只用标准库，输入 `bye` 结束对话。

```bash
python code/chapter2/ELIZA.py
python code/chapter2/ELIZAExtended.py
```

## 第三章本地模型

沿用已有 Ollama 服务，在项目根目录使用 Python 运行。默认模型是习题推荐的 Qwen3-0.6B，对应 Ollama 包 `qwen3:0.6b`。

```bash
ollama pull qwen3:0.6b
python code/chapter3/LocalModel.py
python code/chapter3/N_gram.py
python code/chapter3/BPE.py
```

`python code/chapter3/Experiments.py` 会运行采样和提示对比，并把结果写入 `docs/task3/`。生成结果随模型版本、硬件和采样设置变化。

## 第四章三种经典范式

使用 Task1 已有环境和项目根目录的配置，可直接运行并保存本次验证记录。

```bash
python code/chapter4/Demo.py react
python code/chapter4/Demo.py plan
python code/chapter4/Demo.py reflection
```

ReAct 使用本机模型、Tavily 搜索和 arXiv 页面。Plan-and-Solve 运行苹果应用题，Reflection 生成并验证素数函数。独立入口为同目录的 `ReAct.py`、`Plan_and_solve.py`、`Reflection.py`。`Experiments.py` 可复现动作解析、计算器恢复及提示对照，并写入 `docs/task4/experiments.json`。

## 第五章 n8n 低代码智能体

本机实操使用项目专用 Node.js 24.22.3 和 n8n 2.49.7，复用 Ollama 的 `qwen3.5:4b`。知识检索使用 Qdrant 与 `nomic-embed-text`，对话记忆使用启用 AOF 的 Redis。已有本机配置保存在 Git 忽略的 `.task5-local/` 中，安装目录为 `.task5-runtime/`。

```bash
.venv/bin/python code/chapter5/start-services.py
.venv/bin/python code/chapter5/start-services.py --status
```

启动后访问 [本机 n8n](http://localhost:5685)。在本机查看 `.task5-local/n8n-owner.json` 获取学习实例的登录信息。工作流 [task5-agent.json](code/chapter5/task5-agent.json) 可以导入 n8n，绑定本机 Ollama、Redis、Qdrant 三份凭证后，点击 Execute。`Test Input` 节点可修改问题与会话标识。重复演示工具调用时使用新的 `sessionId`，避免模型直接沿用旧答复。

首次在其他机器部署时，需要安装对应运行时、建立本机凭证和服务配置，再按[学习笔记](docs/task5/learning-notes.md)导入。仓库不包含模型权重、数据库、密码和安装目录。

## 学习记录

### Task5 · 第五章 基于低代码平台的智能体搭建

- [学习心得](docs/task5/reflections.md) · [课程内容反馈](docs/task5/course-feedback.md)
- [操作过程、踩坑、截图与视频学习笔记](docs/task5/learning-notes.md) · [七道习题解答](docs/task5/exercises.md)
- [n8n 平台实操截图](docs/task5/n8n-platform-run.jpg) · [真实执行记录](docs/task5/execution.json) · [重启持久化与记忆验证](docs/task5/persistence-check.json)

### Task4 · 第四章 智能体经典范式构建

- [学习心得](docs/task4/reflections.md) · [课程内容反馈](docs/task4/course-feedback.md)
- [操作过程、踩坑、截图与视频学习笔记](docs/task4/learning-notes.md) · [七道习题解答](docs/task4/exercises.md)
- [ReAct 截图](docs/task4/react-terminal.png) · [Plan-and-Solve 截图](docs/task4/plan-terminal.png) · [Reflection 截图](docs/task4/reflection-terminal.png)

### Task3 · 第三章 大语言模型基础

- [学习心得](docs/task3/reflections.md) · [课程内容反馈](docs/task3/course-feedback.md)
- [操作过程、踩坑、实验与视频学习笔记](docs/task3/learning-notes.md) · [六道习题解答](docs/task3/exercises.md)
- [本地模型终端截图](docs/task3/local-model-terminal.png) · [完整终端日志](docs/task3/local-model-terminal.txt)

### Task2 · 第二章 智能体发展史

- [学习心得](docs/task2/reflections.md) · [课程内容反馈](docs/task2/course-feedback.md)
- [操作过程、踩坑、视频学习与笔记](docs/task2/learning-notes.md) · [章末七道习题解答](docs/task2/exercises.md)

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

`code/chapter2/ELIZA.py` 来自 Datawhale 同一版本的第二章配套代码。`ELIZAExtended.py` 在其规则之上增加话题匹配与会话记忆，两份文件沿用仓库的 CC BY-NC-SA 4.0 许可。[第二章上游代码](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/code/chapter2/ELIZA.py)

`code/chapter3/N_gram.py` 和 `BPE.py` 来自上述上游版本。`LocalModel.py`、`Experiments.py` 为本章习题实践，使用 Ollama 运行本机模型。模型权重许可见其发布页面，仓库代码与学习材料沿用 CC BY-NC-SA 4.0。[第三章上游代码](https://github.com/datawhalechina/hello-agents/tree/2eb1c7547018b519b85cb57acf5533f12d65bf8e/code/chapter3) · [Qwen3 模型许可](https://huggingface.co/Qwen/Qwen3-0.6B)

`code/chapter4/` 改编自同一上游版本的第四章范式示例。本项目兼容已有配置、复用 Tavily、增加论文元数据和计算器工具，补充结构化动作、错误反馈及素数函数验证。保留教学中的三类循环，源码和笔记沿用 CC BY-NC-SA 4.0。[第四章上游代码](https://github.com/datawhalechina/hello-agents/tree/2eb1c7547018b519b85cb57acf5533f12d65bf8e/code/chapter4)

课程材料可在线阅读。[课程仓库](https://github.com/datawhalechina/hello-agents) · [在线阅读](https://datawhalechina.github.io/hello-agents/#/) · [国内加速](https://hello-agents.datawhale.cc/) · [Extra07 环境配置](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md)

`code/chapter5/task5-agent.json` 为依据第五章 n8n 案例重新搭建的本地学习工作流，将邮件输入改为手动合成输入、回复改为草稿，将内存知识库和聊天记忆替换为 Qdrant 与 Redis，并复用本机 Ollama。`knowledge.json` 是依据课程与本次任务要求整理的三条学习资料，配套脚本用于本机服务启动和知识索引。课程改编与学习材料继续沿用 CC BY-NC-SA 4.0；n8n、Redis、Qdrant 和模型自身许可见各自发布页面。[第五章原文与案例](https://github.com/datawhalechina/hello-agents/tree/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter5)
