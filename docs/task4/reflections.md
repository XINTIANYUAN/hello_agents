# Task4 学习心得

第四章让我开始从执行顺序和反馈来源理解智能体。模型提出下一步，程序解析输出、调用工具、保存结果，并决定继续还是结束。阅读三种范式的代码时，我会逐步核对这些控制点，确认每次模型调用拿到了哪些信息，又把什么结果交给下一步。 [第四章 智能体经典范式构建](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md)

| 范式 | 程序如何推进任务 | 我会检查什么 |
| --- | --- | --- |
| ReAct | 根据当前历史生成行动，执行工具，再把观察加入历史 | 工具是否实际成功，下一步是否使用了观察，搜索结果是否支持最终答案 |
| Plan-and-Solve | 先生成完整步骤，再依次执行，将前面结果传给后续步骤 | 计划是否覆盖问题，步骤是否可执行，中途失败是否被发现 |
| Reflection | 生成初稿，评审问题，再按反馈修订，直到满足停止条件 | 反馈是否指出具体问题，修订是否解决问题，功能与性能是否有可检查的依据 |

这张表也帮助我区分「动作执行了」和「任务完成了」这两种状态。ReAct 返回一段搜索摘要以后，还要核对问题所需的信息有没有找到。Plan-and-Solve 完成最后一步以后，还要核对中间结果与原问题。Reflection 生成新版本以后，可以用同一组验收条件比较前后变化。 [第四章 4.2 ReAct](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md#42-react) · [第四章 4.3 Plan-and-Solve](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md#43-plan-and-solve) · [第四章 4.4 Reflection](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md#44-reflection)

我觉得 Plan-and-Solve 最有启发的部分是状态传递。水果题的后续计算依赖前面结果，执行器把原问题、计划和历史一并传入，才有条件核对整个任务。计划也值得单独检查，例如它是否保留了「三天总共」这个要求。把缺项提早暴露出来，可以减少后续重复计算。 [第四章 4.3.3 执行器与状态管理](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md#433-执行器与状态管理)

Reflection 的素数任务让我更关注反馈的具体程度。如果评审建议换用筛法，就可以核对输出是否仍然正确，以及随着输入增大，运行时间和内存怎样变化。像 `n=0`、`n=1`、`n=2` 这样的边界输入，也应进入同一组检查。每次增加反思轮次都会增加模型调用和等待时间，因此我会同时记录正确性、修订次数与总耗时。 [第四章 4.4.3 Reflection 智能体的编码实现](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md#443-reflection-智能体的编码实现) · [第四章 4.4.5 Reflection 机制的成本收益分析](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter4/%E7%AC%AC%E5%9B%9B%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E7%BB%8F%E5%85%B8%E8%8C%83%E5%BC%8F%E6%9E%84%E5%BB%BA.md#445-reflection-机制的成本收益分析)

如果把这些循环用于灵巧手仿真，可以先规划读取场景、生成候选轨迹、检查和执行的步骤，再根据碰撞或抓取失败的观察调整下一次请求。一个回合结束后，反思阶段可以读取失败记录，提出下一回合要修改的目标或参数。轨迹规划与仿真模块继续提供限位、碰撞和抓取结果，上层智能体的每次调整都有对应的观察可以复查。
