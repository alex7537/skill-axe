---
name: a2d-grasp-evaluation
description: Design, launch, resume, monitor, compare, and report A2D imitation-learning grasp rollout evaluations using a diagnostic funnel for arm arrival, hand commands, hand tracking, target contact, lift, and retention. Use for A2D checkpoint comparisons, Diffusion/CFM inference-start or sampling-step ablations, execute-horizon ablations, grasp/lift success analysis, evaluator progress checks, failure attribution, packaging rollout evidence, or building a traceable success-video GIF gallery. Use with a2d-model-swap-only when the pipeline must remain unchanged; use robot-benchmark-loop for formal multi-task qualification.
---

# A2D Grasp Evaluation

Diagnose the first failed stage of grasp execution instead of hiding arm, hand, contact, lift, and infrastructure failures behind one success percentage.

## Route the request

- Read [references/evaluation-methodology.md](references/evaluation-methodology.md) before designing, launching, or interpreting an evaluation.
- Read [references/generative-inference-ablation.md](references/generative-inference-ablation.md) before comparing Diffusion/CFM sampling start, inference iterations, timestep grids, ODE solvers, or execute horizons.
- Read [references/success-gallery-packaging.md](references/success-gallery-packaging.md) before selecting rollout videos or building a GIF/MP4 success gallery.
- Use `$a2d-model-swap-only` when the comparison must vary only a checkpoint or deployment bundle.
- Use `$robot-benchmark-loop` when several tasks, seeds, models, or simulator tracks need a frozen run manifest, coverage qualification, aggregation, and promotion decision.
- Use `$remote-policy-bundle` first when the requested checkpoint still needs to be exported and verified from a remote machine.

Choose one mode before acting:

- **Design:** freeze the comparison and success contract without launching.
- **Launch/resume:** preflight and start the explicitly requested persistent evaluator.
- **Monitor:** inspect process/socket state and result growth read-only.
- **Compare:** use matched seeds and equal completed counts; change one variable.
- **Diagnose:** find the earliest funnel stage that separates configurations.
- **Report/package:** preserve identities, exact counts, failure taxonomy, and artifact paths.

## Freeze a fair evaluation

Record before launch:

1. Bundle paths, roles, SHA-256 values, and compatibility with the observation/action schema.
2. Evaluator revision or hash, scene/server identity, and RPC capability/readiness.
3. Models, order, episode/layout seeds, requested counts, execute horizon, maximum actions, action rate, sampling mode, and output namespace.
4. Arm-arrival reference, hand-target reference, tracking lags, contact rule, lift thresholds, persistence, final-state rule, and infrastructure-error policy.
5. Resume schema and experiment identity. Start a new namespace when the model matrix, horizon, criterion, evaluator, or record schema changes.

Alternate configurations episode by episode when simulator warming, scene drift, or long-run server degradation could bias sequential blocks.

## Measure the funnel

Keep numerator and denominator for each stage:

1. Valid episode completed without evaluator/server/RPC error.
2. Actual 7D arm pose reached the frozen pre-lift neighborhood.
3. Commanded 6D hand target reached the intended pre-lift shape.
4. Actual 6D hand pose reached the intended shape.
5. Command-to-actual tracking passed at the frozen lags.
6. Valid target-object multi-finger contact occurred.
7. Contact and relative object lift occurred simultaneously for the persistence gate.
8. Contact/lift remained at the final frame.

Keep maximum and final relative lift separate. Keep contact-only, transient lift, sustained lift, and retained lift separate. Do not blame the hand when arm arrival or infrastructure failed first.

## Use named success profiles

Never introduce a threshold after inspecting the model outcomes. Select a named profile before evaluation or define a new versioned one.

The historical `target-contact-lift-5f-v1` profile is:

- object height relative to the episode's initial height;
- thumb contact plus at least two non-thumb fingers, at least three fingers total;
- a frozen per-contact force floor;
- primary tier: simultaneous valid contact and relative lift at least 5 cm;
- higher diagnostic tier: the same condition at least 10 cm;
- five consecutive sampled control frames;
- report ever-sustained and final-retained separately.

Use this profile only when it matches the intended task and simulator signals. Otherwise freeze a new profile and do not compare its percentages with older profiles as if they were the same metric.

## Launch and monitor safely

- A request to evaluate authorizes launching the named evaluator, not killing an existing evaluator or restarting the simulator.
- Before launch, inspect evaluator processes, parent/process groups, established client sockets, server listener, and result growth in the relevant host namespace.
- If a prior evaluator owns the same endpoint/environment, show its identity and outputs and obtain explicit confirmation before stopping it. Never stop the Isaac/gRPC server unless separately requested.
- If host visibility or permission is insufficient, stop before claiming exclusivity.
- Launch long evaluations under an existing persistent supervisor or terminal; do not rely on one tool call staying alive.
- After launch, verify one active evaluator, one intended client owner, advancing status timestamps, and growing append-only records.
- Treat `status=running` without a live process/socket or file growth as stale. Treat concurrent controllers of one single-environment server as contamination.

Resume only from records whose schema and full experiment identity match. Record infrastructure-invalid and contaminated episodes explicitly; do not convert them to grasp failures.

## Summarize and decide

Use `scripts/summarize_a2d_eval.py` for read-only aggregation of summary JSON files. At minimum report:

| Configuration | Completed/requested | Sustained 5 cm | Sustained 10 cm | Valid contact | Errors |
|---|---:|---:|---:|---:|---:|

Add arm/hand/tracking funnel counts, maximum/final lift distributions, streaks, achieved cadence, exact hashes, seed schedule, criterion version, and evaluator status when diagnosing or comparing.

Treat initial episodes as smoke validation only. Compare incomplete runs only at equal completed counts with identical seeds; do not rank models from asymmetric or tiny samples.

For a success-video gallery, use `scripts/build_success_grid.py` when its v17 four-model filename contract matches the source collection. Keep a machine-readable clip manifest beside the GIF and MP4; the visual is showcase evidence, not a substitute for the evaluation report.

## Gotchas

- Successful replay validates much of the execution chain, not policy reproduction.
- Joint-space compatibility does not prove matching preprocessing, temporal offset, action semantics, or chunk sampling.
- `hand_target` is control intent; `hand_actual` includes lag, load, deformation, and actuation response.
- Do not reject a predicted chunk solely because an unexecuted tail leaves the training distribution; separate executed-prefix, full-chunk, and physical-limit diagnostics.
- Smaller execute horizons add feedback and sampling boundaries; larger horizons reduce boundaries and increase open-loop duration. Report both horizon and achieved action cadence.
- Generative inference iterations and execute horizon are different controls: the former changes how one action chunk is generated; the latter changes how long the robot remains open-loop before observing again. Never change both in one comparison.
- Height-only success counts strikes or throws; contact-only success counts failed lifts; final-height-only misses a valid grasp followed by a drop.
- Nominal `rate_hz` is not achieved frequency when observation, contact, ground-truth, rendering, and inference RPCs add latency.
- A reference selected by nearest arm pose may not be object-specific ground truth.
- GitHub README does not reliably autoplay embedded MP4; use a size-controlled looping GIF and keep MP4 as the higher-quality link.
- GIF/H.264 dimensions should be even. A nominal 100×75 tile may be rounded during chroma scaling and then fail padding; 96×72 tiles produce a stable 960×720 10×10 grid.
