# Task5 学习心得

第五章把前面用 Python 表达的调用顺序、工具选择和状态传递放到了画布上。阅读节点时，我会先确认输入来自哪里、字段是什么类型，再看它怎样处理数据、输出交给谁。模型节点处理语言与判断，工具节点取得信息或执行操作，连线和分支决定程序怎样推进。这样看一张工作流，才能把画布上的配置和实际执行对应起来。 [第五章 基于低代码平台的智能体搭建](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E8%83%BD%E4%BD%93%E6%90%AD%E5%BB%BA.md)

| 课程案例 | 主要的数据流 | 我会关注的检查点 |
| --- | --- | --- |
| Coze 每日 AI 简报 | RSS、GitHub 和 arXiv 数据进入汇总节点，生成带链接的条目 | 新闻的日期、重复条目、原始链接，以及实际可用条目数 |
| Dify 个人助手 | 问题分类后进入对应模块，调用模型或工具并返回结果 | 分类是否符合请求、分支是否取到了正确变量、工具返回值是否被完整使用 |
| FastGPT 知识库助手 | 文档分块与索引后，检索相关内容，再生成答复 | 检索命中的片段是否能支撑回答，缺少材料时如何说明 |
| n8n 邮件助手 | 邮件触发流程，模型读取知识和工具结果，再组织回复 | 邮件字段映射、会话标识、工具执行状态和最终输出 |

这四个案例都需要建立「输入内容、节点结果、最终结论」之间的对应关系。例如，Coze 简报里的新闻日期可以回到抓取结果核对，Dify 数据查询后的总结可以逐项对照原始数值，n8n 回复里使用的工作时间可以回到知识库的返回片段核对。工作流运行记录给出了逐步检查这些关系的位置。 [第五章 5.2 Coze、5.3 Dify、5.4 FastGPT 与 5.5 n8n 案例](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E8%83%BD%E4%BD%93%E6%90%AD%E5%BB%BA.md)

Dify 的分类器让我更关注分支的责任。分类器需要知道每类请求的范围，下游节点需要知道这次输入包含哪些参数。遇到「查资料后再润色成一段介绍」这样的请求，还要决定怎样保留前一个任务的结果并传给后一个任务。为每条分支准备固定输入和预期路径，可以帮助发现分类描述重叠、字段遗漏和兜底分支缺失。 [第五章 5.3.2 构建一个超级智能体个人助手](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E8%83%BD%E4%BD%93%E6%90%AD%E5%BB%BA.md#532-构建一个超级智能体个人助手) · [Dify 问题分类器文档](https://docs.dify.ai/en/cloud/use-dify/nodes/question-classifier)

n8n 的知识库与对话记忆需要分别理解。知识库保存待检索的资料，邮件线程标识用于关联同一段对话。排查跨轮次问题时，我会检查哪个节点保存了状态、使用了什么键、下一次执行读到了哪些内容，并检查重启后的行为。课程使用的 Simple Vector Store 把向量保存在应用内存中，它的存储键属于实例范围，重启会丢失数据。清楚这些条件，才能判断测试中看到的连续性来自哪里。 [第五章 5.5 n8n](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E8%83%BD%E4%BD%93%E6%90%AD%E5%BB%BA.md#55-平台四n8n) · [n8n Simple Vector Store 文档](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.vectorstoreinmemory)

测试时，我会先用已知输入检查每个节点，再检查整个任务。除了有完整材料的例子，还需要空结果、字段缺失、工具失败和重复事件。最终答复应能说明已经得到什么、还有什么缺项。把这个方法用于轨迹与数字孪生任务，可以让工作流接收场景标识、调用仿真检查、保存碰撞或限位结果，再由模型组织说明，每条结论都能追溯到对应的工具输出。
