# External Brain and VLM API Contract

Snapshot: commit `d498757`. Re-read the current implementation and configuration before changing or invoking it.

## Configuration path

`config.py` loads `config.yaml` into a singleton `Config`. The `brain` section provides:

- `position_model_name` and `position_api_url` for VLM visual grounding;
- `brain_model_name` and `brain_api_url` for Mahjong decisions.

Do not copy configured hosts into reports or skills. Keep endpoint location, model identity, and backend ownership as separate fields.

## Transport

The snapshot uses synchronous `requests.post`, not an OpenAI SDK. Both model clients expect an OpenAI-compatible Chat Completions endpoint:

```text
POST http://<model-api-host>:<port>/v1/chat/completions
Content-Type: application/json
```

There is no authentication header in the checked implementation. This implies a trusted local/tunneled network assumption, not permission to expose the endpoint.

## VLM request

`VLM_API.send_request` constructs:

```json
{
  "model": "<position-model>",
  "messages": [
    {"role": "system", "content": "<grounding-contract>"},
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/<type>;base64,<bytes>"}},
        {"type": "text", "text": "<task-prompt>"}
      ]
    }
  ],
  "max_tokens": 50,
  "temperature": 0.0,
  "stream": false,
  "logprobs": true
}
```

The response path is `choices[0].message.content`. A regular expression extracts the first integer coordinate pair. Callers then normalize/filter it and may request human review.

Main VLM use cases:

- `choose_wall`: wall-grasp point;
- `place`: free placement point, checked against local YOLO boxes;
- `choose_handover`: point for a tile supplied by another player;
- `choose_hand`: VLM hand-tile grounding retained for compatibility, while the main snapshot often uses local YOLO instead.

## Brain request

`GAME_AI_API.process_question` converts hand state, discard history, melds, selected suit, current event, and legal actions into system/user messages.

`GAME_AI_API.send_request` constructs:

```json
{
  "model": "<brain-model>",
  "messages": "<constructed messages>",
  "max_tokens": 500,
  "temperature": 0.0,
  "stream": false
}
```

The response path is also `choices[0].message.content`. `parse` requires an `<answer>...</answer>` region and maps the content to a legal action and tile code.

Supported decisions in the snapshot are:

- discard;
- claim, normalized to pung or kong;
- concealed kong;
- promote kong;
- pass.

## Caller chain

```text
MJController phase function
  -> Player.make_decision
  -> GAME_AI_API.make_decision
  -> process_question
  -> requests.post(brain_api_url)
  -> parse
  -> cached/current decision
```

```text
MJController motion phase
  -> VLM_API.choose_wall/place/choose_handover
  -> VLM_API.send_request
  -> requests.post(position_api_url)
  -> coordinate regex
  -> local filtering/review
  -> pixel/depth conversion
  -> robot action
```

## Important implementation details

- The Brain `send_request` signature accepts `model_name`, but the snapshot payload reads the instance's configured model field; verify whether the argument is intentionally ignored before refactoring callers.
- Brain and position configurations can point to the same endpoint without proving they use the same deployed model.
- `stream` is false in production wrappers even though the experimental VLM script supports streaming.
- A successful HTTP response proves only transport success; output parsing and semantic validity remain separate gates.

## Verification matrix

| Question | Evidence |
|---|---|
| Which URL is used? | Current `brain` config plus the selected `Config` instance |
| Which model is requested? | Serialized JSON payload, not only a function argument |
| Where does inference run? | Listener/process/tunnel/provider evidence |
| Was the response valid? | HTTP status, JSON schema, `choices` path, semantic parser |
| Did it become an action? | Caller state update, review result, coordinate conversion, controller invocation |

