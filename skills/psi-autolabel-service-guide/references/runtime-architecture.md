# Runtime Architecture Snapshot

Snapshot: repository commit `6930cd3` (`main`). Verify configuration and code in the current checkout.

## Smallest causal model

PSI Autolabel is a FastAPI control plane around multimodal video pipelines. The default server command starts a supervisor. The supervisor separates long synchronous HTTP inference, lightweight API/queue control, WebUI/file work, and queued inference into different processes. PostgreSQL coordinates jobs and process liveness across nodes; Redis coordinates model token quotas; OpenAI-compatible clients call configured model backends; PostgreSQL-backed trackers and Prometheus expose observability.

## Startup and process topology

Console entrypoints are declared in `pyproject.toml`:

- `psi-autolabel-server` -> combined entry and default node supervisor.
- `psi-autolabel-api` -> API-only FastAPI process.
- `psi-autolabel-webui` -> WebUI-only FastAPI process.
- `psi-autolabel-worker` -> async queue worker without an HTTP listener.

The current default is `server.process_model=node` and `server.node_layout=isolated` in `config/config.yaml`.

```text
client
  |
  v
external :8080  http-gateway (api_app)
  |-- exact synchronous POST inference --> sync-worker:0 :8280
  |                                      -> sync-worker:1 :8281 (round robin)
  |-- async submit/status/cancel -------> gateway router + PostgreSQL TaskStore
  |-- health/rate-limit/metrics --------> gateway services
  `-- unmatched UI/static paths --------> webui :8180

PostgreSQL tasks queue <---- async worker processes ----> model/video pipelines
Redis quota pools      <---- every model-calling process
```

Ports are derived from the external port when explicit internal ports are absent. The supervisor creates children with a shared `node_id`, a distinct role/index, `external_worker` job mode, and a force-single marker so children do not recursively become supervisors. It restarts unexpectedly exited children and propagates shutdown signals to process groups.

### Why the split exists

- Sync requests can hold HTTP connections for minutes and consume large native/ML memory; dedicated sync workers isolate that load and allow round-robin concurrency.
- Async submits must return quickly; the gateway only validates and persists work.
- Queue workers scale independently from HTTP. Each worker process runs up to `worker_job_concurrency` jobs and can trim allocator memory after jobs.
- WebUI browsing, media serving, prompt management, and result-file operations do not compete in the same event loop as synchronous model inference.

## Application construction

`server/api_app.py:create_app` performs startup-time wiring:

1. Load dotenv, YAML config, environment, and PostgreSQL pool registry.
2. Build `PromptRepository`, domain configs, and workflow config.
3. Generate a unique process `instance_id`; record role, index, node ID, and job execution mode in shared app state.
4. In lifespan startup, configure the asyncio thread pool, in-flight tracker, Redis `DistributedRateLimiter`, stats trackers, PostgreSQL `TaskStore`, heartbeat and maintenance loops, inference clients, pipelines, and prompt sync where this role owns it.
5. Router factories close over this shared state and register async job handlers as a side effect.
6. On shutdown, stop accepting work, drain tracked work within configured limits, stop trackers/heartbeats, close sessions, limiter, TaskStore, executors, and PostgreSQL pools.

The worker calls the same `create_app` and enters its lifespan so it gets identical configs, clients, pipelines, TaskStore, and handler registry. It never starts Uvicorn.

## Synchronous request path

Representative AutoClip V2 path:

```text
POST /api/autoclip/v2
  -> gateway exact proxy route
  -> round-robin sync-worker API process
  -> Pydantic request parsing + task/config validation
  -> resolve/download video during execution
  -> sample frames under resolution/model image budget
  -> add task prompt, optional multimodal context/reference frames
  -> Redis token reservation
  -> OpenAI-compatible multimodal request
  -> parse and normalize structured clip boundaries
  -> finalize actual token usage, write metrics/stats
  -> JSON or stream response relayed by gateway
```

The gateway preserves ordinary end-to-end response semantics, strips hop-by-hop headers, streams upstream bytes, and returns `503` when the selected internal upstream is unavailable. Streaming retries are allowed only before the first emitted event; retrying after output begins would duplicate or corrupt the stream.

## Queued async request path

Representative `/api/autoclip/v2/jobs` path:

```text
submit on gateway
  -> Pydantic + cheap validation only
  -> TaskStore.create_task(job_type, request, assign_owner=false)
  -> PostgreSQL tasks row: pending, owner=NULL
  -> return {job_id, pending}

async worker loop
  -> claim_pending_task(registered_job_types)
  -> SELECT oldest matching pending row FOR UPDATE SKIP LOCKED
  -> atomically set owner_node_id + owner_instance_id
  -> strictly reload/verify prompts
  -> dispatch handler by job_type
  -> heavy URL/video/reference I/O in per-job blocking executor
  -> wait for Redis token quota while still pending when applicable
  -> set processing after admission
  -> persist stage/substage progress
  -> set completed(result), failed(error), or observe cancelled
  -> optional gc.collect + malloc_trim
```

The registered job types currently cover AutoClip V1/V2, AutoCaption V1/V2/fixed-segment/label-key-range, AutoTag V1, CheckVideoTaskMatch and its workflow, CaptionDiffTranslation, and AutolabelWorkflow.

Legacy `single`/in-process mode assigns the submitting process as owner and schedules a tracked FastAPI background task. Do not assume that path in the default node deployment.

## TaskStore state and ownership

`TaskStore` combines a bounded in-process cache with PostgreSQL persistence.

Primary tables:

- `tasks`: hot queue and recent task records.
- `archived_tasks`: terminal history, range-partitioned by archive time when schema capability permits.
- `instance_heartbeats`: process identity, node, role/index, last-seen time, worker concurrency, and schema capability.

State machine:

```text
pending (unowned queue)
  -> pending (claimed, possibly waiting for token quota)
  -> processing
  -> completed | failed | cancelled
```

Status polling uses a lightweight projection by default. `include_result=true` loads request/result JSON and should be delayed until terminal state. Terminal cache entries intentionally omit large request and result bodies.

The default maintenance policy archives old terminal rows from the hot table, later removes expired archive rows, and recovers unfinished work only when its owning `instance_id` heartbeat is stale. Recovery marks the abandoned task failed; it does not silently replay potentially non-idempotent work.

### Cross-node invariant

`node_id` can default to hostname, but it is not a liveness identity. Every process gets a random `instance_id`. A restarted process on the same host must be distinguishable from the dead process. Any change that uses hostname alone for recovery can corrupt live work in a shared multi-node deployment.

## Cancellation and shutdown

- Cancel endpoints atomically change non-terminal PostgreSQL rows to `cancelled` and clear result/progress.
- Same-process mode also signals the tracked asyncio task.
- Cross-node workers observe cancellation at cooperative checkpoints through the shared store.
- In-flight LLM calls, OpenCV, ffmpeg, or other blocking native work are not force-killed.
- Shutdown stops new work, waits up to configured drain deadlines, then cancels remaining asyncio tasks. Supervisor grace time must remain longer than child drain time.

## Prompt and configuration consistency

The current default prompt backend is PostgreSQL. Repository YAML prompt files seed an empty prompt DB but are not the normal live source afterward. Prompt synchronization has one configured owner, normally the isolated HTTP gateway. Middleware can lazily reload configs, and async workers perform strict prompt-state verification before every claimed job. A reload failure fails the job rather than running with stale or partially synchronized prompts.

Configuration has three layers worth checking:

- `config/config.yaml`: server topology, shared LLM configs, rate limits, stats, prompt sources, and domain defaults.
- `config/autolabel_workflow_config.yaml`: workflow composition and fallback behavior.
- Environment variables: deployment environment, credentials, database endpoints, local isolation ID, process role/index, and selected overrides.

Never include secret values in reports or skills.

## Model inference boundary

Most current pipelines use a shared OpenAI-compatible async client. A service resolves its named `llm_config`, estimates multimodal prompt/completion tokens, acquires a Redis quota lease, calls either Chat Completions or Responses according to config, parses structured JSON, records actual usage/cost/error metadata, and finalizes the lease.

Image budgets are constrained by both inference resolution and model-specific frame limits. Project multimodal context and reference images consume the same request image budget as current-video frames; required context is preserved first, reducing current-video sampling. Resolution transforms only downsample and do not upscale.

## Domain pipeline essence

- **AutoClip:** temporal segmentation. V2 samples visual evidence, asks for task-aligned boundaries, then normalizes structured clips; identity profile bypasses the model.
- **AutoCaption:** semantic hierarchy. It turns clip frames into summaries and step/Tier segments, uses sliding windows for long inputs, and normalizes left-closed/right-open boundaries.
- **AutoTag:** constrained classification. It samples a caller-specified interval and maps multiple tag keys to free or closed-set values.
- **CheckVideoTaskMatch:** whole-video validation. It judges whether visual evidence matches a selected task and can persist a workflow artifact.
- **CaptionDiffTranslation:** text repair. It translates only the changed semantic portion where possible.
- **AutolabelWorkflow:** orchestration. It composes clip detection, validation/fallback, per-clip captioning, optional tags, aggregation, and artifact output.

## Observability

- `/health/debug` identifies the responding role and process instance.
- `/metrics` exposes Prometheus HTTP and business counters; the gateway aggregates sync-worker metrics.
- Business stats track service-level counts, latency, errors, usage, cost, clips, and steps.
- Backend-LLM stats track request rate, in-flight work, TPM, cost, error events, and remaining quota.
- Job queue stats sample processing load, active worker capacity, unowned queue wait, and quota-wait duration from PostgreSQL.
- Progress is stage-level and persisted across nodes; high-frequency token/frame events must not be written as progress.

## High-value evidence files

- `config/config.yaml`: deployed default topology and operational limits.
- `pyproject.toml`: executable entrypoints.
- `src/psi_autolabel/server/app.py`: supervisor and combined legacy app.
- `src/psi_autolabel/server/api_app.py`: API process construction, lifespan, and route order.
- `src/psi_autolabel/server/proxy.py`: exact sync paths and WebUI catch-all.
- `src/psi_autolabel/server/worker.py`: worker polling, dispatch, prompt verification, cleanup, and drain.
- `src/psi_autolabel/common/server/async_jobs.py`: job-type registry.
- `src/psi_autolabel/common/server/task_store.py`: queue claim, state, heartbeat, recovery, archive, and cache.
- `src/psi_autolabel/common/inference/openai_client.py`: provider call, token reservation/finalization, retry, and metrics boundary.
- `tests/test_process_layout.py`, `tests/test_task_store.py`, `tests/test_job_status_lease.py`, `tests/test_graceful_shutdown.py`, `tests/test_rate_limit_routes.py`: focused contracts.

## Falsification checks

- Compare configured process model/layout with `/health/debug` on each reachable internal process.
- Submit a lightweight valid async request and verify the row transitions from ownerless pending to claimed/processing/terminal without fetching full result during polling.
- Stop one worker and verify only tasks owned by its stale `instance_id` are recovered; live instances on the same node must be untouched.
- Check route order when a sync request unexpectedly executes on the gateway.
- Compare Prometheus gateway totals with sync-worker aggregation when metrics appear duplicated or missing.
