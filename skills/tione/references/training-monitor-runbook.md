# TI-ONE Training Monitor and Feishu Alert Runbook

Use this reference when the task is to inspect, design, deploy, or hand off a monitor for TI-ONE task-style training jobs. It does not authorize deployment or message sending.

## Source and evidence boundary

This runbook was distilled from the Feishu page [部署 TI-ONE 训练任务飞书告警服务的操作手册](https://psi-robot.feishu.cn/wiki/BosAwkLfUi0ifYkdvIGcsvsSnaf), revision 15, read as the authenticated user with `docx:document:readonly` on 2026-08-26.

The page describes one working deployment pattern. Concrete machine names, usernames, creator lists, open IDs, resource groups, hosts, directories, and secrets are examples or local state, not portable defaults. Resolve them from the current authorized environment.

Current TI-ONE API behavior and this skill's `tione_api.py` output outrank the dated page. Live Feishu application permissions and availability also require read-only verification before any send test.

## Smallest causal model

```text
long-lived runtime
  -> periodically call DescribeTrainingTasks
  -> filter and normalize relevant tasks
  -> compare with previous state snapshot
  -> emit new/status/failure-change events
  -> route each event to an approved recipient
  -> send through a Feishu application bot
  -> persist new state and structured logs
```

This is a state-change monitor, not a training scheduler. It must not create, start, stop, restart, or delete training tasks.

## Event contract

Define events before writing code:

- a previously unseen task enters the monitored scope;
- task status changes;
- failure reason or failure message changes;
- optionally, a selected runtime field changes when the business explicitly needs it.

Normalize and compare at least:

- task ID and name;
- status;
- creator identity;
- resource group;
- creation/start/update/end time and runtime;
- message, failure reason, and failure message where present.

Do not alert on unstable fields, ordering changes, or redacted payload differences. Preserve a schema/version field in monitor state so upgrades can distinguish migration from real task events.

## First-run baseline

Default first-run behavior should baseline existing tasks without notifying them. Otherwise installing a monitor or expanding filters can flood recipients with historical work.

Required modes:

- `init-baseline`: read current matching tasks and write them as known state without sending;
- `once --dry-run`: compute and print prospective events without writing state or sending;
- normal loop: poll, diff, send approved events, then persist state;
- optional replay/test fixture: validate diff rules without live APIs.

Changing creator, name, resource-group, or status filters requires reviewing whether a new baseline is needed.

## Read-only audit mode

Before deployment, use only read operations:

1. List or describe matching training tasks.
2. Confirm whether list output includes creator identity; describe candidates when needed.
3. Inspect the proposed long-lived Notebook/development machine, runtime, persistent mounts, and write target.
4. Verify Python availability and network reachability without creating files.
5. Verify the Feishu application identity, required send scope, and intended recipients without sending a probe message.
6. Produce a redacted configuration plan and predicted dry-run event set.

Read-only audit must not generate a presigned Notebook URL unless the user requests it, install secrets, create directories, initialize state, start a process, or send a message.

## Deployment layout

Use an approved persistent directory, conceptually:

```text
<persistent-root>/tione-training-monitor/
  monitor.py
  config.env
  secrets.env
  secrets.env.example
  state/
    state.json
    monitor.lock
  logs/
    monitor.log
  backups/
  start.sh
  stop.sh
  status.sh
  run_once.sh
```

Keep non-sensitive filters and timing in `config.env`. Keep Tencent Cloud credentials and Feishu application secrets only in `secrets.env` or an approved secret store. Restrict the local secret file to the service account and never print its contents.

## Concurrency and persistence

- Use a single-instance lock so two monitor loops cannot race on state or duplicate notifications.
- Write state atomically: temporary file, flush/fsync where appropriate, then replace.
- Persist state only after the corresponding notification outcome is known and the chosen retry policy is applied.
- Use bounded HTTP timeouts and bounded retries with jitter.
- Log structured JSON lines with timestamps, poll duration, task count, event count, send result, and redacted error category.
- Do not log secrets, access tokens, raw authorization headers, presigned URLs, or complete unredacted provider responses.

Decide duplicate semantics explicitly. At-least-once delivery can repeat messages after a crash; at-most-once delivery can lose an alert. Record the chosen event ID and deduplication strategy.

## Filtering and routing

Supported filters should be explicit and independently optional:

- creator allowlist;
- task-name substring or pattern;
- resource-group allowlist;
- status allowlist;
- optional start/update time boundary.

Recipient routing can map creator to a Feishu `open_id`, with an approved default recipient or an explicit drop/error policy when no mapping exists.

Never publish raw recipient identifiers in shared documentation. Verify that the Feishu application's availability scope includes each recipient before a test send. A send-scope grant alone does not guarantee the bot is available to that user.

## Deployment gates

Treat these as separate authorization checkpoints:

1. **Read-only discovery:** task filters, target runtime, persistent path, application identity, and recipients.
2. **File deployment:** exact directory and file list, no real secrets yet.
3. **Secret installation:** source, destination, file permissions, and non-echoing method.
4. **Baseline write:** expected matching task count and no-send guarantee.
5. **Test notification:** exact recipient and exact sanitized test content.
6. **Service start:** process model, poll interval, PID/lock/state/log paths, and restart behavior.

Do not combine these into one broad approval.

## Verification sequence

1. Syntax-check the monitor and shell scripts.
2. Run deterministic state-diff tests from fixtures.
3. Run a one-shot live read-only dry run.
4. Initialize baseline and verify state permissions/content without exposing secrets.
5. Send one approved test message per routing branch.
6. Start the loop and verify PID, lock, poll log, and task count.
7. Simulate a state transition with a fixture or approved test task rather than mutating production work.
8. Restart the monitor and confirm deduplication.
9. Document manual restart/recovery after the development machine restarts.

## Reliability boundary

A TI-ONE development machine can be long-lived but may not provide `systemd`. A background `nohup` loop can stop after machine restart and requires manual or platform-level recovery.

For stronger availability, prefer an approved VM, container service, scheduler, or process supervisor with health checks and restart policy. The monitoring location must not share a failure domain with the only resource it monitors when high availability matters.

## Common failures

| Symptom | Likely layer | Check |
|---|---|---|
| Bot unavailable to user | Feishu application availability | Recipient is in the app's released availability scope |
| Missing availability-management scope | Feishu admin authorization | Do not expand availability through trial writes; obtain explicit admin approval |
| Invalid app secret | Secret provisioning | Secret source, app identity, file permissions, newline/quoting |
| No automatic recovery after machine restart | Runtime/process model | Documented restart command or migrate to supervised runtime |
| Historical task alert flood | State/baseline | Reinitialize baseline after widening filters |
| Duplicate alerts | Lock/dedup/state ordering | Single process, stable event ID, atomic state update, crash point |
| Missing alert | Filter/routing/API pagination | Page traversal, creator fallback, time filters, send failure logs |

## Handoff checklist

- Target runtime is approved, long-lived, and not a sleeping personal computer.
- Persistent deployment path, owner, backup, logs, and restart procedure are documented.
- Filters and normalized task schema are explicit.
- Baseline behavior prevents historical floods.
- Locking, atomic state, retry, and deduplication semantics are tested.
- Secrets are outside Git/docs/chat and readable only by the service account.
- Feishu application scope and recipient availability are verified.
- Dry run, route-specific test messages, status command, and restart recovery are verified.
- The monitor is explicitly read-only toward TI-ONE training tasks.

