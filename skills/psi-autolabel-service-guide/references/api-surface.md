# API Surface Snapshot

Snapshot: repository commit `6930cd3` (`main`). Always verify against the current checkout.

## Router assembly

The API application registers routers in `src/psi_autolabel/server/api_app.py`. The combined legacy application registers the same domain routers plus WebUI in `src/psi_autolabel/server/app.py`. The isolated WebUI process registers only the WebUI router in `src/psi_autolabel/server/webui_app.py`.

In the default isolated layout, the gateway first registers exact synchronous POST proxy routes, then the domain routers, then a catch-all WebUI proxy. Therefore the exact sync paths below execute on sync workers; async submit, status, cancellation, config, health, rate-limit, and metrics endpoints execute on the gateway.

## Platform endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness response for the current process. |
| GET | `/health/debug` | Node, instance, role, process index, PID, and runtime diagnostics. |
| GET | `/metrics` | Prometheus HTTP and business metrics; gateway can aggregate sync-worker metrics. |
| GET | `/docs` | Swagger UI. |
| GET | `/redoc` | ReDoc UI. |
| GET | `/openapi.json` | FastAPI-generated OpenAPI document. |

## Model-facing services

All video endpoints accept `video_path`; supported implementations resolve local paths or HTTP(S) URLs during execution. Video base64 and multipart job inputs are not part of the current contract.

### AutoClip — prefix `/api/autoclip`

Splits a multi-task video into clip boundaries. V1 uses the legacy windowed/vLLM path. V2 extracts sampled frames and calls an OpenAI-compatible multimodal backend. `clip_profile=identity` returns one `[0, nframes)` clip without LLM inference; `task` uses prompt-driven segmentation.

| Method | Suffix | Purpose |
|---|---|---|
| GET | `/config-options` | Task IDs, LLM configs, and clip profiles. |
| POST | `/v1`, `/v2` | Synchronous or streaming inference. |
| POST | `/v1/jobs`, `/v2/jobs` | Queue an async job. |
| GET | `/v1/jobs/{job_id}`, `/v2/jobs/{job_id}` | Poll status; use `include_result=true` only for the terminal result. |
| POST | `/v1/jobs/{job_id}/cancel`, `/v2/jobs/{job_id}/cancel` | Cooperative cancellation. |

Source: `src/psi_autolabel/autoclip/server/routes.py`; schemas: `src/psi_autolabel/autoclip/server/schemas.py`.

### AutoCaption — prefix `/api/autocaption`

Converts video clips into structured bilingual captions. V1 supports several two-stage/two-tier/three-tier profiles. V2 is summary-only. Long inputs use windowing; frame ranges are left-closed/right-open. Fixed-segment mode preserves caller-supplied boundaries. Label-key-range/key-frame mode emits labeled ranges plus key frames.

| Method | Suffix | Purpose |
|---|---|---|
| GET | `/config-options` | Available prompts, profiles, and LLM configs. |
| POST | `/v1`, `/v2` | Synchronous or streaming caption inference. |
| POST | `/v1/jobs`, `/v2/jobs` | Queue caption jobs. |
| GET | `/v1/jobs/{job_id}`, `/v2/jobs/{job_id}` | Poll caption jobs. |
| POST | `/v1/jobs/{job_id}/cancel`, `/v2/jobs/{job_id}/cancel` | Cancel caption jobs. |
| POST | `/fixed_segment/v1` | Caption caller-defined Tier2 segments without changing boundaries. |
| POST | `/fixed_segment/v1/jobs` | Queue fixed-segment captioning. |
| GET | `/fixed_segment/v1/jobs/{job_id}` | Poll fixed-segment work. |
| POST | `/fixed_segment/v1/jobs/{job_id}/cancel` | Cancel fixed-segment work. |
| POST | `/LabelKeyRangeKeyFrame/v1` | Produce label ranges and key frames. |
| POST | `/LabelKeyRangeKeyFrame/v1/jobs` | Queue label-range/key-frame work. |
| GET | `/LabelKeyRangeKeyFrame/v1/jobs/{job_id}` | Poll the job. |
| POST | `/LabelKeyRangeKeyFrame/v1/jobs/{job_id}/cancel` | Cancel the job. |

Source: `src/psi_autolabel/autocaption/server/routes.py`; schemas: `src/psi_autolabel/autocaption/server/schemas.py`.

### AutoTag — prefix `/api/autotag`

Uniformly samples a requested frame range and asks a multimodal model for one or more `key:value` attributes. Optional `allowed_values` makes each value a closed-set choice; invalid model output gets one correction attempt.

| Method | Suffix | Purpose |
|---|---|---|
| GET | `/config-options` | LLM and frame-budget options. |
| POST | `/v1` | Synchronous tag inference. |
| POST | `/v1/jobs` | Queue tag inference. |
| GET | `/v1/jobs/{job_id}` | Poll the job. |
| POST | `/v1/jobs/{job_id}/cancel` | Cancel the job. |

Source: `src/psi_autolabel/autotag/routes.py`; schemas: `src/psi_autolabel/autotag/schemas.py`.

### CheckVideoTaskMatch — prefix `/api/check_video_task_match`

Samples the full video and returns a structured judgment of whether it matches the selected task prompt. Workflow variants also persist `check_video_task_match.json`.

| Method | Suffix | Purpose |
|---|---|---|
| GET | `/config-options` | Task IDs, service configs, and LLM configs. |
| POST | `` | Synchronous match check. |
| POST | `/jobs` | Queue match check. |
| GET | `/jobs/{job_id}` | Poll match check. |
| POST | `/jobs/{job_id}/cancel` | Cancel match check. |
| POST | `/workflow` | Synchronous check plus workflow artifact write. |
| POST | `/workflow/jobs` | Queue workflow check. |
| GET | `/workflow/jobs/{job_id}` | Poll workflow check. |
| POST | `/workflow/jobs/{job_id}/cancel` | Cancel workflow check. |

Source: `src/psi_autolabel/check_video_task_match/routes.py`; schemas: `src/psi_autolabel/check_video_task_match/schemas.py`.

### CaptionDiffTranslation — prefix `/api/caption_diff_translation`

Updates the English caption from a changed Chinese caption while preserving unchanged phrasing where possible. It is text-only even though it accepts compatibility fields shared with WebUI forms.

| Method | Suffix | Purpose |
|---|---|---|
| GET | `/config-options` | Available LLM configs. |
| POST | `` | Synchronous diff-aware translation. |
| POST | `/jobs` | Queue translation. |
| GET | `/jobs/{job_id}` | Poll translation. |
| POST | `/jobs/{job_id}/cancel` | Cancel translation. |

Source: `src/psi_autolabel/caption_diff_translation/routes.py`.

### AutolabelWorkflow — prefix `/api/autolabel_workflow`

Orchestrates AutoClip, AutoCaption, and configured optional AutoTag steps, applies post-AutoClip validation/fallback rules, and writes workflow-shaped results.

| Method | Suffix | Purpose |
|---|---|---|
| POST | `` | Run the workflow synchronously. |
| POST | `/jobs` | Queue the workflow. |
| GET | `/jobs/{job_id}` | Poll workflow status/result. |
| POST | `/jobs/{job_id}/cancel` | Cancel workflow. |

Source: `src/psi_autolabel/autolabel_workflow/routes.py`; schemas: `src/psi_autolabel/autolabel_workflow/schemas.py`; composition config: `config/autolabel_workflow_config.yaml`.

## Rate-limit inspection — prefix `/api/rate-limit`

| Method | Suffix | Purpose |
|---|---|---|
| GET | `/remaining-tpm` | Remaining-token snapshots for selected LLM configs. |
| POST | `/remaining-tpm/service-configs` | Resolve service config names to quota pools and return remaining TPM. |

These routes expose display-safe pool identifiers rather than complete internal quota keys. Source: `src/psi_autolabel/common/server/rate_limit_routes.py`.

## WebUI routes

The WebUI router has no prefix. In isolated layout the gateway catch-all proxies these paths to the internal WebUI process.

### Pages and browsing

- `GET /`, `GET /viewer/{sample_id}`
- `GET /api/browse-dirs`
- `POST /api/samples`, `POST /api/samples/tree-node`
- `GET /api/sample/{sample_id}`, `GET /api/sample-init/{sample_id}`
- `GET /api/frames/{sample_id}/{clip_id}`, `GET /api/frame-image/{sample_id}`
- `GET /api/video/{sample_id}/{clip_id}`, `GET /api/step-video/{sample_id}`, `GET /api/original-video/{sample_id}`
- `GET /api/windows/{sample_id}`, `GET /api/window-video/{sample_id}/{window_id}`, `GET /api/window-frames/{sample_id}/{window_id}`
- `GET /api/statistics/{sample_id}`, `POST /api/compare`, `GET /api/export/{sample_id}`

### Online request and result persistence

- `GET /api/autolabel-workflow/config-options`
- `GET /api/online-request/config-options`, `GET /api/online-request/task-options`
- `GET /api/server/tasks/{task_id}`, `POST /api/server/process`, `POST /api/server/tasks`, `GET /api/server/sample`, `POST /api/server/submit`
- `POST /api/save-result`, `POST /api/save-fixed-segment-caption-result`, `POST /api/save-label-key-range-key-frame-result`
- `POST /api/save-autocaption-result`, `POST /api/delete-autocaption-result`

### Prompt management

- `GET /api/prompts`, `GET /api/prompts/meta`, `GET /api/prompts/list`
- `GET|PUT|PATCH|DELETE /api/prompts/{task_id}`
- `POST /api/prompts/{task_id}/patch`, `POST /api/prompts/{task_id}/delete`
- `PUT /api/prompts` for bulk replacement
- `POST /api/prompts/project/{project_id}/refresh`
- `POST /api/prompts/{task_id}/copy-to-prod`
- `POST /api/task-id-compare`
- `GET /api/prompt-env-compare/config`
- `GET /api/prompt-env-compare/{target_env}`
- `GET /api/prompt-env-compare/{target_env}/task/{task_id}`
- `POST /api/prompt-env-compare/{target_env}/task/{task_id}/copy`

Prompt mutations have environment-specific guards. Inspect the handler before assuming a write is allowed.

### Statistics

- `GET /api/stats`, `GET /api/stats/config-options`, `GET /api/stats/timeseries`
- `GET /api/stats/backend-llm/options`, `GET /api/stats/backend-llm/timeseries`
- `GET /api/stats/backend-llm/errors/summary`, `GET /api/stats/backend-llm/errors/events`
- `GET /api/stats/job/options`, `GET /api/stats/job/timeseries`

Source for all WebUI groups: `src/psi_autolabel/webui/routes.py`.

## Route extraction check

When the snapshot may be stale, search all decorators and inspect multiline arguments:

```bash
rg -n -A4 '^\s*@(app|router)\.(get|post|put|patch|delete|api_route)\(' src/psi_autolabel -g '*.py'
```

Also search `include_router`, `register_sync_proxy_routes`, `register_webui_proxy_route`, and `setup_metrics`; decorators alone do not reveal prefixes or handler precedence.
