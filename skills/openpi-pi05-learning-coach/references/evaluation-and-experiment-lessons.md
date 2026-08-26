# Evaluation and Experiment Lessons

## Evaluation ladder

Keep outcomes separate:

1. **Static contract:** config, checkpoint, normalization, shapes, masks.
2. **Infrastructure smoke:** one random observation produces finite output.
3. **Controlled diagnostic:** fixed image/state/noise interventions reveal sensitivity.
4. **Offline action quality:** requires the same embodiment/action contract and expert targets.
5. **Simulation/closed loop:** task success, failure stage, latency, recovery.
6. **Robot qualification:** requires an authorized operator and safety runbook; this skill does not authorize it.

An exit code and action JSON establish only the rung they actually test.

## Verified infrastructure case

Historical local evidence (2026-08-07 to 2026-08-24):

- OpenPI commit: `15a9616a00943ada6c20a0f158e3adb39df2ccac`;
- checkpoint: `pi05_droid`, 20 files, about 12.43 GB apparent size;
- environment: Python 3.11.15, JAX/JAXLIB 0.5.3, CPU Torch 2.7.1, about 1.9 GB inference-only environment;
- PRO 5000 Blackwell smoke: `(15,8)`, finite, first load/infer about 48.1/10.1 s, cached about 5.39/2.58 s;
- A800 CUDA 12.4 smoke: `(15,8)`, finite, cold about 27.0/31.2 s, warm about 9.53/4.93 s;
- repeated A800 fixed-seed actions were bitwise identical;
- PRO 5000 versus A800 actions had mean absolute difference about `0.00299` and maximum about `0.01182`, passing the recorded `atol=rtol=1e-2` comparison.

These measurements are hardware/runtime observations, not model-quality rankings.

## Fixed-noise visual/language diagnostic

A diagnostic-only probe used one exposed train episode with three RGB streams and selected five near-equispaced frames. Because its dual-arm action contract was incompatible with DROID, the probe fixed one synthetic DROID state and one noise tensor and evaluated sensitivity only.

Recorded mean absolute action differences:

| Intervention | Mean absolute difference |
|---|---:|
| exact repeat | `0.0000` |
| synonym (`pick up`→`grasp`) | `0.0251` |
| target (`phone`→`box`) | `0.0375` |
| `do nothing` prompt | `0.0389` |
| left versus right wrist mapping | `0.0357` |
| adjacent selected times | `0.0357–0.0712` |

This proves deterministic sensitivity under controlled noise. It does not prove that the model grounded the correct object, that the action was physically correct, or that the policy could control the dual-arm robot.

## Why fixed noise matters

For paired prompts `L1` and `L2`, compare:

```text
a1 = policy(I, s, L1, epsilon_fixed)
a2 = policy(I, s, L2, epsilon_fixed)
```

Without fixing `epsilon`, `a1-a2` mixes language effect with generative sampling variation. Also reset or control any policy RNG that affects preprocessing/sampling.

## Better causal probes

Use a factorial intervention rather than one prompt pair:

```text
images: original / target-occluded / black / camera-swapped
prompt: correct / synonym / counter-target / shuffled / empty or no-op
state: fixed / small plausible perturbation
noise: fixed across each paired cell
```

Measure:

- final action difference by timestep and dimension;
- Flow velocity difference at each solver step;
- synonym versus counter-target ordering;
- language×visual interaction, not only main effects;
- saturation, continuity, velocity/acceleration/jerk under known units;
- repeated-call determinism and latency.

Sensitivity alone is not correctness. Add labeled object/action expectations, same-embodiment expert actions, simulator success, or closed-loop outcomes before making capability claims.

## Dataset and embodiment gate

Do not compare DROID `(7 joint velocity + 1 gripper position)` output against a dataset with dual-arm 14D joints, multi-joint hands, waist actions, or different units. Options are:

1. use the data only for vision/language diagnostics and label it `diagnostic-only`;
2. find same-contract DROID-like data;
3. define and train a new robot adapter plus normalization and output mapping;
4. fine-tune a base checkpoint on the target embodiment.

Never synthesize a scalar gripper from a multi-joint hand without a reviewed semantic mapping.

## Next-experiment decision

- If the question is **how language enters the model**, inspect tokens, masks, prefix shapes, and fixed-noise prompt interventions.
- If the question is **whether language is used**, run shuffled/counterfactual language under fixed image/state/noise.
- If the question is **whether grounding is correct**, combine target occlusion or spatial relocation with labeled expectations.
- If the question is **whether actions are correct**, require same embodiment/action semantics and expert or simulator evidence.
- If the question is **whether high-level planning works**, first obtain or implement a subtask-generation runtime; the public Flow-head call cannot answer it.
