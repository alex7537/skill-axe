---
name: feishu-migration-supervisor
description: "Plan, supervise, resume, and audit a bounded Feishu cross-account document migration with a reviewed manifest, target library structure, resource checks, and duplicate prevention. Use for 批量迁移飞书文档、公司个人文档写入 personal、迁移监督、断点续跑 or 整理目标文档库. Account login repair belongs to feishu-cli-multi-account-auth; this skill does not grant permission to share or migrate arbitrary company resources."
---

# Feishu Migration Supervisor

Own the migration ledger and acceptance checks; use installed `lark-cli` domain skills for API details. Compose `feishu-cli-multi-account-auth` for identities and `adaptive-task-coach` for milestone updates. This is a user-driven workflow, not a background service: resume only when an agent is actively executing the authorized task. No subagents are required.

## Contract before bulk writes

Resolve the source profile, target profile, exact source container/list, target library, transfer mode, and fidelity limits. A personal library inventory is not all documents accessible to a company account, nor proof that every document is owned by that user. Enumerate pages fully, deduplicate canonical objects, preserve node paths, and verify ownership when needed. Distinguish original creator, owner and reader.

Use a durable **local task directory outside the skill and Git repositories**. Store `manifest.json`, source snapshots, media, write receipts and verification reports there. Never put tokens, app secrets, device codes, temporary download URLs or raw CLI auth dumps into the ledger. Source titles, IDs and content are private task data, not skill backup material.

The manifest has:

- `version: 1`, `phase`, `source_profile`, `target_profile`, `scope_description`, `scope_complete`, `target_root`, `mode`.
- `approval`: `status` (`pending` or `approved`), `plan_digest`, and `evidence` identifying the user's exact confirmation. Digest comes from the audit helper, not a claim invented by the executor.
- `items`: each has `source_key` (canonical object token), `source_url`, `source_path`, `source_revision`, `target_path`, `status`, `target`, and `verification`.
- `containers`: proposed target index pages, each with `path`, `status`, `target` and `verification`; creation counts include these pages.
- `status`: `pending`, `reading`, `prepared`, `creating`, `created`, `verifying`, `verified`, `needs_review`, `blocked`, `skipped`, or `unknown_write`.
- `target`: confirmed `document_id`, `node_token`, `space_id`, `owner_id`, `url` when known. No guesses. Use an empty object before creation.
- `verification`: evidence paths and booleans for `body_match`, `structure_checked`, `resources_checked`, `links_checked`, `owner_checked`, `placement_checked`; detail any transformations or loss.

Build a human-readable plan containing every source URL and target path, plus container pages and reuse rules. Follow the user's applicable bulk-write gate: obtain confirmation of this concrete plan once, preserve it across turns, and ask again only for scope expansion or materially changed effects. Asking to create this skill is not approval of the pending migration list. The audit helper reports missing approval; it never grants it.

## Stages and oversight

1. **Inventory:** list exact source nodes, pagination and exceptions. Preserve source files unchanged. Do not call a missing search scope a missing document ACL. Browsing an already-authorized named container is valid but does not prove global coverage.
2. **Plan:** preserve source subtrees under a few topic index pages in the target library. Classify from titles first; do not rewrite substantive source text. Mark existing verified targets for reuse. No deletion of earlier duplicates without separate authorization.
3. **Prepare:** fetch each source with `--doc-format xml --detail full`; keep content and reference map together. Inspect images, files, tables, formulas, boards, synced blocks, embedded Sheets/Base and child-page lists. Record source revision and media inventory. Confirm the intended transfer is allowed; stop on source ACL/export/policy denial rather than evading it.
4. **Write:** create parent containers before children, one mutation at a time, using explicit target profile and `--as user`. Save a `creating` checkpoint before mutation and its returned target ID immediately after success. Check warnings and asynchronous result state, not just exit code.
5. **Verify:** read each target through the target account; verify owner, library node/space and parent, title, text, heading/code/table structure, formulas, media and links. Check content again if source revision changed during migration. Mark verified only with recorded evidence for all checks.
6. **Reconcile:** count candidates, verified, reused, skipped, blocked and unresolved writes. Publish a local old-to-new mapping and a target index only within approved scope. Finish only when all planned items and containers meet acceptance, or report partial completion explicitly.

At each meaningful checkpoint, report completed/total, current document, failures and next action. Keep one mutation in flight. Process in small checkpoints (for example five documents); do not require renewed approval for each checkpoint within the approved plan. On pause/interruption, persist state and stop issuing new writes.

## Select the transfer mode deliberately

- **Native copy:** default for a request to create a faithful copy when the target user can access/copy the source. Use installed `lark-drive` copy guidance.
- **Read then write:** when explicitly requested by the user, source-user read followed by target-user creation is the selected operation. It need not grant the target access to the source. Preserve content rather than summarizing it. Do not mistake a target copy-ACL failure for a source read denial, or use this mode to evade an actual source restriction.
- **Offline export/import:** use when the user selects format conversion or offline backup; record conversion limitations and validate resources.

For XML replay, remove old block IDs; retain formatting where supported. Cross-account resource tokens may not work: download through the authorized source identity and upload through the target identity using the installed media references. Avoid silently copying inaccessible references or replacing media with unexplained empty blocks.

Use a source-to-target map to rewrite document links after destinations exist. References outside the approved set remain labeled source links; never silently expand the scope to migrate them. Native child-page lists must refer to target children, not the old company's tree. Unsupported embeds require explicit degradation notes or `needs_review`; never call a text-only reconstruction a complete backup.

## Target placement is an acceptance condition

For a new root page in the user's **我的文档库**, explicitly use:

```bash
lark-cli --profile <target> docs +create --as user --doc-format xml \
  --content @./content.xml --parent-position my_library
```

For children, use the verified target parent node token with `--parent-token` (not together with `--parent-position`). Resolve the created Docx using `wiki +node-get --node-token <document-id> --obj-type docx --as user` and record its real library node/space/parent and owner. Default creation can land outside the library even when the user owns and can edit it.

Before modifying any existing target, freshly check its identity, owner and effective permission with read-only APIs according to the user's rules. Account OAuth scopes alone do not prove per-resource edit permission. Permission changes, sharing, ownership transfer, deletion, and bulk scope expansion are separate actions, not recovery defaults.

## Recovery rules

For XML replay, nested-list paragraph loss, byte verification, large-file omissions and static embed conversions, read [references/xml-replay-verification.md](references/xml-replay-verification.md) before preparing bulk writes. These cases were exercised in a completed migration; successful API responses did not detect dropped paragraphs.

- A create timeout, connection loss after submission, or process crash in `creating` means **unknown outcome**, not permission to create again. Mark `unknown_write`; inspect the intended target parent and receipts to reconcile the object before retrying. Titles alone are not stable IDs.
- Persist each successful target mapping atomically. Resume by source key; do not create a second target for an already mapped source.
- For an asynchronous job, resume the existing job/ticket, not the original create request. Never persist temporary access URLs with the job state.
- Bounded retries apply only to clearly non-mutating reads and known transient errors. Respect returned rate-limit hints; keep sequential writes to the same parent.
- Stop writes for authentication/permission errors, uncertain identity, unknown-write reconciliation, or repeated equivalent failures. Continue independent read-only preparation where useful. Do not change user/bot identity to recover access.

## Local supervisor check

```bash
python3 scripts/audit_manifest.py /path/to/private-task/manifest.json
```

This read-only helper checks identities in the ledger, duplicate mappings, verification evidence, plan approval digest and completion counts. It **does not** call Feishu, verify live permissions, enforce a lock, execute writes or guarantee exactly-once API semantics. Live readback remains required. Update state via atomic replacement and keep only one executing agent per task.
