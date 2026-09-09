# Robot-policy resume evidence checks

Use these checks when translating policy-training and rollout iterations into career claims. These are interpretation rules, not a frozen record of one project's current performance.

## Action supervision and observations

A policy can observe actual joint positions while predicting commanded targets. Inspect the dataset mapping and normalization contract independently for observations and actions.

Hybrid labels may retain executed arm positions while replacing only the hand portion with commanded hand targets. Do not compress this into “replaced all executed actions with targets.” Distinguish the user's diagnosis that labels taught jitter/lag from a controlled experiment proving that causal explanation.

Zero target rows can be placeholders or meaningful commands. Reuse the implementation's established validation, not a universal assumption that targets are cleaner than actual states.

## Padding, sampling, and deduplication

- A fixed-length action window may repeat its last valid action near an episode boundary. Confirm whether the window is included in training and whether the actual loss consumes its validity mask.
- Keeping terminal windows can preserve grasp/lift supervision that full-window-only sampling discarded. Do not claim a safety or success-rate improvement without outcome evidence.
- A 2× transition sampling factor may duplicate windows containing a key event. It is neither 2× video FPS nor necessarily a 2× coefficient in the loss. Overlapping sampling categories can change total sample counts.
- Exact consecutive joint-state deduplication may keep the final row of each identical run. This preserves endpoint/phase information; it is distinct from approximate RGB deduplication or removal of all stationary motion.
- Verify that aligned RGB, actual state, commanded labels, phase flags, and split identities remain on the same timeline.

## Architecture and optimization

Read encoder output dimensions, feature adapters, concatenation axis, proprio projection, time embedding, action projection, and prediction head separately. For example, two views with 49 spatial tokens each plus one state token yield 99 condition tokens, not 99 action timesteps. Do not reuse those dimensions for another checkpoint without reading its config.

For Conditional Flow Matching, straight-line interpolation between noise and clean action commonly yields a velocity target of `action - noise`. A masked velocity MSE is an implementation/design choice; it does not justify claiming a novel learning algorithm. Static/keyframe/lift metrics may only be detached diagnostics.

Frozen-versus-fine-tuned comparisons should retain dataset size, split, steps, seed, and parameter-group learning rates. Report a held-out action-MSE reduction as that metric. Do not infer rollout success from it. A completed cosine schedule at zero learning rate also differs from a new continuation schedule; a config named “100 epochs” is not completion evidence.

## Rollout outcome and contribution

Check checkpoint identity, task/object, simulator versus physical robot, success definition, numerator/denominator, and evaluation completion where available. Transient contact, sustained lift, and final retention are different outcomes. A small smoke test does not establish a benchmark score.

If the user supplies “approximately 70% success” but no denominator, preserve it as a user-reported approximate outcome and flag the missing evaluation scope outside the resume block. Do not invent “70 of 100,” “real-world,” or a standardized benchmark claim.

When another repository provides inference, verifying data/action compatibility and using rollout feedback supports “evaluated through an existing inference pipeline.” It does not establish that the user designed the simulator, RPC service, or control stack.

World-model code, video-auxiliary smoke tests, completed policy training, and post-training rollout gains are separate milestones. Report only the milestone with evidence; a training-only video auxiliary objective does not imply video generation during deployment.
