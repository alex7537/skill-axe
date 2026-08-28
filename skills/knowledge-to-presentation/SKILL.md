---
name: knowledge-to-presentation
description: Turn Obsidian notes, personal Codex skills, research documents, or technical knowledge into a concise PPTX with concept compression, accessible mathematics, annotated sources, and optional 5/10-minute speaker notes. Use when the user says 把知识总结做成PPT, 从Obsidian/skills生成演示文稿, 讲透模型架构, 给演讲稿, or asks to migrate a research knowledge map into slides. Do not use for styling-only edits or when the user only wants a prose summary.
---

# Knowledge to Presentation

Convert a semantic knowledge base into a presentation people can understand and deliver. Do not paste notes into slides or treat a source-path list as speaker support.

## Responsibility

This Skill owns the transformation between knowledge and presentation:

- identify the audience-facing thesis;
- compress sources into a cumulative slide narrative;
- explain technical mechanisms at multiple levels;
- write useful speaker notes and timed scripts;
- preserve evidence boundaries and traceability.

Use the installed `$presentations` Skill for PPTX authoring, rendering, and layout verification. Use `$math-principles-coach` when the topic needs variables, probability, objectives, gradients, or training/inference distinctions. Domain Skills supply facts and evaluation contracts; they do not replace synthesis.

## Evidence contract

- Treat Obsidian, Skills, papers, code, and run logs as different evidence types. Do not merge claims whose confidence differs.
- Read source repositories and documents without modifying them unless the user explicitly requests that write.
- Separate public facts, local implementation facts, mathematical consequences, and hypotheses.
- Keep raw logs, full code, checkpoints, and long source excerpts out of the deck. Retain revisions, hashes, or links in notes when they matter.
- Never copy secrets, signed URLs, private credentials, or raw session transcripts into a deck or Skill.

## Build the knowledge model before slides

For a technical or ML topic, answer the smallest relevant subset of:

1. What problem is being solved?
2. What are the conditions or inputs?
3. What is predicted or decided?
4. What representation or architecture transforms the inputs?
5. What objective creates the learning pressure?
6. How do training and inference differ?
7. What evidence would prove or reject the claimed capability?

Do not organize the deck by paper names unless chronology is the communication job. Prefer a mechanism, decision, or learning progression.

Read [references/content-contract.md](references/content-contract.md) before planning a technical deck, an accessible-math explanation, or timed speaker notes.

## Compress for the page budget

- Give each slide one narrative job and one claim-style title.
- Preserve only details needed to understand, decide, or perform the next step.
- Use visible slides for the audience and speaker notes for derivations, caveats, provenance, and talk tracks.
- A five-page technical deck usually needs: thesis, core tension, mechanism comparison, implementation/experiment contract, and evaluation/action closure. Adapt when the topic demands a different arc.
- Do not create an agenda slide merely to fill space.

## Explain without losing rigor

Use an explanation ladder:

1. one sentence without jargon;
2. a concrete everyday analogy;
3. a tiny numerical or geometric example;
4. the minimum useful equation with every symbol defined;
5. what gradient, sampling, or integration mechanically does;
6. what the equation guarantees and does not guarantee;
7. a falsifiable experiment or understanding check.

For every loss, state the target, randomness, reduction, gradient recipient, and train/inference difference. A lower loss is never automatic proof of closed-loop task success.

## Speaker notes are a teaching artifact

When the user wants to present or learn the material, notes should contain only useful sections from this list:

- `[本页一句话]`
- `[给爷爷奶奶的一句话]`
- `[符号账本]` or `[张量和形状]`
- `[最小数学]`
- `[公式怎样推动学习]`
- `[5分钟基础稿｜本页约…秒]`
- `[10分钟扩展｜在基础稿后追加约…秒]`
- `[理解检查]`
- `[Sources]`

The 5-minute segments must form one complete talk. The 10-minute mode is the complete 5-minute talk plus clearly labeled extension segments. Budget time across the whole deck rather than assigning five minutes to every slide.

Every source line must say what that source contributes, for example:

```text
- <knowledge-note>: supports the conditional-action-distribution definition and evaluation boundary.
- <domain-skill>: supplies the staged failure funnel and promotion gate.
```

A bare path or URL is not a knowledge summary.

## Produce and verify the deck

1. Resolve topic, audience, purpose, page count, and whether speaker notes are required.
2. Inventory the narrowest relevant sources; prefer canonical knowledge notes and current domain Skills over broad vault searches.
3. Write the knowledge model and slide claims before authoring.
4. Use `$presentations` to create or edit the PPTX. Preserve an existing deck's layout and visible hierarchy when notes are the only requested change.
5. Render every final slide and inspect it at full size.
6. Inspect the exported PPTX notes, not only the render. Run:

```bash
python3 scripts/validate_speaker_notes.py <deck.pptx> \
  --require-accessibility --require-timed-scripts --require-annotated-sources
```

7. Report the final deck, the source categories used, and any evidence limitations.

## Success criteria

- the audience can state the central mechanism without repeating unexplained jargon;
- equations have defined symbols and a concrete interpretation;
- training, inference, and evaluation are not conflated;
- visible slides remain low-density and coherent;
- speaker notes support both a short and extended delivery when requested;
- sources are annotated with their contribution;
- the final PPTX passes visual, overflow, note-content, and source-traceability checks.

## Gotchas

- A source list is provenance, not explanation. Summarize the contribution beside each source.
- More model names do not create a knowledge map. Organize by mechanism and evidence.
- Do not put the full derivation on the slide when it belongs in notes.
- “High-school accessible” does not mean deleting mathematics; it means defining symbols, using one small example, and stating the physical meaning.
- Do not say deterministic MSE can never learn multimodality. The failure is a single point estimate under separated valid modes; generative methods may also use MSE with noise/time conditioning.
- Do not compare raw losses across methods that predict different targets.
- Do not describe training-time random-step regression as the full multi-step inference chain.
- A polished render does not prove notes were exported. Inspect the PPTX notes XML or presentation notes objects.
- Editing only speaker notes must not change visible slide geometry, theme, or text.

