---
name: corporate-git-push-gate
description: Gate every Git push, remote-branch deletion, tag publication, force push, or other remote mutation targeting company or ambiguous repositories. Use automatically before mutating remotes such as code.<internal-domain>, when a local worktree inherited a company origin, when switching between personal GitHub and corporate GitLab, or whenever the user says push/sync without naming the exact repository. Always require a fresh explicit confirmation after showing the resolved target; successful SSH authentication is not authorization.
---

# Corporate Git Push Gate

Prevent repository-context mistakes by separating local implementation permission
from permission to mutate a specific remote.

## Mandatory two-turn gate

Before any remote mutation, run:

```bash
python3 ~/.codex/skills/corporate-git-push-gate/scripts/git_push_preflight.py \
  --repo <working-tree> --remote <remote> --operation <operation> \
  --target-ref <branch-or-tag>
```

Treat `classification=corporate` or `classification=unknown` as gated. Show the
user a concise confirmation card containing:

```text
Operation
Repository root
Remote name and sanitized push URL
Classification and reason
Local branch and HEAD SHA
Target remote ref
Commits and files that would be published or deleted
Whether force/non-fast-forward behavior is involved
```

Then stop without mutating the remote. Ask the user to confirm this exact
operation. Even when the user initially requested a company push, the
confirmation must occur after the resolved card is shown, in a later user turn.

Confirmation is valid for one operation only. Re-run the preflight and ask again
if HEAD, remote URL, local branch, target ref, operation, commit set, or file set
changes.

## Classification

- Corporate: `code.<internal-domain>`, a `dev-algorithm`/company namespace, or another
  remote identified by the user as company-owned.
- Personal: `github.com/<github-owner>/...` unless the user states otherwise.
- Unknown: anything that cannot be confidently classified. Unknown is gated.

Repository architecture, checked-out base branch, configured credentials, write
access, and successful earlier pushes do not determine where the user wants code
published. A worktree inherits its repository's remotes; never treat that as
publication intent.

## Additional boundaries

- Do not copy company-derived source into a personal/public repository without
  explicit authorization and a provenance/license check.
- Force pushes, remote deletion, protected branches, and tags require the card
  to call out the destructive or release effect explicitly.
- A vague response such as “继续” is insufficient if more than one target or
  operation is possible. Require the exact target to be unambiguous.
- Never display private keys, credential helpers, tokens, embedded URL secrets,
  or raw authentication debug output.
- Read-only commands (`remote -v`, `status`, `diff`, `log`, `ls-remote`) do not
  require approval.

## After an approved mutation

Perform only the confirmed operation. Verify the exact remote ref with a
read-only query, report its resulting SHA or absence, and state whether local
work remains recoverable. Do not chain another push, merge, tag, or deletion
under the same confirmation.

## Gotchas

- “Create a new branch” authorizes a local branch, not a remote push.
- “Push” in a personal-repository conversation does not authorize a company
  remote discovered later during implementation.
- Git `user.name`/`user.email` are commit metadata, not the authenticated server
  identity or ACL.
- Deleting an accidentally published remote branch repairs visibility but does
  not prove nobody fetched it; avoid the initial push instead.
