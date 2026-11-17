# Order Contract

Use an order only when it makes dependencies or permissions clearer. Keep it in memory unless the user asks for a saved artifact.

## Shape

```yaml
objective: concrete user-visible outcome
mode: read-only | local-change | external-mutation
selected_skills:
  - name: skill-name
    reason: unique responsibility
stages:
  - id: short-stage-id
    skill: skill-name
    depends_on: []
    deliverable: observable result
    evidence: how completion will be checked
    mutation: none | local | external
final_verification: integrated success check
```

## Rules

1. One owner per stage. If two Skills appear to own the same work, narrow their roles or select one.
2. Dependencies determine sequence. Stages without a dependency may be parallelizable, but that does not authorize subagents or concurrent execution.
3. Mutations need an explicit gate. A read-only inspection can inform a later change but cannot silently authorize it.
4. A stage is complete only when its stated evidence exists. Producing prose about an intended action is not evidence that the action occurred.
5. Integrate once at the end. Resolve conflicting specialist advice using the user's goal, project evidence, and authorization boundary.

## Design basis

This contract adapts the useful separation in Poteto's Noodle between state, scheduling, validation, execution, and integration, without importing its unattended loop or worktree/merge machinery. Source studied: `poteto/noodle` at commit `82d2921c52370f23f29086de81ccfb600939c037`.
