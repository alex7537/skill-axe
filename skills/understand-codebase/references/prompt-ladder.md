# Prompt Ladder for Understanding a Codebase

Use these prompts sequentially. Replace bracketed fields; do not ask all levels at once.

## Prompt formula

A strong repository prompt specifies:

1. **Goal** — the decision or understanding needed
2. **Scope** — repository, feature, subsystem, symbol, or execution scenario
3. **Evidence rules** — required files, symbols, line references, and fact/inference labels
4. **Depth** — overview, mechanism, runtime, algorithm, protocol, OS, or mathematics
5. **Output shape** — map, trace table, sequence, state machine, explanation, or experiment
6. **Stopping point** — what to deliver before expanding further

Template:

> 请帮我理解 `[scope]`，目标是 `[goal]`。先检查仓库规则与文档，再用代码、配置和测试交叉验证。重要结论给出 `path:line`，区分事实、推断和未知。解释到 `[depth]`，输出为 `[shape]`。本轮先停在 `[checkpoint]`，不要修改代码。

## Level 0 — Five-minute reconnaissance

> 快速扫描这个仓库，不修改代码。告诉我它解决什么问题、主要语言和框架、如何构建/运行、顶层模块、可能的入口，以及最值得先读的 5 个文件。每个关键判断附 `path:line`；明确哪些只是推断。最后给我 3 条可选的深入路线。

Use this to replace vague prompts such as “介绍一下这个项目”.

## Level 1 — Architecture map

> 基于刚才的扫描，画出可验证的架构地图：组件职责、依赖方向、数据/控制流、外部系统边界。不要只根据目录命名判断；用 import、注册、配置、构建文件或启动代码证明。指出架构文档与实现不一致之处。

## Level 2 — Representative execution path

> 选择 `[request/command/event/test]` 作为代表场景，从入口追踪到最终结果。逐跳列出 symbol、`path:line`、输入、输出、状态变化和下一跳依据。覆盖正常路径与一个主要失败路径，并指出框架隐式调用发生在哪里。

## Level 3 — Mechanism deep dive

> 深挖 `[subsystem/mechanism]`。先说明它解决的约束，再解释核心不变量、对象所有权与生命周期、数据结构、并发/事务/缓存/重试语义、错误传播和扩展点。用代码与测试交叉验证，不要给脱离本仓库的通用介绍。

## Level 4 — Symbol-level reading

> 带我逐段阅读 `[file or symbol]`，但不要逐行翻译。先说明它在调用链中的位置，再按“意图 → 关键分支 → 状态变化 → 边界条件 → 被谁调用/调用谁”分块解释。对复杂部分给一个具体输入，手工演算执行过程。

## Level 5 — Underlying principles

> 把 `[mechanism]` 从仓库实现追到底层原理：它解决的问题、必须维持的不变量、代码如何维持不变量、依赖的 `[algorithm/protocol/runtime/OS/database/math]` 原理，以及替代方案的权衡。指出解释中的最薄弱假设，并设计一个最小实验验证。

## Level 6 — Challenge the model

> 反驳我们目前对 `[topic]` 的理解。寻找至少两个可能推翻当前模型的证据：测试、异常路径、动态注册、生成代码、配置覆盖或并发时序。更新后的结论必须区分“已证实、较可能、未知”。

## Learning-plan prompt

> 根据我的背景 `[background]` 和目标 `[goal]`，为这个仓库制定 `[time budget]` 的源码学习路线。以一条真实执行链为主线，每阶段列：要回答的问题、必读文件/符号、建议运行的命令或测试、底层知识补充、验证理解的小练习。控制每阶段在可完成范围内。

## Prompt-improvement prompt

> 请先诊断下面这个源码阅读 Prompt 缺少哪些信息：目标、范围、证据规则、深度、输出形式、停止点。然后给出一个最小改写版和一个深入改写版，并解释每处新增约束会改善什么。原 Prompt：`[prompt]`

## Productive follow-ups

- “这条调用链里，哪一步是静态可见，哪一步依赖运行时注册？”
- “如果删除这个抽象，最先破坏哪个不变量？”
- “用一个具体输入演算状态如何变化。”
- “哪个测试最接近可执行规格？它没有覆盖什么？”
- “把这个机制和最常见替代方案放到同一组约束下比较。”
- “给我一个断点/日志/最小测试方案验证这项推断。”
- “继续向下一层：这里依赖的是框架、语言运行时、系统调用还是协议？”

## Weak prompts and repairs

| Weak prompt | Problem | Repair |
|---|---|---|
| “详细介绍所有代码” | No goal or stopping point | Anchor to one representative execution path |
| “解释底层原理” | “Bottom” is undefined | Name the desired layer: algorithm, runtime, OS, protocol, database, or math |
| “画架构图” | Encourages directory-based guessing | Require wiring evidence and dependency direction |
| “逐行解释这个文件” | Produces translation, not a mental model | Ask for intent, invariants, state changes, and callers |
| “这个设计好吗？” | Missing constraints and alternatives | Ask for trade-offs under explicit workloads and failure modes |
