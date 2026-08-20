# PSI Policy Benchmark Plan

Use this template when combining WAN 82D offline evaluation and MolmoSpaces simulator evaluation into one benchmark loop without immediately launching either track.

## Goal

- Objective:
- Candidate checkpoints:
- Baseline or incumbent:
- Promotion scope:

## Shared identities

- Repository commit:
- Policy/config revision:
- Checkpoint SHA256 or selection set:
- Dataset/split revision:
- Normalization/preprocessing revision:
- Benchmark asset release:
- Decision owner:

## Track A: WAN 82D Offline

- Role: `pre-gate` | `promotion-critical` | `diagnostic-only`
- Entry command:
- Frozen sampling rule:
- Frozen source/view roster:
- Primary metrics:
- Regression thresholds:
- Required artifacts:
  - `metrics.json`
  - `sweep_summary.json` if sweeping
- Disqualifiers:
- Retry policy:

## Track B: MolmoSpaces Simulator

- Role: `pre-gate` | `promotion-critical` | `diagnostic-only`
- Entry command:
- Benchmark dir/source:
- Frozen episode/layout selection:
- Action/observation schema:
- Primary metrics:
- Required artifacts:
  - `summary.json`
  - `episode_results.jsonl`
  - `results.csv`
  - shard `manifest.json`
  - merged `submission_manifest.json`
- Disqualifiers:
- Retry policy:

## Acceptance Matrix

| Track A | Track B | Decision | Resume phase |
|---|---|---|---|
| pass | pass | promote | package/release or stop |
| pass | infrastructure-invalid | retry-eval | evaluate |
| pass | fail | new-experiment | earliest invalidated phase |
| fail | not-run | stop or new-experiment | train/evaluate design |
| fail | pass | new-experiment unless Track A is diagnostic-only | earliest invalidated phase |

## Qualification Rules

- Partial progress may be reported, but official promotion requires:
- Missing-result policy:
- Invalidity ceiling:
- Abandoned/retry ceiling:
- Required review artifacts:

## Notes

- Keep one machine-readable run manifest per runnable track.
- Do not blend offline and closed-loop scores unless the formula is frozen before evaluation.
