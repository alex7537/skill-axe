---
name: research-gap-mapping
description: Test candidate research gaps against a structured literature evidence matrix and targeted second-pass searches, then rank defensible thesis entry points. Use for 研究空白二次检索、研究切入点、related-work synthesis、选题新颖性与可行性判断. Do not use before a corpus is verified, for generic brainstorming, or for writing final thesis paragraphs.
---

# Research Gap Mapping

Convert observed limitations into tested, bounded research opportunities. A gap is a claim about the literature coverage—not merely a topic the current corpus did not contain.

## Required input

Start from a `$paper-deep-analysis` evidence matrix with stable source IDs, locators, evidence status, and corpus limitations. If the input is only a list of titles or summaries, return to discovery/analysis rather than inventing a gap.

## Build and challenge candidate gaps

1. Group evidence by problem, mechanism, data/setting, evaluation, and deployment boundary.
2. Turn recurring limitations or contradictions into candidate gap statements. Use the taxonomy and falsification tests in [references/gap-tests.md](references/gap-tests.md).
3. For every candidate, run a targeted second-pass search using synonyms for both the missing capability and likely alternative terminology. Search recent primary work, review references, citing papers, and relevant adjacent fields.
4. Record supporting evidence, counterevidence, search coverage, and papers that partially close the gap. Search absence is `not found under recorded scope`, never proof of nonexistence.
5. Narrow surviving gaps to the smallest claim supported by the evidence. Distinguish novelty, importance, feasibility, and evaluability; none implies the others.
6. Rank thesis entry points by evidence strength, expected contribution, six-month feasibility, required data/hardware, available baseline, measurable outcome, and major confounders.

Use [assets/research-gap-matrix.csv](assets/research-gap-matrix.csv) for the decision record. Send only gaps with `supported` or `provisional` status to `$thesis-argument-builder`. Run `$citation-integrity-auditor` on the underlying claim/source ledger before finalizing.

## Deliverable

- field map: established, contested, under-tested, and out of scope;
- candidate gap matrix with supporting and disconfirming sources;
- exact second-pass queries, sources, dates, and coverage limits;
- ranked research entry points and a feasible minimum study for each;
- explicit status: `supported`, `provisional`, `rejected`, or `insufficient-search`.

## Gotchas

- “Few papers in our 15” is a corpus limitation, not automatically a field gap.
- “No one has done X” is almost never defensible without a broad, recorded search; prefer a bounded statement about population, setting, comparison, or evaluation.
- A method limitation does not imply a thesis contribution unless the user can access the required data, system, baseline, and evaluation.
- Do not hide counterexamples. A partially closing paper often helps define the remaining gap more precisely.
