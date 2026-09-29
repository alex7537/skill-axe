# RGB-to-mask-to-policy integration recipe

This is a portable implementation and acceptance specification, not a copied company implementation or a claim that the existing local prototype passes it. Use `psi-policy-case.md` for dated evidence and branch mismatches.

## 1. Establish inputs and provenance

Collect before implementation:

- runnable policy commit, policy class, action-backbone class, checkpoint initialization/resume mode;
- standalone generator repository, immutable revision, weight SHA256, label semantics and preprocessing config;
- RGB key, channel order, original dtype/range, policy normalization, observation horizon and camera geometry;
- condition token order, embedding width, action horizon/dimension, control timing;
- externally stored dataset version, train/validation split hash, label validity manifest and run identifier.

Raw data and real split payloads need not be placed in the code repository, but their versioned identities must remain recoverable in approved storage. A public example config is not a historical training config. Never invent missing teacher-label provenance.

## 2. Separate the three learned components

1. Generator: a domain-fine-tuned segmenter, mapping RGB to a probability map.
2. Mask-token encoder: a vision encoder or adapter mapping that map to condition tokens.
3. Action model: the existing conditional action network, consuming the augmented condition sequence.

The reviewed case uses a SegFormer generator and a timm MAE ViT mask-token encoder, with Flow Matching action generation. Classify RDT only from the actual backbone/config and weight origin. Random action-network construction does not establish that a run did not subsequently resume weights.

## 3. Add the observation branch

Declare one composite encoder that reads an existing RGB key and emits a new token name. The original RGB encoder continues reading the same key. Route validation must allow duplicate input readers while rejecting duplicate output names.

Required tensor path:

```text
policy RGB [B,T,3,H,W]
 -> inverse policy normalization, with verified range
 -> generator resize/normalization [B*T,3,Hg,Wg]
 -> single-channel logits
 -> resize to the mask-encoder spatial contract
 -> sigmoid probability [B,T,1,Hm,Wm]
 -> mask-token encoder [B,T*K,Dmask]
 -> projection if needed [B,T*K,Dpolicy]
```

Validate RGB/mask spatial alignment under crop, resize, flip and other geometric augmentation. Explicitly decide whether photometric or background augmentation is applied before generation; record it and test the resulting distribution. Do not casually normalize twice.

Inspect the mask encoder's input adapter: a one-channel map is not automatically compatible with a pretrained three-channel patch embedding. Use an explicitly implemented one-channel stem or a documented channel mapping, and verify its checkpoint compatibility.

Do not threshold before mask-token encoding in the recommended baseline. The standalone binary API's threshold, such as 0.70, is for binary output/visualization, not an implied policy operation. Thresholding also changes end-to-end gradient behavior.

Append the new token explicitly in the composer's order. Update sequence-length accounting, masks and positional embeddings if required. Keep the action schema unchanged. Example 6-to-7 tokens or 768-wide embeddings are case-specific, not universal constants.

## 4. Implement independent freezing

Recommended first experiment: frozen generator, trainable token encoder and action model.

The following is a semantic configuration sketch, not a runnable Hydra config. Verify the actual constructor accepts and applies each field; a permissive `**kwargs` can silently ignore unsupported flags.

```yaml
mask_branch:
  input_key: rgb_head
  output_name: generated_mask_token
  generator:
    source: <approved-model-reference>
    revision: <immutable-revision>
    weight_sha256: <verified-sha256>
    frozen: true
  token_encoder:
    model: <verified-backbone-or-adapter>
    pretrained: true
    frozen: false
  representation: soft_probability
  tokens_per_frame: 1
```

Freeze the generator with `requires_grad_(False)`, keep it in eval mode even after parent `train()`, and exclude its parameters from the optimizer. Use no-grad for generator execution when frozen, but keep token encoding outside that no-grad region so the adapter learns.

Construct optimizer groups by parameter identity and `requires_grad`; reject duplicate membership. Every intended trainable parameter must belong to one group. A smaller encoder learning rate can be evaluated, but historical values are not universal defaults. Learning rate zero alone is not a complete freeze contract.

## 5. Train with the correct objective

Standalone segmentation stage: RGB plus aligned valid mask labels, using the chosen segmentation objective. The observed release code uses weighted BCE plus Dice; it does not identify the teacher that produced stored pseudo-labels.

Policy stage: RGB/low-dimensional observations plus demonstrated action targets. Internally generated mask conditions mean deployment does not need GT masks. Retain the existing action objective and noise/time sampling contract. In the frozen baseline, gradients update the action network, token encoder and any explicitly trainable existing encoders, but stop at the generator.

If the generator is deliberately unfrozen, declare this as a different experiment. Provide paired segmentation diagnostics and, if used, an explicitly weighted preservation objective. Never describe action-only training as preserving segmentation semantics by construction.

## 6. Load and save without hiding mismatches

- Pin and verify the standalone generator before policy training.
- For a new branch on an existing policy, inspect every missing/unexpected state key. Extending token position tables or adapters needs an explicit initialization rule; broad `strict=False` is not proof of compatibility.
- When resuming a full policy, its embedded generator can overwrite the standalone initialization. Audit loading order and compare the final embedded weights before optimization.
- Save the composite module, token encoder, concat contract, preprocessing and source revision with the complete policy.
- Distinguish an inference checkpoint from exact optimizer/scheduler/RNG resume state. A frozen module remains part of inference weights.
- Specify whether deployment restores all weights locally or resolves an external pinned dependency; test in an environment without the original training directory.

## 7. Reuse the same inference path

On each new observation, compute the RGB/lowdim/mask condition tokens once and reuse them across the action model's denoising/integration steps when conditions are fixed. Do not cache tokens across changed observations. No dataset GT mask, new threshold, or alternative preprocessing should appear only at inference time.

## 8. Acceptance evidence

| Check | Required evidence |
|---|---|
| Generator parity | Same RGB produces matching probabilities via standalone and embedded paths within declared tolerance |
| Shape and finite values | B/T/K/width, concat order and unchanged action shape verified |
| Freeze and gradients | Generator eval, no gradients, zero optimizer membership; adapter receives gradients |
| Weight preservation | Embedded generator tensor equality before/after training for a frozen baseline |
| Initialization | Recorded action-backbone and vision-weight origins; loading mismatches explained |
| Save/reload | Fixed input and fixed policy sampling noise yield matching outputs |
| Mask semantics | Same valid-frame set, label rule and threshold for paired segmentation diagnostics |
| Token usage | Normal/zero/shuffled token comparisons with fixed evaluation noise/seeds |
| Task benefit | Compare against the no-mask policy under matched data/budget and rollout protocol |

Token sensitivity indicates use, not necessarily improvement. A no-mask baseline is needed to assess benefit; shuffled-token performance alone can reflect out-of-distribution inputs. Report segmentation agreement separately from action error and robot success. Do not promote a diagram, YAML, successful forward pass or skill validation into a completed training/rollout claim.
