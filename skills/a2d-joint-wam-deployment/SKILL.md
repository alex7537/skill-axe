---
name: a2d-joint-wam-deployment
description: Package, transfer, validate, and launch A2D Joint WAM checkpoints for Isaac rollout with online nine-frame Wan2.2 VAE conditioning. Use when requests mention Joint WAM bundle deployment, 9-frame video history, external Wan VAE/runtime verification, cross-device inference handoff, or world-model rollout smoke tests. Do not use for action-only CFM/DP/IMLE bundles or training-only Wan video auxiliary heads.
---

# A2D Joint WAM Deployment

Deploy Joint WAM as a versioned inference system, not as a checkpoint copied beside an action-only runner. The essential runtime addition is `nine consecutive head-RGB frames -> frozen Wan VAE -> condition latent` before joint video/action ODE sampling.

## Required evidence

Resolve before changing or launching anything:

- the exact `joint_latent_wam` checkpoint and selection role;
- training config, summary, data provenance, epoch, step, raw/EMA variant, and SHA256;
- the checkpoint-bound Wan VAE SHA and public Wan runtime implementation;
- the target `fk-issac-logistics` revision and its existing A2D gRPC contract;
- whether another GPU job is active;
- whether the request authorizes prediction-only smoke or real action execution.

Read [references/deployment-contract.md](references/deployment-contract.md) before implementing, exporting, or launching. Use `$remote-policy-bundle` for verified remote export/transfer when its exporter supports schema-v3 Joint WAM bundles. Use `$robot-benchmark-loop` for formal multi-seed qualification after infrastructure smoke.

## Checkpoint decision

Do not collapse the two training losses into one ambiguous “best”:

```text
total loss = action_loss_weight * action_flow_loss
           + video_loss_weight  * video_flow_loss
```

- Robot rollout priority: prefer `best_ema_action_mse.ckpt` with EMA weights, plus `latest.ckpt` raw as a terminal control.
- Joint-generation quality: also inspect the checkpoint selected by weighted total validation loss and report both component losses.
- Never infer the best epoch from the filename alone; read checkpoint selection metadata or `summary.json`.

## Deployment workflow

1. Confirm that the training checkpoint requires `video_condition_latent` and that bundle export is not silently falling back to an action-only policy.
2. Export a schema-v3 bundle containing Joint WAM weights, config, normalization, split, checkpoint provenance, and external Wan artifact identities. Keep the multi-GB Wan VAE and public runtime external unless the user explicitly requests a larger all-in-one release.
3. Run `scripts/audit_joint_wam_bundle.py` against the archive. A bundle-only audit is partial; rollout readiness requires the exact external VAE and runtime to pass.
4. Confirm the target adapter accumulates every simulator-step `rgb_head` frame returned by the gRPC trace. Replan-only frames are not equivalent to consecutive 30 Hz training history.
5. On reset, record the cold-start rule. Repeating the first frame to reach nine frames is allowed only as an explicit approximation; collecting eight no-op frames is a distinct evaluation protocol.
6. Prove checkpoint/runtime graph compatibility by matching every state-dict key and tensor shape before loading weights strictly.
7. On a known training-cache window, compare online nine-frame VAE encoding against the stored `condition_prefix`. Treat this as a required GPU parity gate, even when the VAE is described as causal.
8. Start the established Isaac gRPC scene unchanged and run prediction-only smoke without `--execute`.
9. Validate finite `[16,13]` actions, training-range guards, nine-frame order, seed behavior, and inference latency. Only then run one short closed-loop episode with explicit execution authorization.
10. Scale evaluation only after recording bundle SHA, VAE SHA, runtime revision, policy adapter revision, seed, execute horizon, simulator identity, and every invalid/crashed episode.

## Safety boundaries

- Never add `joint_latent_wam` to an exporter allow-list without also supplying the online condition-latent path; that produces a bundle which loads but fails at inference.
- Never bypass a VAE SHA mismatch or silently substitute another Wan version.
- Do not consume a GPU already running training for a parity or rollout smoke unless the user explicitly chooses that trade-off.
- Prediction-only validation does not authorize robot/simulator action execution. Require the established explicit execution flag.
- Do not push repository changes unless the user requests the exact remote operation; company/ambiguous remotes remain separately gated.

## Verification outcome

Report separate states:

- `bundle-valid`: internal files and hashes pass;
- `runtime-valid`: external VAE/runtime identities pass;
- `model-load-valid`: strict key/shape/load check passes;
- `condition-parity-valid`: online prefix matches cached training prefix;
- `infrastructure-smoke-valid`: prediction-only path produces finite actions;
- `closed-loop-smoke-valid`: one authorized short episode runs;
- `scientifically-qualified`: only after the frozen benchmark contract and coverage pass.

Do not summarize an earlier state as a later one.

## Gotchas

- Training config may intentionally contain `deployment.eval_bundle.enabled: false`; check the actual exporter revision rather than forcing the flag.
- A standard action-only rollout wrapper provides current RGB/proprio but no `video_condition_latent`.
- At inference, future RGB does not exist and is not “masked real video”; future video latent and action both start from random noise.
- `video_future_mask` is a training tail-padding mask. Current joint inference marks generated future latent steps valid.
- Four executed actions followed by one replan observation provide only one frame unless the runner preserves intermediate trace observations.
- The first live prediction has a cold-start history mismatch unless the protocol deliberately warms up eight frames.
- EMA can improve stability but does not optimize a separate video objective; always name the metric that selected it.
