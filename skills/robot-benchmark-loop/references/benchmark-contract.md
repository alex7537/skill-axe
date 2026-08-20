# Robot benchmark contract

Use this reference when designing or auditing the portable interfaces between tasks, policies, runners, results, and lifecycle decisions.

## Contract layers

| Layer | Owns | Must not silently own |
|---|---|---|
| Suite registry | task IDs, dimensions, variants, embodiments, sample counts | policy code or checkpoint selection |
| Task adapter | reset, observation, action application, success/progress, termination | global aggregation |
| Policy adapter | preprocessing, model transport, reset, action decoding | task success logic |
| Runner | episode scheduling, deadlines, retries, artifacts, resume | scientific denominator changes |
| Result writer | atomic episode records and provenance | score weighting |
| Aggregator | coverage, per-task/seed/dimension metrics, uncertainty | selecting convenient completed subsets |
| Lifecycle | retry/promote/stop decision and return phase | changing frozen benchmark rules |

## Capability record

For each dimension require:

```text
name
claim
task families
paired perturbation or controlled variation
expected invariant
primary failure signal
critical gate
known confounders
```

## Task record

```json
{
  "task_id": "stack_bowls",
  "dimension": "generalization",
  "variant": "standard",
  "paired_task_id": "stack_bowls_random",
  "embodiment": "dual_arm",
  "config_revision": "sha256:...",
  "layout_selection_hash": "sha256:...",
  "required_episodes_per_seed": 25,
  "max_steps": 800,
  "success_predicate_version": "v1",
  "progress_score_version": "v1",
  "observation_schema": "obs-v1",
  "action_schema": "action-v1"
}
```

## Episode identity

An episode is immutable under the tuple:

```text
benchmark version
task/config/success-predicate revisions
policy adapter revision and checkpoint hash
environment/container and asset release
seed + layout ID + variant + episode index
observation/action/preprocessing/control schema
```

Resume may skip an episode only when the full tuple and a valid terminal result match.

## Status taxonomy

Use mutually exclusive terminal statuses:

- `success`: valid task episode and terminal success;
- `task_failure`: valid task episode but policy did not satisfy success;
- `timeout`: valid episode reached frozen step/deadline limit;
- `infrastructure_invalid`: simulator, asset, sensor, transport, or policy-process fault invalidated the sample;
- `abandoned`: frozen recovery policy could not produce a valid episode for the assigned sample;
- `cancelled`: authorized operator or budget gate ended execution.

Do not encode all non-success outcomes as `failure`. Task failure affects policy quality; infrastructure invalidity affects qualification and may permit a bounded replacement.

## Qualification gate

A benchmark result is qualified only if:

1. benchmark, policy, environment, task, asset, metric, and selection identities validate;
2. every expected task×seed×variant cell has its required valid episode count;
3. no duplicates or unexpected sample identities exist;
4. invalid, abandoned, crash, and retry rates satisfy frozen limits;
5. critical task/dimension gates are present and pass where required;
6. missing-result and aggregation policies were not changed after observing outcomes;
7. the result records whether it is diagnostic, validation, or sealed-holdout evidence.

## Aggregation choices

- Keep raw per-episode outcomes.
- Aggregate layouts within task and seed first.
- Report per-seed values before combining seeds.
- Make task weighting explicit; prefer equal task weights for capability summaries unless another policy is justified before evaluation.
- Make dimension weighting explicit; avoid allowing a dimension with more tasks to dominate accidentally.
- Preserve paired base/random differences as well as their combined generalization score.
- Report progress score and success rate separately.
- Use paired bootstrap or paired seed/layout differences for checkpoint comparisons when sample identities match.
- Never treat an incomplete partial average as official.

## Failure and retry policy

Freeze:

- which errors are infrastructure-invalid versus task failures;
- maximum retries per episode/process/task/run;
- whether the same layout is retried or replaced;
- maximum invalid/abandoned fraction;
- restart/resume identity and atomic state path;
- fail-fast conditions and kill switch;
- whether retry exhaustion disqualifies a task, dimension, or full run.

Changing retry rules after seeing a difficult policy or layout creates selection bias.

## Hybrid offline and closed-loop programs

When one benchmark decision depends on more than one evaluation track, such as an offline regression filter plus a closed-loop simulator benchmark:

- keep one top-level acceptance plan that names the tracks and their roles;
- keep one machine-readable run manifest per runnable track;
- define whether each track is `pre-gate`, `promotion-critical`, or `diagnostic-only`;
- define the cross-track decision rule before seeing outcomes;
- do not collapse dissimilar tracks into one scalar unless the weighting formula is frozen in advance.

## Recommended output tree

```text
benchmark_runs/<run_id>/
  run_manifest.json
  manifest_validation.json
  assignment_manifest.json
  episodes/<task>/<seed>/<layout>/episode_result.json
  artifacts/<task>/<seed>/<layout>/...
  logs/runner/... and logs/policy/...
  coverage.json
  invalidity_report.json
  aggregate.json
  report.md
  decision.json
```

Filenames aid navigation; file contents and hashes establish identity.

## PSI handoff

For PSI WAM:

- obtain task/action/video metric definitions from `$psi-wam-learning-coach`;
- obtain split/holdout exposure rules from `$dataset-split-protocol`;
- pass qualified `aggregate.json`, `coverage.json`, `invalidity_report.json`, and `decision.json` to `$robot-ml-lifecycle`;
- if evaluation rejects the checkpoint, return to the earliest invalidated lifecycle phase rather than mutating the benchmark contract.
