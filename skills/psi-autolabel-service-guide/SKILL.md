---
name: psi-autolabel-service-guide
description: Explain, trace, review, or modify the PSI Autolabel FastAPI service, including API endpoints, isolated-node process topology, sync and async execution, PostgreSQL TaskStore workers, prompt reload, Redis rate limiting, metrics, WebUI proxying, production/test workflow clients, and multi-node recovery. Use in the psi-autolabelling repository when asked about API nodes, service startup, request flow, job lifecycle, runtime ownership, documented operational behavior, or cross-node safety. Do not use for standalone model-label quality or benchmark analysis that does not involve service behavior.
---

# PSI Autolabel Service Guide

Build an evidence-backed model of the current checkout before answering or editing. The bundled references describe commit `6930cd3` and are a navigation aid, not authority over newer code.

## Route the investigation

- Read [references/api-surface.md](references/api-surface.md) for endpoint discovery, router prefixes, service responsibilities, and WebUI route groups.
- Read [references/runtime-architecture.md](references/runtime-architecture.md) for startup topology, sync proxying, async workers, TaskStore state, rate limiting, shutdown, observability, and operational invariants.
- Read [references/feishu-operations.md](references/feishu-operations.md) when reconciling production/test usage, workflow side effects, polling and lease behavior, pressure limits, incidents, or services documented outside the current checkout.
- For request or response field details, inspect the relevant `schemas.py`, route handler, focused test, and the matching file under `docs/`.
- For feature-specific behavior, query the matching concise file under `AGENTS/MEMORY/` rather than loading every memory file.

## Verify before concluding

1. Read the repository `AGENTS.md` and current configuration.
2. Confirm route prefixes and decorators in `src/psi_autolabel/**/routes.py`, then confirm registration order in `server/api_app.py`, `server/app.py`, or `server/webui_app.py`.
3. Trace one concrete path as `entry -> validation/dispatch -> pipeline or queue -> state/I/O -> result/error`.
4. Establish the evidence tier: current code and focused tests; live OpenAPI/health/metrics; current Feishu revision; repository docs; historical examples. Do not let an older curl example override executable behavior.
5. When a Feishu page documents another deployment or repository, label it `documented external service` until its own code or live schema is verified.
6. Cite repository-relative `path:line` evidence. Mark inference and unresolved runtime state explicitly.

## Preserve these invariants

- Production is multi-node. Async coordination is PostgreSQL-backed; `task_dir` is compatibility configuration and is not the queue database.
- Liveness belongs to a per-process `instance_id`, not hostname alone. Never recover, evict, or clean work solely by hostname.
- External-worker async submission must stay light: validate cheap fields, persist an unowned `pending` job, and return `job_id`. Do not download URLs, decode videos, extract frames, or load large reference data before returning.
- Workers claim jobs atomically with PostgreSQL `FOR UPDATE SKIP LOCKED`. A claimed job can remain `pending` while waiting for Redis token quota and becomes `processing` only after quota admission.
- Status polling is lightweight by default. Fetch the full terminal payload only with `include_result=true`.
- For upstream lease renewal, use monotonically increasing `progress.updated_at`; do not parse display-oriented `stage` or renew merely because a job remains pending.
- Distinguish ordinary API calls from workflow calls that write artifacts beside the input. Set `save_output=false` when the caller owns result persistence and fetch the terminal result explicitly.
- Cancellation is cooperative across nodes. It does not forcibly terminate an in-flight LLM call or blocking native operation.
- In isolated layout, exact synchronous inference POST routes are registered before the local API routers and round-robin proxied to sync workers. The gateway handles async submit/status/control routes itself, then proxies unmatched paths to WebUI.
- Any recovery, cleanup, archival, or ownership change must be reviewed against a shared PostgreSQL store and simultaneous live instances.
- Bound total in-flight work across submissions. Submission concurrency alone does not prevent a queued backlog from saturating workers, upstream model bandwidth, CPU preprocessing, memory, or database connections.

## Report the system clearly

Lead with the smallest causal model, then provide endpoint groups, one representative flow, state ownership, failure semantics, and verification points. Separate startup-time construction from request-time work and synchronous inference from queued execution.

## Gotchas

- Router imports prove availability, not which handler wins; registration order matters because gateway proxy routes shadow the same synchronous paths.
- The worker builds the API application to reuse lifespan initialization and handler registration, but it does not serve HTTP.
- `BackgroundTasks` is the legacy in-process mode. Default node mode uses external workers and leaves queued tasks ownerless until claim.
- `pending` does not always mean unclaimed; a claimed job may intentionally remain pending during rate-limit wait.
- `include_result=true` changes the TaskStore read path and can load a large PostgreSQL result.
- A `pending` job with `progress.stage=waiting_for_rate_limit` is claimed work waiting for quota, not an idle queue item.
- Prompt reload failure is fatal for that job; workers do not run with unverified prompt state.
- Adjacent services can use different state vocabularies, persistence rules, and concurrency models; do not impose the core TaskStore contract on AutoSeg or FaceBlur solely because their docs use `/jobs`.
- README endpoint tables may lag decorators. Re-extract routes after changing any router.
