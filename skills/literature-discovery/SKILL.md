---
name: literature-discovery
description: Search, verify, screen, and cluster recent academic literature into a defensible core-paper set. Use for 近3–5年核心文献检索、系统检索式设计、15篇核心论文筛选、文献去重与纳排, or when a thesis needs a traceable search log. Do not use for job/thesis-opening searches, deep full-text analysis, or prose drafting.
---

# Literature Discovery

Build a reproducible candidate set before interpreting the field. The deliverable is a verified search-and-screening record, not a list produced from memory or one ranking page.

## Evidence boundary

- Search current scholarly indexes and primary publisher, proceedings, repository, or official project pages. Time-sensitive metadata and citation counts require live verification.
- Verify every included paper's title, authors, year, venue/status, and DOI or arXiv identifier against a primary record. A search-result snippet is discovery evidence only.
- Never invent a paper, DOI, venue, citation count, access link, or inclusion reason. Mark unavailable fields `unknown`.
- Treat citation counts as dated, source-specific signals. Do not merge counts from different indexes or equate popularity with relevance or quality.
- Prefer peer-reviewed versions when available; retain a preprint only when it is the relevant/latest public version and label its status.

## Search and screen

1. Freeze the research question, date window, adjacent terminology, inclusion/exclusion criteria, languages, and desired corpus size. Use the current calendar date to calculate “recent 3–5 years”; state exact years.
2. Read [references/search-contract.md](references/search-contract.md), then search at least two complementary scholarly sources plus backward/forward chaining from strong seeds when access permits.
3. Record every query, source, filters, date, and result count. Export or preserve stable identifiers before deduplication.
4. Deduplicate by DOI first, then normalized title plus first author/year. Keep version relationships rather than counting a preprint and its published article twice.
5. Screen title/abstract, then accessible full text for finalists. Record one explicit inclusion or exclusion reason per candidate.
6. Select the core set by topical fit, methodological coverage, evidence quality, and field influence. Do not pad to 15; report a shortfall when fewer papers satisfy the criteria.
7. Cluster included papers by method/problem/evidence role. Allow clearly labeled foundational exceptions outside the date window only when they are necessary to interpret the recent field.

Use [assets/literature-candidate-matrix.csv](assets/literature-candidate-matrix.csv) as the handoff. The downstream `$paper-deep-analysis` skill should receive the verified identifiers, URLs, screening decisions, and search log rather than re-discovering papers from prose.

## Prompting and worked example

- Read [references/prompt-patterns.md](references/prompt-patterns.md) when the user wants a reusable prompt, a staged search prompt, or help turning a topic into an auditable request.
- Read [references/example-2d-materials-mechanocoupling.md](references/example-2d-materials-mechanocoupling.md) for a complete 2021–2026 worked example. Its reusable candidate table is [assets/example-2d-mechanocoupling-candidates.csv](assets/example-2d-mechanocoupling-candidates.csv).
- Read [references/example-flow-matching-thesis-pipeline.md](references/example-flow-matching-thesis-pipeline.md) for a repository-grounded five-skill prompt chain and preliminary thesis-background analysis for `alex7537/flow-matching-test-a2d-v2`.
- Example metadata and citation signals are dated snapshots. Re-run live verification instead of copying their current-status fields into a later search.

## Deliverable

- exact scope and year window;
- query log and source coverage;
- candidate matrix with verified metadata and version status;
- selected core set, short relevance note, cluster, and selection rationale;
- exclusions and unresolved access/metadata issues;
- limits such as database coverage, language bias, inaccessible full text, and the date/source of citation signals.

## Gotchas

- “Highly cited” is meaningless without the index and retrieval date.
- A recent review is useful for terminology and chaining, but it cannot replace checking the primary studies used for thesis claims.
- Search absence is not evidence that no paper exists. Preserve the searched sources and queries so the boundary is auditable.
- Topic relevance and reference value are separate: a paper can be close in wording but weak in evidence, or methodologically important but outside the exact application.
