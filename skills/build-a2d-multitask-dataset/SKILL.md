---
name: build-a2d-multitask-dataset
description: Build and audit a directly trainable, task-balanced A2D V3 dataset from two or more already-processed RGB HDF5 datasets. Use when requests mention mixing box/bottle or multiple object tasks, selecting an equal number of episodes per task, rebuilding a fresh 9:1 split, resolving duplicate episode names, reusing JPEG data without copying, recomputing joint normalization, or calculating the resulting CFM budget. Do not use for raw 450GB RGB ingestion, Wan latent precomputation, or segmentation-label adjudication.
---

# Build A2D Multitask Dataset

Create a new immutable dataset version from processed V3 sources. Preserve the
source HDF5 payloads; change only membership, namespacing, split manifests, and
train-bound normalization.

## Establish the contract

Before building, verify every source has:

```text
image_keys       = [rgb_head, rgb_right_hand]
image_size       = 224
observation      = arm actual(7) + hand actual(6)
action_semantics = arm_executed_hand_commanded_joint_position
```

Clarify whether “N episodes per task” means total or train-only. Unless the user
says train-only, interpret it as total and apply the requested train/val ratio
inside each task. For N=300 and 9:1, use 270 train + 30 val per task.

## Use the canonical repository script

Locate `scripts/create_balanced_multitask_dataset.py` in the active
`flow-matching-test-a2d-v2` repository. Inspect and test it before execution;
do not reconstruct an ad-hoc merger when the script is available.

The builder must:

- sample without replacement with a stable task-specific seed;
- prefix filenames such as `box__` and `bottle__`;
- use hard links when sources and destination share a filesystem;
- write to a PID-scoped temporary directory and atomically rename on success;
- recompute `norm_stats.json` from combined train episodes only;
- emit dataset, split, derivation, and index manifests with hashes;
- leave source datasets untouched.

Read [references/verified-contract.md](references/verified-contract.md) for the
verified command shape, manifest fields, budget calculation, and acceptance
report.

## Environment choice

Prefer a local machine when both processed sources are local and a development
machine is training. A migrated Linux virtualenv is not portable to macOS ARM.
The builder needs only Python, `numpy`, and `h5py`; create a lightweight local
data venv rather than installing torch/timm/CUDA.

Do not scan a shared CFS during a live training run merely because the training
environment already has dependencies. If one source exists only remotely,
either wait for training to finish or transfer the compact processed source.

## Acceptance gate

Require all of the following before calling the output trainable:

- exact per-task train and val episode counts;
- zero train/val overlap and complete split coverage;
- zero duplicate content hashes;
- every destination HDF5 verified as the intended hard link;
- dataset-manifest hash bound by the split manifest;
- derivation manifest bound to the split hash;
- normalization train count/digest bound to the selected train set;
- actual base/transition/lift/tail and effective sample counts;
- task exposure ratio reported after oversampling;
- config warmup recomputed from actual total steps.

If equal episode counts yield an effective-window ratio close to 1:1, use the
ordinary shuffled DataLoader. Add a balanced sampler only when the measured
window ratio materially differs or the user explicitly requires fixed per-batch
composition.

## Boundaries

- The builder creates a new dataset version; never overwrite a source or prior
  derived version.
- Hard links save physical space but require one filesystem. Fail rather than
  silently copying gigabytes.
- Historical split roles may be discarded only when the user explicitly defines
  the output as a fresh scratch multi-task experiment.
- Creating data does not authorize uploading it, starting training, stopping a
  live run, deleting a partial version, or pushing repository changes.
- Separate task-level validation is still needed when one aggregate metric could
  hide negative transfer.
