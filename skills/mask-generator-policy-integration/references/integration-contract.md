# Integration contract

Use this contract while implementing or reviewing an RGB-to-mask-to-token branch.

## Tensor path

The recommended internal path is:

```text
normalized policy RGB       [B,T,3,H,W], commonly in [-1,1]
RGB restored to [0,1]       [B*T,3,H,W]
generator preprocessing     model-specific mean/std
segmentation logits         [B*T,1,h,w]
bilinear resize             [B*T,1,H,W]
sigmoid probability         [B,T,1,H,W]
mask token encoder          [B,T*K,D]
explicit concat             [B,L_existing+T*K,D_policy]
policy output               unchanged action contract
```

Check the actual normalizer rather than assuming `[-1,1]`. Avoid double normalization when the released model already wraps preprocessing.

## Interface boundaries

- Input: reuse an existing RGB observation key unless deployment is intended to supply an external mask.
- Internal mask: keep it as a floating probability map for downstream encoding.
- Output token: use a unique semantic name such as `mask_head`; its width must match the concat/policy width or pass through a projection.
- Dataset: do not add a mask field merely because a mask exists internally.
- Inference: run the same generator and token encoder used during training.

## Freeze modes

| Generator | Token encoder | Meaning |
|---|---|---|
| frozen | trainable | Preserve offline mask semantics; learn how the policy consumes them. Recommended baseline. |
| frozen | frozen | Fixed feature branch; useful for a strict ablation or pre-trained token encoder. |
| trainable | trainable | End-to-end adaptation; requires explicit semantic-preservation evaluation. |
| trainable | frozen | Usually poorly motivated; generator must conform to a fixed adapter using action gradients. |

A frozen generator should satisfy all of the following:

```text
requires_grad == False for every parameter
training == False even when the parent policy enters train mode
no parameter identity appears in any optimizer group
no gradients after backward
weights remain identical before and after training
```

## Checkpoint meanings

```text
standalone model release
  = generator weights + architecture/preprocessing config

full policy inference state
  = RGB encoder + embedded generator + mask-token encoder + policy head + other encoders

full training checkpoint
  = full policy inference state + optimizer/scheduler/step/random-state metadata
```

Training amount does not determine file size. Architecture, dtype, optimizer choice, and saved state do.

## Validation ladder

1. One-sample deterministic generator parity against the standalone inference package.
2. Composite-encoder forward shape and finite-value check.
3. Backward check: generator has no gradients; token encoder does.
4. Optimizer membership audit by parameter identity.
5. Save/reload parity for the full policy.
6. Fixed-batch before/after-training mask comparison.
7. Normal/zero/shuffled token ablation on validation data.
8. Rollout comparison only after offline contracts pass.

Report mask agreement and policy usefulness separately. Dice measures spatial agreement with a reference mask; it is not action or grasp success rate.
