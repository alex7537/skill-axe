# Generative policy inference ablations

Use this protocol to compare sampling controls on one frozen A2D checkpoint. Its purpose is to separate numerical generation quality from closed-loop control frequency.

## Classify the knob before testing

| Layer | Diffusion Policy | Conditional Flow Matching | Robot execution |
|---|---|---|---|
| Training path | beta/alpha-bar schedule and training timestep count | probability path and sampled continuous time | dataset action horizon |
| Inference start | highest reverse timestep or a justified lower start | normally the noise endpoint; a later start needs a compatible warm-start state | not applicable |
| Inference discretization | DDIM/DDPM step count and timestep spacing | ODE solver, integration step count, and time grid | not applicable |
| Physical feedback | unchanged | unchanged | execute horizon and achieved action cadence |

Do not interpret a larger beta, higher timestep, or later path position as a larger parameter gradient. Gradient magnitude also depends on prediction error and the network Jacobian; measure it if the claim matters.

## Freeze the comparison

Keep the exact bundle/checkpoint, weights variant, observation preprocessing, action semantics, normalization, initial poses, seeds, simulator state, success profile, and maximum executed actions fixed. Change one row of the table above at a time. Put the effective value in run metadata; do not trust a similarly named but inactive YAML field.

Recommended order:

1. Establish the existing bundle settings as the baseline.
2. Compare the generative start or time grid while keeping inference iterations and execute horizon fixed.
3. Select the start/grid, then compare inference iterations and end-to-end latency.
4. Select the generator settings, then compare execute horizons.

## Diffusion start-timestep rule

Starting below the maximum trained timestep is an inference ablation, not additional training. Initializing that lower timestep with standard Gaussian noise is defensible only when its forward marginal is still close to Gaussian (very small alpha-bar). At materially larger alpha-bar, pure-noise initialization is out of distribution; use a justified prior/warm start or reject the comparison.

Record the chosen timestep sequence, alpha-bar and signal coefficient at its start, predicted-x0 clamp/saturation fraction, action smoothness, inference latency, and rollout funnel. A lower start can reduce terminal amplification but can also reduce mode coverage or bias the sample.

## CFM start and integration rule

For a straight conditional path

```text
x_t = (1 - t) * noise + t * clean_action
```

pure Gaussian noise belongs at the noise endpoint. Starting at an interior `t` with the same pure noise does not match the trained path because the unknown clean-action component is missing. Treat a later CFM start as valid only when constructing a compatible warm start, for example from the unexecuted suffix of the previous chunk plus calibrated noise.

Changing ODE steps changes numerical integration accuracy, not the training objective. Compare a small ordered grid such as 5/10/20 steps, report solver and evaluation times, and stop increasing steps when rollout metrics and trajectory diagnostics saturate relative to latency.

## Execute-horizon rule

Execute horizon controls how many predicted actions are physically applied before a new observation and replan. At action rate `r`, open-loop duration is `execute_horizon / r`. Smaller values increase feedback frequency but also increase inference calls and action-chunk boundaries; they can improve correction while worsening boundary jitter.

Compare horizons only after fixing generator settings. Report requested and achieved action rate, action discontinuity at replan boundaries, contact/lift/retention, and end-to-end latency.

## Acceptance evidence

A candidate is promoted only when matched-seed rollout improves the frozen success profile or an explicitly chosen funnel stage without unacceptable regressions in:

- action velocity/acceleration/jerk and chunk-boundary jumps;
- multi-finger contact, lift persistence, and final retention;
- clamp/saturation or physical action-range violations;
- inference latency and achieved closed-loop cadence;
- infrastructure-invalid episode count.

Offline loss or smoother videos alone do not select the winner.

## Gotchas

- A config field named `num_inference_steps` may belong to CFM while Diffusion uses a policy-specific field. Verify factory wiring and runtime state.
- More DDIM/ODE iterations do not guarantee better rollout; model error and latency can dominate solver error.
- A lower Diffusion start can look numerically stable because it removes the hardest reverse region while also reducing diversity.
- A smaller execute horizon is not a better denoiser; it is a more frequent feedback controller.
- Preserve the same sampling seeds when measuring numerical changes, then use multiple rollout seeds to measure policy stochasticity.
