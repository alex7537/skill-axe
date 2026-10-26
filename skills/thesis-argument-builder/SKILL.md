---
name: thesis-argument-builder
description: Build evidence-linked Chinese and English academic arguments for a thesis introduction, related work, motivation, or research questions. Use for 中英文学术论证、研究动机、引言/相关工作段落、从现有方法局限推导本文切入点. Requires verified claim and gap evidence; do not use to invent citations or perform the literature search itself.
---

# Thesis Argument Builder

Write a logically explicit argument whose substantive claims can be traced to verified evidence. The structure is claim-driven, not citation-driven.

## Input gate

Require a claim/source ledger plus a `$research-gap-mapping` result. Each factual or comparative premise must have source IDs and locators. If evidence is missing, either narrow the sentence, label it as a proposal/hypothesis, or leave a visible evidence placeholder; never manufacture a citation.

Read [references/argument-contract.md](references/argument-contract.md) before drafting a thesis section. Use [assets/argument-outline.md](assets/argument-outline.md) to preserve the reasoning chain.

## Build the argument

1. State the research problem and why it matters at the supported level of scope.
2. Group existing approaches by method or assumption; do not write a paper-by-paper catalogue.
3. State what each family achieves, then its evidenced boundary or unresolved contradiction.
4. Derive the bounded gap from those premises and acknowledge strong counterevidence or partial solutions.
5. State the thesis motivation, research question/hypothesis, proposed contribution, and evaluation needed to test it. Use future/proposal language for work not yet completed.
6. Attach citations at the exact claim they support. A citation must not be stretched to support a broader claim than its evidence.

## Chinese and English versions

Create one shared claim outline first, then produce both languages from it. Preserve claim IDs, scope, certainty, and citations across versions. Prefer natural academic phrasing over sentence-by-sentence literal translation. After drafting, run a semantic parity check: neither version may add stronger novelty, causality, results, or generality.

Use neutral evidence language such as “reported,” “observed under,” “suggests,” or “remains under-tested” according to the source. Avoid “proves,” “solves,” “significantly,” “state of the art,” and “first” unless the evidence and statistical/provenance context support them.

Run `$citation-integrity-auditor` on the finished section before treating it as submission-ready.

## Deliverable

- claim-outline with premise → limitation → gap → question → contribution → evaluation;
- Chinese academic version;
- English academic version with equivalent claims;
- claim-to-source table and unresolved evidence placeholders;
- notes separating sourced facts, synthesis, and proposed work.

## Gotchas

- Multiple citations after a sentence do not prove that any one source supports the whole sentence.
- A method paper can support how its method works, but not a field-wide absence claim without broader search evidence.
- Research motivation is not a promised result. Keep proposed effects falsifiable and future-facing.
- Translation can silently strengthen claims; compare the two versions against the same claim IDs.
