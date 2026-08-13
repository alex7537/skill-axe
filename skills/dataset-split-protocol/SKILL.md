---
name: dataset-split-protocol
description: Build and audit leak-free train/val/diagnostic/holdout roles for grouped or temporal datasets. Use when creating splits for robot trajectories, videos, clips, episodes, sessions, or volumes; rebuilding after leakage; ingesting incremental data; preserving old evaluation roles; sealing a holdout; checking volume/clip/path/session overlap; or deciding whether evaluation results are independent. Consume quarantine and valid-frame outputs from $seg-label-audit when segmentation labels are involved. Do not use for label adjudication or generic training-budget calculations.
---

# Dataset Split Protocol

Split correlated data by the strongest collection group and preserve an auditable exposure history. A holdout stops being blind when any sample from its group is viewed or used for a decision.

## Workflow

1. **Freeze source identity.** Record source version/hash, group/sample/resource keys, counts, and exposure ledger. For segmentation data, run `$seg-label-audit` first and consume its quarantine and valid-frame manifests.
2. **Choose the isolation key.** Prefer scene/session/collection run, then episode/trajectory, then volume. Never random-split frames or clips from a correlated group.
3. **Allocate by sample weight.** Use `scripts/generate_group_split.py` to assign whole groups while approximating target sample ratios. Exclude quarantine before allocation and preserve preassigned historical roles.
4. **Assign explicit roles.** Use `train` for optimization, `val` for checkpoint/threshold decisions, `diagnostic` for viewed or exploratory evaluation data, `holdout` for one-time final evaluation, and `quarantine` for unusable/unresolved supervision.
5. **Seal the holdout.** Exclude every group exposed through smoke tests, overfit tests, visualization, failure review, checkpoint selection, threshold search, or prior reporting. Hash its manifest and record `sealed`; never reset a consumed holdout to sealed.
6. **Validate independently.** Run `scripts/validate_role_manifests.py` rather than trusting the generator. Require pairwise disjoint group/sample/resource identities and source conservation. Read [references/invariants-and-manifests.md](references/invariants-and-manifests.md).
7. **Audit incremental sources.** Compare proposed new train against old val, diagnostic, sealed holdout, and new val at group, sample, resource, recording, episode/session, and timestamp levels when available. Run `scripts/audit_incremental_overlap.py` and disclose undetectable same-scene/object risk as soft overlap.
8. **Freeze evaluation roles before reporting.** A dataset used to choose checkpoint, threshold, preprocessing, loss, or architecture is diagnostic—not test. Keep old val as forgetting protection and new val as new-domain selection.
9. **Emit a gate report.** Include hashes, counts, intersections, conservation, exposure status, unavailable identity checks, and `pass`, `diagnostic-only`, or `block`.

## Holdout opening contract

Before opening, freeze model/checkpoint, preprocessing, threshold, sampling/frame rules, primary metric, downstream interface, and failure policy. Require explicit final-evaluation authorization. Record opening time and permanently change the seal state to `consumed`.

Use [references/holdout-and-incremental-data.md](references/holdout-and-incremental-data.md) for the exposure ledger and incremental-role rules.

## Gate

- `pass`: hard identities are disjoint, source is conserved, quarantine is excluded, role ownership is preserved, and the holdout remains sealed.
- `diagnostic-only`: hard checks pass but no untouched holdout exists, or same-scene/session independence cannot be established from available metadata.
- `block`: any hard overlap, duplicate/missing sample, repaired sample role drift, quarantine leakage, source mismatch, or unauthorized holdout access exists.

## Gotchas

- Different group IDs can still describe the same physical scene or collection run.
- Balancing group counts can badly distort sample ratios; allocate whole groups by sample weight.
- A cleaned or repaired sample returns to its original role.
- Smoke/overfit samples and failure visualizations contaminate their entire correlated group.
- A leaked val measures memory; lower metrics after a clean re-split are expected.
- Val used for checkpoint selection is not an unbiased final report.
- Fixed midpoint evaluation can overestimate complete-sequence quality; freeze full-temporal evaluation rules before holdout access.
- Empty-GT metrics require semantic decisions from `$seg-label-audit`; the split layer must not guess.
- Thresholds and checkpoints selected on diagnostic permanently downgrade it from test.
- Training-budget changes after dataset resizing belong to `$plan-training-run`; do not hide them inside a split comparison.

## Safety boundaries

- Do not overwrite old manifests, role indices, audit reports, or holdout seals.
- Do not read underlying holdout RGB/masks merely to validate its manifest hash.
- Do not create a replacement “test” from already exposed groups.
- Do not force a `pass` when metadata cannot rule out soft overlap; report the limitation.
- Do not store credentials, signed URLs, personal identities, or raw session transcripts.
