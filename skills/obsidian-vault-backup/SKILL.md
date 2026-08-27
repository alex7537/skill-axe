---
name: obsidian-vault-backup
description: Safely preview, commit, and push a Git-versioned Obsidian vault to its existing backup remote. Use when the user asks to 备份 Obsidian, 同步 Vault, push notes, keep an Obsidian backup current, inspect backup drift, or plan a periodic archive. Do not use for reorganizing notes, changing repository visibility, creating a remote, or treating Obsidian Sync as Git history.
---

# Obsidian Vault Backup

Back up reviewed Vault content without turning every editor state, plugin cache, credential, or unfinished attachment into Git history.

## Route the request

- **Inspect/preview:** resolve the Vault and run the bundled script without `--execute`.
- **Commit/push:** preview first, show selected and excluded paths plus remote drift, then obtain explicit confirmation for the exact scope before `--execute --commit --push`.
- **Periodic archive:** read [references/backup-policy.md](references/backup-policy.md). A skill does not run by itself; installing `launchd` or another scheduler is a separate external-write decision.
- Use `$obsidian-vault-versioned-reorg` for moves, deduplication, archives, MOCs, protected-folder audits, or branch merging. This skill owns backup transport, not Vault organization.

## Configuration

Use machine-local `config.json`; copy from `config.example.json` after restoring the skill. Keep it out of skill backup repositories because it contains a private Vault path and branch policy.

The target must already be:

- the exact Vault root containing `.obsidian/`;
- the root of an existing Git worktree;
- on the configured branch with an existing configured remote.

This skill never creates a GitHub repository, changes visibility, adds a remote, rebases, force-pushes, or merges branches.

## Safe synchronization

Preview:

```bash
python3 scripts/sync_vault.py
```

The preview fetches remote refs read-only, refuses a behind/diverged branch, lists local tracked/untracked changes, selects only policy-allowed content, excludes machine-local paths, checks size and high-confidence credential patterns, and performs no staging, commit, or push.

After the user approves the displayed scope:

```bash
python3 scripts/sync_vault.py --execute --commit --push \
  --message 'backup: checkpoint Obsidian research notes'
```

Use `--include-obsidian-config` only when the user explicitly approves stable `.obsidian` preferences. Workspace state, plugins, Claudian data, trash, temporary backups, and secrets remain denied.

Use `--include-untracked-binary` only after reviewing every new attachment and confirming repository size/file limits. Existing tracked attachments remain eligible within the configured size limit.

## Verification

After a push, require:

- local `HEAD` equals `<remote>/<branch>`;
- no force push occurred;
- excluded paths remain unstaged;
- the reported commit contains only approved paths;
- remaining dirty paths are reported rather than silently hidden.

Git remote backup is an off-device history copy, not continuous Obsidian Sync and not a complete disaster-recovery plan for ignored plugin state.

## Gotchas

- The existing `skill-axe` workflow is invocation-driven, not real-time; copying its safety model means preview and approval before push.
- A private remote still does not make secrets safe to commit.
- `git add -A` across a Vault can capture machine-local state or unfinished binaries; the bundled script stages explicit allowed paths only.
- Frequent automatic commits can capture half-written notes and create noisy history. Prefer meaningful checkpoints or a reviewed 15–30 minute schedule.
- A branch can be clean locally but behind the remote because another device pushed. Stop and reconcile; never auto-rebase Vault content.
- Obsidian Sync, iCloud, Dropbox, and Git solve different problems and can conflict when they edit the same files concurrently.
