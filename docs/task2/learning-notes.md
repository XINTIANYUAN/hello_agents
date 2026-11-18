# Task2 学习笔记 · 第二章 智能体发展史

课程原文使用 Datawhale 仓库版本 `2eb1c754`。我从知识来源、决策方式和行动反馈三个角度串起本章。[第二章原文](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter2/%E7%AC%AC%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%8F%91%E5%B1%95%E5%8F%B2.md) · [国内在线阅读](https://hello-agents.datawhale.cc/) · [课程仓库](https://github.com/datawhalechina/hello-agents)

| 方法或案例 | 运行机制 | 边界 |
| --- | --- | --- |
| 专家系统 MYCIN | 把领域知识写成条件规则，用反向链从目标倒推所需证据。 | 规则和证据可追查，覆盖范围取决于知识库、输入和适用条件。 |
| SHRDLU | 用显式状态描述积木世界，结合语言解析、规划和模拟动作。 | 能在已建模的对象和动作内处理指代、前置条件和状态变化。 |
| ELIZA | 匹配句式，截取输入片段、转换代词，再填入回复模板。 | 看起来相关的回应也可能来自表面匹配，同义改写可能落入兜底。 |
| 明斯基的心智社会 | 多个简单过程通过激活和抑制协同，组成更复杂的任务行为。 | 状态、反馈与依赖事项需要交接。分工的系统可以有不同的协调结构。 |
| 强化学习与预训练 | 强化学习根据交互和奖励改进策略，预训练从大量数据学习可迁移的表示与语言规律。 | 奖励设计和数据覆盖决定一部分能力边界。应用时结合明确的工具和状态。 |
| LLM 驱动的智能体 | 模型接收上下文，规划和选择动作，应用调用工具并回填观察。 | 工具结果需要核对，运行时记忆需要由应用管理。 |

我把第一章旅行助手的天气追踪重新理解为一次任务状态的更新。查到天气后，程序把结果放进下一轮提示，后续搜索才有了新的依据。第二章 ELIZA 扩展也更新会话状态，不过它用固定句式写入字段。两种代码都能展示状态怎样影响下一轮，改变模型权重则发生在训练流程中。[第一章运行记录](../task1.1/learning-notes.md) · [第二章 §2.4](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter2/%E7%AC%AC%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%8F%91%E5%B1%95%E5%8F%B2.md#24-学习范式的演进与现代智能体)

## 本机实操

在项目根目录沿用 Task1 的 Python 3.11.17 虚拟环境。原版取自课程仓库，并核对了 Git 对象哈希。两个脚本都只用 Python 标准库，可直接离线运行，无需 API Key。

```bash
.venv/bin/python -m pip check
.venv/bin/python code/chapter2/ELIZA.py
.venv/bin/python code/chapter2/ELIZAExtended.py
```

| 程序 | 做了什么 | 实际结果 |
| --- | --- | --- |
| 原版 | 输入 `I need my notebook`，再输入 `bye`。 | 捕获 `my notebook`，代词转换成 `your notebook`。本次回答 `Are you sure you need your notebook?`，退出码为 `0`。 |
| 扩展版 | 单独验证工作、学习、爱好和压力四种新增句式。 | 四句均命中各自模板，未匹配的输入沿用原版规则。 |
| 扩展版 | 用虚构信息记录姓名 Lin、年龄 28、职业 GIS analyst。在后续轮次逐一查询，再把年龄更正为 29。 | 程序回忆三项信息，更新后回答 `You told me you are 29 years old.`。 |
| 扩展版 | 启动新进程，再问姓名、年龄和职业。执行 `bye`，另测输入结束。 | 新会话的三个字段都返回尚未提供，正常结束，退出码为 `0`。 |

2026 年 11 月 18 日在 macOS 上完成以上验证，`pip check` 通过。也核对了第一章脚本、依赖清单和前期文档相对 `v1.1` 的差异。第一章代码在原解释器下通过语法编译。[原版代码](../../code/chapter2/ELIZA.py) · [习题扩展代码](../../code/chapter2/ELIZAExtended.py)

## 踩坑和排查

- **教材把运行会话接在 Python 代码块末尾。** 将控制台提示符 `>>>` 连同代码复制到 `.py` 会产生语法错误。直接使用仓库的 `ELIZA.py` 即可运行。[课程 §2.2.3](https://github.com/datawhalechina/hello-agents/blob/2eb1c7547018b519b85cb57acf5533f12d65bf8e/docs/chapter2/%E7%AC%AC%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E5%8F%91%E5%B1%95%E5%8F%B2.md#223-核心逻辑的实现)
- **特定规则要早于宽泛规则。** 原版的 `I am (.*)` 会接住很多表达。扩展版优先检查年龄和学习句式，再交给原版；姓名、年龄和职业都只在当前进程内持有。
- **有记忆也会听不懂改写。** 实测 `My name is Lin.` 后，`Can you remind me of my name?` 命中原版兜底，本次答 `Can you elaborate on that?`。接着问 `What is my name?` 仍可准确取回 Lin。前一次失败来自输入表达超出规则覆盖范围，字段本身仍在会话里。

## 视频学习

Datawhale 的公开视频索引暂未列出第二章。本次选看了 MIT CSAIL 的 SHRDLU 原始演示片段，并用 ELIZA 复原团队和 DeepMind 的一手材料对照课文。[Datawhale 视频索引](https://github.com/datawhalechina/hello-agents/blob/main/Extra-Chapter/Extra13-Hello-Agents%E8%A7%86%E9%A2%91%E8%AF%BE%E5%BD%95%E5%88%B6%E5%85%B1%E5%88%9B.md)

- **SHRDLU 原始演示，对照 §2.1.3。** 在约 03:00 的片段中，屏幕接收了包含两块红积木及备选物体的叠放请求。约 04:20 的指令用 `it` 指代上文对象，模拟夹具和积木可见。此前录屏还展示了回答盒外积木数量。这些画面把两类输入区分开：有些问题只读取世界状态，有些指令要解析对象并执行动作。[MIT CSAIL 视频档案](https://www.csail.mit.edu/node/6658) · [影片 04:20](https://projects.csail.mit.edu/video/history/aifilms/26-robot.mp4#t=260)
- **ELIZA 复原团队的演示和解说，对照 §2.2。** 团队在模拟的 IBM 7094 和重建的 CTSS 中运行历史版本，用早期 DOCTOR 脚本还原对话。对照本机版时，我关注回复怎样利用原句的一部分。历史复原与课程 Python 示例采用不同实现，两份材料都可以用来观察模式匹配和文本替换。[复原团队说明与录像入口](https://elizagen.org/blog/eliza-reanimated.html)
- **AlphaGo 纪录片片段索引和研发团队说明，对照 §2.4.2。** 第 2 局的第 37 手是对局中一个动作选择的例子。经典 AlphaGo 先从人类棋谱学习，再通过自我对弈提升。AlphaGo Zero 才以规则和自我对弈为起点。对局录像展示行为，版本和训练方式由研发说明核对。[纪录片第 2 局章节](https://www.youtube.com/watch?v=WXuK6gekU1Y&t=1700s) · [DeepMind 对第 37 手的回顾](https://deepmind.google/blog/10-years-of-alphago/) · [AlphaGo Zero 训练说明](https://deepmind.google/blog/alphago-zero-starting-from-scratch/)

另附与本章同主题的社区讲解，方便复习时对照课文。[第二章社区视频](https://www.bilibili.com/video/BV1Qn2wBzEwr/)

[七道章末习题解答](exercises.md) · [学习心得](reflections.md) · [课程内容反馈](course-feedback.md)
