---
name: skill-authoring
description: Best practices for creating, reviewing, and improving agent skills (SKILL.md folders), distilled from how Anthropic uses hundreds of skills internally. Use this skill whenever the user wants to write a new skill, turn a workflow into a skill, review or refactor an existing skill, decide how to structure a skill folder, write a skill description, distribute skills to a team, or asks "how do I make a good skill". Trigger even if the user just says "把这个流程做成 skill" or "帮我写个 skill".
---

# Skill Authoring

Distilled from "Lessons from Building Claude Code: How We Use Skills" (Thariq, Anthropic, 2026-03-17). Core insight: **a skill is a folder, not a markdown file.** It can contain scripts, reference docs, assets, data, and hooks — things the agent discovers and uses on demand.

## Step 1 — Classify the skill

Before writing, identify which single category the skill belongs to. The best skills fit cleanly into ONE category; skills that straddle several become confusing and should be split. See `references/skill-types.md` for the 9 categories with examples. Quick index:

1. Library & API Reference · 2. Product Verification · 3. Data Fetching & Analysis · 4. Business Process Automation · 5. Code Scaffolding & Templates · 6. Code Quality & Review · 7. CI/CD & Deployment · 8. Runbooks · 9. Infrastructure Operations

## Step 2 — Structure the folder

```
skill-name/
├── SKILL.md          # frontmatter (name, description) + core instructions
├── references/       # detailed docs, API signatures, examples — loaded on demand
├── scripts/          # executable code for deterministic steps
└── assets/           # templates, snippets, data files
```

Use **progressive disclosure**: keep SKILL.md short and point to reference files ("read `references/api.md` before writing queries"). The agent reads them only when needed, saving context. Split anything detailed (function signatures, long examples) out of SKILL.md into `references/`.

## Step 3 — Write the content

Apply these rules, roughly in priority order:

1. **Don't state the obvious.** Claude already knows how to code and has default opinions. Only include knowledge that pushes it OUT of its default behavior (e.g. "avoid Inter font and purple gradients" — not "use good typography").
2. **Build a Gotchas section.** This is the highest-signal content in any skill. Seed it with known failure points; keep appending every time the agent hits a new edge case. Most great skills started as "a few lines and a single gotcha."
3. **Avoid railroading.** Give the goal and constraints, not prescriptive step-by-step instructions. Skills get reused in situations you didn't anticipate; the agent needs flexibility to adapt.
4. **Prefer scripts over prose.** Bundled scripts/libraries let the agent spend its turns on composition and decision-making instead of reconstructing boilerplate. The agent can also generate new scripts that compose your bundled ones.
5. **Description field = trigger condition, written for the model.** The agent scans a listing of all skill descriptions to decide "is there a skill for this?" So the description must state WHEN to use the skill (user phrases, contexts, file types), not just summarize it. Skills tend to under-trigger, so be a bit pushy: enumerate trigger phrases and edge contexts.
6. **Think through setup.** If the skill needs user-specific context (IDs, credentials, preferences), store it in a `config.json` inside the skill dir. If config is missing, instruct the agent to ask the user (use AskUserQuestion for structured choices) and write the file.
7. **Memory.** Skills can store state: append-only logs, JSON files, or SQLite. Logging previous runs helps consistency in recurring workflows (e.g. weekly reports). In Claude Code plugins, write persistent data to `${CLAUDE_PLUGIN_DATA}` — the skill directory itself may be wiped on upgrade.
8. **On-demand hooks.** Skills can register hooks active only for the session in which the skill is invoked. Use for opinionated guardrails you don't want globally, e.g. a `/careful` skill blocking `rm -rf` / `DROP TABLE` / force-push via a PreToolUse matcher, or `/freeze` blocking edits outside a directory.

## Step 4 — Distribute, compose, measure

- **Distribution:** small teams → check into repo under `.claude/skills`. At scale → package as plugins in an internal marketplace, so teams choose what to install (every installed skill costs a little context).
- **Marketplace curation:** don't centralize approval. Let skills incubate in a sandbox folder; once one gains organic traction, its owner PRs it into the marketplace. Curate before release to avoid redundant skills.
- **Composition:** skills can reference other skills by name; the model will invoke them if installed. No native dependency management yet — document dependencies in the description or body.
- **Measurement:** log skill invocations with a PreToolUse hook to find popular skills and ones that under-trigger vs. expectations.

## Gotchas

- Writing a skill that straddles multiple categories → split it into two skills.
- Putting "when to use" info in the body instead of the description → the agent never sees it at trigger time; it must live in the description.
- Over-specifying steps → agent follows them rigidly in situations where they don't apply.
- Restating Claude's default knowledge → wasted context, no behavior change.
- Storing mutable data inside the skill folder in plugin setups → lost on upgrade; use `${CLAUDE_PLUGIN_DATA}`.
- One giant SKILL.md → move detail to `references/` and point to it.
