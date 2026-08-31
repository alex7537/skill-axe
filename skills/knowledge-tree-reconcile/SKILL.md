---
name: knowledge-tree-reconcile
description: Globally search personal Codex skills and an Obsidian vault, compare incoming knowledge with existing nodes, classify it as duplicate, extension, contradiction, new concept, or new workflow, and update the smallest canonical skill, note, or knowledge-map entry without creating duplicate truth. Use when the user says 检查并更新知识树、全局检索之前的知识、把新知识归入已有版图、判断该更新 skill 还是 Obsidian, or asks to reconcile a completed explanation/workflow against their existing knowledge system. Do not mutate the vault or skills unless the user explicitly requests the update.
---

# Knowledge Tree Reconcile

Treat the knowledge tree as a set of canonical owners plus navigation links, not as one giant document. Search globally, decide locally, and make the smallest verified update.

## Canonical roles

- **Codex skill:** repeatable method with a trigger, required evidence, decisions, safety boundaries, failure modes, and verification.
- **Obsidian note:** durable mental model, concept relationship, decision, failure lesson, or evidence-backed conclusion.
- **Obsidian map/index:** navigation, maturity, gaps, and links; never the full operational procedure.
- **Repository/runtime system:** executable source, logs, data, checkpoints, and other live facts. Link them instead of copying payloads into the tree.

## Reconciliation workflow

1. Convert the incoming material into a compact evidence packet:
   - candidate concept or procedure;
   - trigger/use case;
   - verified evidence and date;
   - known limits, unresolved claims, and whether the fact is time-sensitive.
2. Resolve the exact personal skill roots and Obsidian Vault. Confirm the Vault with `.obsidian/` and inspect its Git status before any write.
3. Run `scripts/scan_knowledge_tree.py` with 2–6 discriminating terms, including synonyms in both English and Chinese. This is a global candidate search, not the final decision.
4. Read the top matching skill descriptions and relevant bodies/references; read the top matching notes and their nearest map/index. Do not decide from filenames alone.
5. Classify each incoming item as `duplicate`, `extension`, `contradiction`, `new-concept`, `new-workflow`, or `transient`. Read `references/decision-matrix.md` for routing and conflict rules.
6. Choose the smallest canonical update:
   - same trigger and responsibility → update the existing skill;
   - same durable concept or decision → update the existing Obsidian note;
   - distinct repeatable workflow → create a focused skill;
   - distinct durable concept → create a focused note under the nearest domain;
   - method plus mental-model change → let the skill own procedure and let Obsidian keep only the insight, evidence, boundary, and link/entry.
7. Update the nearest existing map/index only when navigation, maturity, ownership, or a gap changed. Do not create a new global dashboard for one node.
8. Validate and re-read:
   - skills: validate frontmatter, scripts, references, and realistic behavior;
   - Obsidian: inspect the isolated diff, Wiki-link targets, frontmatter, and surrounding structure;
   - ensure unrelated dirty files remain untouched and no unique content was replaced by a summary.
9. Report the comparison result, canonical owner, exact files changed, verification evidence, remaining conflicts, and whether backup/commit is still pending.

## Write safety

- A request to inspect or recommend is read-only. Writing requires an explicit request to update/create the relevant knowledge assets.
- Resolve exact targets before writing. Preserve user changes and stage edits outside protected locations when direct writes are restricted.
- Never store raw chat transcripts, tokens, credentials, private keys, signed URLs, QR codes, raw logs, proprietary samples, or large generated payloads in portable skills or notes.
- Do not commit, push, reorganize folders, delete duplicates, or rewrite archive history unless separately requested.
- For a contradiction, retain the older claim as historical evidence when useful; add a superseding statement with source/date rather than silently erasing it.

## Completion criteria

- global candidates were searched with explicit terms;
- the closest existing nodes were actually read;
- the novelty class and routing decision are stated;
- exactly one canonical owner holds the full knowledge;
- maps contain links/status rather than duplicated instructions;
- changed artifacts pass their format/behavior checks;
- unrelated worktree changes are preserved.

## Gotchas

- “No filename match” is not proof of novelty; search descriptions, aliases, bodies, and references.
- A new incident usually belongs in an existing skill's `Gotchas`; it rarely deserves a new skill.
- A tutorial can contain both concept and procedure. Split ownership by purpose instead of copying the whole tutorial into both systems.
- Installed-skill count, note count, and dashboard count are inventory metrics, not evidence of understanding.
- Current machine state decays quickly. Store the reusable inference and dated evidence, not a timeless claim that a service or model is still online.
- Do not let a broad meta-skill absorb domain logic. It owns retrieval, comparison, routing, and verification; the domain skill owns the actual procedure.
