# Inference and Language Conditioning

## Public policy assembly

`create_trained_policy` assembles transforms in this order:

```text
optional repack
-> inject default prompt if absent
-> robot adapter (e.g. DroidInputs)
-> normalize with checkpoint assets
-> resize/tokenize/pad model transforms
-> batchify
-> sample actions
-> model output transforms
-> unnormalize
-> robot adapter output (e.g. first 8 DROID dimensions)
```

This order matters: π0.5 tokenizes the normalized state, not raw joint values.

## Prompt/state tokenization

For π0.5, `PaligemmaTokenizer` constructs a string shaped like:

```text
Task: <cleaned prompt>, State: <256-bin normalized state IDs>;
Action:
```

The maximum token length is 200 in the tested config. Long text is truncated. Missing prompt is an error unless a default prompt is injected.

Verified with one deterministic DROID example:

- `pick up the phone`: 43 valid tokens;
- `grasp the phone`: 42 valid tokens;
- `pick up the box`: 43 valid tokens;
- phone→box changed one token position in that example;
- the complete padded prompt array remained length 200.

Token difference proves encoding changed; it does not prove correct grounding.

## Prefix and action expert

`Pi0.embed_prefix`:

1. encodes every camera slot through SigLIP;
2. embeds prompt/state IDs with the Gemma 2B expert;
3. concatenates visual and language embeddings;
4. uses masks to remove padded language and missing cameras;
5. permits full attention within valid prefix tokens.

`Pi0.embed_suffix`:

1. projects noisy continuous actions into Gemma 300M width;
2. injects flow time through π0.5 AdaRMS conditioning;
3. creates one action token per future timestep;
4. allows action queries to attend to the full prefix and action block.

During `sample_actions`, the prefix is computed once and cached; each Flow step recomputes the action suffix and velocity while reusing the prefix KV cache.

## DROID adapter contract

Raw required inputs:

```python
{
  "observation/exterior_image_1_left": uint8[224,224,3],
  "observation/wrist_image_left": uint8[224,224,3],
  "observation/joint_position": float[7],
  "observation/gripper_position": float[1],
  "prompt": str,
}
```

`DroidInputs` maps them to:

- `base_0_rgb`: external image, valid;
- `left_wrist_0_rgb`: wrist image, valid;
- `right_wrist_0_rgb`: zeros, masked invalid;
- `state`: seven joints plus scalar gripper.

`DroidOutputs` keeps only the first eight internal action dimensions. A third raw camera is ignored unless the adapter/model contract is deliberately changed and trained for it.

## High-level and low-level semantics

The paper system factors behavior conceptually as:

```text
subtask z ~ p_theta(z | current images, long-horizon goal)
actions  a ~ p_theta(a | current images, state, z)
```

High level is autoregressive text such as `pick up the plate`; low level is a continuous action chunk. The same unified model performs both modes in the paper, with high-level inference at lower frequency.

Public OpenPI's standard `policy.infer()` path does not generate `z`; the caller supplies the prompt and the Flow head generates actions. Treat this as low-level language-conditioned action inference, not evidence that hierarchical planning ran.

## End-to-end meaning

Within the learned policy boundary:

```text
RGB + language + proprioception -> continuous action chunk
```

The system may still use a high-level text bottleneck and external engineering. “End-to-end” does not mean one forward pass, one loss through sampled discrete text, no controller, or no safety layer.

## Runtime checks

Before claiming a runnable policy:

- load the exact checkpoint and its normalization assets;
- print `jax.devices()` or the PyTorch device;
- confirm input keys/shapes/dtypes and masks;
- run one deterministic fixed-noise call;
- require expected physical output shape and finite values;
- measure cold load, first compile, and warm inference separately;
- compare model horizon with client assertion and execution horizon;
- preserve representative action arrays and environment versions.

### Tested DROID client mismatch

At commit `15a9616a...`, `pi05_droid` configured horizon 15 and returned `(15,8)`, while `examples/droid/main.py` documented/asserted `(10,8)`. This would fail before execution. Never carry the historical fix forward without checking the active checkout.
