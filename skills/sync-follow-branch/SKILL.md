---
name: sync-follow-branch
description: Safely preserve uncommitted Git work, switch or retarget a local follow branch, fetch and rebase it onto the latest remote commit, then restore local files without losing work. Use when the user says they are changing the branch they follow, switching from one teammate branch to another, tracking the latest remote commit, saving dirty working-tree changes before switching, using stash around fetch/rebase, or asks for a safe Git branch-switch workflow. By default continue local edits on the synchronized follow branch; create a personal branch only when the user later chooses to commit, push, isolate, or publish the work.
---

# Sync Follow Branch

Safely move a dirty working tree onto the latest commit of a chosen remote branch. Treat the synchronized local follow branch as the default place for continued uncommitted edits; do not create a personal branch unless the user requests one or decides to commit/push/isolate the work.

## Inspect before changing state

Run the bundled read-only preflight script from the target repository:

```bash
bash <skill-dir>/scripts/git-follow-preflight.sh <target-branch> [remote]
```

Also inspect recent checkout history when the origin of the dirty files matters:

```bash
git reflog --date=iso -20
```

Identify:

- current branch and target follow branch;
- remote, defaulting to `origin` only when that remote exists;
- tracked modifications, untracked files, and staged files;
- whether the local target exists and what it tracks;
- ahead/behind counts after fetching.

Do not infer that dirty files belong to the currently checked-out branch. Git may have carried them across an earlier switch.

## Preserve dirty work

If the worktree is dirty, create a named stash before switching or rebasing:

```bash
git stash push -u -m "WIP before syncing <target-branch>"
```

Use `-u` to include untracked files. Do not use `-a` unless the user explicitly wants ignored files included. Immediately verify the stash, including its untracked-file parent:

```bash
git stash list
git stash show --stat --include-untracked 'stash@{0}'
git status --short --branch
```

If the changes are important or must survive repository deletion, explain that stash is local-only and offer a backup branch plus WIP commit. Do not create that branch or commit by default.

## Synchronize the follow branch

Fetch close to the rebase so the remote reference is fresh:

```bash
git fetch --prune <remote>
```

If the local target exists:

```bash
git switch <target-branch>
```

If only the remote target exists, create a local tracking branch:

```bash
git switch --track -c <target-branch> <remote>/<target-branch>
```

Inspect divergence before rewriting any local commits:

```bash
git rev-list --left-right --count HEAD...<remote>/<target-branch>
git log --oneline --left-right HEAD...<remote>/<target-branch>
```

Use the user's chosen rebase workflow:

```bash
git rebase <remote>/<target-branch>
```

When the local follow branch has no unique commits, this normally fast-forwards it. When it has unique commits, state that rebase will replay them and change their commit IDs before proceeding.

For a rebase conflict, inspect `git status`, resolve each file, stage it, and run `git rebase --continue`. Use `git rebase --abort` to return to the pre-rebase state. Never force-push, reset, or discard files as part of this workflow.

## Verify alignment

Require both a clean worktree and zero divergence before restoring the saved edits:

```bash
git status --short --branch
git rev-list --left-right --count HEAD...<remote>/<target-branch>
```

The count must be `0 0`. If the remote advances during the operation, fetch again and repeat the rebase.

## Restore local edits on the follow branch

Remain on the synchronized local follow branch by default. Restore with `apply`, not `pop`, so the backup remains until verification:

```bash
git stash apply 'stash@{0}'
git status
git diff
```

Treat conflicts here as stash-application conflicts, not rebase conflicts: resolve files and stage them normally; do not run `git rebase --continue`.

After the user verifies the restored files and any relevant tests, offer to remove the exact stash:

```bash
git stash drop 'stash@{0}'
```

Do not drop it automatically. Record or report its message and selector so it remains discoverable.

## Create a personal branch only when needed

Do not create a personal branch during routine synchronization. If the user later wants to commit, push, open a merge request, preserve a stable experiment, or separate unrelated changes, offer to create a branch at that point before committing:

```bash
git switch -c <personal-branch>
```

Uncommitted working-tree changes remain present across this switch when Git can apply it safely.

## Gotchas

- `git fetch` updates remote-tracking refs such as `origin/topic`; it does not move the local `topic` branch.
- Rebase preserves/replays commit order, not the order of uncommitted edits. A stash is a saved working-tree snapshot, not a commit series.
- Stashes belong to the repository, not to one branch, and are not pushed to the remote.
- A plain `git stash show` may omit untracked files; use `--include-untracked` when verifying a stash created with `-u`.
- Stash before switching or rebasing. Once a rebase is conflicted, do not try to stash as the normal recovery path.
- Keep generated files such as `.DS_Store` out of a future commit unless explicitly required.
