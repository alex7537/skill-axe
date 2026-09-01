---
name: decision-grilling
description: Relentlessly clarify and stress-test an underspecified plan, design, experiment, or consequential decision before planning or implementation. Use when the user says grill me, 拷打我, 追问我, 帮我把想法问清楚, wants hidden assumptions exposed, or has a fuzzy idea with unresolved trade-offs. Do not use for a concrete task that is already ready to execute; hand that to the relevant planning or implementation workflow.
---

# Decision Grilling

Turn a loose idea into explicit, defensible decisions without taking ownership of those decisions away from the user.

## Operating contract

- Model the discussion as a **design tree**: each settled decision may unlock dependent decisions.
- The **frontier** is every unresolved decision whose prerequisites are already settled. Ask the whole useful frontier in one round, then wait.
- Finding facts is the agent's job. Inspect the available environment or authoritative sources instead of asking the user for information that can be discovered safely.
- Making trade-offs is the user's job. Give a recommendation and rationale, but do not silently decide on the user's behalf.
- Treat “I don't know” as evidence. If discussion cannot resolve a question, identify the smallest prototype, research task, or experiment that could.
- Do not plan, edit files, launch work, or otherwise implement the result until the user confirms the shared understanding and separately requests the next action.

## Run the interview

Start by stating the root decision and the current scope in one or two sentences. Include any assumption needed to begin.

For each round:

1. Recompute the frontier from what is already settled.
2. Resolve discoverable facts before presenting questions when practical. If a fact remains unknown, name it as an unresolved prerequisite instead of converting it into a user preference.
3. Ask the frontier as numbered questions. Keep dependent questions for a later round.
4. For every question, provide a recommended answer, the main reason, and the most important trade-off.
5. Process the user's response as one of: decided, rejected, out of scope, unknown, or requires evidence. Then recompute the tree.

Use this compact format:

```text
❓ Q1 - <decision title>: <question and meaningful options>

➡️ Recommendation: <answer, reason, and main trade-off>
```

Keep a round coherent. Do not inflate a narrow decision into an exhaustive questionnaire, but do not drip independent frontier questions one at a time unless the user asks for that pace.

## Know when discussion is insufficient

A question is not grillable when its answer depends on seeing, measuring, or trying something rather than choosing a preference. Examples include interaction feel, model quality, runtime performance, and whether an uncertain integration works.

When this happens:

- state why discussion cannot settle it;
- define the smallest evidence-producing prototype, investigation, or experiment;
- mark the downstream branch as deferred;
- continue with independent frontier questions.

## Close the session

The interview is complete when the frontier is empty and every remaining unknown has an explicit evidence path or is consciously out of scope.

Summarize:

- decisions and their reasons;
- constraints and non-goals;
- deferred experiments or research;
- unresolved risks;
- the recommended next workflow.

Ask the user to confirm that this is the shared understanding. After confirmation, use `$adaptive-task-coach` when the result needs decomposition, sequencing, evidence tracking, or execution coaching.

## Gotchas

- Repeated agreement is not proof of alignment. Invite correction and surface the recommendation's strongest counterargument.
- A very large tree usually means the root scope should be split into separate grilling sessions.
- Do not keep rephrasing an evidence-dependent question. Route it to a prototype or experiment.
- Recommendations must not be presented as settled decisions before the user answers.
- A completed interview is context for future work, not authorization to perform that work.
