---
name: robot-benchmark-loop
description: Design, audit, implement, or run reproducible robot-policy benchmarks and closed-loop simulation or real-robot evaluation harnesses. Use when building a benchmark like RoboDojo, defining task suites and capability dimensions, integrating policy adapters, orchestrating seeded rollouts, validating result manifests and coverage, aggregating scores, adding resume/failure handling, or connecting evaluation to a robot-ML experiment loop. Do not use for training-budget design or a single isolated offline metric calculation.
---

# Robot Benchmark Loop

Treat a benchmark as a versioned verification product, not a collection of eval scripts. Bind every score to the exact policy, task suite, environment, sampling plan, runtime, metric implementation, and coverage state that produced it.

## Operating contract

- Freeze a machine-readable run manifest before scientific rollouts. Use [assets/benchmark-run-manifest.template.json](assets/benchmark-run-manifest.template.json) as a starting point and validate it with `scripts/validate_benchmark_manifest.py`.
- When evaluation mixes offline and closed-loop tracks, freeze a top-level acceptance contract first. Use [assets/psi-policy-benchmark-plan.template.md](assets/psi-policy-benchmark-plan.template.md) as a planning shape, then keep one manifest per runnable track.
- Separate three outcomes: infrastructure validity, policy/task outcome, and scientific qualification. A process exit code is not a task result; a task result is not a qualified benchmark score.
- Define tasks from capability claims and failure modes. Object or texture reskins alone do not establish generalization, memory, precision, long-horizon behavior, or open-ended instruction following.
- Keep the policy interface narrower and more stable than any model implementation. Resolve observation, action, reset, batching, timeout, and transport semantics in an adapter.
- Preserve per-episode artifacts before aggregation. Never make an aggregate the only surviving evidence.
- Record invalid, unstable, abandoned, crashed, timed-out, and retried episodes explicitly. Do not silently shrink the denominator.
- Keep benchmark code and task success logic independent of the policy under test. For official or promotion decisions, use a maker/checker boundary.
- Do not infer permission to start cloud jobs, operate robots, expose a sealed holdout, publish results, or modify a remote leaderboard.

## Route the task

- Read [references/benchmark-contract.md](references/benchmark-contract.md) when designing a suite, run manifest, result schema, aggregation rule, or promotion gate.
- Read [references/robodojo-patterns.md](references/robodojo-patterns.md) when borrowing RoboDojo's task registry, server/client split, seeded layout replay, recovery, sweep, or reporting patterns.
- Read [references/psi-policy-eval-bridge.md](references/psi-policy-eval-bridge.md) when working in `psi-policy` or combining WAN 82D offline metrics with MolmoSpaces simulator evidence under one promotion decision.
- Use `$psi-wam-learning-coach` for WAM-specific codec, future-video, conditioning, action, rollout, and WorldArena/Psi-WMBench metric semantics.
- Use `$dataset-split-protocol` when benchmark independence, grouped/temporal leakage, diagnostic exposure, or sealed holdout roles are unresolved.
- Use `$robot-ml-lifecycle` for the larger source→data→train→evaluate→package/release loop. This Skill owns the evaluation product and evidence contract inside its `evaluate` phase.

## Build the benchmark in layers

### 1. State the claims

For each capability dimension, write the claim, perturbation, expected invariant, failure signal, and minimum episode coverage. A dimension name without a falsifiable task family is taxonomy, not evidence.

Prefer paired constructions where possible:

- base versus randomized layout for generalization;
- visible cue versus delayed/occluded cue for memory;
- generous versus tight tolerances for precision;
- short versus long composition for horizon;
- familiar versus compositional language or object sets for openness.

### 2. Freeze identities

Record before rollout:

- benchmark name/version and Git commit;
- task and capability registries plus hashes;
- external asset/layout release and selection hash;
- environment/simulator version and immutable container digest when available;
- policy adapter revision, checkpoint role, and checkpoint SHA256;
- observation/action schema, preprocessing, normalization, control frequency, and action horizon;
- seeds, layouts, variants, per-task episode counts, time/step limits, and retry policy;
- metric code revision, direction, aggregation, qualification, and missing-result policy.

If any identity changes, start a new benchmark run. Do not append incompatible episodes to the old score.

### 3. Validate task contracts

Require one registry record per runnable task with:

- task ID, capability dimension, standard/random/diagnostic role, embodiment, and config path;
- deterministic reset/layout identity for each sample;
- meaningful terminal success predicate;
- optional progress-score state machine with monotonic semantics;
- maximum steps and termination reason;
- observation/action requirements;
- asset/config validation and a smallest runtime smoke test.

Check task/config/class names and labels mechanically. Review success predicates for trivial truth, unreachable conditions, dependence on hidden policy information, or incorrect final-state timing.

### 4. Stabilize the policy boundary

Define an adapter contract such as:

```text
reset(run_id, task_id, episode_id, seed, schema_versions)
act(observation, step, deadline) -> action | explicit error
close(reason)
```

Record protocol, endpoint, timeouts, batching, reset acknowledgement, action mode, shape/unit/range validation, and policy-side logs. Keep simulator and policy dependencies separable so one policy can be evaluated across the suite without benchmark-specific model edits.

### 5. Layer validation before scale

Advance through distinct gates:

1. static inventory/config validation;
2. dry-run command and manifest rendering;
3. one task, one seed, one episode;
4. small capability smoke set;
5. full per-task episode counts;
6. multiple frozen seeds;
7. optional parallel execution, proven equivalent to sequential execution on a golden subset.

Infrastructure smoke success only proves that the path ran and produced a valid artifact. It does not certify policy quality.

### 6. Write atomic episode results

Each episode should record at least:

```text
run_id, benchmark_version, task_id, dimension, variant
policy_id, adapter_revision, checkpoint_sha256
seed, layout_id, episode_index
status, terminal_reason, success, progress_score
steps, wall_time, inference_latency summary
retry_count, invalid_reason, artifact paths
observation/action schema versions and environment identity
```

Write results atomically. Make resume idempotent by keying completed work on the full immutable episode identity, not on filenames or exit codes alone.

### 7. Qualify before aggregating

Before publishing an aggregate:

- verify required task×seed×variant coverage;
- reject duplicates and unexpected episodes;
- enforce invalid/abandoned/crash limits;
- confirm result schema and source identities;
- preserve base/random halves and per-seed results;
- state macro versus micro weighting;
- compute uncertainty or paired differences when comparing policies;
- expose partial progress separately from official qualified results.

Do not average only the tasks that happened to finish and call it the benchmark score.

### 8. Close the decision loop

Return a structured decision:

- `promote`: frozen primary and critical gates passed;
- `retry-eval`: only infrastructure/evaluator assumptions failed;
- `new-experiment`: policy/data/training hypothesis must change;
- `stop`: evidence rejects the current direction or budget/gate ends the run.

When evaluation invalidates an earlier lifecycle assumption, return to the earliest affected phase without rewriting completed evidence.

## Deliverables

For benchmark design or audit, produce the smallest useful set of:

- capability/task matrix;
- multi-track acceptance matrix when offline and closed-loop evidence both matter;
- run manifest and validation output;
- policy adapter contract;
- representative execution trace;
- episode result schema;
- qualification and aggregation rules;
- smoke/full-run commands;
- failure taxonomy and retry limits;
- gap list against the current repository;
- exact next gate and evidence needed to pass it.

## Gotchas

- Exit `0` plus a result file only proves infrastructure smoke, not scientific completeness.
- Replacing unstable scenes until the target count is met can bias the evaluated distribution; report every invalid and abandoned layout.
- Selecting the latest timestamped result can mix stale or incompatible runs unless immutable identities are checked.
- Hard-coded capability lists duplicated in task inventory and summarization code will drift; generate both from one versioned registry.
- Partial averages are useful operationally but must be visibly disqualified from official comparison.
- Fixed `N` first layouts are reproducible only when the layout release and ordered selection hash are frozen.
- Parallel task grouping by estimated duration changes scheduling, not the statistical sample. Verify sequential/parallel equivalence and record the assignment manifest.
- Retrying simulator crashes is different from retrying policy failures. Only infrastructure-invalid episodes may be replaced under the frozen rule.
- A progress score can reward unintended intermediate states. Validate state transitions and terminal success independently.
- Benchmark-owned preprocessing or control interpolation can materially change policy behavior; include it in the versioned contract.
- Repository README, package metadata, and license file can disagree. Resolve the legal source of truth before redistributing code or assets.
