# Holdout and incremental-data protocol

## Exposure ledger

Count these as access to a correlated group:

- training or gradient computation;
- smoke and overfit tests;
- checkpoint or threshold selection;
- metric reporting;
- RGB/GT/prediction visualization;
- failure categorization;
- using the sample to change preprocessing, labels, architecture, or evaluation rules.

The ledger records group ID, access reason, time, dataset role at access, and evidence/report reference. Do not include credentials or personal information.

## Holdout seal

Record manifest hash, frozen configuration hashes, state (`sealed` or `consumed`), actions that count as opening, authorization, and final report. Manifest validation may read identifiers and hashes but not underlying RGB/masks.

## Incremental data

Classify each incoming group:

- historical repaired group: restore its original role;
- truly new group: eligible for new allocation after label audit;
- exposed new group: diagnostic or train, never sealed holdout;
- hard overlap with old evaluation role: preserve the old role or block;
- soft same-scene/domain overlap: disclose and downgrade final claims if independence matters.

Check proposed new train against old val, old diagnostic, old holdout, and new val using all available IDs. A “no overlap detected” result is scoped to the available metadata, not proof of physical independence.

## Evaluation naming

- `val`: chooses checkpoint/threshold/configuration;
- `diagnostic`: supports analysis and controlled regression comparison;
- `holdout`: untouched final evaluation;
- avoid the word `test` once data has influenced any decision.
