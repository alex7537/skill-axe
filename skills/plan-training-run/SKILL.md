---
name: plan-training-run
description: Plan, compare, and audit machine-learning training budgets from dataset samples, episodes, batch size, optimizer steps, epochs, warmup, and learning-rate schedules. Use whenever a user asks how many epochs or steps to train, how to rescale an old experiment to a larger or smaller dataset, whether early stopping is equivalent to a shorter schedule, how to configure frozen versus fine-tuned backbones, or whether loss curves justify stopping or extending a run.
---

# Plan Training Run

Treat optimizer steps and sample exposure as the primary budget. Never compare raw epoch counts across different dataset sizes without converting them to steps.

## Workflow

1. Inspect the resolved dataset and trainer rather than trusting configuration comments.
   - Record train episodes, base samples, effective samples after oversampling, batch size, drop-last behavior, and validation samples.
   - Confirm whether LR scheduling uses epochs or total optimizer steps.
2. Identify the comparison objective:
   - **Baseline-equivalent:** preserve the old run's total optimizer steps.
   - **Data-pass:** choose how many full passes over the new dataset are justified.
   - **Fixed-step ablation:** give every model variant identical optimizer steps and evaluation points.
3. Run `scripts/plan_training.py` for deterministic calculations.
4. Read `references/training-principles.md` before recommending LR scaling, changing batch size, stopping early, or extending a schedule.
5. Produce a plan containing:
   - effective train samples and steps per epoch;
   - epochs, total steps, warmup steps, and LR schedule endpoint;
   - base LR and per-parameter-group multipliers;
   - logging/evaluation/checkpoint cadence;
   - explicit stop, extend, and failure criteria;
   - assumptions and differences from the comparison baseline.
6. Before launching, inspect the resolved config and calculate the numbers again. After launch, verify the first completed epoch, LR values, process health, and checkpoint provenance.

## Decision rules

- Keep dataset split, seed, batch size, augmentation, policy, and step budget identical for a frozen-versus-finetuned ablation unless the user explicitly changes the scientific question.
- Recompute the whole LR schedule when shortening a run. Stopping a 30-epoch cosine schedule at epoch 5 is not equivalent to configuring a 5-epoch cosine schedule.
- Use validation loss components and task-level evaluation together. Do not stop solely because aggregate train loss is small.
- Treat `keyframe` or other rare-event loss separately when sampling oversamples transitions.
- Prefer a staged run when the right budget is uncertain: run a small complete schedule, inspect checkpoints, then design a new extension. Do not silently extend a cosine schedule that has already decayed to zero.
- For a live training mutation, preserve completed checkpoints and record the stop/restart reason before changing state.

## Gotchas

- Effective samples may exceed base windows because of transition oversampling.
- `ceil(samples / batch)` versus `floor(samples / batch)` depends on `drop_last`.
- Changing batch size changes both steps per epoch and gradient noise; it is not only a throughput adjustment.
- Validation lower than epoch-average training loss can be normal because training loss averages early and late model states and often includes augmentation.
- An online dashboard can remain empty when the trainer logs only at epoch boundaries.
- A manually interrupted run may look crashed remotely even when its last completed checkpoint is valid.
