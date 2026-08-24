---
name: mask-generator-policy-integration
description: Integrate a separately pretrained RGB-to-mask generator into a robot policy as an internal mask-token encoder. Use when adding or reviewing a SegFormer/SAM-derived mask branch, reusing one RGB observation across encoders, configuring generator versus token-encoder freezing and learning rates, checking whether action loss corrupts mask semantics, or verifying that training checkpoints and deployment behavior preserve the intended mask model. Do not use for training the standalone segmenter, mask-label auditing, or rollout success evaluation.
---

# Mask Generator Policy Integration

Treat the mask generator as a pretrained perception contract, not merely another freely trainable policy layer. The intended chain is:

```text
RGB observation
  ├─> existing RGB encoder -> RGB token
  └─> pretrained mask generator -> soft probability mask
                                  -> mask token encoder -> mask token
all condition tokens -> policy/action head -> action
```

Keep external observation and action schemas unchanged unless the user explicitly requests a new runtime input. The environment supplies RGB; the policy creates the mask internally.

## Integration workflow

1. Trace the current observation composer, encoder interface, concat order, optimizer-group construction, checkpoint loading, and inference entrypoint before editing.
2. Freeze an explicit contract for tensor ranges and shapes. Read [references/integration-contract.md](references/integration-contract.md) before implementation.
3. Add one composite encoder that reads an existing RGB key, generates a soft mask, encodes it into policy-width tokens, and returns a unique output name.
4. Permit multiple encoders to read the same raw observation key. Enforce uniqueness on produced token names, not exclusive ownership of raw inputs.
5. Add the mask token explicitly to concat order and token-length accounting. Do not rely on dictionary iteration order.
6. Separate `mask_generator_frozen` from `mask_encoder_frozen`. A legacy `frozen` flag may freeze both, but it must not be the only control when the intended configuration is frozen generator plus trainable adapter.
7. Build optimizer groups from `requires_grad=True` parameters. A frozen generator must contribute zero optimizer parameters and zero gradients.
8. Verify training and inference through the same RGB-to-mask-to-token path. Thresholding belongs to visualization or an external binary-mask API; the policy branch should normally consume soft probabilities.

For the concrete PSI implementation and its file-level changes, read [references/psi-policy-case.md](references/psi-policy-case.md).

## Required verification

Do not call the integration complete from a successful forward pass alone. Verify:

- input contract: RGB shape, channel order, dtype, range, normalization, and spatial size;
- output contract: mask logits, sigmoid probability, resized mask, token shape, concat order, final action shape;
- freeze contract: generator stays in eval mode, has no gradients, and is absent from optimizer groups;
- checkpoint contract: the embedded frozen generator is tensor-identical to the intended standalone release;
- learning contract: the trainable mask-token encoder receives gradients from action loss;
- usage contract: normal versus zeroed versus batch-shuffled mask-token ablations change validation loss or rollout behavior if the policy actually uses the token.

Use [scripts/compare_submodule_state.py](scripts/compare_submodule_state.py) to compare a generator embedded in a policy checkpoint with standalone weights when their state-dict prefixes are known.

## Decision rules

- If explicit mask semantics must be preserved and there is no segmentation loss during policy training, freeze the generator by default.
- Train only the mask-token encoder at a smaller backbone-style learning rate when it must adapt the fixed probability map to the policy embedding space.
- Fine-tune the generator only with an explicit experiment and a preservation signal or paired mask evaluation. Action loss alone is not evidence that mask semantics will survive.
- Keep the full policy checkpoint and standalone mask release conceptually separate. The policy checkpoint contains an embedded copy of generator weights; optimizer moments are training-resume state, not inference capability.

## Gotchas

- Reusing `rgb_head` in two encoders is intentional; rejecting duplicate raw-key readers silently blocks this architecture.
- A frozen module still appears in the policy state dict and increases checkpoint size. Freezing removes gradients and optimizer state, not inference weights.
- `module.eval()` alone does not freeze parameters; `requires_grad_(False)` alone does not stop train-mode behavior. Apply both, and keep the generator in eval mode when the parent enters train mode.
- `torch.no_grad()` saves activation memory but is not a substitute for excluding parameters from the optimizer.
- Converting the mask to binary before its token encoder discards confidence and boundary information and introduces a brittle threshold into policy training.
- A good standalone Dice score does not prove the policy uses the mask token. Conversely, an RGB ViT heatmap does not measure mask-token use.
- When only action loss reaches an unfrozen generator, it may learn action-predictive shortcuts such as arm or gripper location and lose the original package-mask meaning.
- A full policy checkpoint may embed a degraded generator from an earlier joint-training run. Do not assume every large checkpoint contains the published standalone weights.
