---
name: personal-skill-chef
description: Route complex requests through the user's personal Codex Skill library by choosing, sequencing, validating, and integrating the smallest relevant set, with optional supervised resumable orders. Use when the user says to use their Skills or Skill library, asks for a master-chef analysis, requests combined multi-domain analysis, or a task clearly needs multiple Skills. Do not use when one installed Skill plainly owns a simple request or for unattended scheduling.
---

# Personal Skill Chef

Own the routing and final synthesis; let selected specialist Skills own their domains.

## Build the mise

Capture a compact working snapshot before acting:

- the user's actual outcome, scope, and success evidence;
- whether the request is read-only, allows local changes, or includes external mutations;
- relevant project state and constraints;
- installed Skill metadata from `~/.codex/skills`;
- backup metadata from the configured backup `skills/` directory only when installed Skills do not clearly cover the request.

Read only frontmatter during discovery. Prefer the installed copy when a Skill exists in both locations. Use `scripts/inventory_skills.ps1` when a deterministic inventory or keyword filter is useful.

## Prepare and validate the order

Choose the smallest set that covers the request, normally one to three Skills. For each selected Skill, state its job in one sentence. Read its complete `SKILL.md`, then only the references required for this request.

For a multi-stage request, keep a lightweight order in memory. Read [references/order-contract.md](references/order-contract.md) when dependencies, parallel work, mutation boundaries, or more than two Skills make the order non-obvious.

Before execution, verify that:

- every selected Skill exists and has a distinct purpose;
- dependencies are ordered and independent stages are merely identified as parallelizable;
- plan-only guidance does not silently become permission to execute;
- every write, install, synchronization, external message, commit, push, deletion, or other mutation remains within the user's authorization;
- the D-drive library is instructions and evidence, not permission to install or modify it;
- selected Skills do not require loading the whole library into context.

If validation fails, simplify or repair the order. Ask the user only when a missing choice would materially change the outcome or authority.

## Route tools deliberately

Choose tools from the evidence the stage must produce, not from habit. Read [references/tool-routing.md](references/tool-routing.md) when a request crosses filesystem, browser, desktop UI, connector, or long-running boundaries. Verify behavior on the same surface where the user experiences it whenever practical.

For work that must survive multiple turns or be resumed after interruption, read [references/supervised-loop.md](references/supervised-loop.md) and use `scripts/chef_runtime.ps1`. The runtime records state and enforces stage transitions; it does not execute stages, create agents, or grant permissions.

## Execute and integrate

Briefly tell the user which Skills were selected and why. Apply them in dependency order. The current Codex agent remains responsible for conflicts, evidence, verification, and the final integrated answer.

Do not start a background scheduler, create subagents, or parallelize agent work merely because the order has independent stages. Delegate only when the user explicitly requests it and the active environment permits it.

Do not install, synchronize, edit, commit, push, or run mutating operations merely to make routing convenient. A backup-only Skill may be read and followed in place; installation is a separate action.

## Reflect selectively

After substantial work, capture a reusable lesson only when it is specific, demonstrated, and likely to matter again. Read [references/learning-routing.md](references/learning-routing.md) before proposing or making a persistent routing or Skill improvement. Prefer fixing structure, scripts, or the owning Skill over accumulating generic notes. Do not write reflection artifacts by default.
