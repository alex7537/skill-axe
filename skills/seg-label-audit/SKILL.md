---
name: seg-label-audit
description: Audit segmentation and mask label trustworthiness before training or evaluation. Use when onboarding a mask dataset, finding all-zero masks or annotation holes, questioning whether GT is missing or truly empty, seeing suspicious empty-frame false positives, reviewing pseudo-labels, checking instance-ID semantics, or producing quarantine and valid-frame manifests. Use for human or model-generated segmentation labels; do not use for dataset role allocation or holdout construction—hand those outputs to $dataset-split-protocol.
---

# Segmentation Label Audit

Treat missing supervision as neither positive nor negative. Produce a reviewable label-validity decision before training, splitting, or interpreting metrics.

## Workflow

1. **Freeze the label contract.** Record RGB/mask shape, dtype, value range, instance-ID meaning, binary-conversion rule, clip/frame bounds, source revision, and label-generation method. Do not assume `mask > 0` is correct until nonzero IDs are known to represent the intended target.
2. **Scan every relevant frame.** Stream by shard or group; never load the full dataset into memory. Emit one JSONL record per frame containing stable group/sample/frame identity, foreground-pixel count, and nonzero IDs. Use `scripts/summarize_mask_scan.py` to identify whole-empty clips, partial holes, empty runs, and multi-ID frames.
3. **Build review evidence.** For suspicious ranges, render synchronized RGB, raw GT, binary GT, overlay, neighboring frames, and optionally model probability/prediction. A model can nominate evidence but cannot declare GT wrong.
4. **Classify semantics.** Assign `valid_nonempty`, `true_empty`, `confirmed_missing`, `partial_annotation_hole`, `boundary_ambiguous`, `multi_instance_ambiguous`, or `corrupt_or_unreadable`. Read [references/classification-protocol.md](references/classification-protocol.md) before adjudication.
5. **Write decisions, do not alter source data.** Store affected ranges, confidence, evidence reference/hash, original role, rules version/hash, and status in a quarantine/review manifest. Validate it with `scripts/validate_label_decisions.py`.
6. **Build valid-frame candidates.** Permit training/evaluation only on frames classified valid under the frozen rule. Preserve legitimate `true_empty` frames as separately identifiable negatives.
7. **Hand off.** Pass the source manifest, label decisions, quarantine manifest, and valid-frame manifest to `$dataset-split-protocol`. Repaired samples retain their original group and role.

## Decision rules

- Quarantine `confirmed_missing`; do not count it as background or include it in official metrics.
- Keep `ambiguous` data diagnostic-only until the label owner resolves it.
- Retain `true_empty` as valid negative supervision and evaluate it separately from nonempty Dice.
- Preserve a partially valid clip through a valid-frame allowlist instead of discarding the whole clip.
- Escalate multi-ID frames until single-target versus all-instance semantics are explicit.
- Record when no legitimate empty scenes remain; the trained model then has no supervised empty-output behavior.

## Required outputs

- source/label-contract manifest;
- streaming scan summary;
- review evidence index;
- versioned label-decision or quarantine manifest;
- valid-frame manifest;
- unresolved questions for the label owner;
- gate status: `pass`, `diagnostic-only`, or `block`.

Use [references/manifest-contract.md](references/manifest-contract.md) for portable schemas. For pseudo-label or distillation data, also read [references/pseudo-label-audit.md](references/pseudo-label-audit.md).

## Gate

- `pass`: label semantics are frozen; all suspicious zero/multi-ID/corrupt ranges are resolved or excluded; valid-frame coverage is complete.
- `diagnostic-only`: ambiguous supervision remains but is excluded from official train/evaluation roles.
- `block`: unresolved labels enter training or official metrics, binary conversion is unverified, scan coverage is incomplete, or source data was silently rewritten.

## Gotchas

- Whole-zero, midpoint-zero, and local zero-filled ranges are different conditions.
- Empty GT may mean true empty, missing annotation, merge/padding fill, or propagation beyond a valid boundary.
- Empty GT plus a confident prediction is evidence for review, not proof of missing GT.
- A nonempty midpoint does not prove the rest of a clip is valid.
- `raw_mask > 0` silently merges instances.
- “Empty-frame FP” is meaningless until empty labels are classified.
- Filtering every zero mask can improve a contaminated benchmark while destroying empty-scene behavior.
- Repair does not reset exposure history or authorize moving a sample into train.

## Safety boundaries

- Keep raw RGB/masks read-only; quarantine logically rather than deleting.
- Never auto-promote predictions into ground truth.
- Do not embed credentials, signed URLs, personal identifiers, or raw session transcripts.
- Do not decide dataset roles here; invoke `$dataset-split-protocol` after label audit.
