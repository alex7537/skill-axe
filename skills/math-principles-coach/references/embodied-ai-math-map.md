# Embodied-AI Mathematical Map

Use only the section relevant to the active model or experiment.

## Behavior cloning and trajectory prediction

Track:

- observation/context `o`;
- demonstrated action or trajectory `a` with shape `[B,T,D_a]`;
- policy prediction `πθ(o)` or conditional distribution `pθ(a|o)`;
- masks for padding and invalid timesteps.

Core questions:

- Is the loss MSE, negative log likelihood, classification, or a mixture?
- Does a point estimate average multiple valid behaviors?
- Is the rollout distribution different from the demonstration distribution?
- Are coordinate frames and action scaling consistent?

Minimum tests: overfit one batch, shuffle observations, inspect error by timestep and action dimension, and run open-loop versus closed-loop evaluation.

## Flow Matching

Common construction:

```text
x₀ ~ base distribution
x₁ ~ data/action distribution
t ~ Uniform(0,1)
xₜ = (1-t)x₀ + tx₁
target velocity uₜ = x₁ - x₀
loss = E ||vθ(xₜ,t,c) - uₜ||²
```

This common form usually couples an independent `x₀` sample with a data pair `(x₁,c)`. Repository variants may use a different coupling, path, noise schedule, target, or conditioning `c`; read the actual implementation.

Under squared loss, the pointwise optimum is the conditional mean velocity:

```text
v*(x,t,c) = E[uₜ | xₜ=x, t, c]
```

This states the regression pressure precisely. It does not guarantee recovery of the particular `x₁` paired with each `x₀`, closed-loop robot success, or preservation of every mode under finite data and model capacity.

Explain:

- what randomness supplies `x₀` and `t`;
- why regression estimates a conditional velocity field;
- why training samples intermediate points but inference integrates an ODE;
- discretization error, solver steps, multimodality, and conditioning failures.

Minimum tests: plot target/predicted velocity norms versus `t`, overfit a tiny multimodal dataset, vary ODE steps, and fix random seeds. Compare endpoint distributions with task-relevant statistics chosen in advance—such as per-dimension moments, mode coverage, trajectory distance, constraint violations, and success—stratified by conditioning when applicable.

## Diffusion policies

Track clean action `x₀`, noise `ε`, noisy state `x_t`, schedule coefficients, timestep embedding, and whether the model predicts noise, clean data, or velocity.

Explain the exact forward corruption and reverse update used by the repository. Check that loss weighting, normalization, and inference scheduler agree.

Minimum tests: reconstruct at several noise levels, compare deterministic and stochastic samplers, vary denoising steps, and inspect per-timestep errors.

## IMLE and best-of-many objectives

Track the set of sampled candidates, distance metric, nearest-sample selection, and where gradients flow after selection.

Core questions:

- Does the candidate set cover multiple valid modes?
- Is the distance metric aligned with task success?
- How does sample count change optimization bias and cost?
- Can one candidate win for the wrong geometric reason?

Minimum tests: vary candidate count, visualize selected candidates, compare multiple distance metrics, and evaluate coverage separately from precision.

## World models

Separate representation, transition, observation reconstruction, reward, and termination models. State whether prediction is deterministic or stochastic and whether training uses teacher forcing.

Core failure modes: compounding rollout error, latent collapse, visually plausible but control-irrelevant predictions, and exploitation by the policy.

Minimum tests: one-step versus multi-step error, open-loop latent rollout, intervention tests, and downstream control performance with frozen components.

## VLA policies

Track visual tokens, language tokens, proprioception, temporal context, action tokenization or continuous heads, and attention/masking rules.

Separate pretrained representation capability from action-supervision effects. Check frame timing, camera/action alignment, normalization, and causal leakage.

Minimum tests: language shuffle, image occlusion, temporal permutation, action-delay sweep, camera removal, and task-level failure taxonomy.

## Trajectory metrics

For positions `p_t` sampled every `Δt`:

```text
velocity:     v_t = (p_t - p_{t-1}) / Δt
acceleration: a_t = (v_t - v_{t-1}) / Δt
jerk:         j_t = (a_t - a_{t-1}) / Δt
```

State coordinate frame, units, sampling rate, filtering, boundary handling, and aggregation. Do not compare jerk across different `Δt` or filters without normalization and disclosure.

Pair smoothness metrics with task success and constraint violations; a stationary failed trajectory can be perfectly smooth.
