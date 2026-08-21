# A2D model-only contract

## Purpose

Separate model quality or compatibility from pipeline drift. The baseline manifest is the evidence boundary: it freezes every input to the experiment except the model bundle and designated result namespace.

## Required identities

Freeze:

- workspace repository, branch, commit, and dirty-state decision;
- protected implementation/config files with SHA-256;
- environment type/name plus an immutable lock, image, or package-list identity when available;
- exact argument vector containing one `{MODEL_BUNDLE}` placeholder;
- allowed write roots and output naming rule;
- simulator/server identity and endpoint;
- observation/action schemas, normalization, preprocessing, temporal offsets, action rate, chunk/horizon, maximum actions, seeds, and success profile;
- expected result schema and smallest smoke check.

The baseline should be reviewed before testing. Do not automatically update hashes after detecting drift; that would redefine the experiment after the fact.

## Protected versus writable surfaces

Protected surfaces include code, configs, dataset, assets, environment, simulator/server configuration, evaluation criteria, and existing evidence. Writable surfaces should be limited to a new versioned output root and unavoidable runtime locations already declared in the baseline.

If the baseline command inherently writes into the protected workspace, the contract is not model-only safe. Redesign the output location under separate authorization before comparing models.

## Command rendering

Store the command as a JSON argv list, not a shell string:

```json
[
  "python",
  "path/to/evaluator.py",
  "--bundle",
  "{MODEL_BUNDLE}",
  "--output",
  "{OUTPUT_ROOT}",
  "--execute-horizon",
  "4"
]
```

Only placeholders listed by the manifest may be replaced. Preserve every other token exactly. Avoid `shell=True`, `eval`, or reconstructing a quoted shell command.

## Drift handling

Classify differences:

- **pre-existing recorded drift:** visible before the run; comparison may proceed only if the approved baseline explicitly includes it;
- **unexpected pre-run drift:** stop before execution;
- **expected output mutation:** inside an allowed result root;
- **unexpected post-run mutation:** disqualify the run and preserve evidence for diagnosis.

Do not restore files automatically. Restoration can destroy unrelated work and does not prove the executed run used the restored content.

## Compatibility result

Before performance comparison, establish:

- bundle loads under the frozen environment;
- observation keys/shapes and preprocessing revision match;
- action keys/dimensions/units/ranges and decoding match;
- normalizer and model config are resolved from the intended source;
- one smoke episode completes and emits schema-valid fields.

Failure at this stage is a model/baseline compatibility result. It is not a policy-quality score.

## Authorization boundary

Model selection and execution do not authorize:

- environment or package mutations;
- source/config/data edits;
- simulator/server restart or termination;
- deletion or overwrite of prior results;
- changing thresholds, horizons, seeds, or retry rules;
- exporting or publishing checkpoints.

Obtain separate explicit authorization and exit model-only mode for any such action.
