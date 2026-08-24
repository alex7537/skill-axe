# Feishu Operations and Documentation Boundary

Use this reference when a task depends on the PSI Autolabelling Wiki rather than only the current repository. It summarizes a read-only review of the [Psi-Autolabelling Wiki](https://psi-robot.feishu.cn/wiki/QMrOwR8CDiEjZ6knAG0crGbAnsc). Concrete hosts, credentials, personal paths, model aliases, task IDs, and capacity values are intentionally omitted; resolve them from the current authorized source.

## Evidence scope

The reviewed Wiki tree contained 40 accessible Docx pages and no traversal failures. High-signal pages actually read were:

| Page | Revision | Use in this skill |
|---|---:|---|
| Psi-Autolabelling | 53 | Root taxonomy and repository/service scope |
| AutoLabel 在线服务 | 27 | Operational document index |
| Autolabel-prod/test 服务使用方法 | 17 | Environment and sync API examples |
| Autolabelling For Workflow Pipeline | 610 | Async lifecycle, result retrieval, progress, and lease guidance |
| Autolabel服务压测记录 | 316 | In-flight, CPU, memory, latency, and provider limits |
| Autolabel服务问题复盘 | 101 | Saturation incident and corrective actions |
| AutoLabel TODO | 387 | Known gaps and planned work |
| AutoClip V2 设计架构 | 3 | V1/V2 tradeoffs and long-video limits |
| AutoSeg 使用方法 | 131 | Adjacent async GPU workflow contract |
| CheckVideoTaskMatch服务使用方法 | 150 | API-versus-workflow persistence contract |
| AutoFaceBlur服务-视频人脸模糊 | 92 | Adjacent service with a different job model |

This is not a claim that every example is current. Re-read the exact page and verify code/live schema before acting.

## Authority order

Resolve contradictions in this order:

1. current route/schema/config implementation and focused tests;
2. live OpenAPI, health, metrics, and a read-only job/status observation;
3. latest relevant Feishu page revision;
4. repository README/docs;
5. old curl snippets, experiment logs, or personal examples.

Feishu is particularly valuable for operational intent, deployment history, incident context, and caller expectations. It does not prove which handler is registered in the current checkout.

## Canonical async client flow

For core TaskStore-backed services, prefer:

```text
submit lightweight request
  -> receive job_id + pending
  -> poll lightweight status without full result
  -> observe pending/processing progress
  -> on completed, fetch once with include_result=true
  -> on failed, record error and stop
```

Default polling intentionally avoids loading large request/result JSON. Use `include_result=true` only when the caller needs the terminal payload.

### Status meaning

- `pending`: unclaimed, or claimed but waiting for a quota lease.
- `processing`: admitted and executing business logic.
- `completed`: terminal success; lightweight polling can still return `result=null`.
- `failed`: terminal failure with an error; progress is cleared.
- HTTP 404 `Job not found` is not a job status.

Cancellation exists on supported core routes but remains cooperative. Verify the route and current handler; do not infer cancellation support from a generic `/jobs` shape.

## Progress and lease renewal

Business progress can include:

- `stage`: display label, possibly suffixed with `[current/total]`;
- `updated_at`: last persisted business-progress timestamp;
- `current`, `total`, and `unit`: structured completion count;
- `detail`: service-specific context.

If an upstream system renews a timeout/lease only when work advances:

1. require status `pending` or `processing`;
2. renew only when `progress.updated_at` exists and increases;
3. do not renew when it is absent or unchanged;
4. stop renewal at `completed` or `failed`;
5. do not parse `stage` for liveness and do not use `current/total` as the renewal clock.

Quota-wait progress may omit `updated_at`, so merely remaining in `pending` is not evidence of progress.

## API versus workflow persistence

Do not treat `/api/<service>` and `/api/<service>/workflow` as interchangeable.

- Ordinary API calls commonly return a result without writing beside the source video.
- Workflow calls can deliberately write a named JSON or media artifact beside the input.
- For Autolabel workflow, `save_output=false` lets the caller avoid a colocated result file and retrieve the terminal payload with `include_result=true`.
- CheckVideoTaskMatch ordinary async calls avoid the workflow artifact; the workflow variant writes a match JSON using a temporary directory plus atomic replace.
- AutoSeg and FaceBlur workflows are documented to write outputs near the input according to their own configuration and naming rules.

Before submission, state who owns persistence, whether the input mount is writable, whether output already exists, and whether replay is idempotent.

## Capacity and overload lessons

The pressure records and incident review show multiple independent bottlenecks:

- external model bandwidth or token quota;
- worker backlog and total in-flight requests;
- CPU-bound video decode/downsampling;
- memory pressure from high-resolution inputs;
- database connection consumption;
- long terminal results and excessive result polling.

Increasing request concurrency can raise latency without improving throughput. High-resolution video preprocessing can saturate CPU and memory before model quota is exhausted.

Operationally:

- control total in-flight work, not only new submission rate;
- wait for existing work to drain before submitting more;
- monitor provider errors, quota wait, queue wait, worker capacity, CPU, memory, and database connections together;
- use bounded admission and priority pools when workloads have different urgency;
- do not rely on a service restart as routine backlog cancellation.

The documented incident showed that pausing new submissions did not reduce upstream load because already queued work continued running. Recovery required stopping existing work and increasing provider capacity; the durable fix was in-flight control and monitoring.

## Service-family boundaries

### Verified in the current service guide snapshot

The current code-derived references cover AutoClip, AutoCaption, AutoTag, CheckVideoTaskMatch, CaptionDiffTranslation, AutolabelWorkflow, rate-limit inspection, WebUI, and the shared TaskStore runtime.

### Documented adjacent services

The Wiki also documents AutoSeg, AutoFaceBlur, and AutoAction. Treat these as separate deployments or repositories until verified:

- AutoSeg reads an episode directory, selects a segmentation preset, can write JSON atomically, and optionally renders visualization video.
- AutoFaceBlur preloads a GPU model, supports workflow and lower-level server APIs, and documents serialized service execution plus request-internal batch concurrency.
- AutoAction has a page in the tree, but the targeted read returned no substantive body; do not invent its contract.

Adjacent services can use different status names. For example, a FaceBlur page documents `running`, while the shared TaskStore contract uses `processing`. Preserve each service's actual schema.

## Model and pipeline lessons

- AutoClip V1 uses many overlapping window calls and aggregation; V2 uses global sampled frames and usually a single multimodal call.
- V2 improves engineering simplicity and cost visibility but can truncate long videos at its frame cap and lacks automatic divide-and-merge in the reviewed design.
- AutoCaption model experiments indicate that an untrained open model may meet a current requirement, but every requirement revision needs fresh quality evaluation before changing providers.
- AutoSeg experiment notes distinguish human hands from robot hands as separate semantic classes and recommend running AutoClip before segmentation when irrelevant frames should be excluded.

These are design and experiment observations, not universal production defaults.

## Benchmark boundary

The Wiki contains separate benchmark and price-comparison pages. Do not merge their numbers into the service runtime summary unless the user asks for model-quality or cost analysis.

When benchmark work is requested, preserve:

- dataset/project and sample selection;
- ground-truth definition and annotation review;
- AutoClip versus AutoCaption metric schema;
- model/config version;
- inference resolution and frame budget;
- quality, latency, token usage, and cost as separate axes;
- partial/WIP status and known confounders.

The TODO page marks a formal cross-model benchmark as WIP/P0, so isolated experiment examples must not be presented as a settled model ranking.

## Documentation gaps

The TODO page explicitly calls for documenting each service's purpose and request/response fields. Therefore:

- assume coverage is incomplete;
- re-extract routes and schemas from code;
- distinguish current, WIP, deprecated, and historical examples;
- report pages with empty bodies or infrastructure-only content instead of padding them into a conclusion.

