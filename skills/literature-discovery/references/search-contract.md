# Search contract

Use this contract when the request asks for a recent core set or a reproducible search.

## Freeze before searching

- Research question and concepts: population/system, intervention/mechanism, comparator, outcome/evidence.
- Exact publication window and whether online-first/preprints count.
- Included publication types, languages, domains, and study settings.
- Exclusions such as editorials, patents, theses, non-primary summaries, or papers without accessible evidence.
- Target size is a planning number, not an obligation to include weak papers.

## Query construction

Build concept blocks with synonyms, abbreviations, earlier names, and application terms. Record the literal query used by each source because syntax differs. Run a broad recall-oriented pass, inspect vocabulary, then a narrower precision pass. Use seed-paper references and citing papers to catch terminology drift.

## Source roles

- Scholarly index: candidate discovery and source-specific citation signal.
- Publisher/proceedings/repository record: canonical metadata and publication status.
- Full text or accepted manuscript: methods, results, limitations, and locator evidence.
- Review/survey: vocabulary and chaining; not a substitute for primary-study verification.

## Screening record

Every row needs one decision: `include`, `exclude`, `maybe`, or `unavailable`. Give a concrete reason such as wrong mechanism, outside window, non-primary evidence, insufficient methodological detail, duplicate version, or inaccessible full text. Do not use vague reasons such as “not useful.”

## Minimum completion gate

- Queries and retrieval dates are preserved.
- Included items have verified stable identifiers or an explicit metadata exception.
- Duplicate versions are linked.
- The selected set covers the important method/evidence clusters rather than only one author group or database ranking.
- Coverage and access limitations are stated.
