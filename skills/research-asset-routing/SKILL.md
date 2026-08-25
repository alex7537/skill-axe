---
name: research-asset-routing
description: "Route robot-ML and embodied-AI research outputs to the correct canonical home: distilled ideas and decisions in Obsidian, executable source and pipelines in GitHub, released checkpoints in Hugging Face, run telemetry in experiment infrastructure, and raw data in data platforms. Use when the user says 把 Obsidian 当大脑, 整理研究成果, 这段内容该放哪里, Obsidian/GitHub/Hugging Face 如何分工, or wants a lightweight idea→code→checkpoint knowledge chain. Do not use to perform the actual model release or reorganize the Vault filesystem."
---

# Research Asset Routing

Keep the research brain semantic and lightweight. Route each artifact to one canonical home, then cross-link immutable identities instead of copying payloads.

## Canonical ownership

```text
Obsidian       = why, insight, decision, failure lesson, next hypothesis
GitHub         = source, pipeline, config schema, tests, reproducible command
Hugging Face   = released weights, inference config, model card, compact metrics
W&B / TI-ONE   = run logs, task state, curves, periodic checkpoints
Data platform  = raw/processed data, labels, split manifests, large evaluations
Codex Skill    = repeatable method with triggers, gates, and deterministic tooling
```

Read [references/routing-contract.md](references/routing-contract.md) when classifying mixed artifacts, writing an Idea Card, or auditing duplication across systems.

## Core workflow

1. Identify the artifact's consumer and lifecycle: thought, source, run, data, checkpoint, or reusable procedure.
2. Choose exactly one canonical home. Other systems receive links, revisions, hashes, and compact conclusions—not copies.
3. For a meaningful research result, create or update one Obsidian Idea Card using [assets/idea-card.md](assets/idea-card.md).
4. Bind the card to executable evidence:
   - GitHub repository + full commit SHA + entry/config;
   - dataset/split identity without private raw paths;
   - run/task identity and decisive metrics;
   - Hugging Face repository + immutable revision + artifact hash when released.
5. Record the decision: `continue`, `reject`, `promote`, or `archive`, plus the next falsifiable test.

## Obsidian admission rule

Content belongs in the brain only when it changes at least one of:

- the mental model of how the system works;
- a design or project decision;
- an experiment hypothesis or acceptance gate;
- a reusable failure lesson;
- the relationship among data, policy, world model, evaluation, and release.

Otherwise store it at the operational source and link it if needed.

## Compression rule

An Obsidian project note should normally contain:

- one-sentence project role;
- 3–7 key ideas or invariants;
- current evidence date and confidence;
- pointers to code, data, run, and checkpoint;
- one decision and next experiment.

Avoid copying full READMEs, code blocks, logs, command transcripts, file trees, checkpoint lists, or generated reports. Preserve a short command only when it defines a stable reproduction contract not already documented in GitHub.

## Composition

- Use `$publish-model-release` when creating or auditing an actual GitHub/Hugging Face release.
- Use `$robot-ml-lifecycle` when controlling a multi-phase data→train→evaluate→release loop.
- Use `$obsidian-vault-versioned-reorg` for Vault paths, links, deduplication, Git history, and safe restructuring.
- Use `$capture-session-to-skill` when a repeated method should become executable rather than remain a note.

## Success criteria

- every artifact has one canonical owner;
- Obsidian contains a concise Idea Card rather than duplicated payloads;
- Git commit, data/split, run, and checkpoint identities are traceable;
- a reader can tell what was learned, why it matters, and what happens next;
- deleting a noncanonical copy would not destroy unique information.

## Gotchas

- A project dashboard is navigation, not the source of real-time training status.
- A GitHub README explains software; copying it into Obsidian creates a stale second source.
- A Hugging Face upload without an exact Git commit and inference contract is not a reproducible release.
- W&B curves and TI-ONE logs are evidence, not durable conceptual memory; summarize only the decisive result.
- A checkpoint path is not an identity. Prefer repository/revision plus SHA256 and role.
- A failed experiment belongs in Obsidian when the failure changes future decisions; raw logs remain with the run.
- Do not store secrets, private dataset paths, signed URLs, raw sessions, QR codes, or proprietary samples in portable notes or skills.
