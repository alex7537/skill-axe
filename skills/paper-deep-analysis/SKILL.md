---
name: paper-deep-analysis
description: Deeply analyze and compare a verified corpus of academic papers using full-text evidence, common fields, and cross-paper contrasts. Use for 15篇论文深度拆解、方法与实验横向比较、逐篇创新与局限提取, or corpus-level synthesis after screening. Use quick-paper-review for one-paper triage; do not discover the corpus or draft thesis prose here.
---

# Paper Deep Analysis

Turn a verified paper set into comparable evidence. Optimize for faithful method/result extraction and explicit uncertainty, not polished narrative.

## Inputs and evidence

- Require stable paper identifiers plus full text or the best accessible primary version. If only an abstract is available, label every affected field `abstract-only` and do not infer experimental detail.
- Use the paper itself for method, experiment, result, and author-stated limitation claims. Secondary summaries may help navigation but are not evidence for those fields.
- Attach a locator to consequential evidence: page and section, equation, table, figure, appendix, or paragraph marker. Keep quotes short; prefer faithful paraphrase.
- Separate `reported` facts, `author interpretation`, and `analyst inference`. Never turn an inference into the authors' claim.

## Analyze each paper

Read [references/analysis-contract.md](references/analysis-contract.md) and populate [assets/paper-evidence-matrix.csv](assets/paper-evidence-matrix.csv). Capture:

- research question and claimed contribution;
- inputs, outputs, architecture/pipeline, objective/loss, training and inference;
- datasets/tasks, splits, baselines, metrics, ablations, compute/hardware when material;
- principal quantitative result with comparator and conditions;
- author-stated limitations, observed design limitations, and reproducibility blockers;
- relationship to the target thesis and the other papers.

## Compare the corpus

Normalize terminology before comparison. Compare like with like: matched task, data, metric definition, split, evaluation mode, and budget. When conditions differ, explain the confounder instead of ranking raw numbers.

Produce a cross-paper table organized by mechanisms and evidence, not a sequence of mini-abstracts. Identify agreements, contradictions, dependency chains, missing baselines, and repeated evaluation weaknesses. Use `$citation-integrity-auditor` before treating the matrix as writing-ready.

## Deliverable

- one row per paper with locators and evidence status;
- a mechanism/evaluation comparison table;
- strongest supported findings and unresolved conflicts;
- limitations of the corpus and missing full texts;
- candidates for targeted gap testing, without declaring a research gap yet.

## Gotchas

- “Novel” in the abstract is a claim to test against related work, not a fact to copy.
- A higher metric is not comparable when datasets, splits, sensors, horizons, or success definitions differ.
- No ablation is not proof that a component has no effect; it is missing attribution evidence.
- The absence of a limitation section does not mean the method has no limitations. Label analyst-identified limits separately.
