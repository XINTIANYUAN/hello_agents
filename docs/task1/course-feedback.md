# Task1 课程内容反馈

## 值得保留的设计

第一章先解释智能体的任务环境和运行循环，再把它落实成一个可阅读的 Python 脚本。天气与景点之间存在清楚的依赖关系，容易观察外部工具如何改变下一步决策。Extra07 的独立连通性检查也适合新手排查，让天气、Tavily 和模型服务都可以单独验证。 [第一章 初识智能体](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md) · [Extra07 环境配置](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md)

## 建议改进的地方

- **让 `.env` 与脚本使用同一套变量。** Extra07 推荐配置 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL_NAME` 和 `TAVILY_API_KEY`。配套脚本启动时会使用 `YOUR_*` 占位符，并覆盖进程里的 `TAVILY_API_KEY`。可以提供 `.env.example`，在脚本启动时显式读取环境变量，并在缺项时提示变量名。排查示例可以只输出凭证是否已配置，避免把完整密钥留在终端记录里。 [Extra07 环境变量配置](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md#43-环境变量配置) · [FirstAgentTest.py](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter1/FirstAgentTest.py)
- **给安装命令加引号或提供依赖文件。** 在 macOS 的 zsh 中，`pip install requests>=2.31.0` 中的 `>` 会被解释为输出重定向。文档可以改成 `python -m pip install 'requests>=2.31.0'`，或为第一章提供 `requirements.txt` 并使用 `python -m pip install -r requirements.txt`。用 `python -m pip` 也更方便确认安装动作对应当前虚拟环境里的解释器。 [Extra07 安装依赖包](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md#42-安装依赖包)
- **把成功示例和验收条件一起给出。** 终端里的 `Observation` 也可能是一条错误信息。更易核对的打卡条件是先看到天气工具返回天气和气温，再看到景点搜索返回结果，最后用 `Action: Finish[...]` 结束。可以补充一段短的失败示例，让学员练习区分模型认证问题、工具连接问题和 `Action` 格式问题。 [第一章运行案例分析](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md#134-运行案例分析) · [Extra07 运行验证](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra07-%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md#六运行验证)
