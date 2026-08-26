# Current OpenPI π0.5 Map

This is an orientation snapshot, not permanent truth. Live source claims were re-checked on 2026-08-26. The locally verified deployment used OpenPI commit `15a9616a00943ada6c20a0f158e3adb39df2ccac`; a later local source snapshot existed at `215abfb217dbac7d5f1273282331b9b1866c0479`. Re-read the active checkout before treating defaults as current.

## One-sentence architecture

Public OpenPI π0.5 encodes multi-view RGB with SigLIP, embeds a prompt plus discretized normalized robot state with PaliGemma/Gemma, and lets a smaller Gemma action expert attend to that prefix while a Flow Matching ODE converts Gaussian action noise into a continuous action chunk.

## Source map

| Concern | Source path | Tested anchor |
|---|---|---|
| Public support boundary/checkpoints | `README.md` | lines 3–10, 59–118 |
| Model family and input spec | `src/openpi/models/pi0_config.py` | lines 18–84 |
| Prompt/state tokenizer | `src/openpi/models/tokenizer.py` | `PaligemmaTokenizer.tokenize` |
| Model transforms | `src/openpi/training/config.py` | `ModelTransformFactory` |
| DROID config | `src/openpi/training/config.py` | `pi05_droid` |
| Vision-language prefix/action suffix | `src/openpi/models/pi0.py` | `embed_prefix`, `embed_suffix` |
| Training loss/sampling | `src/openpi/models/pi0.py` | `compute_loss`, `sample_actions` |
| Policy assembly/normalization | `src/openpi/policies/policy_config.py` | `create_trained_policy` |
| Inference wrapper | `src/openpi/policies/policy.py` | `Policy.infer` |
| DROID raw adapter | `src/openpi/policies/droid_policy.py` | `DroidInputs`, `DroidOutputs` |
| DROID client/runtime | `examples/droid/main.py` | request/action execution loop |

## Tested `pi05_droid` shape ledger

| Stage | Tensor | Shape | Meaning |
|---|---|---:|---|
| Raw input | external RGB | `[224,224,3]` | one external view |
| Raw input | wrist RGB | `[224,224,3]` | one wrist view |
| Raw input | joint state | `[7]` | DROID Panda joints |
| Raw input | gripper state | `[1]` | scalar gripper position |
| DROID adapter | state | `[8]` | concatenated joint + gripper |
| Model slots | images | `3 × [224,224,3]` | base, left wrist, right wrist; third masked for DROID PI05 |
| Padded model state | state | `[B,32]` | internal action/state width |
| Prompt IDs | tokenized prompt | `[B,200]` | task and discretized state, padded |
| Verified prefix | embeddings | `[1,968,2048]` | `3×256` visual positions + `200` text positions |
| Verified valid prefix | mask sum | `555` | two valid images `512` + `43` valid text/state tokens |
| Action expert input | noisy actions | `[B,15,32]` | one token per future step |
| Action expert hidden | action tokens | `[B,15,1024]` | Gemma 300M expert width |
| Internal action | sampled chunk | `[B,15,32]` | padded continuous action |
| DROID output | actions | `[15,8]` | first eight unnormalized physical dimensions |

The general model defaults may differ: `Pi0Config` defaults to horizon 50 and action dimension 32; `pi05_droid` overrides the horizon to 15.

## Modules and information flow

```text
external RGB ─┐
wrist RGB ────┼─> SigLIP So400m/14 ─> visual tokens (256 per slot)
masked slot ──┘

prompt + normalized state
  -> "Task: ..., State: ...;\nAction: "
  -> SentencePiece IDs (max 200)
  -> Gemma 2B embeddings

visual tokens + language/state tokens
  -> full-attention prefix / KV cache (width 2048)

Gaussian action noise [B,H,32] + flow time
  -> linear projection + Gemma 300M action expert (width 1024)
  -> attends to prefix at every solver step
  -> velocity [B,H,32]
  -> Euler integration
  -> continuous action [B,H,32]
  -> adapter/unnormalizer -> physical action dimensions
```

## π0 versus π0.5 in the public code

The tested `Pi0Config` documents two implementation differences:

1. π0.5 puts normalized robot state into the discrete language token sequence; π0 uses a continuous state token in the action suffix.
2. π0.5 injects Flow Matching time through AdaRMS conditioning in the action expert; π0 mixes action and time embeddings with an MLP.

Do not confuse these public Flow-head differences with the full paper training recipe, which also uses discrete FAST action pre-training and high-level semantic tasks.

## Comparison with the familiar PSI action-only baseline

| Layer | PSI Flow Matching action baseline | Public OpenPI π0.5 |
|---|---|---|
| Visual encoder | multi-view ViT tokens | pretrained SigLIP visual tokens |
| Language | absent or small added condition | PaliGemma/Gemma token prefix |
| State | continuous proprio condition | normalized then discretized into prompt tokens for π0.5 |
| Action model | Transformer/RDT conditioned on observation | Gemma 300M action expert attending VLM prefix |
| Generative target | continuous action chunk | continuous action chunk |
| Objective | Conditional Flow Matching MSE | Conditional Flow Matching MSE in public head |
| Inference | several Euler/ODE steps | default 10 Euler steps |
| Main new claim | stable action generation | semantic transfer and heterogeneous-data generalization |

Both are observation-conditioned generative action policies. π0.5 does not become a world model merely because it uses a VLM; it predicts actions, not future RGB.

## End-to-end boundary

Model-level end-to-end means:

```text
RGB + prompt + state -> learned policy -> action chunk
```

It does not remove image preprocessing, network transport, action unnormalization, clipping, control-frequency logic, safety interlocks, or the low-level servo controller. The paper system is hierarchical but still learning-enabled end-to-end because both semantic subtask selection and continuous action prediction are learned rather than hand-coded planners.
