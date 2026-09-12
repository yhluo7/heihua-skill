# 结构说明

普通使用只需中文 Markdown。为了做自动检查或接入自己的工具，才需要结构化 JSON。
`assets/work-package.schema.json` 是本仓库数据契约，遵循 JSON Schema 2020-12 的书写格式。
本地校验器只实现该文件实际使用的关键词，不是完整的 JSON Schema 通用实现。

| 字段 | 说明 |
| --- | --- |
| schema_version | 固定为 1.0 |
| request | 用户给出的原话，保持原意 |
| task_understanding | 当前对任务的工作性解释，不是读心结论 |
| execution_status | ready 全部可准备，partial 部分等待，blocked 全部等待 |
| evidence | E1 起编号，source 是 input.request 或授权目录内的相对文本路径，quote 是逐字片段 |
| facts | 每条至少关联一项依据，不把建议混为事实 |
| interpretations | 一至三个候选解释，只能有一个 selected 为 true，记录改变判断的条件 |
| assumptions | A1 起编号，只放低或中风险可逆假设，并写复核节点和退路 |
| question_policy | 默认 budget 为 2，exception_reason 通常为空 |
| clarifications | Q1 起编号，写必要性、答案影响、无回复时方案及被阻塞任务 |
| deliverables | D1 起编号，列格式和验收，proposed 是建议，confirmed 需明确要求的证据 |
| tasks | T1 起编号，依赖只能指向前面任务，state 为 ready 或 waiting |
| approval_gates | G1 起编号，confirmed 为 false 时阻塞所列任务，为 true 时需要授权依据 |
| risks | 风险、影响、处理方式、相关依据，可无额外依据但不得冒充已知事实 |
| out_of_scope | 明确本轮不做的事情，至少一项 |
| reply_draft | 给上级的回复草稿，不自动发送 |
| stop_condition | 足够交付的停止条件 |

时间、预算、负责人等可在事实、假设和任务描述中记录，但来源类别必须清楚，不需要虚构字段值来凑完整。
所有列表可以为空的条件见 schema。facts、evidence、interpretations、deliverables、tasks 和 out_of_scope 不能为空。
任务完全不可开工时可以列一个 waiting 的待明确任务，通过 clarifications 或 approval_gates 表明它为何受阻。

## 检查能做什么

校验字段与类型、重复编号、证据引用是否存在、任务依赖顺序、等待状态传播、提问数和审批门槛。
使用 source-root 时，额外检查引用是否是实际文本的逐字片段。只读该目录内不超过 2 MiB 的 UTF-8 文本，拒绝目录穿越和目录外符号链接。

## 检查不能做什么

它不能判断引用是否足以证明结论，不能识别全部暗含承诺，不能知道引用里的批准是否真实，也不能校准置信程度。
PASS 表示声明的结构和规则通过，不表示上级意图判断正确或项目可以直接执行。
审批门槛和风险分类仍需要模型及用户判断，脚本不是权限系统。
