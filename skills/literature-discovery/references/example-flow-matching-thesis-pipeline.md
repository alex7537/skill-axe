# Worked example: Flow Matching robotic-policy thesis pipeline

Snapshot date: **2026-10-26**. Repository inspected: [`alex7537/flow-matching-test-a2d-v2`](https://github.com/alex7537/flow-matching-test-a2d-v2), default-branch commit `eb3890a`. This is a project-grounded prompt chain and preliminary research framing, not a substitute for the final full-text evidence matrix.

## 1. Freeze the project truth before searching literature

The following statements are supported by the repository at the snapshot commit. They are inputs to the literature workflow, not literature claims.

| Project fact | Repository evidence | Current status | Safe paper wording |
|---|---|---|---|
| The project implements CFM, Diffusion Policy, and IMLE behind a shared policy interface. | `flow_matching_test/policies/`, `README.md` | Implemented | “We implement three action-generation paradigms under a shared observation/action interface.” |
| The common observation is two RGB views plus optional 13-D proprioception; the output is a 16×13 absolute joint-position chunk with `obs[t] -> action[t+1:t+17]`. | `README.md`, configs, data-contract tests | Implemented and documented | State the exact contract and dataset version used in each experiment. |
| CFM uses straight-line velocity regression and 5-step Euler inference; Diffusion predicts Gaussian noise with 100 train levels and 15-step DDIM; IMLE selects the closest of 20 latent candidates and generates in one forward pass. | `README.md`, `policies/factory.py`, policy modules | Implemented defaults | Compare task metrics and latency, not the raw training losses. |
| CFM has extensive offline ablations and reproducible bundles. | `reports/`, `artifacts_index.md` | Evidence exists | Report values only with dataset, split, checkpoint and locator. |
| DP and IMLE historical bundles load and pass prediction-only checks. | `README.md`, `artifacts_index.md` | Loading verified; closed-loop effectiveness not verified | Do not describe them as successful grasping policies yet. |
| The fair-comparison protocol freezes dataset, split, vision trunk, training steps, seed, rollout initial states, and success criteria. | `docs/POLICY_COMPARISON_PROTOCOL.md` | Protocol defined | Present this as experimental design, not a completed comparison. |
| Closed-loop Isaac evaluation is the intended final arbiter. | `README.md`, `目标架构.md`, rollout code | Still incomplete for the full comparison | Any method ranking remains provisional until matched rollouts finish. |
| Video-Aux, Joint WAM, RDT, enhanced proprioception and retry logic exist as extensions. | `README.md` and linked branches | Mixed: prototype, branch, or planned evaluation | Keep outside the primary three-policy causal comparison unless separately budgeted. |

Two repository inconsistencies must be resolved before thesis drafting:

1. `目标架构.md` records an older 66-episode decision that favored Frozen ViT, while the later 1,090-episode ablation report favors 0.1× fine-tuning on offline metrics. Always bind an encoder claim to its dataset and report.
2. Some reports describe completed offline runs while `README.md` explicitly says the decisive closed-loop rollout is pending. “Training completed” must never be rewritten as “method proved effective.”

## 2. Recommended thesis scope

### Defensible working title

**Chinese:** 面向多视角机器人抓取的连续动作生成策略：Conditional Flow Matching、Diffusion 与 IMLE 的可复现实证比较

**English:** Reproducible Comparison of Conditional Flow Matching, Diffusion, and IMLE for Multi-View Joint-Space Robotic Grasping

### Primary research question

Under the same dataset, observation encoder, joint-space action contract, optimization budget and closed-loop evaluation protocol, how do CFM, Diffusion Policy and IMLE trade off task success, failure mode, inference latency, sample efficiency and deployment reliability?

### Secondary questions

1. Do offline action errors and training diagnostics predict closed-loop grasp success for each generative objective?
2. How sensitive is CFM to inference-step count and visual-backbone freezing/fine-tuning under the selected data regime?
3. Which method fails at approach, closure or lift, and are these failures explained by action multimodality, temporal alignment, or hand-command tracking?

### Contribution boundary

The project should **not** claim:

- the first use of Flow Matching for robot manipulation;
- the first comparison of Flow Matching and Diffusion Policy;
- the first three-way comparison including IMLE;
- that a lower CFM/DP/IMLE training loss proves better behavior;
- real-world generalization when the evidence is Isaac-only;
- closed-loop effectiveness from bundle loading or offline MSE alone.

The strongest six-month contribution is instead a reproducible, deployment-aware empirical study on a specific high-dimensional joint-setpoint task, with matched controls, provenance, staged failure analysis and an explicit account of when offline metrics disagree with closed-loop outcomes.

## 3. Five project-specific prompts

These prompts are designed to be run in sequence. Preserve the artifacts from each stage; do not collapse the chain into a single unconstrained request.

### Prompt A — literature discovery

```text
使用 $literature-discovery，为 GitHub 项目
https://github.com/alex7537/flow-matching-test-a2d-v2 建立论文背景文献集。

研究主题：多视角视觉与 proprioception 条件下，生成 16×13 连续关节位置 action chunk，
比较 Conditional Flow Matching、Diffusion Policy 与 IMLE 在机器人抓取中的成功率、
多模态建模、推理速度、数据效率和部署稳定性。

时间范围：2021-01-01 至 2026-10-26；允许把奠基性论文作为明确标注的时间窗外例外。
核心集合最多 15 篇，不为凑数而纳入弱相关论文。

必须覆盖：
1. Flow Matching/Conditional Flow Matching 理论；
2. Diffusion Policy 与 action-chunk visuomotor control；
3. Flow Matching robot policy、PointFlowMatch、FlowPolicy/consistency-flow 类方法；
4. IMLE Policy 及单步多模态策略；
5. 少数据、推理步数、延迟、闭环 rollout 和失败恢复；
6. 双 RGB / proprioception / joint-space absolute setpoint 与 action horizon 的相关设计。

必须主动检索反例：
- 已经直接比较 Flow Matching 与 Diffusion Policy 的论文；
- 已经同时比较 IMLE、Diffusion 和 Flow Matching 的论文；
- 表明少步 Flow Matching 会 mode collapse、轨迹不平滑或闭环失败的论文；
- 表明普通回归或非生成策略在相同骨架下同样有效的论文。

检索至少使用两个互补学术来源，并用出版社、会议、arXiv 或官方项目页核验题名、作者、
年份、venue/status、DOI/arXiv ID。记录全部查询、日期、过滤条件和结果数量。
输出候选矩阵、纳排理由、版本关系、证据角色和最多 15 篇核心集。
不要把搜索摘要当作全文证据，不要虚构 DOI、引用量或 venue。
```

### Prompt B — paper deep analysis

```text
使用 $paper-deep-analysis，对 literature-discovery 交付的核心论文逐篇做全文拆解。
输入必须包含稳定 ID、核验 URL、版本状态和可访问全文；无法取得全文的条目标记
FULL_TEXT_UNAVAILABLE，不用摘要填补实验细节。

针对 flow-matching-test-a2d-v2 的研究问题，逐篇抽取：
- 研究问题、方法创新、模型骨架、观察模态、动作表示和 action horizon；
- 数据集、演示数量、任务、仿真/真实机器人、train/val/test 划分；
- CFM path/solver/步数，Diffusion schedule/采样器/步数，IMLE 候选数与选择规则；
- 训练预算、seed、硬件、推理频率或 median/P95 latency；
- offline 指标、closed-loop 成功率、失败类型、主要结果与不确定性；
- 作者明确承认的局限；
- 对本项目每个 claim 的支持、冲突或不可比原因。

每个关键事实必须给出页码、章节、表格、图或公式定位。
分开标记 REPORTED、AUTHOR_INTERPRETATION 和 OUR_INFERENCE。
最后生成跨论文证据矩阵，特别比较 Robot Manipulation with Flow Matching、
Diffusion Policy、IMLE Policy、PointFlowMatch、FlowPolicy、Consistency Policy 和 ManiFlow。
禁止横向比较不同定义的训练 loss。
```

### Prompt C — research gap mapping

```text
使用 $research-gap-mapping，输入 paper-deep-analysis 的证据矩阵和下面的仓库事实，
对候选研究空白做二次检索：
- 三个 policy 已共享双 RGB、proprio、16×13 action contract 和 Transformer 主体；
- CFM 有较完整 offline ablation；DP/IMLE 已训练并能加载，但同协议闭环排名尚未完成；
- 最终计划以 matched Isaac rollout success、approach/close/lift 失败、sample MSE、
  median/P95 latency 和资源成本联合评价。

候选 gap：
G1 同一高维 joint-setpoint 抓取任务上的严格同骨架三方法比较；
G2 offline action error 与 closed-loop success 的跨方法相关性；
G3 少步 CFM 的速度—平滑性—成功率权衡；
G4 小数据/关键帧稀疏分布下，CFM、Diffusion 和 IMLE 的失败阶段差异；
G5 enhanced proprioception 是否改善手部跟踪与 lift，而不只是降低 offline loss。

对每个 gap 设计至少一条支持检索和一条反证检索，保留所有反例。
特别核验 IMLE Policy 是否已经完成三方比较；若是，禁止“首次三方比较”表述。
给出 SUPPORTED / PROVISIONAL / REJECTED / INSUFFICIENT_SEARCH 状态、证据链、
新颖性边界、六个月可行性、最小实验和停止条件。
优先选择无需新硬件、可复用现有 bundle/rollout harness 的切入点。
```

### Prompt D — thesis argument builder

```text
使用 $thesis-argument-builder，根据已验证的 gap matrix、claim ledger、仓库 commit、
实验 manifest 和论文定位，生成中英文引言论证。

论证链必须是：
连续机器人动作具有多模态与时序相关性
→ Diffusion/Flow/IMLE 提供不同生成机制与计算代价
→ 既有工作已分别或成对比较这些方法，IMLE Policy 甚至包含三方基线
→ 但既有证据不能直接回答本项目的双 RGB、13-D absolute joint setpoint、16-step chunk、
  小数据抓取与 Isaac 部署条件下，离线指标、延迟和闭环成功率如何对应
→ 因此本论文进行受控、可复现、部署感知的实证比较
→ 贡献是协议、证据与任务范围内的经验结论，而不是发明新的生成范式。

要求：
- 中文和英文保持同一 claim 强度；
- 使用“在本研究设置下”“结果表明/尚待验证”等边界词；
- 已完成与计划中实验严格分开；
- 每条可引用论断绑定 citation key 和 locator；
- 不得声称 first、state of the art 或普遍优越，除非二次检索与实验共同支持；
- 输出引言结构、claim ledger、贡献列表和仍需补证的占位符，不生成虚构引用。
```

### Prompt E — citation integrity audit

```text
使用 $citation-integrity-auditor，审计 Flow Matching 大论文正文、图表、参考文献和仓库证据。

对每个 claim 检查：
1. 引用是否真实，题名/作者/年份/venue/DOI/arXiv 是否匹配；
2. 引用版本是否重复或把预印本与正式版算成两篇；
3. locator 是否能定位到原文、表、图或公式；
4. 原文是否支持当前 claim 的对象、任务、指标和强度；
5. 是否把论文作者的解释写成事实，或把本论文推断写成既有结论；
6. 是否把 repository planned/prototype/load-only 状态写成 completed/effective；
7. 是否跨 policy 比较不可比的训练 loss；
8. 是否由 offline MSE 推导 closed-loop success；
9. 是否把 Isaac 结果外推为真实机器人或普遍结论。

逐条输出 PASS/WARN/FAIL、问题类型、证据定位和最小修改建议。
FAIL 项包括：虚构引用、元数据错误、定位缺失、证据不支持、过度概括、
错误版本、仓库状态误述和未完成实验被写成结论。
审计未通过时，不得输出“引用完整”或“结论成立”。
```

## 4. Preliminary literature map and novelty threats

The live discovery pass identified these high-priority seeds for full-text analysis:

| Evidence role | Primary record | Relevance to this project |
|---|---|---|
| Flow Matching foundation | [Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747) | Defines simulation-free vector-field regression and the probability-path framing. |
| Diffusion robot-policy baseline | [Diffusion Policy](https://diffusion-policy.cs.columbia.edu/) | Establishes action diffusion, visual conditioning and receding-horizon action prediction. |
| Direct FM-vs-DP precedent | [Robot Manipulation with Flow Matching](https://openreview.net/forum?id=l8DzhzIcEj) | Directly weakens any claim that FM-vs-DP comparison is novel. |
| Geometry-conditioned CFM | [PointFlowMatch](https://openreview.net/forum?id=vtEn8NJWlz) | Shows CFM policy learning with point clouds and rotation-aware action spaces. |
| Single-step/low-data baseline | [IMLE Policy](https://arxiv.org/abs/2502.12371) | The strongest novelty threat: compares IMLE against Diffusion and one-step Flow Matching. |
| Fast distilled policy | [Consistency Policy](https://arxiv.org/abs/2405.07503) | Shows that iterative-policy latency can be reduced without using the project’s CFM formulation. |
| Consistency flow | [FlowPolicy](https://arxiv.org/abs/2412.04987) | Relevant to few-step flow inference and 3D conditioning. |
| General/dexterous flow policy | [ManiFlow](https://openreview.net/forum?id=etSYDtRO0Z) | Raises the bar for claims about flow-policy robustness, efficiency and dexterity. |
| Large VLA flow decoder | [π0](https://www.physicalintelligence.company/download/pi0.pdf) | Shows flow matching as an action decoder in a large cross-embodiment setting, but is not a matched small-model comparison. |
| Action-chunk baseline | [Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware](https://arxiv.org/abs/2304.13705) | Grounds action chunking and temporal aggregation; useful for distinguishing chunking from the generative objective. |

Preliminary conclusion: the broad method gap is already crowded. The viable thesis gap is narrower and empirical. It concerns whether conclusions from established benchmarks and large/standard robot platforms transfer to this exact dual-camera, 13-DoF joint-setpoint, keyframe-heavy grasping setup under a rigorously matched deployment protocol.

This gap remains **PROVISIONAL** until the full candidate set, forward/backward citation chains and matched closed-loop results are complete. Search absence is not proof of novelty.

## 5. Six-month experiment plan aligned with the claim

### Core, required

1. Freeze one dataset version, split, stats digest, action contract, encoder, optimizer-step budget and seed set.
2. Train or finalize CFM, Diffusion and IMLE with method-specific parameters recorded but shared confounders fixed.
3. Export self-contained bundles and pass identical Level 0/1 checks.
4. Run the same closed-loop initial-condition grid with the same success predicate.
5. Report success with confidence intervals, approach/close/lift failures, sample MSE, median/P95 latency and compute cost.
6. Test whether offline ranking agrees with rollout ranking; if not, analyze concrete failure trajectories.

### Secondary, only after core completion

- CFM inference-step ablation (for example 1/5/10) under identical checkpoints and seeds;
- Frozen versus 0.1× ViT fine-tuning on the selected dataset only;
- enhanced-proprio ablation for hand tracking/lift;
- action execution horizon 16/8/4.

### Exclude from the main causal claim

- Video-Aux, Joint WAM, RDT-170M, retry state machine and a new task dataset all at once;
- cross-dataset rankings without matched budgets;
- model-selection claims based only on stochastic validation loss;
- “general robot policy” conclusions from a single simulator/task family.

## 6. Minimum evidence needed before writing results

| Claim | Minimum evidence |
|---|---|
| Method A succeeds more often than Method B | Same grid/seeds/success rule, enough trials, confidence interval and failure counts |
| Method A is faster | Same hardware/software, batch 1, warm-up, median/P95 end-to-end timing |
| Method A is more data-efficient | Controlled dataset-size curve with unchanged optimization and evaluation protocol |
| Few-step CFM is sufficient | Matched checkpoint, multiple solver-step settings, success plus latency and trajectory diagnostics |
| Offline MSE predicts deployment | Predefined correlation analysis across comparable checkpoints; otherwise report non-predictiveness |
| Enhanced proprio improves grasping | Matched initialization/budget and stage-specific closed-loop gains, not only lower loss |

Until these conditions are met, use future tense or label the claim provisional.
