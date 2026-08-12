---
name: adaptive-task-coach
description: Break a complex, ambiguous, or multi-stage goal into an executable sequence, teach the user the reasoning needed for each step, track evidence and blockers, and revise pending work from progress or learning feedback. Use when the user asks to 拆分任务, 安排执行顺序, 制定可落地计划, 边做边学, 根据反馈实时更新计划, continue a long-running project, or recover a stalled task. Do not use for a single obvious action or a request that only needs a short factual answer.
---

# Adaptive Task Coach

Treat the interaction as an adaptive runbook: keep the objective stable, expose one manageable next action, verify its result, and update later steps from evidence.

## Operating contract

- Separate the **delivery track** (what must be produced) from the **learning track** (what the user must understand or practice).
- Distinguish advice from authorization. A request to explain or plan does not authorize edits, training runs, deployments, messages, or other mutations.
- Keep completed steps and their evidence immutable. If they become invalid, append a superseding step and explain why.
- Keep at most one step `in_progress`.
- Mark a step `completed` only with its stated verification evidence.
- Replan pending work whenever new evidence changes risk, prerequisites, effort, or the best route.
- Do not manufacture estimates, results, file paths, metrics, or completion evidence.

## Workflow

### 1. Frame the task

Extract or infer:

- objective and concrete deliverable;
- acceptance criteria;
- scope and explicit non-goals;
- constraints: time, compute, data, budget, permissions, safety;
- known evidence and unresolved assumptions;
- the user's current knowledge and preferred learning depth.

Ask only for information that materially changes the first safe action. Otherwise state the assumption and proceed.

For a composite request, summarize the frame in five compact fields:

```text
Goal:
Done when:
Constraints:
Known / unknown:
Current phase:
```

### 2. Build two linked tracks

Create 3–8 milestones on the delivery track. Each milestone must produce an observable outcome, not merely an activity.

For every milestone define:

- `id` and title;
- outcome;
- prerequisites;
- smallest executable actions;
- verification command, artifact, observation, or decision;
- risk and rollback/recovery note when relevant;
- status: `pending`, `in_progress`, `completed`, or `blocked`.

Add a learning item only where understanding changes the user's ability to choose, execute, diagnose, or repeat the work. Give it:

- the concept in plain language;
- why it matters now;
- one check question or hands-on exercise;
- the evidence that shows understanding.

Link each learning item to the delivery milestone it enables. Do not turn the plan into a generic course.

### 3. Choose the next executable step

Prefer a step that:

1. removes the largest uncertainty or prerequisite;
2. is safe and reversible;
3. produces evidence quickly;
4. fits the available resource budget.

Present the immediate action with:

```text
Why now:
Do:
Expected result:
How to verify:
If it differs:
```

Give exact commands only after resolving repository, environment, input, and output paths. Never present destructive commands with unresolved variables or broad targets.

### 4. Process feedback

Classify each user report before changing the plan:

| Feedback | Meaning | Response |
| --- | --- | --- |
| `understood` | Concept is clear | Compress later explanation and continue |
| `needs_explanation` | Mental model is missing | Re-explain with a smaller example, then check understanding |
| `attempted_success` | Action produced expected evidence | Record evidence, complete the step, unlock dependents |
| `attempted_failed` | Action ran but result differs | Preserve output, diagnose, add a recovery step |
| `blocker` | External prerequisite prevents progress | Work around it if in scope; otherwise mark blocked and state the exact unblock condition |
| `scope_change` | Goal or acceptance criteria changed | Show the impact and obtain direction if materially different |
| `preference` | User changes style, pace, or tradeoff | Adjust pending steps without rewriting evidence |

When feedback is ambiguous, separate observed facts from the user's interpretation. Base replanning on the facts first.

### 5. Replan transparently

After meaningful feedback, report only:

- what changed;
- why it changed;
- which completed evidence remains valid;
- the new immediate next action.

Do not recreate the whole plan on every turn. Expand the next 1–3 steps and keep later work milestone-level until prerequisites are known.

### 6. Close or hand off

Close only when every acceptance criterion has evidence. Provide:

- delivered artifacts or results;
- verification summary;
- concepts the user can now repeat independently;
- remaining risks or optional follow-ups;
- the exact resume point if work is not finished.

## Persistent state

For a multi-turn task, offer or create a project-local state file at:

```text
<project>/.codex/task-coach/<task-slug>.json
```

Do not store task state inside this Skill directory. Do not create a state file for a short answer or when the user requested planning only and did not authorize workspace changes.

Use `scripts/task_state.py` for deterministic state transitions. Read `references/state-schema.md` before creating or modifying persistent state.

Typical sequence:

```bash
python3 <skill-dir>/scripts/task_state.py init --path <state.json> --objective "<goal>" --acceptance "<criterion>"
python3 <skill-dir>/scripts/task_state.py add-step --path <state.json> --id M1 --title "<title>" --outcome "<observable result>" --verification "<evidence>"
python3 <skill-dir>/scripts/task_state.py transition --path <state.json> --id M1 --status in_progress
python3 <skill-dir>/scripts/task_state.py feedback --path <state.json> --id M1 --kind attempted_success --message "<observed result>"
python3 <skill-dir>/scripts/task_state.py transition --path <state.json> --id M1 --status completed --evidence "<verification evidence>"
python3 <skill-dir>/scripts/task_state.py set-task-status --path <state.json> --status completed
python3 <skill-dir>/scripts/task_state.py show --path <state.json>
```

## Gotchas

- “Make a plan” is not permission to execute the plan.
- Epochs, time estimates, and confidence labels are not acceptance evidence.
- A failed attempt is new evidence, not a reason to erase history or restart blindly.
- Do not let explanations indefinitely block delivery; teach only the concept needed for the next decision.
- Do not declare the whole task blocked while a safe diagnostic, smaller experiment, or independent milestone remains.
- When domain-specific expertise is needed, compose with the relevant Skill; this Skill owns decomposition and feedback state, not domain truth.
