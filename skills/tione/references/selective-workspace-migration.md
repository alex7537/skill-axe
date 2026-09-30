# Selective development-workspace migration audit

Use after `development-workspace-storage.md` when inventorying a shared research workspace for selective preservation or a knowledge-only handoff. Classification: extension of TI-ONE infrastructure operations, not a new migration executor.

## Decide what must survive

Follow the user's requested outcome: knowledge only, selected assets, or full copy. An audit or knowledge-capture request does not authorize transfer, cleanup, environment installation or remote Git mutation.

Build an asset ledger with project/relative path, purpose, evidence date, source identity, unique work, dependency target, preservation choice, confidence and unresolved checks. Classify by reproducibility:

- Unique evidence: editable source including dirty/untracked files, source snapshots, resolved configs, split/normalization/derivation manifests, quarantine/audit records, selected checkpoint provenance, per-episode metrics and reports.
- Resume versus inference: a deployment bundle can omit optimizer, scheduler, RNG and full EMA state. Preserve full checkpoints when continuation is required; choose best raw/EMA independently from latest. Keep selection metrics and data bindings.
- Reconstructible with prerequisites: public weights need exact revision and hashes; derived latents need source data, codec version, preprocessing and regeneration cost. A folder called `cache` can contain indispensable weights or expensive training inputs.
- Disposable only after inspection: package-download caches, abandoned environments and temporary outputs. A filename alone is insufficient evidence for deletion.

## Bounded read-only discovery

- Verify SSH identity through `tione-ssh-diagnose`; do not disable host-key checks. Accepted replacement must match the exact fingerprint scanned before any targeted trust-record repair.
- Probe `findmnt -T` on the exact personal directory. A Lustre child mount can exist below an overlay parent. `df` capacity belongs to the filesystem, not the user; do not infer account quota or retention after access revocation.
- Start with shallow directory listing and selected README/config/manifest files. Find nested source roots (`code/`, `src/`), source snapshots, and datasets inside code directories. Do not inventory credential contents or shell history.
- Prefer Git status with optional locks disabled and a timeout. If Git is unavailable, `.git/HEAD` plus loose/packed refs can identify a recorded ref; they cannot establish a clean tree, exact deployed source, or remote backup. Do not install tools just to complete an audit without need/authorization.
- Inspect direct symlinks and target existence. Record whether a target is inside the project, elsewhere in the personal root, or external. Results centralized in an `experiments/` tree must travel with their project references. Check deeper dependency levels selectively; a shallow pass is not a full symlink audit.
- Check `pyvenv.cfg`, `bin/python` resolution and external interpreter existence without importing project code. An existing interpreter alone does not prove ABI/CUDA compatibility. A shared environment may survive while `/opt/conda` or a uv-managed interpreter disappears.
- Check scoped activity only when necessary. No process with cwd under a project does not prove that no process reads/writes it; GPU utilization does not establish ownership. A safe cutover needs stronger job/process evidence than inventory alone.

## Measure without overstating completeness

Use a bounded `du` only where needed; report timeout and coverage. Never present partial output as total migration size. For a bounded checkpoint census, enumerate explicit file patterns at a known depth and report count, logical bytes and whether unique `(st_dev, st_ino)` pairs were counted. Distinct inodes can still contain identical content; inode deduplication is not content deduplication.

Hardlinked datasets share bytes. A selected-file sample with `st_nlink > 1` proves linking for that sample, not the complete tree. A future transfer should preserve the relevant link set (for example, an authorized rsync with `-H`) or explicitly budget expansion. Cross-invocation copying may lose shared topology. Symlink preservation and dereferencing are separate choices: neither silently collect another user's data nor leave required external targets unresolved.

## Reconcile with knowledge

Use existing notes and skills as hypotheses, then compare with dated runtime artifacts:

- Directory names such as `smoke` can contain later formal runs. Read completion/status artifacts and checkpoint structure before assigning maturity.
- Run completion is not quality validation, checkpoint integrity, or successful closed-loop deployment.
- An old project map may describe a different local branch. Preserve that historical evidence and append a scoped current observation; do not rewrite it as a claim about all machines.
- Store method here; store a dated project/asset comparison and conceptual lesson in Obsidian, with short links from its existing map. Keep raw logs, secrets, full config dumps and private host fingerprints out of portable skills.
- If only experience capture is requested, stop after validated local knowledge edits. Do not use an unresolved migration target as a reason to block that deliverable.

## Completion boundary

Report what was inspected and what remains unknown: dirty source state, external data origins, full capacity, cache regeneration, checkpoint load/hash validation, active-job safety, and target compatibility as applicable. These gaps do not prevent a useful inventory, but they prevent claiming a fully reproducible or safely completed migration.

When selected migration is later authorized, derive a concrete manifest and verify destination hashes, source/config/data bindings, link targets, checkpoint loading and minimal model execution before proposing source removal. Keep bulk data transfers, remote publication and deletions outside a knowledge-only task.
