---
name: a2d-wan-video-aux
description: Add, audit, or smoke-test a frozen Wan VAE future-video auxiliary objective on an A2D Flow Matching action policy. Use when requests mention 9+16 video clips, Wan latent loss, a training-only video branch, flow/WAM environment mixing, upgrading an existing CFM checkpoint, or validating that deployment remains action-only. Do not use for a full joint video-action WAM or ordinary action-only CFM training.
---

# A2D Wan Video Auxiliary Objective

Implement the smallest auxiliary-prediction experiment that can answer whether
future-video supervision improves the existing action policy. Preserve the
action observation and rollout contract unless the user explicitly changes it.

## Establish the contract

Inspect the live dataset, policy factory, checkpoint loader, exporter, and WAM
runtime before editing. Do not infer current behavior from an older branch or
document.

Default V1 contract:

```text
action observation: current dual RGB + current proprio
video condition:    head RGB[t-8:t]       (9 real frames)
video target:       head RGB[t+1:t+16]    (16 real frames)
action target:      action[t+1:t+16]
Wan input:          [B,3,25,H,W]
Wan latent:         [B,48,7,h,w] = 3 condition + 4 future steps
loss:               L_action + lambda_video * L_future_latent
```

Call this an **auxiliary video-loss policy**: the Wan VAE is frozen, while the
small latent head and shared action network receive video-loss gradients. It is
not a frozen video-feature-only observation branch and not joint WAM denoising.

## Preserve gradient and deployment boundaries

- Load the Wan VAE lazily from an external cache under `no_grad`.
- Keep VAE weights outside the optimizer, policy state dict, EMA, and bundle.
- Encode action observations once; reuse condition tokens for action and video
  objectives instead of running the visual encoder twice.
- Teacher-force clean actions only for the auxiliary context in V1.
- Rollout must need only the original action observations and must not initialize
  the Wan runtime.
- Permit model-only initialization from the matching action CFM checkpoint, but
  accept missing keys only under the new auxiliary head.

## Handle incomplete tails independently

Keep action padding and video validity separate. A tail sample may retain valid
action steps through `action_mask` while contributing zero video loss when fewer
than 16 real future frames exist. Fixed-shape repeated frames are transport
padding, never valid future supervision.

## Isolate environments

Keep the action-training environment first on `sys.path`. Append WAM-specific
site-packages lazily inside the codec immediately before importing its runtime.
Never prepend the WAM virtual environment to the whole training process.

Read [references/verification-runbook.md](references/verification-runbook.md)
before running remote tests or diagnosing environment failures.

## Acceptance criteria

- Existing policy tests still pass.
- Dataset tensors and temporal indices match the declared contract.
- Invalid future clips skip the codec and yield zero auxiliary loss.
- Real Wan encoding is finite and returns four supervised future latent steps.
- Backward gives gradients to the auxiliary head and shared action network, but
  not the VAE target.
- Total loss numerically equals action loss plus the weighted video loss.
- Old CFM checkpoint upgrade reports only auxiliary-head missing keys.
- A deployment bundle round-trip performs action inference without Wan assets.

For formal training, precompute frozen video latents first. On-the-fly VAE
encoding is a smoke-test path because repeated JPEG decoding and VAE inference
otherwise dominate every epoch.

## Authorization boundary

Use a new worktree/branch and an isolated remote code snapshot. Do not overwrite
a live training checkout, launch a long run, push a branch, or change cached
model assets unless the user explicitly requests that action.
