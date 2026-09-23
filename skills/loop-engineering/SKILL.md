---
name: loop-engineering
description: Design, run, or audit a bounded AI/agent experiment loop that proposes, executes, evaluates, and selects successive improvements under KPI, token, GPU, cost, safety, and human-approval constraints. Use when the user asks for Loop Engineering, agentic optimization, iterative experiment search, Pareto trade-offs, or an AI loop that keeps trying variants. Do not use for one-off implementation or for unattended high-risk operations without explicit approval.
---

# Loop Engineering

Treat Loop Engineering as **bounded heuristic search**, not a promise of global optimization. Its output is a reproducible set of evaluated candidates and a justified next experiment.

## Frame the loop

Before an executable loop, state the smallest decision contract that makes a candidate comparable:

- the hypothesis or direction to explore;
- immutable baseline and identities (code, data/split, evaluator, seed policy, checkpoint rule);
- primary KPI, critical guardrail KPIs, and their minimum thresholds;
- resources to minimize or cap: agent tokens, GPU-hours, cloud cost, wall time, human interventions;
- permitted variables and variables that must remain fixed;
- maximum attempts/cycles plus stop, pause, and escalation conditions.

Do not accept “make it better” as an experiment objective. Convert it into a measurable objective and constraints. If a user has not chosen the relative priority of competing outcomes, preserve the non-dominated alternatives rather than inventing scalar weights.

## One bounded cycle

1. Load only verified current state: prior candidate records, evidence, budgets, and outstanding human decisions.
2. Propose the smallest high-information next experiment. Change one principal causal factor unless a deliberate factorial design is required.
3. Preflight the frozen identities, permission boundary, budget, and failure breaker.
4. Execute only authorized actions; capture immutable artifacts and resource consumption.
5. Verify independently where material decisions depend on the result. A training job exit or a loss curve alone is not a quality verdict.
6. Classify the result: update the Pareto frontier, retry an invalid evaluation, create a new experiment cycle from the earliest invalidated assumption, promote, stop, or escalate to a human.

Read [references/pareto-and-decision-contract.md](references/pareto-and-decision-contract.md) before defining a multi-objective scorecard, Pareto frontier, or experiment selection rule.

## Pareto rule

Candidate A dominates B only if A is at least as good on every frozen objective/constraint and strictly better on one, after validity checks. Keep all valid non-dominated candidates in the evaluated set.

Do not claim that heuristic search “guarantees Pareto optimality.” It only preserves the frontier among candidates actually tested under a comparable contract.

## Routing

- Use `$robot-ml-lifecycle` for robot-ML source→data→train→evaluate→release provenance, phase gates, ledger, and circuit breakers.
- Use `$plan-training-run` for fair step/LR/epoch budgets.
- Use `$robot-benchmark-loop` for reproducible simulator or real-robot evaluation contracts.
- Use `$a2d-grasp-evaluation` for A2D rollout monitoring and grasp-funnel diagnosis.
- Use `$decision-grilling` before the loop when the objective, constraints, or trade-offs are materially ambiguous.

This Skill selects and governs the next experiment; the domain Skill owns the actual execution and scientific interpretation.

## Autonomy and safety

- Begin at report/plan level unless the user explicitly authorizes a bounded execution action.
- Never let an executor change its own KPI threshold, budget, verifier, or approval gate.
- Stop on repeated equivalent failures, exhausted budget, unavailable verifier, or a missing/rejected human gate. Preserve evidence and ask for the exact next decision.
- Keep exploration proportional: prefer a cheap diagnostic before a costly training run when it can eliminate the same uncertainty.

## Deliverable

Report the decision contract, candidate table/frontier, evidence validity, resources consumed, the next proposed experiment, and the precise reason for promotion, retry, stop, or escalation.
