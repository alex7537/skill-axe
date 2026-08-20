# Reusable WAM experiment lessons

## High-confidence lessons

1. **Validate semantics before scale.** Wrong pose slots, truncated rotation, masked gripper, duplicated normalization, or conflicting text/action make larger runs uninterpretable.
2. **Keep condition tracks separate.** Text, action, and joint answer different questions; their raw score differences contain length and input-contract confounders.
3. **Use rollout-aligned checkpoint selection.** Historical loss curves and partial EWM rankings did not reliably identify the best rollout checkpoint.
4. **Treat schema as part of the result.** A number without metric set, version, coverage, direction, preprocessing, and checkpoint is not comparable evidence.
5. **Shorter windows and rolling history are strong candidates.** Historical W220 coverage and episode-start mismatch make long single-shot prediction an expensive, weakly supervised default.
6. **Mask heterogeneous slots.** Zero-filled inactive dimensions can dominate training and make aggregate action loss optimistic.
7. **Profile communication honestly.** Time charged to clipping or optimizer access may actually be deferred collective wait.
8. **Do not confuse appearance stability with dynamics.** Static or low-motion video can score well on some consistency metrics while failing control.

## Historical training trend

Early RoboTwin experiments showed:

- action-conditioned results generally exceeded text-only results;
- joint conditioning was usually strongest under matched benchmark profiles;
- most improvement occurred from early to mid training, followed by smaller gains;
- task/semantic fidelity and trajectory accuracy remained weaker than motion/perceptual dimensions;
- later checkpoints did not uniformly improve every metric, especially photometric/temporal stability.

The later Psi-WMBench result snapshot reinforced this pattern: Epoch 6 produced a large gain over Epoch 2; Epoch 13 and 17 added smaller gains; Text-Action was highest, Action next, Text lowest. Treat these as evidence for diminishing returns and condition value—not a universal epoch schedule.

## Recommended experiment queue

### Gate 0 — contract tests

- raw action → canonical 82D → normalized tensor → adapter input;
- quaternion sign equivalence and relative rotation identity;
- continuous gripper visibility;
- slot-valid masks and per-source coverage;
- text/action/robot conditions reaching the intended attention path;
- fixed inference seed and recipe fingerprint.

### Gate 1 — no-training interventions

- zero action;
- swap actions within a batch/episode set;
- change only gripper;
- create a deliberate text/action conflict;
- change only text with a scene-compatible instruction;
- encode the same prefix before two futures to test VAE causality.

### Gate 2 — small controlled runs

- no-mask versus strict-mask versus soft-mask action loss;
- old dropout versus mutually exclusive 85/5/5/5 conditioning;
- action AdaLN-only versus action tokens/cross-attention;
- W220 versus 49/81 future with rolling history;
- episode-start-balanced versus ordinary window sampling;
- current resolution versus native 480p under a matched token/step budget.

### Gate 3 — scaling and auxiliary signals

- task/robot/source-balanced Mix sampling;
- reliable TCP supervision with frame-aware masks;
- depth/normal/keypoint/flow/contact auxiliary targets;
- HSDP/FSDP/sequence-parallel scaling after loss parity;
- A14B LoRA/adapter only after the 5B contract baseline is trustworthy.

## Minimal acceptance criteria for an ablation

- one independent variable;
- same data selection and training budget;
- same evaluation track/profile/recipe;
- exact checkpoint and code revision;
- complete metric coverage and per-source results;
- paired seeds or paired bootstrap comparison;
- action block metrics and video dimensions reported together;
- rollout examples and known failure cases included.

## Common invalid conclusions

- “Lower training loss means a better world model.”
- “Action Following is high, so the action is correct.”
- “Joint beats text, therefore the visual head caused better actions.”
- “One partial EWM is higher, therefore the checkpoint is globally better.”
- “More motion means more correct dynamics.”
- “A14B should fix action semantics.”
- “An epoch means the full Mix dataset was seen once.”
