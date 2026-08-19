# MJ-Demo Runtime Architecture

Snapshot: commit `d498757`. Verify the current checkout before using this as evidence.

## System role

MJ-Demo is the robot-side control plane for a Mahjong demonstration. It owns sensor acquisition, local perception, game state, prompt construction, model-client calls, response parsing, optional human review, coordinate conversion, speech/emotion output, and physical actions.

It does not implement the Brain or VLM inference server. Those calls use an OpenAI-compatible HTTP contract whose backend can be local, tunneled, or remote.

## Startup shape

`control_panel.py` initializes the singleton configuration, constructs `ControlPanel`, creates `MJController`, and starts the controller loop in a background thread.

`MJController` constructs:

- the external-model client wrapper `VLM_API`;
- dual-arm and hand control;
- RealSense and top-camera interfaces;
- local CUDA YOLO;
- local microphone/ASR management;
- the Mahjong `Player`, which owns `GAME_AI_API`;
- speech, voice, emotion, and review state.

The repository also contains Flask/WebSocket components for speech, instruction reception, and emotion/video display. These are local support services, not model inference implementations.

## Ownership map

| Capability | Snapshot execution owner | Evidence to recheck |
|---|---|---|
| Camera acquisition and RGB/depth state | Robot-side process | `mj_controller.py`, camera modules |
| Mahjong tile detection | Local YOLO on CUDA | `MJController.__init__`, `yolo_choose_hand`, `get_all_objects` |
| Point-conditioned segmentation | Local SAM on CUDA | `realsense_image_foundationpose_module.py` |
| 6D pose estimation | Local FoundationPose on CUDA | `realsense_image_foundationpose_module.py`, `estimater.py` |
| Streaming speech recognition | Local Sherpa-ONNX | `audio_asr_module.py` |
| Mahjong action selection | External Brain API | `rule_player.py`, `game_ai_api.py` |
| Visual grounding for wall/place/handover | External VLM API | `vlm_api.py` |
| Prompt construction and response parsing | Robot-side Python | `game_ai_api.py`, `vlm_api.py` |
| Human review and fallback point selection | Robot-side UI/state | `mj_controller.py` |
| Pixel/depth to pose and physical motion | Robot-side controller | `mj_controller.py`, arm/hand modules |
| Emotion/video display distribution | Local Flask/WebSocket processes | `emo/`, `psi_majiangDeploy/` |

## Representative draw flow

1. The camera thread updates color, depth, and top-camera frames.
2. The robot asks the VLM for a wall-grasp point.
3. Local YOLO identifies the new tile and current hand state.
4. The code handles deterministic cases locally: missing-suit discard and win checks can bypass the Brain API.
5. For an ordinary hand, three `Player.make_decision` calls may run concurrently for discard, concealed-kong, and promote-kong decisions.
6. Each decision constructs a textual game-state prompt and calls the Brain endpoint synchronously.
7. The VLM may concurrently propose a placement point; local YOLO boxes filter unsafe/occupied placements.
8. Parsed actions and coordinates update cached state.
9. The review gate either accepts the proposed point or waits for an operator-supplied replacement.
10. Local depth/geometry converts the point to a target pose, then the arm/hand controller executes the selected motion.

This flow makes the repository an orchestrator: remote inference supplies decisions or 2D proposals, but local code owns state transitions and physical consequences.

## Decision branches that do not require the external Brain

Do not assume every turn calls the Brain API. The snapshot has local rule branches for cases such as:

- rejecting an invalid claim because the hand lacks enough matching tiles;
- immediately discarding a tile from the selected missing suit;
- detecting a winning hand;
- returning pass when concealed/promote-kong preconditions are absent.

Trace the current branch before attributing latency or behavior to the remote model.

## Local-versus-remote determination

A URL using a loopback host means only that the client connects to the local network interface. The compute can still be remote through SSH local forwarding.

Verify separately:

1. configured URL and path;
2. listener on the configured local port;
3. SSH/autossh `-L` forwarding for that port;
4. model-server process when the listener is local;
5. `/v1/models` or another read-only provider check when supported;
6. request logs or model-server metrics that identify the actual backend.

Report physical compute ownership as unknown unless this evidence resolves it.

## Live-readiness checklist

- Configuration parses and contains non-empty model identifiers when required by the backend.
- Every configured local dependency has a listener or documented forwarding path.
- The Brain and VLM endpoints return the expected OpenAI-compatible response structure.
- The TTS and display support services are distinguished from model inference.
- Camera, local CUDA models, and robot controllers initialize independently of API availability.
- A no-motion path validates parsing, coordinates, and state transitions before physical execution.
