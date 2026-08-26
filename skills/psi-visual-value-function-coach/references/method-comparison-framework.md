# Visual value method comparison framework

Use this framework to add one stable method card per baseline or proposal. Compare methods only after separating task definition, learning method, and evaluation contract.

## Method card

### Identity

- Method name and version:
- Repository commit / checkpoint provenance:
- Primary question: state value, state-action value, success probability, progress stage, preference, or ranking?
- Output semantics: higher means success, lower cost, remaining return, probability, or another quantity?
- Policy dependence: recorded trajectory, behavior policy, target policy, or policy-free label?

### Supervision contract

- Annotation source and task-stage ontology:
- Per-step reward formula and polarity:
- Target equation:
- Discount `gamma`, horizon, and terminal semantics:
- Whether targets are fixed labels, MC trajectory targets, bootstrapped targets, or mixed:
- Known label noise, missingness, leakage, or circularity:

### Input/data contract

- RGB views, Mask source, proprioception, language, and action inputs:
- Single frame or temporal context:
- Exact tensor shapes and normalization:
- Transition construction and episode-boundary behavior:
- Train/validation/diagnostic/holdout split unit:

### Architecture

- Visual encoder and pretraining:
- Frozen, partially tuned, or fully tuned:
- Mask fusion: none, fourth channel, separate branch, tokens, or gating:
- Spatial/temporal aggregation:
- Value/Q/classification head:
- Parameter count and shared parameters:

### Training

- Predicted tensor and target tensor:
- Loss equation and reduction:
- Optimizer, learning rate, batch size, steps/epochs, schedule, seeds:
- Gradient ownership, clipping, and target networks:
- Checkpoint selection rule:
- Training cost and peak memory:

### Inference

- Required inputs and preprocessing parity with training:
- Returned scalar, distribution, Q values, advantage, or confidence:
- Latency, throughput, and device:
- Calibration or aggregation step:
- How predictions are consumed by policy, evaluator, or human reviewer:

### Evidence

- Offline metrics on episode-held-out data:
- Stage/trajectory plots:
- Calibration and ranking metrics:
- RGB/Mask/encoder ablations:
- Correlation with rollout success:
- Failure slices and counterexamples:
- Status: **observed**, **inference**, or **hypothesis** for every conclusion.

## Baseline comparison table

| Dimension | Scalar MC | Distributional MC/C51 | IQL critic |
|---|---|---|---|
| Primary prediction | `V(s)` | `p(V=z_i|s)` and expected V | `V(s)`, `Q1(s,a)`, `Q2(s,a)` |
| Supervision | fixed trajectory RTG | RTG projected to support | expectile Q target and bootstrapped TD target |
| Output support | unbounded scalar | bounded fixed atoms | bounded V expectation, scalar Q |
| Core loss | MSE | cross-entropy | expectile MSE + twin TD MSE |
| Action input | no | no | yes, 26-D |
| Bootstrapping | no | no | yes, through `V(s')` |
| Main strength | simplest auditable baseline | represents a numerical distribution | can rank actions and learn from transitions |
| Main risk | averages ambiguous targets | support/projection/calibration errors | target coupling, terminal errors, optimizer sharing |

## Fair-comparison contract

Hold these constant unless they are the explicit ablation:

- same source episodes and episode-level split;
- same reward schedule, polarity, discount, and terminal definition;
- same observation/action preprocessing and image augmentation;
- same visual encoder initialization and freezing policy;
- comparable optimizer-update and sample-exposure budgets;
- same checkpoint-selection metric and holdout access policy;
- same seeds, preferably at least three when variance matters;
- same inference preprocessing and output interpretation.

If one of these changes, name the experiment as a joint-system comparison rather than attributing the result to the algorithm alone.

## Minimum metric set

Do not reduce method quality to training loss. Report:

1. **Target fit:** MAE/MSE for scalar value; cross-entropy plus expected-value error for distributional value.
2. **Ranking:** Spearman correlation or pairwise ordering accuracy when the method should rank progress/actions.
3. **Calibration:** predicted success/value bins versus empirical outcomes where semantics permit it.
4. **Trajectory behavior:** value curves aligned to task stages, terminal events, regressions, and failures.
5. **Generalization:** episode-held-out and, if available, scene/object/session-held-out results.
6. **Ablations:** zero/shuffled Mask, zero/shuffled RGB, frozen/unfrozen encoder, shuffled targets.
7. **Rollout relevance:** correlation between offline score and actual success, while avoiding causal claims from correlation alone.
8. **Efficiency:** training cost, inference latency, memory, and artifact size.

## Decision rules

- Prefer scalar MC first when establishing data and reward correctness.
- Add distributional MC only when the distributional target, support, and calibration provide observable benefit beyond expected-value error.
- Add IQL when action-conditioned ranking or offline bootstrapping is needed and transition/terminal contracts are trustworthy.
- Treat success classification as a different question from remaining return; compare it only after explicitly aligning semantics.
- Reject apparent improvements that disappear under episode-held-out splits, shuffled-target controls, or equal sample exposure.

## Experiment record template

```text
Claim:
Compared methods:
Only intentional difference:
Shared data/split/reward contract:
Shared encoder/training budget:
Seeds:
Primary metric and stopping rule:
Diagnostics/ablations:
Observed result:
Failure slices:
Interpretation:
What this result does not prove:
Next falsifying experiment:
```
