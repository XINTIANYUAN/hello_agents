# Task1.1 课程内容反馈

## 建议保留的编排

第一章用同一个旅行助手贯穿 LLM 智能体、PEAS 和行动循环。读完 1.1 和 1.2 就能带着具体问题看 1.3，例如程序在哪里解析行动、天气数据在哪里进入下一轮上下文、什么时候应该结束。这个顺序也适合把章节练习组织成「读定义、查代码、核对日志」三个步骤。 [第一章 初识智能体](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md)

## 建议补充的细节

- **增加一张同一案例的分类对照表。** 1.1.3 从内部架构、时间与反应性、知识表示三个维度介绍分类。前两个维度都出现了「反应式」，初学时容易把三组分类当成一张互斥的类型表。可以用简单恒温器和旅行助手分别示范如何回答这三个维度的问题，并在表格里允许写「材料不足以判断」。也可以在同一张表里标注哪些设计会用经验更新决策策略，让学习能力与其他架构的关系更直观。 [第一章 1.1.3 智能体的类型](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md#113-智能体的类型)
- **统一协议讲解和可运行示例的参数格式。** 1.2.3 用 `get_weather("北京")` 举例，1.3 的解析器则从 `get_weather(city="北京")` 中读取命名参数。建议两处都使用命名参数，并加一句说明解析器如何把函数名映射到已登记的工具。读者便可以直接对照概念示例和终端里的 `Action`。 [第一章 1.2.3 智能体的感知与行动](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md#123-智能体的感知与行动) · [FirstAgentTest.py 上游示例](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/code/chapter1/FirstAgentTest.py)
- **把运行案例变成可以核对的练习。** 建议让学员在三轮日志里标出天气结果、传入景点查询的天气参数，以及 `Finish` 依赖的信息。再给一条明确标注为模拟的天气超时记录，要求学员说明缺少哪项观察、最终答复可以怎样交代限制。这样能把 1.2 的「部分可观察」落实到代码阅读，也能避免拿示例里的晴天和固定气温当作验收标准。 [第一章 1.2.1 任务环境定义](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md#121-任务环境定义) · [第一章 1.3.4 运行案例分析](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter1/%E7%AC%AC%E4%B8%80%E7%AB%A0%20%E5%88%9D%E8%AF%86%E6%99%BA%E8%83%BD%E4%BD%93.md#134-运行案例分析)
- **展示模型输出格式失配的处理。** 实测过两种情况。模型把模板中的 `function_name=` 写进了动作，导致工具未调用。工具成功后，模型又将最终答案拆成多行，单行解析器无法识别 `Finish` 的闭括号。课程可以给出可直接复制的工具调用示例，并说明单行工具协议和跨行答案的解析区别。 [本次踩坑记录](learning-notes.md#踩坑与修复)
