完成第五章「基于低代码平台的智能体搭建」的 n8n 本机实操。平台界面实际运行成功，执行记录显示知识库检索与计算器调用，结果为 `38069.25`，已保存实操截图。

- [Task5 中文学习心得](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/reflections.md)
- [Task5 中文课程内容反馈](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/course-feedback.md)
- [Task5 操作过程、踩坑、截图与视频学习笔记](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/learning-notes.md)
- [第五章七道习题解答](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/exercises.md)
- [n8n 平台实操截图](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/n8n-platform-run.jpg)

本次新增本地学习助手工作流、知识资料和导入脚本，以及服务启动脚本。隔离安装 Node.js 24.22.3 与 n8n 2.49.7，复用已有 Ollama 模型。课程邮件案例改为手动合成输入与回复草稿，接入 Qdrant 知识向量、Redis 聊天记忆和计算器，未启用定时对外投递。

n8n、Redis、Qdrant 优雅重启后，知识向量与会话记录校验值保持一致。随后在输入中省略姓名，智能体仍回忆出此前的称呼，并再次检索成功。[真实执行记录](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/execution.json) · [持久化与回忆验证](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/persistence-check.json)

保留第一至第四章的 16 个代码与配置文件，内容与 v1.4 一致，已有 Python 环境通过 `pip check`。本机密码、API Key、安装目录、模型权重及数据库未提交。

[视频画面学习记录](https://github.com/XINTIANYUAN/hello_agents/blob/v1.5/docs/task5/video-study.md)依据社区 EP5 覆盖整段时间轴的公开预览图及画面字幕整理，注明实际核看范围；官方小红书入口本次未能读取，未宣称完整播放或听完视频。习题中的定时投递、附件处理、电商流程和 Dify 插件为设计解答，实操范围与设计方案分别标明。
