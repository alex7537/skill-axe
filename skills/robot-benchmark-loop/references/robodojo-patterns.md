# RoboDojo patterns and cautions

Use this reference for design inspiration, not as permanent truth about RoboDojo or PSI. Re-read the live repository before asserting current paths or counts.

## Evidence snapshot

- Repository: https://github.com/robodojo-benchmark/RoboDojo
- Reviewed default-branch commit: `57b8c52424ff1198ade242505656511515c58792`
- Reviewed: 2026-08-20
- Repository role: evaluation-only simulator, task, orchestration, and result layer; policy implementations and servers are delegated to the XPolicyLab submodule.
- Observed inventory: 42 canonical simulation tasks plus 12 runnable `_random` variants, organized into generalization, memory, precision, long-horizon, and open dimensions.

## Representative execution path

```text
scripts/robodojo.sh eval|smoke|benchmark
-> scripts/internal/run_policy_eval.sh or smoke_all_tasks.sh
-> policy setup server script (policy-directory CWD)
-> WebSocket readiness check
-> scripts/eval_policy.sh
-> src/eval_client/main.py
-> compose sim/scene/camera/robot/task/deploy config
-> dynamic task registry
-> create_eval_env(...)
-> seeded layout reset and stability check
-> XPolicyLab deploy adapter eval_one_episode[_batch]
-> observation -> WebSocket policy -> validated action -> simulator step
-> task reward/progress/terminal checks
-> per-episode video + _result.json + resume manifest
-> sweep summary and leaderboard-style aggregation
```

High-value evidence:

- `scripts/robodojo.sh`: public CLI and command routing.
- `scripts/internal/task_inventory.py`: task/config/class inventory and capability taxonomy.
- `scripts/internal/smoke_all_tasks.sh`: task selection, multi-GPU grouping, resume, pass/fail smoke gate, logs, JSON/Markdown summaries.
- `scripts/internal/run_policy_eval.sh`: policy server/client lifecycle, readiness wait, CWD contract, cleanup.
- `scripts/eval_policy.sh`: simulator launch and bounded process restart.
- `src/eval_client/main.py`: config composition, seed batches, PhysX recovery, resume.
- `src/eval_client/eval_env.py`: adapter calls, action execution, task outcome, progress score, video/result artifacts.
- `env/seed_manager/seed_manager.py`: external layout replay and resume filtering.
- `env/reward_manager/reward_manager.py`: final predicates and staged/transition progress scores.
- `scripts/internal/summarize_result.py`: base/random pairing, seed coverage, partial versus complete tables.

## Patterns worth borrowing

### Benchmark and policy ownership are separated

RoboDojo owns simulator, tasks, assets/config validation, rollout client, and results. XPolicyLab owns policy dependencies, checkpoints, deployment config, server, and `deploy.py` adapter functions. The WebSocket boundary prevents every benchmark task from importing every policy stack.

For PSI, keep WAM/action-policy loading behind one adapter. The benchmark should validate observations/actions and record policy identity, not understand each model architecture.

### Capability dimensions drive task selection

Tasks are grouped by claimed capability rather than only scene category. Generalization pairs base tasks with `_random` variants; other dimensions target memory, precision, long horizon, and open instructions.

For PSI, define which WAM or policy claim each suite falsifies. Add a task only when it changes coverage or isolates a failure mode.

### Layout replay separates samples from process RNG

`SeedManager` maps layout IDs to external saved scene files. Resume excludes completed or abandoned IDs. This is stronger than recording only a global RNG seed, but still requires an asset/layout release hash.

### Task outcome and progress are separate

Tasks define terminal success with reward checks and may register staged process scores. For example, a manipulation task can receive partial progress before final success. This supports diagnosis without replacing the binary task gate.

### Recovery preserves progress

The client writes atomic resume manifests, cleans unfinished video streams, keeps a stable run ID through restarts, bounds in-process and shell-level retries, and records task logs. This is a useful pattern for long simulator sweeps.

### Scale follows smaller gates

The repository exposes static inventory checks, doctor, dry-run, single eval, smoke, benchmark, resume, fail-fast, and sequential or duration-balanced multi-GPU execution. This makes the smallest sufficient verification loop available before expensive runs.

## Cautions and improvements

### Smoke PASS is intentionally weak

In `smoke_all_tasks.sh`, PASS requires exit code zero plus `_result.json` with `eval_time >= 1`. This is suitable for infrastructure smoke only. It does not prove the native episode count, all required seeds, result identity, or policy quality.

### Invalid-layout accounting can bias results

Unstable or broken environments may be excluded and replaced. Official evaluation should report attempted, valid, invalid, abandoned, retried, and completed layouts, enforce a frozen invalid policy, and investigate correlation between invalidity and task difficulty.

### Aggregation depends on external conventions

The summarizer uses fixed seed IDs, first-N episode slices, base/random pairing, and latest timestamp folders. Freeze the ordered layout selection and verify every result's immutable identities before aggregation.

### Registry duplication risks drift

Capability groups appear in both task inventory and result summarization. A reusable benchmark should generate inventory, runner selection, coverage expectations, and aggregation from one versioned registry.

### Partial overview scores are not official scores

RoboDojo marks incomplete progress with a dagger and can compute partial averages. Preserve that operational convenience, but disqualify partial results from promotion or cross-policy ranking.

### Runtime balancing needs provenance

The sweep partitions tasks using embedded duration estimates and improves groups by move/swap search. Record the assignment and actual runtimes; stale weights should affect throughput only, never episode selection or score.

### Automated tests are limited

The reviewed repository contains no conventional test files; acceptance relies on static inventory, shell/config checks, dry runs, and simulator smoke tests. Extract pure manifest, aggregation, and reward-state logic into unit-testable components where possible.

### License metadata conflicts

At the reviewed commit, `LICENSE` and `pyproject.toml` say MIT while the README says non-commercial research. Do not infer redistribution terms; resolve the conflict with the maintainers or authoritative release metadata.

## Mapping to the current PSI repository

The current PSI repository already has:

- active-dimension 82D offline metrics, source/view summaries, checkpoint sweeps, timing, and W&B reporting;
- WAM evaluation protocols that separate codec, future prediction, conditioning, action, rollout, and closed-loop claims;
- a MolmoSpaces simulator evaluation entry and a closed-loop WAM policy;
- a lifecycle control plane with immutable cycles, phase gates, retry limits, and promotion decisions.

The missing product layer is a single benchmark contract that binds:

- capability/task registry;
- simulator/environment adapters;
- policy adapter and checkpoint hash;
- frozen seed/layout/variant matrix;
- episode/result schema;
- smoke versus qualified-run gates;
- coverage, invalidity, aggregation, uncertainty, and promotion rules;
- resume and assignment manifests.

Use the generic contract in `benchmark-contract.md` to add that layer without replacing the existing metric or lifecycle skills.
