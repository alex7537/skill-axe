# PSI policy benchmark bridge

Read this reference when the current repository is `psi-policy` and the benchmark request spans both:

- WAN 82D offline evaluation (`metrics.json`, checkpoint sweeps, source/view slices); and
- MolmoSpaces closed-loop simulator evaluation (`summary.json`, `episode_results.jsonl`, `results.csv`, sharded submission outputs).

Treat these as two evaluation tracks under one acceptance decision, not as one blended score by default.

## Evidence snapshot

- Reviewed repository: local `psi-policy`
- Reviewed on: 2026-08-20
- Relevant evidence:
  - `docs/wan_82d_offline_eval.md`
  - `psi_policy/eval_wan_82d_sweep.py`
  - `psi_policy/eval_molmospaces_sim.py`
  - `run_official_ms_pick_submission_multigpu.sh`

## Current repository shape

The repository already has strong track-local tooling:

- WAN 82D offline eval can sweep checkpoints, freeze current-FSDP compatibility, write one `metrics.json` per checkpoint, and maintain `sweep_summary.json`.
- MolmoSpaces sim eval can resolve benchmark sources/directories, infer checkpoint action semantics, run official or smoke benchmarks, write `summary.json`, `episode_results.jsonl`, `results.csv`, shard manifests, and merged submission bundles.

The main missing product layer is a top-level benchmark contract that says:

- which track is diagnostic versus promotion-critical;
- which identities must match across tracks;
- which failures disqualify a run;
- how much coverage is required before a checkpoint may advance;
- what lifecycle decision follows from each track outcome.

## Use a two-track acceptance contract

Define a benchmark plan with at least these tracks.

### Track A: WAN 82D offline

Use this as the fast filter and regression detector, not as sole evidence for embodied quality.

Freeze:

- checkpoint SHA256 and checkpoint role;
- eval code revision and metric implementation revision;
- dataset revision, source/view roster, and sampling rule (`samples_per_source` or full coverage);
- active-dimension semantics from `action_mappings`;
- normalizer source (`policy_normalizer` and `metric_normalizer`);
- checkpoint selection rule for sweeps.

Collect:

- one `metrics.json` per checkpoint;
- `sweep_summary.json` when sweeping;
- optional W&B run name and step-aligned logging only as convenience, not source of truth.

Qualify only if:

- every required source/view slice is present;
- active semantic blocks are evaluated under the frozen rule;
- timing/runtime failures are explicit rather than silently skipped;
- the comparison uses the same metric and normalization semantics.

Typical gate role:

- `required`: no major offline regression versus baseline on primary source/view summaries;
- `diagnostic`: block-level or threshold metrics explain likely failure causes before sim eval.

### Track B: MolmoSpaces closed-loop simulator

Use this as the benchmark-style embodied gate.

Freeze:

- benchmark directory or benchmark source plus selector;
- benchmark asset release and ordered episode/layout selection;
- checkpoint SHA256 and inferred action semantics;
- observation camera set, action chunk size, control/task horizon, and worker/shard layout;
- success condition, retry/resume policy, and shard assignment manifest.

Collect:

- per-run `summary.json`;
- per-run `episode_results.jsonl`;
- `results.csv` and any benchmark-named CSV;
- shard `manifest.json` files and merged `submission_manifest.json`;
- preview videos only as debugging artifacts.

Qualify only if:

- expected benchmark episodes/houses are covered under the frozen selection;
- shard resume did not silently drop required samples;
- success/invalid/abandoned counts are visible and attributable;
- merged outputs preserve the original benchmark identity.

Typical gate role:

- `required`: closed-loop success or official benchmark CSV summary meets the promotion threshold;
- `diagnostic`: shard logs, preview videos, and episode JSONL expose failure modes without changing score semantics.

## Cross-track decision contract

Do not average Track A and Track B into one scalar unless the benchmark explicitly defines that formula before evaluation.

Use a decision table such as:

| Track A WAN offline | Track B MolmoSpaces sim | Decision |
|---|---|---|
| pass | pass | `promote` |
| pass | infrastructure-invalid | `retry-eval` |
| pass | fail | `new-experiment` |
| fail | not-run | `stop` or `new-experiment` |
| fail | pass | `new-experiment` unless Track A is declared diagnostic-only |

Make the role of each track explicit:

- `promotion-critical`: failure blocks promotion.
- `diagnostic-only`: failure informs debugging but does not block promotion by itself.
- `pre-gate`: must pass before the next track launches.

## Minimal benchmark-plan fields

Use [assets/psi-policy-benchmark-plan.template.md](../assets/psi-policy-benchmark-plan.template.md) and fill:

- objective and candidate checkpoint set;
- baseline and comparison rule;
- Track A identities, commands, artifacts, pass/fail thresholds;
- Track B identities, commands, artifacts, pass/fail thresholds;
- invalidity/retry policy per track;
- final promotion rule and lifecycle return phase on failure.

Keep each runnable track's manifest separate. The top-level plan decides how the track outputs combine into one lifecycle decision.

## Gaps to call out in the current repository

- No single top-level acceptance file binds WAN offline and MolmoSpaces sim into one benchmark decision.
- No canonical capability registry links offline claims, sim tasks, and promotion thresholds.
- MolmoSpaces task outputs are rich, but cross-run coverage and invalidity qualification are still mostly encoded in shell workflow and merged summaries rather than one frozen contract.
- WAN offline sweeps record checkpoint-level metrics, but there is no built-in benchmark-level decision artifact that says which regression is promotion-blocking versus merely diagnostic.

## Recommended next gate for a design-only request

When the user asks for design and acceptance thresholds without running eval:

1. write the two-track acceptance matrix;
2. freeze the exact artifacts each track must emit;
3. define qualification and disqualification rules;
4. define the lifecycle decision table;
5. stop before launch commands unless the user separately authorizes execution.
