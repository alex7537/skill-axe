# Capture criteria

## Create a new skill

Create a new skill when the workflow has a distinct trigger, stable responsibility, repeatable inputs/outputs, and enough verified procedure or tooling to improve a future task. Prefer a short verb-led name.

Examples:

- diagnosing TI-ONE SSH host-key changes;
- publishing oversized Docker images through a same-region relay;
- reproducing a remote attention-heatmap comparison pipeline.

## Update an existing skill

Update the closest skill when the new lesson is another failure mode, validation step, provider variant, or script improvement inside its existing responsibility. Add high-signal findings to `Gotchas`; avoid duplicate trigger descriptions.

## Do not create a skill

Skip capture for:

- a one-line fact or obvious command;
- a one-off output with no reusable method;
- an unresolved attempt without verified success criteria;
- information already captured accurately in an installed skill;
- workflows whose only reusable content would be secrets or machine-specific credentials.

## Minimum artifact

A captured skill should state:

1. when it triggers;
2. what evidence or inputs it needs;
3. the safe workflow and decision points;
4. known failure modes;
5. how success is verified;
6. which actions require explicit confirmation.
