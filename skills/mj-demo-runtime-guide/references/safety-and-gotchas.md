# Safety and Gotchas

Read this reference before changing external API calls or any path that can affect robot motion.

## Transport and availability

- The snapshot's model calls do not set an HTTP timeout. A stalled backend can block a controller thread indefinitely.
- The production wrappers do not consistently call `raise_for_status`, catch connection errors, validate JSON, or verify the full response schema.
- A configured loopback address can have no listener or tunnel. Check live readiness before diagnosing application logic.
- README tunnel examples, checked configuration, and active runtime forwarding may disagree; runtime evidence wins.
- No authentication header is present in the model wrappers. Do not expose the service to an untrusted network as a workaround.

## Retry behavior

- Brain parsing retries until a valid answer with no fixed attempt cap or total deadline in the snapshot.
- The retry loop increases temperature without an explicit upper bound.
- VLM placement can call the external model repeatedly while checking proposed positions against local YOLO boxes; the snapshot caps this path but can still generate high latency and cost.
- Do not add retries around physical action. Retry only the idempotent inference/validation portion, then fail safely.

A safe retry policy needs:

- per-request connect/read timeout;
- total operation deadline;
- bounded attempts and bounded temperature;
- exponential or deliberate backoff where appropriate;
- cancellation/stop integration;
- explicit fallback: pause, operator review, local rule, or abort;
- metrics that distinguish transport, protocol, parse, and semantic rejection.

## Parsing and validation

- `choices[0].message.content` is accessed directly. Missing fields or non-JSON responses can raise exceptions.
- Coordinate extraction is regex-based and does not by itself prove the point is inside the image or safe workspace.
- Brain parsing uses strict Chinese output patterns; a semantically correct but differently formatted response can trigger retries.
- Validate action membership against locally computed legal actions even after parsing.
- Treat model text, model names, URLs, and error bodies as untrusted data in logs and UI.

## Motion boundary

- VLM coordinates can feed 2D-to-3D conversion and arm motion. HTTP 200 is never a motion authorization.
- The human-review setting can automatically accept a proposed point. Review-disabled mode needs equivalent deterministic bounds and safe failure behavior.
- Preserve local checks for image bounds, depth validity, workspace limits, collision risk, coordinate frames, and left/right arm selection.
- Use a no-motion mode to observe the request, response, parsed action/point, and target pose before enabling hardware.
- Stop when model/config identity, endpoint ownership, coordinate frame, calibration, or emergency-stop readiness is unknown.

## Local compute misconceptions

- External Brain/VLM calls do not make the whole system remote. YOLO, SAM, FoundationPose, ASR, game state, geometry, and control remain local in the snapshot.
- A loopback endpoint does not make the large model local; it may terminate an SSH tunnel.
- `psi_majiangDeploy` and emotion Flask/WebSocket endpoints handle display commands rather than inference.
- A model checkpoint path in a comment or experimental script does not prove the active backend uses that checkpoint.

## Change checklist

Before merging an API-related change:

- trace all callers and concurrent cached-result consumers;
- confirm model and endpoint fields reach the serialized payload;
- add focused tests for timeout, connection error, non-200 response, invalid JSON, missing `choices`, malformed answer, out-of-bounds point, and retry exhaustion;
- confirm deterministic local branches still bypass the external model when intended;
- confirm logs do not expose configured hosts, tokens, personal paths, raw private images, or full provider error bodies;
- run static/no-motion verification before any controlled hardware test.

