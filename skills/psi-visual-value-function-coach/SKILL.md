---
name: psi-visual-value-function-coach
description: Explain, audit, and compare PSI reward-model visual value methods from task stages and reward schedules through return-to-go or IQL targets, ViT/Mask encoding, SpatialSoftmax, MLP/C51 heads, training, inference, and evaluation. Use in the psi-reward-model repository when the user asks how value, reward, GT, value atoms, logits, cross-entropy, MSE, MC, or IQL work; wants the current strategy/architecture/training/inference summarized; or wants a stable reference for comparing and improving alternative value methods. Do not use for generic vision models unrelated to value learning.
---

# Psi Visual Value Function Coach

Teach the repository's value-learning chain from evidence in the current checkout. Keep the explanation at the user's requested altitude; begin with one sentence and expand only the link they are asking about.

## Establish the active path

Inspect the current configs and callers before explaining. Determine whether the question concerns:

- scalar MC value: image/state to `ValueNet`, supervised by `return_to_go` with MSE;
- distributional MC value: image/state to value-atom logits, supervised by projected `return_to_go` with cross-entropy;
- IQL critic: expectile regression for `V(s)` and TD regression for twin `Q(s,a)`.

Do not describe these targets as interchangeable. State explicitly which path is active and distinguish repository fact from a hypothetical reward design.

## Use the causal chain

Trace explanations in this order:

`task stages -> reward schedule -> per-step reward -> return-to-go/TD target -> visual features -> value prediction -> loss -> gradients -> inference value`

When the user is confused about one link, explain that link without restarting the entire chain. Read [references/value-chain.md](references/value-chain.md) for formulas, shape defaults, common misconceptions, and repository-specific validation checks.

## Route method summaries and comparisons

- Read [references/current-repository-methods.md](references/current-repository-methods.md) when summarizing the current strategy, architecture, training, inference, configuration, or implementation risks. Re-check the live repository before treating the captured values as current.
- Read [references/method-comparison-framework.md](references/method-comparison-framework.md) when comparing MC, C51, IQL, success classification, progress estimation, or a future value-learning method. Fill one method card per method and compare evidence under the same data/evaluation contract.

Keep three layers separate in every comparison:

1. **Task definition:** stages, reward polarity, discount, horizon, and terminal semantics.
2. **Learning method:** target construction, architecture, output representation, loss, and optimization.
3. **Evaluation contract:** split, metrics, ablations, seeds, and rollout relationship.

Do not attribute a gain to the learning algorithm when the reward schedule, data split, encoder, or training budget also changed.

## Preserve the important distinctions

- Humans define task stages and reward rules; they do not manually define the model's predicted probabilities.
- `return_to_go` is a scalar future discounted reward target, not a stage label.
- Value atoms are numerical support points, not semantic task stages.
- The target atom distribution is derived from a scalar target by interpolation; logits come from the network and Softmax turns them into predicted probabilities.
- Cross-entropy matches distributions; MSE matches scalar values. Both provide gradients to every participating unfrozen parameter, not only the maximum-probability branch.
- Reward/GT quality and visual representation quality are separate. Correct GT does not guarantee the frozen encoder contains enough state information.
- In this repository Mask is normally an extra image channel, not a separate encoder.

## Coaching style

Prefer compact plain-language answers and one small numerical example. Correct terminology gently: `Transformer` is the architecture; image `transform` is preprocessing. If the user asks for a summary, use one sentence or the shortest complete chain.

Attach `path:line` evidence when making implementation claims. If the user requests diagnosis or modification, verify the current code rather than assuming the captured version is unchanged.

## Gotchas

- Check `project_to_distribution` before trusting C51 training: the captured checkout duplicated the lower-atom accumulation, so the target mass could exceed one.
- Check `terminal` versus `terminals` across reward generation and the dataset; the captured checkout used inconsistent names.
- Check whether `use_4_channel_surgery=true` is paired with a frozen encoder. A zero-initialized frozen Mask channel cannot learn.
- Do not interpret the IQL value distribution variance as calibrated uncertainty when training constrains only its expectation.
- Do not call the MC-only critic full AWR unless an actor/advantage-weighted policy update is present.

## Verification

For distributional value, verify target probability mass sums to one and its support expectation reconstructs the clipped scalar target. For learning semantics, verify predictions against an episode-held-out set and inspect value across task progress; compare frozen/unfrozen and RGB/Mask ablations when visual sufficiency is disputed.
