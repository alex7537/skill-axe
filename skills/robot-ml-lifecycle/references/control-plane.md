# Robot ML loop control plane

## Readiness levels

| Level | Allowed behavior | Required controls |
|---|---|---|
| `L0` | Documented design only | objective, non-goals, terminal condition |
| `L1` | Inspect, plan, report, and update local state | durable ledger, constraints, human handoff |
| `L2` | Execute explicitly approved bounded actions | L1 plus isolated attempt, independent verifier, attempt cap, write gates |
| `L3` | Recurring/unattended allowlisted actions | L2 plus proven gates, budgets, kill switch, observability, incident downgrade |

Default to L1. An agent may automatically downgrade after an incident, budget trigger, missing verifier, or kill switch. It must never promote itself.

The ledger CLI enforces this boundary: increasing a level requires `level --human-approved --evidence ...`. The flag means an actual human decision was received; it is not permission for an agent to manufacture approval.

## One run

Execute a recurring run in this order:

1. Acquire the single control node's local Runner lock and read project instructions, constraints, runner state, and lifecycle ledger.
2. Run `check`; exit immediately on pause, budget, stagnation, or attempt cap.
3. Produce compact `context`; do not inject the whole history.
4. Select the first unresolved actionable phase.
5. At L1, report only. At L2/L3, confirm the action is allowlisted and gated.
6. Perform one bounded attempt in an isolated environment when mutation is involved.
7. Run an independent verifier or deterministic gate.
8. Return structured executor and verifier results to the Runner; only the Runner may append attempt, phase evidence, a bound human decision, and outcome.
9. Decide: continue, start a new cycle, wait for human, complete, or retire.

An empty/no-action run is a runner-log `noop`; exit cheaply instead of spawning more work. Never add polling noops to lifecycle attempts.

## Circuit breaker

Stop and escalate when any configured trigger fires:

- loop is paused;
- per-phase attempt cap reached;
- consecutive failures reached the no-progress threshold;
- normalized error signature repeated enough times;
- cycle cap reached before starting another cycle;
- token or monetary cost budget reached;
- required verifier cannot run;
- human gate is missing or rejected;
- project constraints forbid the action.

Escalation is a valid terminal outcome for the current run. Preserve the full ledger and give the human a compact context block containing the objective, active cycle/phase, attempts, repeated failure, consumed budget, and exact requested decision.

## Scheduling and cadence

Keep cadence explicit: `manual`, `event:<event>`, or a documented interval. Prefer event-driven triggers for training completion, failed tasks, or new checkpoints. Do not schedule a heavy full evaluation when a cheap status check can determine that nothing changed.

Recurring execution must define:

- fire condition and no-op condition;
- off-hours behavior;
- maximum concurrent runs;
- one control node and Runner-only ownership for ledger writes; a local lock prevents overlap only on that node;
- notification rule (only actionable human decisions by default);
- pause and retirement procedure.

## Budgets

Use the resource that actually constrains the loop:

- token budget for agent reasoning;
- monetary budget for cloud tasks;
- GPU-hour/task-count cap for training/evaluation;
- storage cap for checkpoints and bundles;
- attempt and cycle caps for convergence risk.

The bundled schema-2 ledger mechanically enforces attempt, cycle, token, and monetary caps when recorded. Add GPU/storage observations and payload-bound decisions together in schema 3 so breaker decisions can consume them without ad-hoc runner-only state.

## State hygiene

Keep the full ledger append-preserving, but feed only the active cycle, next phase, recent attempts, latest relevant human decisions, budgets, and breaker decision into the next run. Reconcile remote task/checkpoint/release identifiers before acting on stale state.
