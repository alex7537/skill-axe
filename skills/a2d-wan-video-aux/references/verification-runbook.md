# Verification runbook

Use the narrowest check first and record predicted shapes before execution.

## 1. Static and unit checks

Run compilation, whitespace validation, and targeted tests for:

- nine condition frames and sixteen future frames;
- full-future versus incomplete-tail masking;
- auxiliary loss arithmetic and gradients;
- inference without video tensors or codec calls;
- bundle export and action-only round-trip.

Then run the full repository test suite to catch DP, IMLE, and ordinary CFM
regressions.

## 2. Isolated remote snapshot

Copy the feature worktree into a new directory below a remote `code_snapshots/`
root. Exclude `.git`, runs, outputs, bytecode, and caches. Do not sync into the
active training checkout. Record the exact snapshot path in the handoff.

## 3. Real codec probe

Using the normal action-training interpreter:

1. Instantiate the new frozen codec with an externally cached Wan VAE and WAM
   runtime repository.
2. Feed `[1,9,3,H,W]` condition and `[1,16,3,H,W]` future tensors in `[-1,1]`.
3. Verify a finite last-condition latent `[1,48,h,w]` and future target
   `[1,48,4,h,w]`.
4. Verify both targets have `requires_grad=False` and record peak GPU memory.

Use a small spatial size for this codec-only check; the trainer smoke validates
the production resolution.

## 4. Real dataset probe

Read first, middle, and final samples from the configured split. Confirm:

```text
obs RGB             [1,3,224,224] per camera
action              [16,13]
action_mask         [16]
video_condition     [9,3,224,224]
video_future        [16,3,224,224]
video_valid_mask    scalar bool
```

The final sample should be allowed to have one real action step while its video
target is invalid. Log episode count, effective samples, and oversampling
statistics because requiring eight history frames changes the base windows.

## 5. One-step trainer smoke

Run one train batch and one validation batch with:

- the real dataset and image resolution;
- the real ViT and Wan VAE;
- the intended action checkpoint as model-only initialization;
- W&B, bundle export, EMA, and data workers disabled for the smoke;
- a dedicated output directory.

Verify the init event, component losses, finite metrics, gradient norms, and
successful process exit. A one-step cosine schedule can report LR zero at the
end; that is a smoke-test artifact, not a training recommendation.

Re-enable and separately test bundle export before declaring the implementation
complete.

## Known failure signatures

### `ModuleNotFoundError: numpy._core`

The WAM site-packages were prepended and replaced the action environment's
NumPy with an older release before `torch.load`. Keep the action environment in
control and append WAM dependencies lazily inside the codec.

### `ImportError: libGL.so.1` from `cv2`

The same global path-precedence mistake selected the WAM OpenCV build during
dataset import. Do not solve this by installing unrelated system libraries until
the path order is corrected.

### Training succeeds but final export fails

The new policy type is missing from the bundle exporter's allowed types or its
round-trip test. Add the type without making Wan assets a rollout requirement.

### Formal training is unexpectedly slow

On-the-fly VAE encoding is still active. Precompute latents with a provenance
manifest and train from the cache rather than repeatedly decoding each clip.
