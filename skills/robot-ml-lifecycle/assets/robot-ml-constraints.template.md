# Robot ML Loop Constraints

## Autonomy

- Current level: L1
- Do not self-promote autonomy.
- Downgrade to L1 after an incident, missing verifier, or budget trigger.

## External writes

- Require explicit approval before Git push, cloud task mutation, holdout opening, registry/model publication, or deletion.
- Bind approval to an exact payload, path, repository, checkpoint, or destination.

## Protected resources

- Never edit or publish credentials, secrets, private keys, signed URLs, or runtime auth files.
- Add project-specific protected paths, datasets, branches, registries, and cloud resources here.

## Verification

- At L2/L3, the maker cannot be the sole checker.
- Require frozen acceptance criteria, deterministic tests/gates, and evidence.

## Limits and kill switch

- Max attempts per phase: 3
- Max consecutive failures: 3
- Max cycles: 10
- Token budget: unset
- Monetary budget: unset
- Pause flag: false
- On trigger: stop, preserve state, and escalate with compact context.
