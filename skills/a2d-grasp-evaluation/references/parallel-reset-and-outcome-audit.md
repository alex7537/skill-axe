# Parallel reset and outcome audit

Use for multi-environment evaluation snapshots and for reports that assign failure stages from nearest-demonstration matches. These checks were distilled from an A2D handoff audit; numerical examples illustrate failure modes, not reusable benchmark baselines.

## Frozen snapshot and denominators

- Verify packaged hashes, then recompute counts from the frozen per-trial records. Do not merge later live records or supporting runs with different assets, schemas, or execution modes.
- Report raw, infrastructure-invalid, reset-invalid, and valid-start counts separately, with an explicit precedence rule if invalidity flags overlap. Show both raw-denominator and valid-start success rates with labels.
- A filename containing a requested episode count does not establish completed coverage. Equal raw counts do not establish equal valid counts or matched initial states.
- Identify the actual catalog asset and compare it with run/dataset names. Naming disagreement is a provenance issue; without training imagery, do not claim independently verified training-object identity.

## Multi-environment reset control flow

Trace client reset calls through RPC to the simulator implementation:

1. Does the multi-environment branch actually apply each requested seed? A seed recorded in JSONL or used for policy noise does not prove it controlled scene randomization.
2. Does resetting one environment step the whole scene? Sequential blocking resets can advance already-reset environments during each later environment's settling loop.
3. Are first policy observations refreshed after all resets and settling? Cached observations returned by early reset calls can precede the common initial-height measurement and first action.
4. Are initial pose, velocity, target identity, and observation timestamps recorded? An initial-height floor rejects obvious fallen objects but does not establish a stable, equivalent layout.

For example, eight sequential resets with 200 global settling steps each expose the first environment to up to seven additional settling loops. Zero RPC errors does not exclude this contamination. Treat matched record seeds as unqualified for paired tests until reset repeatability and initial-state equivalence are verified.

A repair candidate is a coordinated batch reset and settle followed by fresh observations for all environments, with isolated randomization. Validate the simulator's actual semantics before adopting it, and use a new evaluation namespace after changing reset behavior.

## Reference flags versus physical failure

- Count successful trials for which each readiness flag is false. In one audited snapshot, 42 of 216 sustained successes failed the hand-actual reference flag. Such a flag cannot be a necessary grasp-success gate.
- Inspect reduction and conditioning: minimum over all frames versus only arm-ready frames, reference choice by nearest arm pose, and whether command/actual readiness occur at the same time. Sequential and parallel evaluators can share field names while computing different diagnostics.
- A lagged tracking metric reduced to the minimum over time and then over lags only proves one favorable match. It can hide poor tracking during closure under load. Prefer contact-window error distributions, sustained threshold coverage, and lag-specific traces when available.
- Keep heuristic failure-label counts, but describe them as labels. Do not equate hand-reference mismatch with weak drive strength, actuator failure, or incorrect policy commands.
- With summary-only evidence, a defensible task taxonomy is: never achieved valid target contact; contact occurred without sustained contact/lift; sustained contact/lift occurred but final condition was absent. These are outcomes, not established causes.

## Three distinct final metrics

For trials with initial height z0 and frozen lift threshold h, distinguish:

| Metric | Definition | What it cannot establish |
|---|---|---|
| Ever sustained success | contact and z-z0 >= h for the required consecutive sampled frames | final retention |
| Final height | final z-z0 >= h | final target contact |
| Final contact and height | final contact AND final z-z0 >= h | a sustained terminal streak |

Report final conditions over all valid trials and, when useful, among ever-successful trials. A maximum streak anywhere in the episode cannot recover the terminal streak. Missing final-contact fields mean unknown, not false. Do not merge historical `final_lift` fields until their formulas are checked.

Absence of the final condition does not by itself distinguish dropping, placing back, contact loss, or measurement failure. Binary multi-finger contact also does not prove opposing force closure or absence of slip.

## Hypotheses that require additional evidence

- A 400-action rollout extending beyond demonstrations of roughly 140–200 steps motivates a post-demonstration replanning hypothesis. Verify first-success and first-loss timing before attributing retention failures to that extension or testing a HOLD intervention.
- A validation-action-MSE Best checkpoint performing worse than Latest shows selection misalignment in that observed comparison. It does not establish general negative correlation, undertraining, or an intrinsic benefit from multitask data.
- Same-config Best/Latest comparisons and single-task/multitask comparisons have different controls; inspect epoch, split, normalization, observation semantics, and bundle identity.
- Wall-clock elapsed time may include reset and RPC overhead. Executed-actions/elapsed is an inclusive throughput measure, not necessarily control cadence or simulated frequency.

Prioritize reset validity and observation alignment, then a bounded matched comparison, then contact-window telemetry. Avoid changing the model, sampling, horizon, drive parameters, and termination behavior together.
