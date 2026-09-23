---
name: project-to-feishu-visual-report
description: Create an evidence-backed, diagram- and table-led Feishu project summary from a local repository and optional Obsidian notes. Use when the user says 把当前项目总结成飞书文档、参考源码和 OB 文档、尽量图片表格化, or requests a visual project handoff in Feishu. Do not use for read-only Feishu review, PPT creation, or running evaluations.
---

# Project to Feishu Visual Report

Category: Runbooks. Deliver a readable project document whose diagrams and capability claims agree with the inspected checkout. Keep code and notes read-only unless their modification is separately requested.

## Evidence before layout

- Confirm the repository, branch, commit and dirty/untracked files. Read repository instructions, README, manifests, entry points and one representative execution path. Use `understand-codebase` when available for deeper tracing; do not duplicate an entire code audit.
- Locate the Obsidian vault from known context or local application configuration. Search project names and aliases narrowly with `rg`; expand into linked notes only when relevant.
- For **current implementation claims**, prioritize executable source/configuration over README and dated notes. Preserve historical decisions and historical validation as dated evidence; source inspection does not prove runtime correctness.
- Make a compact evidence ledger: claim, source path/symbol or note section, date/commit, current versus historical, validation performed, unresolved boundary.
- Explicitly reconcile disagreements. A note about uncommitted work in another checkout is not proof that this checkout contains it. An untracked helper is locally available but not reproducible from the recorded commit alone.
- Inspect local screenshots/contact sheets and output artifacts. Label real screenshots, sampled data images and explanatory diagrams distinctly. Do not claim freshly run tests from old logs or infer full dataset quality from a sample.

## Compose around reader decisions

For an orientation or handoff, a useful order is purpose → input/entry/output map → core semantics → real evidence → usage → limitations → sources. Adapt the order to the user's task; do not enforce a fixed section or image count.

Use tables for exact mappings and comparisons, diagrams for flow and coordinate/ownership relations, and actual images for appearance or evidence. A visual needs a nearby caption explaining its meaning and limitations. Avoid decorative imagery and benchmark numbers without measurements.

Keep commands tied to actual CLI definitions and environment requirements. Mark examples that were checked against source but not executed. Explain schema, unit, coordinate-frame and timestamp differences before implying equivalence between inputs.

Read [references/lark-cli-workflow.md](references/lark-cli-workflow.md) when publishing. For robot-data projects resembling MCAP/HDF5 playback, selectively read [references/robot-data-evidence.md](references/robot-data-evidence.md).

## Publishing boundaries

- A request to create a Feishu document authorizes creating that document. It does not authorize editing unrelated documents, sending notifications, changing permissions or publishing to a public audience.
- Discover the available connector or authenticated `lark-cli`; read its current documentation rather than embedding a stale API specification here. Keep the authenticated identity consistent.
- If no parent destination was specified, a new document in the user's library is a reasonable default; do not guess a shared Wiki parent from an unrelated prior task.
- Before modifying an existing target, resolve title, type, owner and current effective permission through read-only checks. If owner differs from the current user or cannot be established, present the exact change and obtain separate confirmation. Never probe permissions by writing.
- Permission changes, deletion, ownership transfer, public sharing and bulk writes require separate explicit confirmation for exact targets/effects. Do not switch user/bot identity to bypass access failure.

## Definition of done

1. The requested document exists and creation warnings have been checked.
2. A fresh read confirms the title, expected sections, tables and media references, including the final section; a create success alone is insufficient.
3. Diagram previews have been exported and visually inspected for clipping, overlap and unreadable text. Check source images before upload; when media insertion reports trouble, verify that resource specifically.
4. Claims distinguish inspected source, historical evidence, newly run validation and unresolved tests. A recording verifier passing is not a Viewer visual check.
5. Clean up only the task's temporary draft workspace; preserve user source images and datasets. Return the document link and a concise account of contents or material gaps.

On partial creation/resource failure, retain the returned document ID. Repair only the failed part after applying the existing-target checks; do not create duplicate documents. If blocked by authentication or missing scope, preserve the prepared result as appropriate and report the blocker without claiming publication.

## Gotchas

- Table-heavy content still needs a short narrative explaining the project and the main decision; a field dump is not a summary.
- Native diagrams can export onto a larger white canvas. Inspect the actual rendered content; an API success does not establish legibility.
- Never call an image contact sheet a Viewer screenshot, or interpolated frames original observations.
- Keep document tokens, personal paths, tenant identifiers and raw transcripts out of this portable skill. Runtime output links belong in the task result, not a reusable template.
