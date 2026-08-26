# Current PSI reward-model methods

This is a captured baseline for repository commit `e47ec26` on 2026-08-26. Treat it as a comparison anchor, not as proof that a later checkout is unchanged. Re-read the live configs, entry points, dataset contract, losses, and inference code before reporting current state.

## System objective

Estimate task value from the current robot observation. The visual value is not intrinsic to the image: its semantics come from the human-defined task stages, reward schedule, trajectory target, and terminal convention.

```text
frame labels
-> per-step reward
-> MC return-to-go or IQL transition target
-> RGB / optional Mask observation
-> visual encoder and value/Q heads
-> training loss
-> checkpoint
-> per-frame V, Q, or advantage inference
```

## Shared visual architecture

Default observation and representation:

```text
RGB or RGB+Mask [B, 3/4, 224, 224]
-> timm vit_small_r26_s32_224
-> patch tokens [B, 49, 384]
-> feature map [B, 384, 7, 7]
-> SpatialSoftmax [B, 384, 2]
-> flatten [B, 768]
```

The default configs freeze the visual encoder, disable four-channel surgery, and set all additional state dimensions to zero. Mask, when enabled, is the fourth image channel rather than a separate encoder. The fourth-channel convolution weight starts at zero; it cannot learn while the encoder remains frozen.

The head shared by scalar V, distributional V, and Q is a two-hidden-layer MLP:

```text
Linear -> LayerNorm -> ReLU -> Linear -> LayerNorm -> ReLU -> output
```

Default hidden width is 256. Q concatenates the 26-D action with the visual/state feature before the MLP.

## Method A: scalar MC value ablation

**Question:** Given the current state image, what future cumulative task score occurred in the recorded trajectory?

- Input: current RGB or RGB+Mask, plus optional low-dimensional state.
- Model: `ValueNet`, output `[B, 1]`.
- GT: precomputed dataset `return_to_go`.
- Loss: `MSE(V(s), return_to_go)`.
- Inference: direct scalar `V(s)`.

This path exists behind `algorithm.use_distributional=false`; it is not the default configuration.

## Method B: distributional MC value, current default

**Question:** What numerical value distribution should be assigned to the current observation under the recorded trajectory return?

- Input: same observation as scalar MC.
- Model: `DistributionalValueNet`.
- Output: 101 logits over fixed support points from `-0.1` to `1.2`.
- GT: scalar dataset `return_to_go`, projected onto adjacent support atoms.
- Intended loss: cross-entropy between projected target distribution and predicted Softmax distribution.
- Inference: expected value `V(s) = sum_i p_i z_i`.

Default training configuration captured here:

| Setting | Value |
|---|---:|
| batch size | 512 |
| optimizer | Adam |
| learning rate | 3e-4 |
| max steps | 100,000 |
| visual encoder frozen | true |
| image augmentation | false |
| checkpoint interval | 1,000 steps |

The repository calls the trainer `AWRCritic`, but this path only performs value regression; no actor or advantage-weighted policy update is present.

### MC reward/target source

The V1 reward tool derives dense per-transition scores from the ordered labels `start -> put -> flipped -> lifted`, then computes episode-local reverse cumulative sums. In that concrete implementation, the stored `return_to_go` is undiscounted; the generic discounted-return utility imported by the training entry point is not what the dataset path consumes.

Reward polarity must be reported explicitly. The captured V1 implementation assigns negative score to forward label progression and positive score to regression, so larger predicted value behaves more like cost/failure risk than success value. Do not mix its interpretation with the V2 sparse positive-success reward.

## Method C: IQL critic

**Question:** From offline transitions, what are the state value and state-action values without fitting an explicit actor here?

Transition contract:

```text
s: current RGB / Mask
a: arm(14) + left hand(6) + right hand(6) = 26
r: immediate reward
s': next RGB / Mask
d: terminal flag
```

Networks:

- `DistributionalValueNet` for V, reduced to its expectation during the loss;
- twin scalar `QNetwork` heads for Q1 and Q2;
- a shared visual encoder instance across V, Q1, and Q2.

Losses:

```text
Qmin = min(Q1(s,a), Q2(s,a))
LV = asymmetric expectile regression between V(s) and Qmin, tau=0.7
yQ = r + gamma * (1-d) * V(s'), gamma=0.99
LQ1 = MSE(Q1(s,a), yQ)
LQ2 = MSE(Q2(s,a), yQ)
```

Default training configuration captured here:

| Setting | Value |
|---|---:|
| batch size | 64 |
| optimizer | three Adam optimizers |
| learning rate | 3e-4 |
| max steps | 10,000 |
| gradient clip | 1.0 |
| visual encoder frozen | true |

Inference reconstructs V, Q1, and Q2 from the checkpoint and writes per-frame `predicted_value`, `predicted_q1`, `predicted_q2`, and Q-minus-V advantages to a new Zarr dataset.

## Training and checkpoint behavior

Both entry points use Hydra configuration, optional WandB logging, timestamped checkpoint directories, periodic checkpoints, and a `best.pt` selected from the current training-batch loss. The captured loops construct a fresh DataLoader iterator each step, so steps behave like repeatedly sampled shuffled first batches rather than a conventional epoch iterator.

MC checkpoints store the value network and optimizer directly. IQL checkpoints store a trainer state containing V, Q1, Q2, and all three optimizers. Inference reconstructs architectures from the saved resolved config before loading weights.

## Known blockers before trusting comparisons

1. `project_to_distribution` duplicates lower-atom probability accumulation; target mass can exceed one.
2. Reward V2 writes `terminals`, while the training dataset reads singular `terminal` and silently substitutes zeros when missing.
3. V2 creates next frames by globally shifting arrays, which can cross episode boundaries.
4. Reward/terminal arrays use `N-1` elements while observations and episode metadata may describe `N` states.
5. Four-channel Mask cannot affect a frozen zero-initialized first-layer Mask weight.
6. When the shared visual encoder is unfrozen in IQL, the same parameters appear in three independent Adam optimizers.
7. IQL constrains the distributional V head only through its expectation, so logged distribution variance is not calibrated uncertainty.
8. No independent validation set is used by the captured training entry points; `best.pt` is based on a stochastic training batch.

Fix or explicitly control these issues before treating method deltas as algorithmic evidence.

## Current baseline output contract

| Method | Primary output | Secondary output | Intended use |
|---|---|---|---|
| scalar MC | `V(s)` | none | simple return regression baseline |
| distributional MC | atom probabilities and expected `V(s)` | distribution moments | default visual return model |
| IQL | `V(s)`, `Q1(s,a)`, `Q2(s,a)` | `Q1-V`, `Q2-V` | offline transition critic and action ranking |
