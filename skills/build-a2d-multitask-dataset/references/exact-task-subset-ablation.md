# Exact task-subset ablation

Use this mode to answer whether adding another task helps or hurts a target
task while preserving the target task's demonstrations exactly.

## Causal question first

For a mixed baseline containing `Box300 + Bottle300`, filtering the exact same
Box300 episodes can test:

```text
Does training with Bottle gradients change Box performance when Box episode
membership, split and per-episode passes are held fixed?
```

It cannot by itself test whether Box300 is enough data. That requires a
Box-only size sweep whose smaller membership is nested inside the larger one.

## What changes

The task-subset run should change only the artifacts that logically depend on
dataset membership:

| Change | Reason |
|---|---|
| dataset task membership | remove the comparison task |
| dataset/split/index/derivation manifests and hashes | bind the new immutable dataset identity |
| train-only normalization | production-correct statistics for the retained task |
| effective samples, steps/epoch and total steps | arithmetic consequence of membership |
| warmup steps | retain the frozen warmup ratio against the new total steps |
| run/output/W&B identity | prevent collision and preserve provenance |

Recomputed normalization is part of the operational Box-only recipe. If the
scientific question instead demands membership as the only preprocessing
change, run a second explicit ablation that reuses mixed normalization; label
it accordingly rather than replacing the primary run.

## What stays locked

Require equality with the mixed baseline for:

```text
the retained Box episode names and HDF5 bytes
each retained episode's train/val role
observation/action semantics and temporal offset
RGB keys, size and augmentation
tail padding and action mask behavior
transition/lift oversampling factors
policy type and model architecture
ViT token mode and token count
pretrained initialization and backbone multiplier
batch size, base LR, optimizer, weight decay and grad clipping
seed, deterministic validation and checkpoint selection
EMA settings and rollout contract
```

Never resume from the mixed checkpoint when the question is scratch Box-only
versus scratch mixed training.

## Choose and report the budget axis

Dataset removal changes the number of optimizer steps per epoch. There is no
single comparison that simultaneously fixes every exposure:

### Fixed per-task passes

Keep epochs unchanged. Each retained Box window is presented approximately the
same number of times in Box-only and mixed training, while total optimizer
steps decrease. This is normally the primary negative-transfer comparison.

### Fixed optimizer steps

Increase Box-only epochs until total steps match the mixed baseline. This gives
Box more presentations and answers a different compute-budget question. Keep
it as a separate run rather than silently changing the primary experiment.

### Data sufficiency

Build nested Box-only memberships, for example:

```text
Box300 ⊂ Box600 ⊂ Box1090
```

Freeze the validation role before selecting train subsets. Report both a
fixed-pass comparison and, if needed, a fixed-step comparison. A single
Box300-only run cannot distinguish limited coverage from insufficient compute.

## Required evidence

Before launch, emit and verify:

```text
source dataset/split manifest hashes
exact selected task membership equality
train/val counts and zero overlap
hard-link inode/device equality
train normalization count and digest
base/transition/lift/tail/effective sample counts
batch size, steps/epoch, epochs, total steps and warmup
resolved-config diff against the mixed baseline
one-step CUDA train/val/checkpoint smoke
```

After launch, require the first complete epoch, finite component losses,
correct LR position, raw/EMA checkpoint creation, no failure artifact, and a
live trainer/GPU before declaring the run healthy.

## Interpretation matrix

| Box-only result versus mixed | Supported interpretation | Not yet proven |
|---|---|---|
| materially better | Bottle mixing, shared capacity or mixed normalization may hurt Box | exact mechanism; Box300 sufficiency |
| similar | no large operational gain from removing Bottle under this budget | Box300 sufficiency; equal model behavior on matched layouts |
| worse | Bottle data may regularize/help, or Box-only has fewer total updates | positive transfer unless fixed-step/normalization controls agree |

Use matched rollout protocol and confidence intervals before treating a few
percentage points as a real difference.
