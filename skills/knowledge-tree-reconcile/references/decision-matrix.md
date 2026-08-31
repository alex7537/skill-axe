# Knowledge routing decision matrix

Use this after global candidate search and after reading the closest existing nodes.

| Classification | Evidence test | Canonical action | Map/index action |
|---|---|---|---|
| `duplicate` | Same claim/procedure and no stronger evidence or new boundary | No content update; optionally record that it was checked | None |
| `extension` | Same responsibility, plus a new variant, gotcha, validation gate, or stronger evidence | Patch the existing skill or note | Update maturity/date only if materially changed |
| `contradiction` | New evidence conflicts with a stored claim | Add a dated superseding statement; preserve useful history and explain source authority | Flag resolved/remaining conflict when navigation needs it |
| `new-concept` | Durable mental model or relationship with no adequate note owner | Create/update one focused Obsidian note | Link from the nearest domain map |
| `new-workflow` | Distinct trigger, repeatable inputs/outputs, decisions, safety gates, and verification | Create one focused skill | Add a short capability entry, not the procedure |
| `transient` | Machine status, one-off output, raw log, unresolved attempt, or easily regenerated fact | Keep at the operational source or omit | None |

## Same-skill test

Update an existing skill when most answers are “yes”:

1. Would the same user request trigger both the old and new procedure?
2. Do they produce the same kind of outcome?
3. Does the new material fit as a variant, validation step, or Gotcha?
4. Would two skills cause ambiguous routing?

Create a new skill only when it has a distinct trigger and responsibility and can state its own evidence, decisions, safety boundary, and success checks.

## Same-note test

Update an existing note when the new material answers the same durable question or strengthens the same concept graph edge. Create a note only when no existing note can own it without becoming a mixed-topic dump.

## Dual-output rule

Sometimes both systems change, but they must not contain duplicate truth:

- skill: commands, sequence, branches, failure signatures, repair gates, verification;
- Obsidian: the compressed insight, why it matters, dated evidence, limits, and the skill/map link.

## Source authority for conflicts

Prefer, in order appropriate to the domain:

1. current executable state or primary source;
2. verified local experiment with provenance;
3. official documentation or repository at an identified revision/date;
4. reviewed internal documentation;
5. secondary summaries;
6. remembered or inferred claims.

State when this ordering is an inference rather than a domain rule.
