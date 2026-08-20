# Current WAM orientation snapshot

Use this only to orient the investigation. It was distilled from the `Wam_Pre_Train` branch at commit `d0177cd5`; verify the live branch, commit, config composition, and symbols before treating any value as current.

## Default composition observed

- Workspace: `WanTrainWorkspace`
- Dataset: `WanHeterogeneousVideoDataset`
- Policy: `WanClosedLoopJointActionPolicy`
- Observation encoder: `WanOfficialObsEncoder`
- Representative configs: `psi_policy/config/train_workspace.yaml`, `psi_policy/config/dataset/wam_pretrain.yaml`, and `psi_policy/config/policy/wan_heter_closed_loop_joint82.yaml`

Resolve Hydra defaults and overrides; reading a single YAML file is insufficient.

## Batch and time contract

| Quantity | Observed shape | Meaning |
|---|---:|---|
| Head RGB history | `[B, 9, 3, 224, 224]` | `t-8 ... t` |
| State history | `[B, 9, 82]` | low-dimensional robot state |
| Text embedding | `[B, 80, 4096]` | precomputed task/subtask T5 embedding |
| Robot identity | scalar or batch field | robot soft-prompt condition |
| Future RGB | `[B, 16, 3, 224, 224]` | `t+1 ... t+16` |
| Future action | `[B, 16, 82]` | `t+1 ... t+16` |

The observed default uses `rgb_head`; do not assume a wrist camera without checking the current config.

## RGB and latent path

```text
decoded RGB -> resize/float preprocessing -> frozen pretrained Wan2.2 VAE
-> dense causal spatiotemporal latent -> Wan DiT patch embedding
-> joint transformer tokens
```

Observed geometry:

- 25 RGB frames = 9 condition + 16 future.
- Full clip `[B, 3, 25, 224, 224]` encodes approximately to `[B, 48, 7, 14, 14]`.
- Nine condition frames encode to 3 latent time steps; sixteen future frames correspond to the remaining 4.
- VAE stride is approximately `(4, 16, 16)` with causal temporal convolutions.
- Patch size `(1, 2, 2)` yields about 147 condition video tokens and 343 full video tokens.
- There is no CLS token in this path; global information emerges through attention over dense tokens.

The `4n+1` temporal geometry explains why 9-frame and 25-frame sequences align naturally with the pretrained VAE. Confirm exact padding/caching behavior in the active implementation.

## Conditioning and loss mask

Training encodes the full condition-plus-future clip as the clean target and separately encodes the known prefix. The observed latent condition mask is conceptually:

```text
[known, known, known, predict, predict, predict, predict]
```

The transformer may emit all seven latent steps, while video loss slices away the three known prefix steps and supervises only the four future steps. Do not describe known condition latents as targets merely because they share a tensor.

## Modules and gradient ownership

- Wan2.2 video VAE: pretrained, `eval`, frozen, no-grad.
- Wan2.2 TI2V-5B DiT: pretrained; observed config fine-tunes the joint backbone.
- UMT5-XXL: used offline to precompute text embeddings; not necessarily loaded during training.
- State/action sequence encoders and action head: learned adapters/heads.
- No ViT, CLIP, DINO, R3M, or V-JEPA appears in the observed default RGB path.

Verify freezing, LoRA, and full-training flags from the resolved config and optimizer parameter groups.

## Low-dimensional tokenization

Observed `WanSequenceEncoder` pattern:

```text
Linear(82, 1024) -> SiLU -> Linear(1024, 3072)
-> position embedding -> LayerNorm
```

It is applied per timestep: state `[B, 9, 82] -> [B, 9, 3072]`; noisy action `[B, 16, 82] -> [B, 16, 3072]`. State and action encoders have separate parameters. The MLP maps features; the transformer models temporal relationships.

## 82D semantic container

```text
robot_waist  0:7
cam_pose     7:16
arm_joint   16:34
arm_tcp     34:52
hand        52:82
```

This is a shared semantic container, not proof that every robot controls every slot. In the observed A2D mapping, roughly 46 dimensions are active and the rest may be zero-filled. Training loss was observed over all 82 dimensions while offline evaluation could mask inactive slots. Inspect nonzero rates and report per-block metrics; silent zeros can make a mean loss look better.

## Joint model and rollout

Video, state, and noisy-action tokens are concatenated into one shared Wan DiT self-attention stream. Language and robot prompts enter as cross-attention context. Outputs are split and decoded by a video latent head and an action head.

Observed loss weighting was conceptually `total_loss = 1 * video_flow_loss + 10 * action_flow_loss`. Confirm signs and reductions from code; the observed Flow Matching target used `noise - clean`, while conventions differ across repositories.

The closed-loop policy included shallow CCRT plus OPSR with `rollout_depth_max=1`, while CCS was disabled. Even an action-only API may internally sample both action and video and then discard the video result.

## Evaluation caution

The existing offline WAM evaluator was action-heavy. A complete evaluation must separately measure VAE reconstruction ceiling, future appearance/dynamics, action-conditioned controllability, action prediction by semantic block and time, recursive rollout drift, and deployed task success.

Freeze benchmark schema, metric direction, coverage, weighting, and critical gates. Avoid averaging partially available metrics or treating visual diversity as action correctness.
