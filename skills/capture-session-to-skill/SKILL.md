---
name: capture-session-to-skill
description: Review a completed Codex task, solved incident, or meaningful milestone and decide whether its reusable knowledge should become a new or updated personal skill; then distill the current/local session safely and optionally back up personal skills to GitHub. Use at the end of non-trivial work, after a hard problem is solved, when the user says 完成了, 里程碑, 总结这次 session, 沉淀经验, 做成 skill, 保存长期记忆, 换电脑不丢, or asks to sync/upload personal skills to skill-axe. Do not trigger for trivial answers or while already creating/updating/syncing a skill.
---

# Capture Session to Skill

Turn successful work into a durable, executable asset instead of treating a long chat transcript as the final artifact.

## Completion Check

At the end of a non-trivial task, decide whether the result contains at least one of:

- a repeatable multi-step workflow;
- a difficult failure signature and verified diagnosis;
- non-obvious environment or tool constraints;
- commands, scripts, schemas, checks, or acceptance criteria worth reusing;
- a milestone whose implementation pattern will recur.

If none apply, finish normally. If they apply and the user has not already requested capture, add one concise optional question to the final answer:

> 这次已经形成可复用的「X」流程。是否把它沉淀为新的/更新现有的 `Y` skill，并备份到 `skill-axe`？

Do not interrupt the work before completion and do not create a skill without confirmation.

To install or restore the persistent reminder on a machine, preview and then apply the managed global instruction block:

```bash
python3 scripts/install_global_reminder.py
python3 scripts/install_global_reminder.py --execute
```

## Capture Workflow

1. Prefer the current conversation context. Read a local transcript only when important evidence was compacted or the user identifies another session. Search the narrowest known session; do not sweep all history by default.
2. Extract outcome, prerequisites, decision points, exact verified commands, failure modes, safety boundaries, validation evidence, and reusable artifacts.
3. The local skill may retain machine-specific context needed to run successfully, but keep it in runtime `config.json` or clearly identified private references when possible. Never store secrets, tokens, passwords, private keys, signed URLs, personal access tokens, or raw Docker auth in a skill. If a secret appeared in the session, recommend rotation.
4. Search existing personal skill descriptions first. Update the closest skill when the workflow belongs there; create a new skill only when it has a distinct trigger and responsibility.
5. Use the installed `skill-creator` and `skill-authoring` skills. Store only distilled knowledge, scripts, and focused references—never the raw session JSONL.
6. Validate scripts and run the official skill validator. State what was verified and what still requires a live environment.
7. Offer Git backup only after the skill itself is valid.

Read `references/capture-criteria.md` when choosing between updating an existing skill, creating a new one, or merely writing a short note.

## Git Backup

Use `config.json` and the bundled script. The script manages only `skills/`, `skills-manifest.json`, and the generated `SKILLS.md` usage dashboard in the configured repository; it never uploads sessions, Codex auth/state files, `.system`, or plugin caches.

The manifest preserves each skill's `added_at`, sorts skills newest-first, and merges `usage_count` plus `last_used_at` from the machine-local usage file. Record every personal skill at most once per session:

```bash
python3 scripts/record_skill_usage.py <skill-name> [<skill-name> ...]
```

The usage file is local state outside every skill folder and is not exported. On a restored machine, the recorder bootstraps each counter from the checked-out manifest before incrementing it.

Every executed sync regenerates `SKILLS.md` from the manifest. The dashboard lists every exported skill and its usage count, sorted by usage descending; do not edit it manually.

If `config.json` is absent after restoring from Git, copy `config.example.json` to `config.json` and fill the private repository URL and checkout path. Keep this runtime file local.

Preview first:

```bash
python3 scripts/sync_personal_skills.py
```

The export layer leaves local skills unchanged. It excludes runtime `config.json` and configured private-only files, replaces configured names, hosts, and paths with semantic placeholders in the Git snapshot, then scans the exported bytes for unresolved private information and credentials. Portable setup shapes belong in `config.example.json`.

Review included skills, exclusions, replacement count, privacy/secret scan result, destination, and proposed Git changes. Then ask for explicit confirmation before any commit or push.

After confirmation, run one of:

```bash
# Copy into the local checkout and show the diff.
python3 scripts/sync_personal_skills.py --execute

# One-step copy, commit, and push after the exact diff/scope was approved.
python3 scripts/sync_personal_skills.py --execute --commit --push \
  --message 'Sync personal Codex skills'
```

Use `--prune` only when the user also authorizes removing repository skill directories that no longer exist locally. Never force-push.

## Gotchas

- A session is evidence, not a durable runbook. Preserve conclusions and verified artifacts, not conversational chronology.
- A skill description cannot guarantee end-of-task reminders by itself. Pair this skill with concise global `~/.codex/AGENTS.md` guidance.
- Do not create one skill per incident if an existing skill should gain a new Gotcha.
- Do not back up `~/.codex` wholesale; it contains auth, session, state, logs, and local configuration.
- A successful local copy is not a Git backup until a commit exists remotely.
- Treat secret scanning as a guardrail, not proof that content is safe; always review the staged diff.
- The machine-local `~/.codex/skill-sync-privacy.json` controls `replacements`, `exclude_globs`, `blocked_literals`, and `blocked_regexes`; it is never copied into the skill repository.
- A restored exported skill keeps its reusable workflow and scripts. Machine-specific operations may require recreating `config.json`; this is an intentional setup step, not skill corruption.
- Read `references/restore-on-new-machine.md` when restoring the skill library on another computer.
