# PSI Policy case: offline SegFormer to mask token

This reference records the reusable file-level shape of the PSI integration. Re-check the repository because branch names and config schemas can change.

## Before and after

Before integration:

```text
3 RGB views -> shared RGB ViT -> 3 RGB tokens
3 low-dimensional/preaction streams -> 3 lowdim tokens
6 condition tokens -> FlowMatch -> [B,48,32] actions
```

After integration:

```text
rgb_head -> frozen SegFormer -> soft mask [B,T,1,224,224]
         -> trainable TimmMaskEncoder -> mask_head [B,T,768]

3 RGB + 1 mask + 3 lowdim = 7 condition tokens
7 condition tokens -> FlowMatch -> unchanged [B,48,32] actions
```

The environment still supplies RGB and low-dimensional observations only. It does not supply `mask_head` or a binary mask.

## Code changes

### Composite encoder

Add or maintain `psi_policy/model/observation/encoders/masked_image.py` with these responsibilities:

- declare `input_keys=(rgb_head,)` and a unique output such as `mask_head`;
- validate `[B,T,3,H,W]`, dtype, finite values, expected range, and size;
- restore policy-normalized RGB to the generator's expected range;
- run the released SegFormer and resize its single-channel logits;
- apply sigmoid and pass the soft probability to `TimmMaskEncoder`;
- expose independent generator and mask-encoder freeze flags;
- force a frozen generator to remain in eval mode and run without autograd activation storage.

### Observation-key routing

The RGB ViT and composite mask encoder both read `rgb_head`. The config resolver must therefore allow shared raw-input readers. It should still reject duplicate encoder output names and require that the union of raw input keys covers the model schema.

### Composer and concat

`ObsComposer` already executes each encoder and merges their named outputs. Add `mask_head` explicitly to `concat.order` at the intended position and check the derived part lengths. In the established ordering it sits after the three RGB tokens and before the three lowdim tokens.

### Optimizer

Create groups only from trainable parameters. The intended baseline is:

```text
FlowMatch and lowdim components     policy learning rate
RGB ViT                             reduced backbone learning rate
TimmMaskEncoder                     reduced backbone learning rate
SegFormer                           frozen; no optimizer membership
```

Do not encode freezing only as `lr: 0`; this still permits gradients/state allocation and obscures intent.

### Configuration

The encoder entry should conceptually include:

```yaml
- _target_: psi_policy.model.observation.encoders.masked_image.MaskedImageEncoder
  key: rgb_head
  output_name: mask_head
  mask_generator_source: <local-or-HF-model-reference>
  mask_encoder_model_name: <timm-model-name>
  image_size: 224
  pretrained: true
  local_files_only: true
  mask_generator_frozen: true
  mask_encoder_frozen: false
  tokens_per_frame: 1
```

The exact model path and learning rates belong in the experiment config, not in reusable code.

## Why the frozen-generator version replaced joint action fine-tuning

The original joint version allowed the only loss—FlowMatch action loss—to update SegFormer. There was no BCE/Dice loss preserving the offline package-mask task. Subsequent paired evaluation showed large degradation in explicit mask agreement, with most drift occurring early in policy training. This is consistent with action gradients repurposing the high-bandwidth probability map toward arm, gripper, or task-phase cues.

The corrected baseline freezes the released mask generator and trains only `TimmMaskEncoder` to translate its stable probability map into a useful policy token.

## Acceptance checks

- External observation schema and action output remain unchanged.
- Composite encoder returns one finite 768-wide token per configured frame.
- Condition-token count changes from six to seven in the one-frame configuration.
- Frozen SegFormer has zero trainable parameters and zero optimizer membership.
- TimmMaskEncoder has nonzero gradients after an action-loss backward pass.
- Embedded SegFormer weights match the intended standalone release.
- Full-policy save/reload produces the same action for fixed inputs and fixed flow noise.
- Mask-token zero/shuffle ablation is reported before claiming the policy uses the branch.

## Historical checkpoint caution

A full policy checkpoint stores all module weights even when some modules are frozen. Older checkpoints from the unfrozen joint-training version may therefore contain a semantically degraded SegFormer. Initialize a corrected run from the trusted standalone generator, not by resuming the degraded full checkpoint.
