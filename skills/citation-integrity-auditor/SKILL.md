---
name: citation-integrity-auditor
description: Audit academic claims and citations for source identity, metadata, locator, support strength, retraction/correction risk, and claim-citation fit. Use for 引用真实性核验、禁止虚构引用、参考文献审计、claim-to-source检查, or before thesis text is treated as submission-ready. Do not use as a substitute for literature discovery or domain peer review.
---

# Citation Integrity Auditor

Fail closed on unverifiable citations. This skill checks whether a source exists and whether it supports the exact nearby claim; those are separate questions.

## Audit inputs

Use [assets/evidence-ledger.csv](assets/evidence-ledger.csv) for claim-level provenance. If the user supplies prose and a bibliography only, split the prose into consequential claims and map each citation before auditing. Preserve the original text and bibliography; do not silently replace references.

Run the local structural validator first:

```bash
python scripts/audit_ledger.py <evidence-ledger.csv>
```

Then perform the live/source checks in [references/audit-contract.md](references/audit-contract.md). The script cannot establish that a paper exists, is unretracted, or entails a claim.

## Integrity rules

- Verify title, author list, year, venue/status, and DOI/arXiv/URL against a primary scholarly record. Resolve DOI redirects when possible.
- Check corrections, expressions of concern, retractions, withdrawn preprints, and version changes when relevant. Record the date and authoritative status source.
- Open the primary full text and inspect the exact locator for every central, numerical, comparative, causal, novelty, or limitation claim.
- Classify support as `direct`, `partial`, `contextual`, `counterevidence`, or `inference`. A real paper with a mismatched claim is a failed citation.
- Distinguish the paper's result, the authors' interpretation, and the writer's synthesis. Multiple weak citations do not combine into stronger entailment.
- Never create a plausible-looking identifier, page locator, quotation, author, year, or bibliography entry. Use `unresolved` and name the missing evidence.

## Verdicts

- `PASS`: source identity and status are verified; the cited passage supports the bounded claim.
- `WARN`: the source is real but support is partial/contextual, metadata has a nonfatal ambiguity, or only a non-final version is available.
- `FAIL`: the source cannot be verified, is retracted/withdrawn without appropriate treatment, the locator is missing for a strong claim, or the source contradicts/does not support the claim.

Do not auto-upgrade `WARN` or `FAIL` by weakening or rewriting the user's scientific meaning without showing the change. Suggest one of: narrow the claim, add qualified wording, replace with a verified source, cite counterevidence, or mark the statement unsupported.

## Deliverable

- per-claim verdict, source identity/status, locator, and support classification;
- corrected metadata only when verified;
- unsupported, overbroad, contradicted, and uncited claims;
- suggested minimal remediation;
- audit date, sources consulted, and unresolved access limits.

## Gotchas

- DOI resolution verifies an identifier, not claim support.
- An abstract can support high-level scope but rarely detailed methods, numeric conditions, limitations, or causal language.
- A citation to a review is not automatically adequate for a claim about one primary experiment.
- Citation-manager metadata can be stale or merged incorrectly; verify important records at the source.
- “No citation needed” applies to common knowledge, not to field-wide absence, novelty, performance, or causal claims.
