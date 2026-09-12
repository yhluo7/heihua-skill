# 合成演示案例

所有输入与参考输出均为本次项目编写过程制作，不包含真实个人或公司资料。

参考输出展示目标行为。演示脚本重放这些文件，并检查结构与逐字引用，不会重新调用模型。

| 案例 | 输入 | 参考工作包 | 演示重点 |
| --- | --- | --- | --- |
| 把能汇报转换成决策材料 | [查看](01-report-ready/input.md) | [查看](01-report-ready/expected-output.md) | 已有上下文足够，本轮零追问。页数是建议，扩大试点没有被当成已获批。 |
| 尽快不自动变成今晚交付 | [查看](02-fast-proposal/input.md) | [查看](02-fast-proposal/expected-output.md) | 一个方向问题，准备工作不中断，正式流程等待对象确认。 |
| 同一句深入，先查转化环节 | [查看](03-deeper-analysis/input.md) | [查看](03-deeper-analysis/expected-output.md) | 同一句再深入一点，缺口是分析口径。脚本可独立复核这里的示例算术。 |
| 同一句深入，不再增加图表 | [查看](04-deeper-decision/input.md) | [查看](04-deeper-decision/expected-output.md) | 与上个案例的原话完全相同，交付从漏斗核对变为行动比较。 |
| 你看着办，不等于可以直接采购 | [查看](05-approval-boundary/input.md) | [查看](05-approval-boundary/expected-output.md) | 零个问题，但有一个未解除的授权门槛，部分任务保持等待。 |
| 写得好看，不改事实 | [查看](06-honest-presentation/input.md) | [查看](06-honest-presentation/expected-output.md) | 区分改善表达与改变事实，不把迎合上级作为成功标准。 |
| 只给一句话，先确认对象 | [查看](07-missing-object/input.md) | [查看](07-missing-object/expected-output.md) | 只问一个对象问题，所有具体工作保持等待。 |
| 时限与范围冲突，先给取舍 | [查看](08-impossible-scope/input.md) | [查看](08-impossible-scope/expected-output.md) | 不因紧急或不想追问而许诺不可能验证的交付。 |

测试宿主模型时，只提供输入和相应数据，不提供 expected-output。用 eval 中的规则人工评估，避免把参考答案泄露给被测模型。
