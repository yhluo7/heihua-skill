# 竞品调研记录

查阅日期，2026年9月12日。

## 资料范围与方法

用公开搜索发现候选，再阅读作者维护的原始 SKILL.md。最终保留七个可以直接核对的实现。没有复制或随仓库分发其源码。

本次是功能定位比较，不是实际模型性能评测。没有安装量、星标数或市场排名作为效果证据。未在入口文件明确描述某项机制，不代表整个产品绝对没有该能力。

引用链接指向当时查看的默认分支，不是锁定 commit 的快照。后续发布前应重新阅读，不能把这里的描述当作永久不变的产品事实。

不声称完成全市场检索，也不声称中文办公解码无人做过。

## 原始资料与比较

### C1 requirements-clarity

主要场景，软件功能需求到 PRD。以清晰度评分和分轮提问推动需求成形。

本项目选择，不以完整 PRD 为默认终点，先给办公最小交付。

[作者原始 Skill](https://github.com/softaworks/agent-toolkit/blob/main/skills/requirements-clarity/SKILL.md)。

### C2 clarify

主要场景，实施任务的歧义澄清。先查上下文、记录假设，也支持用户不想追问时自主澄清。

本项目选择，少问问题不是本项目独创。侧重点是中文办公例句、停止条件和对上回复。

[作者原始 Skill](https://github.com/liqiongyu/my-agents/blob/main/skills/clarify/SKILL.md)。

### C3 clarify-ambiguous-requests

主要场景，重要歧义的一问澄清。先找最重要歧义，问一个问题后等待。

本项目选择，允许在等待确认时给出不受阻的准备任务。

[作者原始 Skill](https://github.com/aiming-lab/MetaClaw/blob/main/memory_data/skills/clarify-ambiguous-requests/SKILL.md)。

### C4 stakeholder-requirements-gathering

主要场景，数据分析需求访谈。从业务决定、受众和验收开始，确认后形成分析 brief。

本项目选择，不局限数据分析，也覆盖活动、材料、采购准备和跨部门协调。

[作者原始 Skill](https://github.com/nimrodfisher/data-analytics-skills/blob/main/05-stakeholder-communication/stakeholder-requirements-gathering/SKILL.md)。

### C5 planning-and-task-breakdown

主要场景，可实施的任务计划。强调任务依赖、验收与验证。

本项目选择，增加计划之前的模糊话语解释、低风险假设和对上确认。

[作者原始 Skill](https://github.com/addyosmani/agent-skills/blob/main/skills/planning-and-task-breakdown/SKILL.md)。

### C6 brief-to-tasks

主要场景，设计 brief 到构建任务。基于设计文档和代码上下文，输出有顺序的可构建任务。

本项目选择，输入可以只是办公原话，不要求已有设计 brief 或代码库。

[作者原始 Skill](https://github.com/julianoczkowski/designer-skills/blob/main/brief-to-tasks/SKILL.md)。

### C7 brainstorming

主要场景，想法探索和设计确认。结合上下文讨论方案，在实施前确认设计。

本项目选择，用于日常任务接收，不把每次局部改稿都升级成完整设计流程。

[作者原始 Skill](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md)。

## 应当保留的结论

少问问题、先查上下文、记录假设、拆分任务和设置验收标准，均已存在于相邻项目中。不能将这些通用能力宣传成本项目首创。

heihua-skill 的定位差异来自具体组合。中文办公同句多义，最小交付与停止条件，对内工作包与对上回复，以及只暂停受阻任务的明确边界。它们是设计目标，不是已经实证优于竞品的结论。

六十条词库为本项目人工编写的候选规则，不是从真实公司聊天中提取，也不是已标注的真实意图数据集。用户采纳率、返工率和沟通成本改善均尚未测量。

## 格式和安装依据

[Agent Skills 规范](https://agentskills.io/specification) 说明入口文件及可选资源结构。

[OpenAI 本地 Skill 文档](https://developers.openai.com/codex/skills) 说明本地发现目录与调用方式。该地址在本次查阅时跳转到官方新版文档。

[Claude Code Skill 文档](https://code.claude.com/docs/zh-CN/skills) 说明 .claude/skills 目录与显式调用。

这些文档用于决定包结构和安装说明，不构成对任一桌面客户端已经实测成功的声明。
