# Versioned reorganization runbook

Use this reference only after the user authorizes modifications.

## 1. Resolve and freeze scope

Confirm all of the following:

- exact vault root;
- `.obsidian/` belongs to that root;
- whether the root or a parent is already inside Git;
- protected folders;
- existing uncommitted work;
- whether Obsidian or another process is actively editing notes.

When reading the macOS Obsidian registry, treat it as corroborating evidence rather than overriding the user's named path:

```text
~/Library/Application Support/obsidian/obsidian.json
```

## 2. Establish Git boundary

Initialize Git only at the exact vault root. Before the baseline commit, create a narrow `.gitignore` such as:

```gitignore
.DS_Store
Thumbs.db
.trash/
.backup_*/
.obsidian/workspace*.json
.obsidian/plugins/
.claudian/
```

Track stable Obsidian preferences only when useful, for example `app.json`, appearance, bookmarks, core/community plugin lists, graph settings, and snippets. Inspect new plugin data before tracking it; private repositories are not a license to commit secrets.

If Git identity is missing, ask the user or use a repository-local neutral identity only with their knowledge. Never change the global Git identity as a cleanup side effect.

Create and verify a baseline:

```bash
git init -b main
git add -A
git diff --cached --name-only
git commit -m "baseline: capture vault before reorganization"
git tag -a "vault-v0-baseline-YYYY-MM-DD" -m "Vault before reorganization"
git switch -c "reorg/YYYY-MM-DD"
```

Verify ignored paths are not staged and `git remote -v` is empty unless a remote was already intentionally configured.

## 3. Inventory before moving

Run `audit_vault.py` with every protected folder. Review:

- top-level counts and sizes;
- exact duplicates and duplicate filenames;
- zero-byte files and empty directories;
- path-like missing links separately from concept/author Wiki nodes;
- isolated notes and unreferenced attachments as candidates only;
- existing cleanup plans, indexes, and contradictions among entry notes.

Prefer updating an existing cleanup map when it still reflects the intended structure. Create a new content map when the old plan has a conflicting responsibility or is marked pending after the repository has changed materially.

## 4. Execute reversible batches

Recommended ordering:

1. Content map and maintenance changelog; no moves.
2. Clearly stale status snapshots; archive, do not delete.
3. Exact duplicates; select the main file using content completeness, incoming links, and semantic location.
4. Rename archived duplicate copies so Obsidian no longer sees the same basename twice.
5. Add MOCs and metadata before physically moving evergreen knowledge.
6. Create an Idea intake/validation layer only when it matches the vault's purpose.

For each batch:

- list exact source and destination paths;
- update path-qualified incoming links and moved notes' relative outgoing links;
- keep pure basename links only when the basename becomes unique;
- run the after-audit and comparator;
- inspect `git diff --cached --name-status` before committing;
- commit one intention only.

If filesystem moves are necessary, remember that Obsidian will not necessarily rewrite links. Prefer moves inside Obsidian when practical; otherwise repair links deterministically.

## 5. Review and accept

Create a review tag after all gates pass:

```bash
git tag -a "vault-vX-review-YYYY-MM-DD" -m "Reviewed staged reorganization"
```

Leave the main branch at the baseline until the user reviews the vault in Obsidian. Then merge normally and tag the stable structure. Do not force-reset, force-push, or delete the observation archive as part of acceptance.

## Rollback model

- Reject one batch: revert its commit, preserving later evidence where possible.
- Reject the whole layout: create a new branch from the baseline tag; do not destroy the existing reorganization branch.
- Recover from disk loss: local Git on the same disk is insufficient; use an authorized remote or independent snapshot backup.

