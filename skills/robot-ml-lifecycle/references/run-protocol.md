# Runner-driven protocol

## Data-flow boundary

Use this topology for recurring operation:

```text
scheduler/event
    -> Runner (the only lifecycle-ledger writer)
       -> breaker + compact context
       -> isolated executor
       -> independent verifier
       -> validated append to lifecycle ledger
       -> run log / escalation inbox
```

Prompts and wrappers are cooperation mechanisms, not security boundaries. Enforce the important invariants through ownership and data flow:

- An executor returns `executor-result.schema.json`; it never calls the ledger CLI.
- A verifier receives immutable executor output/artifacts and returns `verifier-result.schema.json`; it never edits the executor result or ledger.
- The Runner validates both results and is the sole process allowed to append attempts, phase transitions, resource observations, or consumed decisions.
- A polling `noop` belongs to runner state and the run log, never to lifecycle `attempts`.
- An external evaluation or data package may provide evidence, but it cannot assert that a lifecycle phase passed or that a human approved an action.

## L1 runner supplied by this Skill

`scripts/run_once.py` is deliberately smaller than the eventual L2/L3 Runner. It:

1. takes a non-blocking local lock;
2. calls `check --json` and `context --window`;
3. returns compact context when ledger state changed;
4. records unchanged polls as run-log noops;
5. applies cadence backoff and pauses its own runner state after repeated empty rounds;
6. renders an actionable escalation inbox entry;
7. invokes no agent/executor and never writes the lifecycle ledger.

This makes L1 safe to adopt before schema 3 and before an executor exists.

Example:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/robot-ml-lifecycle/scripts/run_once.py" \
  --ledger .codex/robot-ml-lifecycle.json
```

Exit codes are `0` for ready/noop/complete, `2` for an actionable escalation or runner pause, and `3` for runner/configuration errors.

## Single-control-node rule

The initial system permits exactly one control node to own runner state and lifecycle-ledger writes. `flock`, PID files, hostnames, or stale timeouts do not create mutual exclusion between independent ledger copies, and network-filesystem lock semantics are not a portable safety boundary.

The L1 Runner stores its originating hostname in runner state and refuses execution on another node. Its lock defaults to the control node's local temporary directory, not a network mount; it prevents overlap only on that control node.

## Manual CLI rule

Interactive/manual ledger changes and a recurring Runner must not operate concurrently. Before a human or interactive Codex session uses `record`, `attempt`, `decision`, `new-cycle`, `pause`, `resume`, or `level`:

1. stop or disable the scheduler;
2. ensure no Runner process owns the local lock;
3. make the bounded manual change;
4. inspect `show`, `check`, and the diff;
5. restart scheduling only after reconciliation.

At L1, `run_once.py` never writes the ledger, but keeping this rule now avoids a protocol change when Runner-owned writes arrive later.

## Noop backoff

Runner state contains `consecutive_noops` and `backoff_level`. A ledger state change resets both. Every configured noop threshold increases the suggested cadence multiplier. After two complete backoff rounds and another unchanged threshold, the Runner pauses itself and creates an inbox item. This protects against a broken event trigger or an infinite empty polling loop without consuming experiment attempts.

## Deferred schema 3 work

Do not represent these features as ad-hoc runner-only fields. Introduce them together in one tested ledger migration:

- resource observations visible to budget/breaker decisions;
- payload-bound human decisions with subject, payload hash, operation, target, validity, and consumed state.

Until then, L1 remains read-only and L2/L3 execution remains disabled by this Runner.
