---
name: a2d-grasp-evaluation
description: Unified A2D policy evaluation entry point (测评、测试监督). Use for evaluation goals and parameters, launch/resume/pause, progress monitoring, success and failure diagnosis, automatic reports, or head/wrist video and GIF collections. Coordinate the existing evaluator and reporting tools without duplicating their implementation. Use specialist benchmark or deployment skills only when the requested phase needs them; not a general skill scheduler or training launcher.
---

# 测评 · A2D（统一入口）

Separate task outcomes from diagnostic reference matches, and locate the earliest failure supported by execution evidence rather than one aggregate success percentage.

## 一个入口，按需执行

用户说“测评”“继续测试”“测试进度”“分析失败”“采集视频”时，在 A2D 语境中由本 skill 接手。沿用已确认的目标、参数和权限；信息缺失才询问。不要为了走完整流程重启已有任务。

| 请求／阶段 | 本入口负责 | 必须交付的证据 |
|---|---|---|
| 目标与配置 | 核对模型/哈希、场景、数量、执行模式、H、动作上限、种子和判据，冻结计划 | 简洁的目标参数表＋plan 路径 |
| 启动／续跑 | 核对进程/端口、调用已验证 runner、按完整身份跳过已有终态 | PID、端口、首轮进展；不以“已启动进程”代替跑通 |
| 暂停／停止 | 在用户指定回合边界保存记录，停止已授权的准确进程，核对续跑位置 | 暂停清单、已完成覆盖、未完成样本隔离记录 |
| 监督 | 检查实际进程、日志增长、异常和计划覆盖 | 每模型完成数、成功/有效、无效、当前回合与告警 |
| 分析 | 用逐步证据核对接触、抬升、持续时间、跟踪与初态差异 | 观测现象与因果假设分开；说明比较限制 |
| 归档 | 默认挂载独立报告 observer，核对完成/中断报告 | 参数导览在开头，本地及指定 vault 报告一致 |
| 视频／展示 | 确定成功/失败筛选、双视角、每模型配额和尝试上限，制作预览 | 原始视频、样本 manifest、GIF；发布单独确认 |

## 代码与专业知识的边界

- 本 skill 是统一操作入口，不是常驻进程，也不会自行调度其他 skill。
- 测评仓库 `flow-matching-test-a2d-v2` 的 `feat/a2d-eval-loop-v0` 分支维护闭环和自动报告实现；本机路径由 `config.json` 或 `A2D_EVAL_REPO` 指定，不假定固定目录。
- 已有运行目录中的 `orchestrate.py` / `supervise.py` / `evaluate.py` 仍承担实际仿真任务。先核对具体入口和契约，不声称它们已全部成为仓库内通用 runner。
- 报告代码只在测评仓库修改；skill 的兼容脚本只转发。已有聚合/展示辅助脚本仅在其输入契约匹配时使用，不复制新的执行后端到 skill。
- 按下方路由读取专业 skill/参考资料；用户不必自行选多个入口。不复制其他 skill 的完整流程，不建立重复的全局调度 skill。
- 仅查看进度时保持只读；修改参数创建新批次。已有明确授权继续有效。报告归档不自动授权发布 GIF、远端代码或下一轮训练。

## Route the request

- For local A2D launch/resume or stop/report, follow [automatic Obsidian reporting](references/automatic-obsidian-report.md): attach the independent report observer by default, verify its first local/vault outputs, and preserve completion/interruption reports. The evaluation repository owns executable reporting logic; this skill owns invocation and verification. A skill edit alone is not running automation.

- Read [references/inference-runtime-lessons.md](references/inference-runtime-lessons.md) for action-only bundle compatibility, RPC timing, fixed policy seeds, timeout diagnosis, or interrupted-batch recovery.

- Read [references/evaluation-methodology.md](references/evaluation-methodology.md) before designing, launching, or interpreting an evaluation.
- Read [references/parallel-reset-and-outcome-audit.md](references/parallel-reset-and-outcome-audit.md) for multi-environment handoffs, equal-count snapshots, reference-based failure labels, or sustained-versus-final retention analysis.
- Read [references/generative-inference-ablation.md](references/generative-inference-ablation.md) before comparing Diffusion/CFM sampling start, inference iterations, timestep grids, ODE solvers, or execute horizons.
- Read [references/success-gallery-packaging.md](references/success-gallery-packaging.md) before selecting successful or failed rollouts and building paired-view GIF/MP4 galleries.
- Use `$a2d-model-swap-only` when the comparison must vary only a checkpoint or deployment bundle.
- Use `$robot-benchmark-loop` when several tasks, seeds, models, or simulator tracks need a frozen run manifest, coverage qualification, aggregation, and promotion decision.
- Use `$remote-policy-bundle` first when the requested checkpoint still needs to be exported and verified from a remote machine.

Choose one mode before acting:

- **Design:** freeze the comparison and success contract without launching.
- **Launch/resume:** preflight and start the explicitly requested persistent evaluator.
- **Monitor:** inspect process/socket state and result growth read-only.
- **Compare:** use matched seeds and equal completed counts; change one variable.
- **Diagnose:** find the earliest funnel stage that separates configurations.
- **Report/package:** preserve identities, exact counts, failure taxonomy, and artifact paths.

## Freeze a fair evaluation

Record before launch:

1. Bundle paths, roles, SHA-256 values, and compatibility with the observation/action schema.
2. Evaluator revision or hash, scene/server identity, and RPC capability/readiness.
3. Models, order, episode/layout seeds, requested counts, execute horizon, maximum actions, action rate, sampling mode, and output namespace.
4. Arm-arrival reference, hand-target reference, tracking lags, contact rule, lift thresholds, persistence, final-state rule, and infrastructure-error policy.
5. Resume schema and experiment identity. Start a new namespace when the model matrix, horizon, criterion, evaluator, or record schema changes.

Alternate configurations episode by episode when simulator warming, scene drift, or long-run server degradation could bias sequential blocks.

## Measure the funnel

Keep numerator and denominator for each stage:

1. Valid episode completed without evaluator/server/RPC error.
2. Actual 7D arm pose reached the frozen pre-lift neighborhood.
3. Commanded 6D hand target reached the intended pre-lift shape.
4. Actual 6D hand pose reached the intended shape.
5. Command-to-actual tracking passed at the frozen lags.
6. Valid target-object multi-finger contact occurred.
7. Contact and relative object lift occurred simultaneously for the persistence gate.
8. Contact/lift remained at the final frame.

Reference-based arm/hand readiness flags are diagnostics, not necessarily monotonic success gates. Before using their failure labels causally, check whether successful trials also fail those flags and whether the measurements refer to the same relevant time window.

Keep maximum and final relative lift separate. Keep contact-only, transient lift, sustained lift, and retained lift separate. Do not blame the hand when arm arrival or infrastructure failed first.

## Use named success profiles

Never introduce a threshold after inspecting the model outcomes. Select a named profile before evaluation or define a new versioned one.

The historical `target-contact-lift-5f-v1` profile is:

- object height relative to the episode's initial height;
- thumb contact plus at least two non-thumb fingers, at least three fingers total;
- a frozen per-contact force floor;
- primary tier: simultaneous valid contact and relative lift at least 5 cm;
- higher diagnostic tier: the same condition at least 10 cm;
- five consecutive sampled control frames;
- report ever-sustained and final-retained separately.

Use this profile only when it matches the intended task and simulator signals. Otherwise freeze a new profile and do not compare its percentages with older profiles as if they were the same metric.

## Launch and monitor safely

- A request to evaluate authorizes launching the named evaluator, not killing an existing evaluator or restarting the simulator.
- Before launch, inspect evaluator processes, parent/process groups, established client sockets, server listener, and result growth in the relevant host namespace.
- If a prior evaluator owns the same endpoint/environment, show its identity and outputs and obtain explicit confirmation before stopping it. Never stop the Isaac/gRPC server unless separately requested.
- If host visibility or permission is insufficient, stop before claiming exclusivity.
- Launch long evaluations under an existing persistent supervisor or terminal; do not rely on one tool call staying alive.
- After launch, verify one active evaluator, one intended client owner, advancing status timestamps, and growing append-only records.
- Treat `status=running` without a live process/socket or file growth as stale. Treat concurrent controllers of one single-environment server as contamination.

Resume only from records whose schema and full experiment identity match. Record infrastructure-invalid and contaminated episodes explicitly; do not convert them to grasp failures.

## Summarize and decide

Use `scripts/summarize_a2d_eval.py` for read-only aggregation of summary JSON files. At minimum report:

| Configuration | Completed/requested | Sustained 5 cm | Sustained 10 cm | Valid contact | Errors |
|---|---:|---:|---:|---:|---:|

Add arm/hand/tracking funnel counts, maximum/final lift distributions, streaks, achieved cadence, exact hashes, seed schedule, criterion version, and evaluator status when diagnosing or comparing.

Treat initial episodes as smoke validation only. Compare incomplete runs only at equal completed counts with identical seeds; do not rank models from asymmetric or tiny samples.

For a success-video gallery, use `scripts/build_success_grid.py` when its v17 four-model filename contract matches the source collection. Keep a machine-readable clip manifest beside the GIF and MP4; the visual is showcase evidence, not a substitute for the evaluation report.

## Gotchas

- Successful replay validates much of the execution chain, not policy reproduction.
- Joint-space compatibility does not prove matching preprocessing, temporal offset, action semantics, or chunk sampling.
- `hand_target` is control intent; `hand_actual` includes lag, load, deformation, and actuation response.
- Do not reject a predicted chunk solely because an unexecuted tail leaves the training distribution; separate executed-prefix, full-chunk, and physical-limit diagnostics.
- Smaller execute horizons add feedback and sampling boundaries; larger horizons reduce boundaries and increase open-loop duration. Report both horizon and achieved action cadence.
- Generative inference iterations and execute horizon are different controls: the former changes how one action chunk is generated; the latter changes how long the robot remains open-loop before observing again. Never change both in one comparison.
- Height-only success counts strikes or throws; contact-only success counts failed lifts; final-height-only misses a valid grasp followed by a drop.
- Nominal `rate_hz` is not achieved frequency when observation, contact, ground-truth, rendering, and inference RPCs add latency.
- A reference selected by nearest arm pose may not be object-specific ground truth.
- GitHub README does not reliably autoplay embedded MP4; use a size-controlled looping GIF and keep MP4 as the higher-quality link.
- GIF/H.264 dimensions should be even. A nominal 100×75 tile may be rounded during chroma scaling and then fail padding; 96×72 tiles produce a stable 960×720 10×10 grid.
