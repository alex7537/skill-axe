# π0.5 Training Recipe and Mathematics

Keep the full paper recipe separate from what the public OpenPI training command implements.

## Full paper system

The paper trains a unified model on heterogeneous example types:

- mobile-manipulator household data;
- non-mobile robots across environments;
- cross-embodiment robot data;
- high-level semantic subtask prediction;
- web image captioning, VQA, and localization examples;
- post-training verbal-instruction data from human supervisors.

The reported recipe has two broad stages:

1. **Pre-training:** represent robot actions with FAST discrete tokens and co-train them with language/vision/high-level examples using autoregressive token prediction.
2. **Post-training:** specialize for mobile manipulation and add a Flow Matching action expert so continuous actions can be generated efficiently; retain high-level semantic supervision.

At full paper inference, the model autoregressively predicts a semantic subtask and then conditions continuous action generation on that subtask. Official OpenPI currently states that its public π0.5 training/inference supports only the Flow Matching head, so do not claim that an ordinary public fine-tune reproduces the full hybrid recipe.

## Public Flow Matching objective

For expert action chunk `a` with shape `[B,H,D_a]`:

```text
epsilon ~ Normal(0, I)             [B,H,D_a]
t ~ Beta(1.5, 1)                   [B]
x_t = t * epsilon + (1-t) * a      [B,H,D_a]
u_t = epsilon - a                  [B,H,D_a]
v_theta = model(x_t, t, context)   [B,H,D_a]
loss = mean_Da (v_theta - u_t)^2   [B,H]
```

This is the tested repository convention: `t=1` is noise and `t=0` is data, opposite to some Flow Matching explanations. Map terms to `Pi0.compute_loss` in `src/openpi/models/pi0.py`.

### Conditioning context

```text
context c = valid visual tokens
          + task text tokens
          + discretized normalized state tokens
```

Under squared loss, the model is pressured toward the conditional mean velocity field `E[u_t | x_t, t, c]`. A lower loss does not guarantee closed-loop success, correct object grounding, preservation of every action mode, or safe cross-embodiment transfer.

## Gradient ownership

The scalar action loss backpropagates through:

- action output projection;
- action expert Transformer;
- prefix/action cross-attention path;
- participating language and vision parameters unless the active freeze/LoRA filter excludes them.

Inspect the active `TrainConfig`, `get_freeze_filter`, optimizer parameter tree, and checkpoint role before stating which blocks are trainable. “Action expert” does not imply that the VLM is always frozen.

## Why language can matter without a language-specific action loss

Robot demonstrations pair context `(image, state, prompt)` with actions. If two prompts demand different behaviors in the same visual state, using prompt tokens can reduce the conditional velocity error. But a model may ignore language when:

- every episode uses the same prompt;
- prompt and scene are perfectly correlated, so vision alone predicts the action;
- task labels are noisy or generic;
- the action expert or adapter is under-trained;
- evaluation changes prompt but not the action-relevant scene.

Therefore use prompt shuffle, synonym, counter-target, and image×prompt interventions rather than reporting only that a prompt field exists.

## Inference equation

Starting from `x_1 = epsilon`, the public sampler uses default `N=10` steps:

```text
dt = -1/N
x <- x + dt * v_theta(x, t, context)
t <- t + dt
```

Language changes the prefix KV cache and therefore can change the predicted velocity at every integration step.

## Training versus inference ledger

| Quantity | Training | Inference |
|---|---|---|
| expert action `a` | observed target | unknown |
| noise `epsilon` | sampled to build `x_t` | sampled start point or explicitly fixed |
| time `t` | random Beta sample | deterministic grid from 1 to 0 |
| velocity target `u_t` | known from `epsilon-a` | unavailable |
| loss/gradient | computed | none |
| iterations | one sampled time per example | repeated solver calls |
| prompt/state | conditioning | conditioning |

## What to verify before fine-tuning

- observation keys, camera roles, resolution, masks, timing, and color order;
- state/action names, units, ordering, absolute/delta/velocity semantics;
- horizon, padding dimension, action mask, and execution horizon;
- normalization assets paired with the checkpoint and adapter;
- task prompt quality and within-scene language variation;
- episode-group split and exposure history;
- active freeze filter and which parameters receive gradients;
- whether the goal is public Flow-head adaptation or a separate reconstruction of the paper's high-level system.
