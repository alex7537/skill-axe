# WAM evaluation protocols

## 1. Evaluate different claims separately

| Layer | Question | Minimum evidence |
|---|---|---|
| Codec | Does the frozen VAE preserve the needed detail? | reconstruction on task clips |
| Open-loop future | Does prediction match a known future? | aligned future metrics and qualitative failures |
| Conditioning | Does changing text/action change the correct behavior? | paired interventions with fixed prefix/seed |
| Action head | Are future actions correct by time and semantic block? | masked per-block action metrics |
| Closed loop | Does error compound under model-generated context? | depth-wise rollout and deployed success |

No single EWM or action MSE answers all five.

## 2. WorldArena version ledger

Do not use “WorldArena score” without a schema name:

- **paper/website:** 16 metrics, including Action Following;
- **GitHub evaluator:** can produce 16, but public aggregation helpers contain known field and missing-value bugs;
- **HF live leaderboard:** 15 metrics; Action Following removed from EWM;
- **PSI historical reports:** EWM7, EWM10, live-15, and older 16-item variants all appear.

Never compare or average EWM7/EWM10/partial results with complete live-15. Require exact metric set and finite coverage.

## 3. WorldArena conditions

The formal PSI flow evaluates one checkpoint in three isolated modes:

- **text:** initial frame + T0/T1/T2, zero state/action;
- **action:** initial frame + factual A0, empty language;
- **joint:** initial frame + factual T0 + A0.

Only T0 has matched `(T0,A0,V0)`. The dataset does not provide matched `(T1,A1,V1)` or `(T2,A2,V2)`. Therefore:

- run the complete main profile on T0 for text/action/joint;
- use T1/T2 only as no-GT text counterfactual diagnostics;
- do not inject A0 with T1/T2 and call it a valid joint counterfactual;
- compare `joint-text` more directly than `action-text`, but still report length/preprocessing confounders.

## 4. Action Following limitation

The historical Action Following implementation computes pairwise CLIP feature distance among T0/T1/T2 videos. It measures output diversity or intervention sensitivity—not correctness. Random artifacts, hallucinated objects, or background changes can increase it.

In a five-episode audit, all three texts were jointly compatible with the shared initial frame in 0/5 cases. Treat this as evidence of a confounder, not an estimate of the full-dataset error rate. Add scene-valid labels and report valid subsets.

Use instruction correctness, semantic alignment, and counterfactual action tests alongside diversity.

## 5. Preprocessing affects the metric

Historical PSI and official WorldArena pipelines differed in generated/GT resolution, FPS, resize, JPEG conversion, batching, caching, and model adapters. Important examples:

- RoboTwin/GT source often 320×240 at 30 FPS;
- submission convention 640×480 at 24 FPS;
- official standard-metric path can resize generated frames while GT remains native;
- VLM, JEPA, and Action Following use their own frame sampling and resize paths.

Optical-flow, image-quality, depth, trajectory, and photometric scores can move even with the same video content. Freeze MP4s and dual-run a golden set when validating a fast implementation against a reference implementation.

## 6. Metric semantics and failure modes

Group the live-15 metrics into:

- Visual: Image Quality, Aesthetic Quality, JEPA Similarity
- Motion: Dynamic Degree, Flow Score, Motion Smoothness
- Content: Subject, Background, Photometric Consistency
- Physics: Interaction Quality, Trajectory Accuracy
- 3D: Depth Accuracy, Perspectivity
- Control: Instruction Following, Semantic Alignment

High-level cautions:

- Dynamic/Flow measure amount of motion, not task correctness.
- High consistency can reward near-static output.
- JEPA is dataset-level in the WorldArena path; do not average shard scores—merge features, then recompute.
- VLM 1–5 divided by 5 has an effective minimum of 0.2 and can shrink its denominator on parse failures.
- Trajectory depends on detector prompts, identity assignment, occlusion, and resolution.
- Depth code/history may differ from paper intent and must be direction-normalized before aggregation.
- Semantic Alignment compares generated and GT descriptions, not necessarily video directly to the instruction.
- Official paper equations and published code differ for several metrics; label which one was used.

## 7. Psi-WMBench-GT1 design

Psi-WMBench replaces leaderboard-relative aggregation with paired GT-relative evaluation:

- one prediction and one GT per sample;
- condition frame excluded; all future frames evaluated;
- matched frame count, FPS, view, and sample identity;
- Text, Action, and Text-Action tracks reported separately;
- Core and Full profiles reported separately;
- raw metrics converted to nonnegative residuals where lower is better;
- metric-specific calibration anchors map residuals to 0–100;
- Datahouse averaging inside source, then equal weighting across 14 sources;
- six dimension scores combined by geometric mean;
- 95% hierarchical bootstrap CI;
- critical Motion, Geometry, and Task gates; incomplete coverage cannot produce an official score.

The v2 document snapshot used 457 datahouses, 914 clips, and 94,745 future frames. Later v3 remediation used a new frozen selection (session snapshot: 446 datahouses, 892 clips, 91,152 future frames). Treat these as different benchmark releases: never reuse selection hashes, profiles, or calibration anchors across them.

The v3 lesson matters more than the exact counts: a benchmark version must bind dataset selection, track, profile, calibration, backend weights, inference recipe, checkpoint hash, and code revision.

## 8. Qualification and aggregation

For a formal result require:

- exactly one valid observation for every required sample/view/metric;
- zero missing, invalid, duplicate, or unexpected observations;
- validated monotonic anchors; do not sort or clamp failed anchors into validity;
- all six dimensions computable;
- critical gates passed;
- track, profile, selection, recipe fingerprint, checkpoint hash, and calibration hash recorded.

Use paired bootstrap differences for checkpoint/condition comparisons. Overlapping or separate confidence intervals are not a substitute for a paired comparison.

## 9. Result-reading order

1. Confirm schema/version/coverage and qualification.
2. Inspect six dimensions.
3. Inspect the lowest metric families and source-level distribution.
4. Compare same-track, same-profile checkpoints under a fixed recipe.
5. Compare condition tracks descriptively, then run paired interventions.
6. Inspect rollout examples selected independently of the score.
7. Only then select a checkpoint or propose an architectural change.
