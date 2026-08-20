# Action-only Flow Matching to WAM

Use this bridge when the learner already understands an observation-conditioned action model.

## Side-by-side contract

| Question | Familiar action model | PSI WAM snapshot |
|---|---|---|
| Observation | two current RGB views + current 13D state | 9 head-RGB frames + 9-step 82D state + text + robot ID |
| Target | future action `[B,16,13]` | future action `[B,16,82]` and future video latent |
| Visual encoder | typically per-image ViT/global features | frozen causal Wan video VAE + dense DiT patch tokens |
| Temporal prediction | action chunk | joint future video/action chunk |
| Backbone | action-policy network | shared Wan DiT over video/state/action tokens |
| Outputs | action velocity/noise target | video latent velocity and action velocity |
| Training signal | action Flow Matching loss | weighted video and action Flow Matching losses |
| Inference | integrate/sample action trajectory | jointly sample video and action, then use action for control |

Do not collapse observation and target. The nine RGB frames are known condition; the sixteen future RGB frames supply supervision during training and are generated during inference.

## Shared Flow Matching skeleton

Let clean target be `x_1`, noise be `x_0`, and sampled time be `tau`:

```text
x_tau = (1 - tau) * x_0 + tau * x_1
```

One convention trains velocity `x_1 - x_0`; the observed WAM code used `x_0 - x_1`. Never transfer the sign from memory—read interpolation, target construction, and inference ODE together.

WAM applies this structure to two modalities:

```text
clean video latent -> noisy video latent -> predicted video velocity
clean future action -> noisy future action -> predicted action velocity
```

They share a sampled timestep and joint transformer context. “Action model plus an extra independent video loss” is incomplete because each modality can influence the shared representation and the other head.

## Gradient questions to answer

1. Does video loss update the shared DiT, video head, state/action adapters, or all of them?
2. Does action loss update visual representations through the shared backbone?
3. Is the video VAE frozen and detached?
4. Is text precomputed and detached?
5. Are inactive action dimensions included in the reduction?
6. Are prefix video latent steps excluded from loss?

Loss weights do not directly equal influence. Compare gradient norms or controlled ablations because modality scale, token count, reduction, and head difficulty also matter.

## VLA versus WAM

- Adding language to an observation-conditioned action policy makes it VLA-like: `p(action | vision, state, language)`.
- Adding future visual prediction learns `p(future visual latent, action | history, state, language)`.
- A WAM can still expose only its action output, but its training pressure and inference computation differ from a pure VLA.
- Whether predicted video improves control is empirical; compare action-only, language-action, and joint video-action ablations under matched budgets.

## Minimum transfer check

Ask the learner to fill this ledger before proceeding:

| Item | Action model | WAM |
|---|---|---|
| known condition |  |  |
| clean target |  |  |
| random variable |  |  |
| corrupted input |  |  |
| network output |  |  |
| scalar loss |  |  |
| frozen modules |  |  |
| inference result |  |  |
