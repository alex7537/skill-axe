# Deep-analysis contract

## Evidence statuses

- `full-text-verified`: checked in the primary paper text.
- `official-supplement-verified`: checked in official appendix, supplement, or repository material.
- `abstract-only`: only title/abstract metadata was available.
- `secondary-only`: known only from a review, index, or third-party summary; exclude from strong synthesis.
- `unresolved`: sources conflict or the relevant detail could not be located.

## Comparison discipline

For a numerical result, preserve metric name/definition, direction, value, comparator, dataset/task, split, evaluation mode, seed or uncertainty reporting, and locator. Do not calculate a cross-paper improvement unless the conditions are genuinely aligned.

For a method claim, preserve the predicted object, conditioning information, architecture role, learning objective, inference procedure, and claimed causal mechanism. Distinguish a renamed familiar component from a genuinely new mechanism.

For a limitation, label the source as `authors`, `design-observed`, or `cross-paper-conflict`. State what evidence would resolve an analyst inference.

## Minimum completion gate

- Every strong conclusion traces to at least one primary-source locator.
- Every paper has a consistent core set of fields or an explicit missing-data reason.
- Results are not ranked across incompatible protocols.
- Contradictory findings preserve both sides and likely confounders.
- The comparison identifies what is established, merely reported, inferred, and unknown.
