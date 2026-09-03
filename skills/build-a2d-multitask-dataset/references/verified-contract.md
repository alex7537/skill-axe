# Verified A2D multitask contract

## Canonical command shape

```bash
python scripts/create_balanced_multitask_dataset.py \
  --source box=<processed-box-v3> \
  --source bottle=<processed-bottle-v3> \
  --destination <new-version-directory> \
  --data-version <new-version-name> \
  --episodes-per-task 300 \
  --val-per-task 30 \
  --seed 42
```

Sources must already contain resized/JPEG RGB and V3 hybrid action labels. This
workflow does not revisit raw 450GB images or re-encode JPEG.

## Verified 300+300 result

```text
episodes                  600
box train / val           270 / 30
bottle train / val        270 / 30
combined train / val      540 / 60

box base windows          44,188
bottle base windows       44,499
box transition windows     4,847
bottle transition windows  4,182
box lift windows          11,855
bottle lift windows       11,807

box effective samples     60,890
bottle effective samples  60,488
effective ratio           50.17% / 49.83%
combined effective       121,378
validation samples         9,884
```

With batch 32 and 100 epochs:

```text
steps/epoch                3,794
total steps              379,400
warmup at 5%              18,970
```

The natural shuffled loader is sufficiently task-balanced for this selection;
no custom sampler is required.

## Required output files

```text
<task>__episode_*.hdf5
index_cache.json
norm_stats.json
dataset_manifest.json
split_manifest.json
derivation_manifest.json
```

`dataset_manifest.json` episode entries retain:

```text
task_id
source_file_name
source_data_version
bytes
length
file_sha256
content_hash
```

## Verification checklist

1. Count namespaced HDF5 files and task/role membership.
2. Assert train and val sets are disjoint and cover the selected set.
3. Assert content hashes are unique across tasks.
4. Compare source/destination inode and device for every hard link.
5. Hash raw manifest bytes and compare all manifest bindings.
6. Verify `norm_stats.train_episode_count` and train digest.
7. Recompute window segmentation from `arm_keyframe` and `phase`.
8. Materialize the final training YAML only after actual steps are known.

## Known failure modes

- **Same episode filename across tasks:** without prefixes, one task overwrites
  the other even when content hashes differ.
- **Reusing source norm stats:** mixed joint/action ranges can be substantially
  wider; normalization must be recomputed.
- **Counting episodes as task balance:** transition/lift oversampling changes the
  effective ratio; measure window exposure.
- **Using a Linux venv after Mac migration:** binary wheels are not portable;
  use a small native data venv.
- **Building on CFS during training:** opening hundreds of small HDF5 files can
  contend with DataLoader metadata I/O even when CPU/GPU use is low.
- **Treating hardlinks as independent backups:** deleting every linked source and
  destination removes the data; preserve at least one durable source version.
