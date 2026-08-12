# Training-budget principles

## Core quantities

Let:

- `N` be effective training samples after oversampling.
- `B` be batch size.
- `S` be optimizer steps per epoch.
- `E` be epochs.
- `T` be total optimizer steps.
- `r` be warmup ratio.

For a loader that keeps the final partial batch:

```text
S = ceil(N / B)
T = S * E
warmup_steps = round(T * r)
sample_presentations = N * E
```

Use `floor(N / B)` when `drop_last=true`.

## Rescaling an old experiment

To preserve optimizer-step budget:

```text
old_total_steps = old_steps_per_epoch * old_epochs
new_epochs = old_total_steps / new_steps_per_epoch
```

Round only after deciding whether exceeding or undershooting the old budget is safer. Report the resulting difference.

Preserving optimizer steps does not preserve sample presentations when batch size changes. State which quantity the comparison controls.

## Learning-rate schedule

For linear warmup followed by cosine decay:

```text
warmup_steps = round(total_steps * warmup_ratio)
```

The schedule depends on planned `total_steps`. An early stop truncates the original schedule; it does not compress it. Reconfigure and restart when a complete short schedule is the experiment being requested.

For parameter groups:

```text
head_lr = base_lr
backbone_lr = base_lr * backbone_lr_multiplier
```

Use multiplier `0` for a frozen backbone. A `0.1` multiplier means the backbone learns at one tenth of the head LR, not that only 10% of the backbone is trained.

## Batch size

Keep batch size fixed for controlled ablations. When changing it:

- recalculate steps per epoch, total steps, and warmup;
- verify memory and actual samples/second;
- treat linear LR scaling as a hypothesis to validate, not a universal law;
- distinguish fixed-step comparisons from fixed-sample-exposure comparisons.

## Stopping and extending

Use completed checkpoints only. A reasonable convergence review includes:

- aggregate validation loss;
- continuous/static/keyframe or rare-event losses;
- task-space or rollout metrics;
- train-versus-validation gap;
- improvement over the last two or more completed evaluations;
- LR position in the schedule.

Example staged criterion: stop after the planned minimum budget when validation improvement is below 1–2% for two consecutive evaluations and task-level metrics no longer improve. This is a heuristic, not a universal threshold.

If the schedule already decayed to zero, do not simply add epochs. Define a new extension schedule and preserve its provenance.

## Failure and monitoring contract

A production training run should expose:

- batch-level heartbeat or step logging;
- epoch-level train and validation components;
- latest and best checkpoints written atomically;
- data, split, stats, code, and resolved-config provenance;
- timeout and uncaught-exception alerts;
- a nonzero exit code on failure so queued experiments do not start accidentally.
