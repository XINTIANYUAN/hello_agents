# Task3 学习心得

## 顺着输入到输出理解模型

第三章把语言模型的任务写成条件概率，再逐步引入词嵌入、RNN 和 Transformer。读到自注意力时，我会把计算拆成「为当前位置查询相关信息、给候选位置分配权重、聚合对应内容」三个步骤。多头注意力把这个过程分到不同表示子空间，前馈网络再加工每个位置的表示。沿着张量的形状读代码，比只记住模块名字更容易看出各层如何连接。 [第三章 3.1 语言模型与 Transformer 架构](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#31-语言模型与-transformer-架构)

Decoder-Only 的因果掩码解释了两个容易混在一起的过程。训练时可以同时计算多个位置的预测，各位置只能读取允许的前文。生成时，新 token 依赖前面已确定的 token，因此一次次续写到停止条件。这也让我更清楚地理解智能体的等待时间。工具返回的信息越长、要求生成的答复越长，越需要检查上下文和输出预算。 [第三章 3.1.3 Decoder-Only 架构](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#313-decoder-only-架构)

## 分词和对话模板也是接口

同一句中文、一个英文术语和一段 JSON，都会经过分词器变成 token ID。模型的上下文预算应按实际 token 数计算。对话模板还会添加角色与轮次边界，所以准备输入时需要核对模型、分词器和模板是否配套。阅读本地调用示例时，我最关心的是格式化后的输入、输入 token 数、生成长度上限，以及解码时怎样截去原输入。这些信息能把一次自然语言对话变成可检查的程序过程。 [第三章 3.2.2 文本分词](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#322-文本分词) · [第三章 3.2.3 调用开源大语言模型](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#323-调用开源大语言模型)

## 用可核对的任务比较提示

零样本和少样本提示可以用同一组信息抽取输入来比较。例如给定「请把红色积木放进左侧托盘」，要求返回目标物体、动作和目的地。少样本示例应展示相同的字段与缺失值约定，再观察新输入是否遵循格式、是否忠实提取信息。采样实验也需要记录具体配置，并重复生成，才能观察输出的变化。调低温度后，仍要逐项核对提取结果和原文。 [第三章 3.2.1 提示工程](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#321-提示工程)

## 把生成内容接到验证环节

第三章讲到幻觉时，我会联系前面旅行助手的工具观察。模型给出的当前天气可以与天气工具返回值核对，景点名称可以继续查验来源。放到轨迹和数字孪生任务中，也可以把语言模型提出的操作目标交给轨迹规划器和仿真检查，并保留碰撞、限位等返回结果。模型选型则围绕同一批任务记录格式通过率、事实一致性、延迟和资源占用，逐项看能否满足实际使用要求。 [第三章 3.2.4 模型的选择](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#324-模型的选择) · [第三章 3.3.2 模型幻觉](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter3/%E7%AC%AC%E4%B8%89%E7%AB%A0%20%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B%E5%9F%BA%E7%A1%80.md#332-模型幻觉)
