---
name: wandb-project-backup
description: Inspect W&B project ownership and export selected projects to a verified offline backup of run configs, summaries, unsampled metric history, uploaded files, and all available Artifact versions. Use for 备份 W&B, 保存训练曲线, 退出组织前导出, W&B 项目属于个人还是团队, or loss of future team access. Does not migrate cloud ownership or retrieve checkpoints never uploaded to W&B.
---

# W&B Project Backup

Category: Data Fetching & Analysis. Preserve authorized experiment evidence independently of future team access. A backup is complete only for its explicitly enumerated scope, not for the entire W&B service.

## Ownership first

- Resolve the actual `entity/project` URL and project visibility. A personal Profile's Projects tab, starred project, creator identity, or Personal workspace layout does not establish personal project ownership.
- A Team-visible project requires parent-team membership. Corporate labels identify organization type, not proof of an Enterprise paid plan or legal ownership of the research.
- Explain that losing membership can remove access. Do not change sharing, leave organizations, or transfer projects while diagnosing ownership.
- Check current official documentation when advising on changing platform rules. Do not preserve dated regional service notices as universal policy.

## Backup contract

1. Resolve exact entity, projects, local output directory and scope. Use existing authorized login; if missing, ask the user to run `wandb login --cloud --verify` locally. Never request API keys in chat, print them, embed them in commands, or extract browser cookies.
2. Prefer a dedicated Python environment. The proven baseline is `wandb==0.30.0`; inspect installed API signatures before adapting to another version. See [references/operations.md](references/operations.md) for commands and dated evidence.
3. Inventory without UI filters: all currently accessible Runs, uploaded file names/sizes/checksums, Artifact types/collections/versions. Empty projects must be recorded. Artifact collection counts need not equal Run counts.
4. Read the manifest before downloading: identify volume, external references and whether weights exist. Curves are not checkpoints; low storage usage is only a clue. Model files can be stored in Files as well as Artifacts; do not decide from type labels alone.
5. Export with `scripts/backup.py`: configs, summaries, metadata, `scan_history()` without a key filter, original Files, and all enumerated Artifact versions. Keep history in JSONL. File MD5 and Artifact manifest verification must pass; partial failures remain visible and retryable.
6. Independently verify and package with `scripts/finalize.py`. It checks inventory coverage, history row counts and JSON, file MD5 when available, Artifact file presence and stored-entry MD5, completion markers, and absence of partial files; then generates INDEX.md, SHA256SUMS and a CRC-tested ZIP with a SHA-256 sidecar.
7. Report counts, failures, local archive path and explicit missing scope. Link the archive; suggest an independent storage copy when appropriate, but do not upload datasets/logs to GitHub, HF or a knowledge repository without an explicit destination and scope.

## Safety and scope

- Scripts only read the remote API and write local files; no `wandb.init()`, Run update, deletion, transfer or permission changes.
- Back up only selected projects. Keep backups outside tracked source, or confirm their path is Git-ignored. A skill repository receives sanitized tooling and knowledge, never the actual experiment payload or credentials.
- Reports, workspace layouts, sweeps definitions, permissions and deleted/inaccessible data are not covered by these scripts. System event Artifacts are saved only when enumerated; the tool does not promise complete system telemetry for every Run.
- External Artifact references can need separate storage credentials. A reference manifest alone is not a content backup; report unavailable bytes. Offline MD5 validation covers stored entries, not every provider's reference digest semantics.
- A running Run is a changing snapshot. Record its state and refresh using a new snapshot after it ends when a final archive is needed.
- `complete.json` skips already completed items during resume. Finalization rechecks bytes; a changed/missing file must be repaired and validated before delivery. Use a new snapshot to capture newer cloud state. An interrupted inventory may be partial: do not export it as complete; remove only that incomplete inventory or choose a new snapshot and rerun enumeration.

## Gotchas

- `history()` is sampled by default; do not substitute it for complete metric export. `scan_history(keys=[...])` can drop rows missing any listed key; omit keys for backup.
- A local browser login does not authenticate the Python SDK. Diagnose missing credentials separately from sandbox/network DNS failures; do not ask the user to log in again for a network restriction.
- API `File.size` can be zero for manifest placeholders; prefer actual downloaded bytes and supplied digests for integrity.
- Artifact history/events are evidence, not automatically model weights. A weights backup may require a separate training-server or HF workflow.
- Public-API deprecations vary by SDK. `Api.artifacts()` replaces `artifact_versions()` in the proven version. UI counts can be stale or filtered; compare the explicit API inventory to exported results.
- Resume is for interrupted transfers, not a fresh cloud snapshot or a complete W&B restore operation.

## Knowledge routing

`research-asset-routing` owns where research artifacts belong. This skill owns W&B access diagnosis and the local export/verification method. Obsidian retains the concise ownership/longevity lesson and a skill link. Keep one canonical procedure here.
