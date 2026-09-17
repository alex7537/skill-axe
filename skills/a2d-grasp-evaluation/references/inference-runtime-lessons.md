# Inference runtime lessons

Use when reproducing A2D action-only DP/CFM/IMLE inference, investigating timing or compatibility gaps, or recovering an interrupted rollout batch. These lessons come from the September 2026 local evaluation audit; they define checks, not an implemented recovery service.

## Establish what actually runs

Separate the lightweight policy client from the Isaac/PsiLab gRPC simulator. Record each interpreter, imported module path, code hash, bundle hash, catalog and resolved USD dependencies. A headless simulator still requires Isaac runtime; it does not mean Isaac Sim is absent. Connecting to an existing remote server does not require copying all simulator assets to the client.

Observations in an online rollout come from simulated cameras and measured robot state after scene initialization/reset. Dataset replay is a separate mode. Trace enabled reset randomization and its seed in the server; do not assume all poses are randomized. Resolve the catalog's actual USD, scale, textures and initial pose rather than inferring identity from a bundle or catalog filename. Verify the actual scene-switch RPC semantics before treating it as target-asset hot reload.

## Semantic adapter preflight

Strict checkpoint loading and a finite `[16,13]` action output do not establish reproduction. Check normalization, joint order, action target semantics, image preprocessing, proprio history and encoder feature selection against the bundle.

For `timm_token_mode=cls`, verify the adapter returns the backbone's actual prefix/CLS feature. Slicing the first remaining patch after discarding prefixes gives the correct shape but wrong semantics. For spatial mode, compare the actual patch sequence with the original spatial adapter. Capture backbone outputs on a real observation and compare selected features directly; retain strict state-dict checks. Do not infer global CLS support from a patch in one run-local adapter.

Freeze effective sampling settings per algorithm, not merely similarly named YAML fields. Record Raw/EMA and Best/Latest independently. Different action-target definitions or enhanced-proprio inputs prevent a pure algorithm-only comparison, even when dimensions match.

## Timing and seeds are part of the protocol

Record the RPC sequence and both wall-clock and simulation timestamps. `Step → GT → contact` with Step-returned observations differs from an extra fresh `get_obs` before the next action. If physics advances between RPCs, telemetry latency changes command holding and the observed state. Removing expensive GT calls is therefore a protocol change until equivalence is demonstrated.

H16 means replan after 16 executed actions; it does not imply one RPC for all 16. Count action RPCs, physics steps, observation refreshes and replans separately. Report achieved cadence and reset/inference/Step/GT/contact latency rather than deriving it from nominal `rate_hz`. A batch action RPC may apply one physics step per action rather than the usual control decimation; inspect implementation.

Freeze policy-noise seed and scene/layout seed separately. Resetting the policy generator to 42 each episode reproduces its random-number sequence under the same call order and runtime; it fixes sampled values, not tensor shape or actions under different observations. It does not mean resetting to identical noise before every prediction. Record generator reset scope and verify scene-seed application and initial states independently.

## Success evidence and limits

Use the existing named success-profile contract. For the audited local diagnostic variant, relative lift was at least 0.05 m with thumb plus two other target-filtered finger force norms above 1e-4 N for five consecutive samples. These are dated settings, not universal defaults.

Five chunk-end samples, five individual control samples and five physics samples imply different durations. Measure timestamps; never translate them to a fixed hold time without evidence. GT and contact queried separately while physics advances are not a synchronized frame: label the diagnostic limitation and do not upgrade it to formal simultaneous success. Prefer signals recorded together after the same physics step when implementing a new protocol.

If the task is grasp-and-lift, report ever-sustained success as primary and final retention separately. A later drop does not retroactively erase that primary event. Keep reset-invalid and RPC-error attempts separate from grasp failures; report raw and valid-start denominators without silently discarding trials. At a step cap, inspect first threshold crossing and remaining streak length before claiming the budget was sufficient. A late crossing is a truncation candidate, not proof that more steps would succeed.

## Interrupted-batch diagnosis and bounded recovery

1. Resolve evaluator, queue, endpoint and server identities from process command lines, sockets and record growth. A live server or a successful health RPC does not prove required observation/contact/GT requests work. Use bounded read-only probes; do not reset or send actions during a monitor-only request.
2. Preserve completed episode records and the failed attempt, including the last fully recorded step, the failing RPC and its deadline. Distinguish the original RPC failure from the orchestration rule that stopped the batch. Current recovery cannot establish the historical root cause without contemporaneous traces.
3. Before an authorized resume, match the full experiment identity. Keep an attempt ID and explicit invalidity reason. A long timeout with continuing physics breaks rollout continuity: reset and rerun that episode rather than appending to the last recorded step. A timed-out Step may already have executed; do not blindly resend it.
4. If implementing automatic recovery, freeze finite attempt and wall-time budgets, read-only probe backoff and a circuit breaker. Escalate to a paused state with evidence when exhausted. Never retry forever or silently restart an unrelated simulator. Existing explicit stop/restart authorization remains valid within its stated scope.
5. Resume from durable completed-record coverage, deduplicated by model/scene/episode/contract identity. A successor scene waits for qualified predecessor coverage, not just a PID disappearing. Store recovery provenance; use a new namespace when changing protocol/schema and link the preserved source results.
6. Validate recovery with controlled failure injection before claiming unattended completion. Required cases include read timeout, uncertain action completion, evaluator exit and exhausted retries. A skill update alone does not add these runtime mechanisms.

For causal debugging, collect RPC queue, scene-lock wait, execution duration and timeout-time thread stacks. Shared-lock contention is a hypothesis unless measured. Report ETA conditional on observed completed-episode throughput and remaining coverage, with infrastructure pauses shown separately.

## Local baseline selected on 2026-09-14

For this user's subsequent A10 mixed-data comparisons, use Step RPC plus the historical per-action full GT and contact queries unless the user changes the protocol. Predict H16 once, apply each of its actions with Step, query GT/contact, and replan after the chunk. Preserve observation-return semantics; do not silently add get_obs, convert to action_sequence or remove telemetry for speed. Use the current same-observation lightweight pose/contact payload for the diagnostic success metric; the extra queries preserve the selected execution timing.

Freeze policy seed42 per episode, requested layout seed schedule, 300-action budget and latest/raw selection separately. Ten trials per model is the current pilot convention, not a universal requirement. Count target-contact plus relative lift>=5cm for five sampled action observations as an ever-success diagnostic; include policy guard stops in the operational denominator and report reset/RPC invalidity separately. Record the guard implementation because CFM and Wan adapters differ.

New timestamp evidence supersedes equating wall-clock waiting with simulated motion: the three local modes had median within-chunk simulated intervals near 1/30, 1/60 and 1/120 second despite wall throughput near 2,11,15 actions/s. This is a measured local outcome, not a guaranteed RPC frequency. Record simulator counters, especially video-history spans. Do not assume a 0.45-second RPC wall interval advances 0.45 simulated seconds.

Success percentages and dated model results belong in the linked experiment reports and Vault note; the skill owns this repeatable protocol. A future speedup should preserve explicit simulation-time action hold and observation cadence before being promoted as equivalent.
