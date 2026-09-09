# A2D Joint WAM deployment contract

## Current reference implementation

The verified local implementation milestone was produced on 2026-09-07:

- deployment repository: `fk-issac-logistics`, branch `feat/joint-wam-online-rollout-v1`, local commit `4c527c4`;
- training/export repository: `flow-matching-test-a2d-v2`, branch `feat/a2d-v3-joint-latent-wam-scratch-v1`, local exporter commit `4eb195d`;
- deploy adapter: `workflows/a2d_policy/joint_wam_policy.py`;
- shared rollout entry: `workflows/a2d_policy/run.py`;
- one-command launcher: `start_a2d_joint_wam_inference.sh`;
- preflight verifier: `workflows/a2d_policy/verify_joint_wam_bundle.py`;
- operator handoff: `workflows/a2d_policy/JOINT_WAM_DEPLOYMENT.md`.

These revisions are evidence anchors, not permanent defaults. Re-read current code and Git state before operating.

## Tensor contract

```text
current rgb_head                     [B,1,3,224,224]
current rgb_right_hand               [B,1,3,224,224]
current actual proprio               [B,13]
past consecutive rgb_head            [B,9,3,224,224]
Wan condition latent                 [B,48,3,14,14]
random/generated future video        [B,48,4,14,14]
random/generated action chunk        [B,16,13]
```

The condition frames use `RGB resize INTER_AREA, uint8 / 127.5 - 1`, matching latent-cache preprocessing. The current two-camera ViT observation continues using its existing action-policy preprocessing.

## Inference sequence

```text
9 observed head frames
  -> frozen Wan2.2 VAE encode
  -> 3 causal condition-latent steps

condition latent + current two-camera tokens + proprio
random 4-step future video latent + random 16x13 action
  -> shared Joint WAM Transformer
  -> configured ODE integrations (reference run: 5)
  -> future video latent + denormalized action chunk
```

Wan VAE is a codec, not the dynamics predictor. The Joint WAM Transformer predicts video/action velocities. A decoder is needed to view generated video, but the encoder is required even when only actions are executed.

## History contract

The action-sequence RPC can return one observation for every executed simulator action. Preserve these frames:

```text
predict at t
execute actions t+1 ... t+4
record returned RGB at t+1, t+2, t+3
use returned RGB at t+4 as current observation for the next prediction
```

The next `predict` appends `t+4`, yielding four new physical-step frames without duplication. Parallel environments require separate history deques keyed by stable stream/environment ID.

## Bundle schema-v3 additions

A Joint WAM bundle retains the ordinary policy files:

```text
ckpt.pt
config.yaml
norm_stats.json
data_split.json
manifest.json
README.md
```

It additionally declares:

- `policy_type: joint_latent_wam`;
- `video_condition.key` and nine-frame preprocessing;
- video latent channels, steps, spatial size, and patch size in policy config;
- `external_artifacts.wan_vae.sha256`;
- public Wan runtime implementation identity;
- raw/EMA weights variant and exact checkpoint-selection criterion.

Do not embed host-specific absolute VAE/runtime paths in portable config. Supply them at launch and verify them against the manifest.

## Verified milestone and remaining gate

At the 2026-09-07 milestone:

- exporter/model regression: 19 tests passed;
- online adapter tests: 5 passed;
- real checkpoint versus deployment graph: 333 keys, no missing/extra keys, no shape mismatch;
- two archives passed remote/local and internal SHA verification;
- live GPU prefix-parity and Isaac rollout were intentionally deferred to avoid interfering with an active training run.

This means packaging and static runtime contracts were verified. It does not prove online Wan prefix equivalence, inference latency, generated-video quality, or closed-loop task success.
