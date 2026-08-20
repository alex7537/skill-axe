# Robbyant ecosystem lessons for PSI WAM

Use this reference when comparing PSI WAM with Robbyant's joint video-action, VLA, streaming geometry, or perception work. These are external repository facts and transferable hypotheses, not PSI implementation facts.

## Evidence snapshot

Reviewed 2026-08-20 from the following public default-branch commits:

| Repository | Commit | Relevant role |
|---|---|---|
| `Robbyant/lingbot-va` | `7c6ffa9bfc4b83582cafc860fab4c82cc7deeeeb` | Autoregressive joint video-action diffusion |
| `Robbyant/lingbot-vla` | `4eb34b7693a0565c67433f8fac9c59a2e67eb60b` | Action policy with optional depth distillation |
| `Robbyant/lingbot-vla-v2` | `951475ae1b1d87553e7dc47c97b53a3d695c0d13` | Action policy with current/future geometry and semantic distillation |
| `Robbyant/lingbot-map` | `c95c33c992d0a6ba7d4e82aacb94ed7519ed25ee` | Streaming 3D reconstruction and bounded memory |
| `Robbyant/lingbot-depth` | `f3a237e434ae987bc38281476d6cfb5df3e4d739` | RGB-D masked modeling and metric geometry |
| `Robbyant/lingbot-video` | `f348dca454c8f1e5707721614dbac10fa5290fed` | Embodied-domain video generation and inference benchmarking |
| `Robbyant/lingbot-vision` | `151e46321bae4399f8568829f190c7bdec216b49` | Dense spatial patch features and teacher-to-student distillation |

Primary sources:

- https://github.com/Robbyant/lingbot-va
- https://github.com/Robbyant/lingbot-vla
- https://github.com/Robbyant/lingbot-vla-v2
- https://github.com/Robbyant/lingbot-map
- https://github.com/Robbyant/lingbot-depth
- https://github.com/Robbyant/lingbot-video
- https://github.com/Robbyant/lingbot-vision

## Relevance map

### LingBot-VA: closest architectural comparator

LingBot-VA jointly predicts video latents and actions, but its temporal contract differs from the observed PSI WAM snapshot:

- it embeds noisy video, clean video context, noisy action, and clean action context as distinct token groups;
- frame IDs order video chunks and action chunks as alternating causal blocks;
- clean tokens attend causally, noisy tokens see only earlier clean blocks, and noisy tokens from the same block can interact;
- the attention window is bounded and training samples variable chunk sizes and window sizes;
- video and action use separate Flow Matching schedulers and SNR shifts;
- the video condition is sometimes noised, while the action condition is clean in the reviewed training path;
- action loss is masked and divided by the count of valid action elements per frame before averaging;
- video and action heads are separate even though the transformer representation is shared.

Do not describe this as the PSI architecture. It is a useful alternative for testing whether explicit temporal interleaving, independent modality noise, or condition corruption improves closed-loop robustness.

### LingBot-VLA 1.0 and 2.0: auxiliary predictive representations

These are action policies, not generative video-action world models. VLA 1.0 optionally distills depth features. VLA 2.0 adds current and future perceptual queries supervised by LingBot-Depth and DINO-Video teachers. Its reviewed configs expose controls that block future-depth information from the action suffix and detach future-image features.

This supplies a lower-cost baseline between action-only training and full future-video generation:

```text
action-only policy
-> action policy + future semantic/geometric feature prediction
-> joint generative video-action WAM
```

Compare these under matched data and optimizer steps before attributing a control gain specifically to generative video prediction.

### LingBot-Map: streaming memory is a resource policy

LingBot-Map separates recent dense context from selected long-range context. Its public runtime supports keyframe-only cache growth, sliding windows, retained special/scale/camera tokens, paged KV cache, and explicit state reset/windowed inference. Its README also states that performance degrades when cached views exceed the training regime and that spatial range remains bounded by training experience.

For a future streaming PSI WAM, treat cache contents as an explicit experiment variable:

- recent dense tokens;
- sparse keyframes;
- stable anchor or task tokens;
- state/action summaries;
- reset and re-localization policy.

Measure task success and revisit consistency, not only memory use and FPS. A longer cache is not automatically better, and a cache is not learned episodic memory.

### LingBot-Depth and LingBot-Vision: teachers and probes

LingBot-Depth masks invalid or missing depth patches and fuses RGB with remaining depth evidence. Its data mixes real sensor captures and synthetic geometry. LingBot-Vision releases dense patch-token backbones trained for boundary-sensitive spatial features and distills a large teacher into smaller backbones.

Possible PSI uses are:

- frozen geometry or boundary probes for generated future frames;
- auxiliary current/future feature targets;
- perceptual metrics that are more spatially local than a global embedding;
- depth-validity masks that distinguish missing sensor returns from numerical zero.

Do not treat predicted or completed depth as ground truth. Validate metric scale, temporal consistency, sensor/domain shift, and failure on reflective or transparent surfaces before using it as supervision or evaluation.

### LingBot-Video: backbone and evaluation reference

LingBot-Video is a video generator trained with web and embodied-domain data. The public repository emphasizes inference and reports separate quality dimensions and embodied-domain dimensions. Its structured prompt contract attaches timestamps to actions; duration must match the timestamp span.

Transfer the following ideas, not the headline model scale:

- evaluate motion, prompt following, visual consistency, and aesthetics separately;
- also stratify by robot, egocentric, navigation, interaction, and physics domains;
- bind text/action descriptions to explicit time intervals;
- document runtime with warmups, steady-state requests, process topology, GPU memory, host memory, precision, and whether an optimized path is numerically exact.

## Cross-repository lessons

### The data contract is part of the model

The reviewed repositories repeatedly encode temporal and embodiment semantics outside the raw tensors:

- LingBot-VA stores action segment start/end frames, action text, sampled frame IDs, source and target FPS, and matching latent filenames.
- LingBot-VLA 2.0 filters video-state and multi-view misalignment, blur/occlusion, abnormal velocity/acceleration/jerk, static signals, and unstable hand/camera estimates.
- VLA configurations map embodiments into canonical containers while retaining joint masks and per-joint normalization rules.
- LingBot-Video uses time-stamped structured actions rather than an unstructured global prompt.

For PSI WAM, audit timestamp alignment, frame sampling, action latency, camera synchronization, subtask boundaries, active dimensions, and normalization provenance before changing the network.

### Padded action containers require masked objectives

LingBot-VA maps embodiments into a shared action container, pads missing dimensions, carries a boolean action mask, and normalizes action loss by active elements. LingBot-VLA also carries joint masks and slices or masks to the active action dimension.

For PSI's 82D container, report both:

1. the current all-dimension training reduction;
2. an active-dimension-only diagnostic using the true embodiment mask.

If changing the training reduction, run it as an explicit ablation. Active-only loss changes both scale and gradient allocation; it is not a metric-only cleanup.

### Modality noise schedules are a design axis

LingBot-VA uses separate video and action Flow Matching schedulers, independent SNR shifts, and different condition-noising behavior. This recognizes that video latents and low-dimensional actions have different scales and denoising difficulty.

For PSI WAM, compare shared versus modality-specific sampled time/SNR under matched compute. Log per-modality loss, gradient norms into the shared DiT, and closed-loop metrics. Loss weights alone do not reveal gradient balance.

### Causal claims need intervention tests

Temporal masks, causal encoders, and future-feature losses can still admit unintended information paths. For any design, perturb future text, video targets, and action targets independently and require earlier outputs to remain invariant. Then intervene on current action while holding history and text fixed, and require the predicted visual consequence to change in the intended time and region.

### Auxiliary prediction and generation answer different questions

Future DINO/depth feature prediction encourages a policy representation to encode future semantics or geometry. Generative latent prediction additionally models appearance and decoding uncertainty. Neither one automatically improves action selection.

Use a three-way matched ablation—action-only, auxiliary future features, generative future video—to identify which supervision is responsible for any improvement.

### Geometry, dynamics, memory, and control need separate metrics

LingBot-Map's benchmark separates trajectory, relative pose, depth, and point-cloud quality, and distinguishes macro from micro aggregation. LingBot-Video separates generic quality from embodied domains. Apply the same discipline to WAM:

- appearance and VAE reconstruction ceiling;
- short-term motion and geometry;
- action-conditioned controllability;
- object identity and revisit memory;
- action error by semantic block and timestep;
- recursive rollout drift;
- closed-loop task progress and success;
- latency and resource use.

Do not combine missing metrics into a single average, and state whether macro or micro aggregation lets long episodes dominate.

## Candidate experiment queue

Prioritize small tests that discriminate mechanisms:

1. **Active-action diagnostic:** compute all-82D and embodiment-masked action losses and metrics on the same checkpoint.
2. **Future-leakage audit:** perturb future video, action, and subtask text separately and test earlier-output invariance.
3. **Independent-noise ablation:** shared timestep versus separate video/action timesteps or SNR shifts.
4. **Condition-robustness ablation:** occasionally corrupt predicted/known video context during training and measure recursive rollout.
5. **Auxiliary-versus-generative ablation:** action-only versus frozen future-feature teacher versus full future-latent loss.
6. **Variable-horizon training:** fixed context/prediction horizon versus sampled chunk/window lengths, evaluated at matched and extrapolated horizons.
7. **Geometry probe:** score predicted futures with a frozen depth or dense-feature model, then verify correlation with human/robot judgments before adopting the metric.
8. **Memory policy prototype:** recent-only versus recent plus keyframes or compact state summaries, with revisit identity and task success gates.

## Gotchas

- LingBot-VA's causal interleaving is an architectural alternative, not evidence that PSI's joint denoising is wrong.
- Separate SNR shifts and sampled times change the optimization problem; do not copy numeric values across latent/action representations.
- VLA 2.0 future-video supervision predicts teacher features, not RGB or VAE latents.
- Blocking future-feature gradients can prevent leakage but can also remove the intended auxiliary influence; inspect the actual attention and detach paths.
- A predicted depth teacher can be confidently wrong and can reward temporally inconsistent video frame by frame.
- Keyframe caches and anchor tokens preserve selected context, not a complete world state.
- Structured prompt rewriting may introduce actions that were not visibly present. Preserve original text and audit generated segment labels.
- Repository benchmark numbers are not comparable without matching checkpoints, data splits, preprocessing, action conventions, and evaluation scripts.
- Throughput claims must state whether they are aggregate or per device, warm or cold, single-request or concurrent, and exact or approximate.
