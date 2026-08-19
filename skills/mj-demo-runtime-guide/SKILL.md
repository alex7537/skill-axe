---
name: mj-demo-runtime-guide
description: "Explain, trace, review, or modify the MJ-Demo Mahjong robot runtime, including camera and speech inputs, local YOLO/SAM/FoundationPose inference, external Brain/VLM API calls, game-state orchestration, human review, and robot action execution. Use only in the mj-demo repository for API ownership, local-versus-remote compute, request flow, runtime dependencies, or safety analysis. Do not use for the PSI Autolabel FastAPI service."
---

# MJ-Demo Runtime Guide

Build an evidence-backed model of the current checkout before answering or editing. The bundled references describe commit `d498757`; they are navigation aids, not authority over newer code.

## Smallest causal model

MJ-Demo is a robot-side orchestrator and API client, not the model-serving backend:

`camera/audio -> local perception -> Mahjong state machine -> external Brain/VLM calls -> validation/review -> 2D-to-3D conversion -> robot action`

Do not describe all model compute as remote. The checked snapshot calls external OpenAI-compatible endpoints for Mahjong decisions and visual grounding, while YOLO, SAM, FoundationPose, Sherpa-ONNX ASR, state management, post-processing, and hardware control run locally.

## Route the investigation

- Read [references/runtime-architecture.md](references/runtime-architecture.md) for startup, component ownership, the representative draw/discard flow, and local-versus-external compute.
- Read [references/external-model-api.md](references/external-model-api.md) for configuration, request/response contracts, callers, parsing, and retry behavior.
- Read [references/safety-and-gotchas.md](references/safety-and-gotchas.md) before changing API calls, retry logic, review gates, coordinate handling, or robot-facing behavior.

## Verify before concluding

1. Read repository instructions and confirm the current Git commit and worktree state.
2. Inspect `config.py` and the current `brain` block in `config.yaml`; never expose configured hosts, credentials, robot addresses, serials, or personal paths.
3. Trace an actual call from `control_panel.py` or `mj_controller.py` through `rule_player.py`, `game_ai_api.py` or `vlm_api.py`, then into validation and robot action.
4. Recheck model construction in `mj_controller.py`, `realsense_image_foundationpose_module.py`, and `audio_asr_module.py` before deciding which compute is local.
5. Treat a loopback URL as an interface location, not proof that inference is local. Inspect listeners and SSH forwarding separately, reporting only sanitized topology.
6. Separate static wiring from live readiness. A configured URL does not prove a listener, tunnel, valid model name, or successful response.
7. Cite repository-relative `path:line` evidence and label runtime inference or unknown service ownership explicitly.

## Preserve these invariants

- Brain and VLM responses are untrusted inputs. Validate protocol shape, semantic output, coordinate bounds, and downstream safety before robot motion.
- Keep the distinction between model selection, endpoint selection, local port forwarding, and physical compute ownership.
- A local perception result and an external VLM result may be combined; identify which result is authoritative at each call site.
- Human-review configuration is part of the motion safety boundary, not merely a UI preference.
- Do not broaden retries without a total deadline, attempt cap, cancellation path, and a safe failure outcome.
- Never test robot-facing changes by enabling physical motion solely because the API returned HTTP 200.

## Report contract

Lead with whether the repository is acting as server, client, or orchestrator. Then provide:

- one representative end-to-end call path;
- a local-versus-external responsibility table;
- the exact API contract and configuration source;
- live readiness evidence versus static code evidence;
- failure, timeout, retry, parsing, review, and robot-motion risks;
- the smallest verification or change that would resolve the user's question.

## Gotchas

- `psi-autolabel-service-guide` describes a different FastAPI service and must not be applied to this repository.
- `psi_majiangDeploy` Flask/WebSocket code distributes display or emotion commands; it is not the Brain/VLM inference backend.
- README tunnel examples and configuration ports can drift independently.
- Passing a `model_name` argument does not prove it reaches the payload; inspect the implementation.
- An OpenAI-compatible path does not identify the provider or machine that performs inference.
- Local code can still perform substantial GPU work even when the largest language/vision-language models are external.

