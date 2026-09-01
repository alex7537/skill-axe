# Dual-store knowledge status audit

Use this mode when the user asks whether the knowledge tree is updated, synchronized, backed up, current, or aligned.

## Required composition

Audit both stores in the same task. Do not substitute a direct `git status` check for either owning skill.

1. **Personal skills side:** invoke `$capture-session-to-skill` in its preview/status mode. Read its current `SKILL.md` and follow its Git-backup workflow to inspect:
   - selected personal skills and files;
   - exclusions, privacy replacements, and secret-scan result;
   - configured `skill-axe` checkout, local dirty state, remote reachability, and ahead/behind state;
   - whether exporting current local skills would produce a diff.
2. **Obsidian side:** invoke `$obsidian-vault-backup` in inspect/preview mode. Read its current `SKILL.md` and use its bundled preview to inspect:
   - exact Vault, branch, and remote;
   - tracked and untracked knowledge changes;
   - selected versus excluded backup scope and scan result;
   - ahead/behind or diverged state.

If either dependency is unavailable, report that side as `not audited`; do not silently replace it with an improvised workflow.

## Read-only default

A status request authorizes inspection only.

- Do not run export/copy modes that modify a sync checkout merely to obtain a cleaner answer unless the user explicitly authorizes that local mutation.
- Do not stage, commit, push, rebase, change remotes, or install automation.
- If a preview cannot establish byte-level equality without an export, report `local export pending` rather than `aligned`.
- If fetch fails, distinguish `remote status unknown` from `out of sync` and include the concrete transport blocker.

Each owning skill retains its own approval gate. A later request to synchronize both sides requires separate exact-scope previews and explicit confirmation before each commit/push.

## Combined status contract

Report the stores separately before giving an overall conclusion:

| Store | Local content | Export/backup diff | Remote drift | Status |
|---|---|---|---|---|
| Personal skills ↔ `skill-axe` | count and relevant changes | none / pending / changed | ahead/behind/unknown | aligned / local-only / behind / diverged / blocked / unknown |
| Obsidian Vault ↔ Vault remote | relevant dirty paths | selected/excluded paths | ahead/behind/unknown | aligned / local-only / behind / diverged / blocked / unknown |

Overall status is `fully aligned` only when both rows are independently verified aligned. If one side is local-only, blocked, or unknown, say `not fully aligned` and name that side.

Keep semantic status separate:

- `discoverable`: the skill/note can be found by knowledge-tree search;
- `canonically routed`: one owner holds the full knowledge;
- `synchronized`: the reviewed content is present at the corresponding remote commit.

None of these states implies the others.
