# Task state schema

Read this reference only when persisting or updating a multi-turn task.

## Location

Default to `<project>/.codex/task-coach/<task-slug>.json`. The file is project state, not Skill configuration.

## Top-level fields

```json
{
  "schema_version": 1,
  "revision": 1,
  "objective": "Observable final outcome",
  "acceptance_criteria": ["Evidence-based criterion"],
  "status": "active",
  "status_reason": null,
  "created_at": "UTC ISO-8601",
  "updated_at": "UTC ISO-8601",
  "steps": [],
  "feedback": []
}
```

- `status`: `active`, `completed`, or `blocked`.
- `status_reason`: required when the overall task is blocked.
- `revision`: increments on every successful mutation.
- `feedback`: append-only observations and learning reports.

## Step fields

```json
{
  "id": "M1",
  "title": "Short action-oriented title",
  "outcome": "Observable result",
  "verification": "Command, artifact, metric, or decision that proves the result",
  "depends_on": [],
  "status": "pending",
  "evidence": [],
  "status_reason": null,
  "created_at": "UTC ISO-8601",
  "updated_at": "UTC ISO-8601"
}
```

Rules enforced by the helper:

- IDs are unique.
- Dependencies must already exist.
- Only one step may be `in_progress`.
- A step cannot start until all dependencies are `completed`.
- Completing a step requires non-empty evidence.
- Blocking a step requires a reason.
- A completed step cannot be reopened; add a new corrective or superseding step.
- The overall task can be completed only after every step is completed.

## Feedback fields

```json
{
  "timestamp": "UTC ISO-8601",
  "step_id": "M1",
  "kind": "attempted_success",
  "message": "Observed output or user learning feedback"
}
```

Allowed kinds:

- `understood`
- `needs_explanation`
- `attempted_success`
- `attempted_failed`
- `blocker`
- `scope_change`
- `preference`

Feedback does not automatically complete or reopen a step. Interpret it, revise pending work if needed, then make an explicit transition with evidence.
