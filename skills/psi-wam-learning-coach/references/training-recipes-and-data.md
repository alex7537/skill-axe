# WAM training recipes and data lessons

## 1. Training objective must follow a verified action contract

The highest-value historical lesson is that scale cannot repair semantically wrong conditioning. Earlier RoboTwin/WorldArena paths contained deterministic action-contract problems:

- a 7D wrist pose (`xyz + quaternion`) was truncated and written into joint slots;
- gripper deltas were masked, making visible grasp state nearly absent;
- real `joint_action/vector` could be used only for video length while another representation drove conditioning;
- already-normalized UNI_STATE values could be normalized a second time;
- text and action dropout composed into an unintended distribution with no action-only samples.

The 2026-07-19 contract repaired these by:

- mapping full wrist pose into dedicated wrist slots;
- converting quaternion to rotation-6D and using relative SO(3) rotation;
- preserving continuous absolute gripper targets;
- introducing an identity-like `uni_state_v2` normalizer for already normalized continuous fields;
- using mutually exclusive modes: 85% text+action, 5% action-only, 5% text-only, 5% unconditional.

This changes the input meaning and requires fresh training. Do not resume a checkpoint across incompatible normalizer/action contracts.

## 2. 82D container and masking strategy

The shared 82D layout is useful for heterogeneous robots, but absent fields must not be mistaken for supervised zeros:

```text
0:7    waist
7:16   camera pose
16:34  arm joint
34:52  arm TCP
52:82  hand/gripper
```

The spreadsheet's planned progression was:

- **V1:** shared Joint82 container, missing slots zero-filled and included in the baseline loss.
- **V2:** retain the container but add `state_valid_mask`/`action_valid_mask`; compare strict masked loss, soft weighting, and no-mask baseline.
- **V3:** add reliable TCP supervision only after unifying frame, units, handedness, and orientation; use masks for sources without TCP.

Required diagnostics include per-block loss, valid-slot ratio by source, nonzero target rate, and small-dimension visibility. A scalar 82D MSE can hide dead or zero-dominated fields.

## 3. Video window and timebase

- RoboTwin 2.0 training data is 30 FPS; current WorldArena rollout export is 24 FPS.
- Official evaluation mostly consumes frames and frame count, but motion metrics remain sensitive to preprocessing, resolution, and effective timebase.
- Zarr frame indices alone do not define physical time. Prefer timestamps; otherwise verify conversion logs, raw/Zarr frame ratios, and content matching.
- Store `source_fps`, `effective_fps`, `subsample_step`, conversion version, and source frame index or timestamp in future datasets.

Historical W220 audit found a severe mismatch:

- only about 15.12% of training windows had a full 220-frame future;
- average valid future was about 102.56/220;
- only about 0.62% of windows began at episode start;
- the benchmark starts from the first frame and many episodes cross more than one W220 chunk.

This supports short-window and episode-start experiments (for example 49/81 frames plus rolling history) before assuming a larger backbone is the main bottleneck.

## 4. RoboTwin and Mix data scale

RoboTwin snapshot:

- about 125,216 episodes, 20.58M frames, 190.55 hours raw;
- about 100,173 training episodes, 152.4 hours;
- 50 semantic tasks, 459 robot/environment variants, five robot families;
- overlapping windows produce about 15.26M DataLoader samples, which must not be described as independent trajectories.

Mix snapshot:

- 942 datahouses, 388,290 train clips, 43.09M frames, about 763.71 hours;
- heterogeneous effective FPS and resolution buckets;
- batches share a resolution bucket across ranks; loss is scaled by video-token budget rather than a fixed sample count;
- the observed enabled Zarr RGB arrays were uint8 `[T,H,W,3]` with bytes+zstd, not JPEG.

Do not let large sources or long clips dominate implicitly. Record the sampler, epoch size, source/group weights, clip reuse, and whether an “epoch” means a deterministic full pass or weighted sampling with replacement.

## 5. Resolution buckets

Observed Mix training used manifest-derived source resolution buckets, letterboxing each RGB stream while preserving aspect ratio. Per-rank batch size was chosen by a video-token budget. This is preferable to pretending all resolutions have equal memory cost.

When comparing runs, fix or record:

- source and target resolution;
- letterbox/crop/resize policy;
- temporal length and VAE latent length;
- token count per sample and per-rank batch;
- loss scaling by tokens versus samples.

Changing any of these changes both optimization and evaluation, especially optical-flow, depth, image-quality, and photometric metrics.

## 6. Distributed training lessons

- A 496-rank DDP run improved step time by about 1.58x after communication optimization, but later failed on a 600-second AllReduce watchdog.
- Profiling showed apparent gradient-clipping time dominated by waiting for asynchronous AllReduce, not clip computation.
- Data wait and sidecar text embedding cache were not the bottleneck in that run.
- On 150 Hygon nodes, observed HSDP hybrid sharding improved batch throughput by roughly 38% versus full-shard FSDP in the recorded comparison.

Performance experiments must keep model/data semantics fixed and validate:

- loss parity for a short controlled run;
- optimizer, normalizer, robot prompt, action head, EMA, and checkpoint save/load/resume;
- samples/sec, step time distribution, memory peak, GPU utilization, data wait, communication wait, and checkpoint time;
- distributed stability over meaningful duration, not only startup throughput.

## 7. Backbone scaling

The documented PSI baseline used Wan2.2 TI2V-5B with frozen VAE/observation encoding and full DiT training. Public A14B world models mainly use I2V-A14B; A14B is a two-expert MoE with roughly 27–28B total parameters and about 14B active per denoising step.

Do not treat 5B→A14B as a checkpoint-name change. It changes expert routing, memory, sharding, VAE/conditioning compatibility, and training strategy. Current evidence favors repairing action semantics, gripper, conditioning injection, dropout, resolution, and window distribution before scaling the backbone.

If testing A14B, begin with a controlled LoRA/adapter smoke test and keep data, action representation, resolution, window, optimizer budget, and evaluation recipe fixed.

## Gotchas

- Training loss is not a rollout selector; use fixed rollout-aligned validation.
- An epoch under weighted Mix sampling may not mean a full pass.
- More steps can improve or collapse different condition tracks differently.
- High photometric consistency can be a static-video shortcut.
- `use_action_condition`-style flags may not own the actual action path; trace the concrete adapter inputs.
- Padded future frames may be excluded from target loss yet still affect context distribution and compute.
