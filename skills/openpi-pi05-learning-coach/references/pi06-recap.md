# π0.6, π*0.6, and RECAP

This is a paper-level map checked on 2026-08-27. Treat the official paper and project page as author claims unless reproduced locally. Re-check the official OpenPI README before stating the current public-code boundary.

## Corrected mental model

```text
π0.5
  -> π0.6: larger Gemma 3 4B backbone, 860M action expert,
            additional robot data and richer conditioning
  -> π*0.6: π0.6 plus a binarized advantage input and RECAP training
```

π0.6 is the supervised base VLA. π*0.6 is the advantage-conditioned VLA trained with **RL with Experience and Corrections via Advantage-conditioned Policies (RECAP)**. The star denotes the RL-trained variant, not a cosmetic version suffix.

## π0.6 model path

Inputs are multi-view images `X`, robot configuration `q`, an overall task prompt, and optional metadata. The model predicts:

- a lower-frequency textual subtask `l_hat` for high-level guidance;
- a FAST-tokenized discrete representation of an action chunk during training;
- a continuous action chunk from an 860M Flow Matching action expert, reported at 50 Hz in the paper system.

The Knowledge Insulation recipe jointly trains token prediction and continuous actions while stopping the Flow Matching expert's gradient from changing the rest of the model through that branch. The discrete and continuous action outputs are trained independently rather than feeding FAST tokens into the action expert.

## RECAP loop

```text
demonstrations + autonomous rollouts + optional expert interventions
  -> outcome rewards
  -> distributional value model
  -> n-step advantages
  -> task-thresholded positive/negative indicator
  -> advantage-conditioned VLA training
  -> deploy with positive conditioning
  -> repeat collection and training
```

RECAP first performs offline-RL pre-training on a heterogeneous demonstration mixture. For a downstream task it performs demonstration SFT, collects robot experience, retrains the task value model, and extracts an improved policy one or more times. Human intervention actions are forced to positive, which assumes the corrections are good.

## Value and advantage ledger

The value model is a separate language-conditioned distributional model:

```text
input:  observation o_t + task language l
output: p_phi(V | o_t, l) over B=201 return bins
backbone reported in paper: Gemma 3 670M
```

It is trained by cross-entropy on discretized Monte Carlo returns. The paper reward is:

```text
terminal success: 0
terminal failure: -C_fail
other steps:      -1
```

Consequently the value approximates negative remaining steps to success, with failed episodes assigned a large negative value. Values are normalized per task to `(-1, 0)`.

For an n-step interval:

```text
A_t = sum_{i=t}^{t+N-1} r_i + V(o_{t+N}, l) - V(o_t, l)
I_t = 1[A_t > epsilon_l]
```

The pre-training implementation sets the task threshold `epsilon_l` from a per-task percentile reported as 30% in the paper. Preserve the paper's wording when exact quantile semantics matter.

## Policy extraction

The indicator is represented as text after the predicted subtask and before the action outputs:

```text
Advantage: positive
Advantage: negative
```

The model trains on all data rather than merely dropping failures. Its conditional action model learns both behavior distributions. At ordinary inference, set the indicator to positive. The value model is therefore not required in the standard β=1 action loop.

This is still RL even though the parameter losses resemble supervised learning: outcome reward trains the value model, the value model determines advantage labels, and those labels define policy improvement. It is not a direct PPO-style reward gradient through the Flow Matching policy.

The paper also trains with randomly omitted indicators, enabling classifier-free guidance from conditional and unconditional Flow Matching predictions. Higher guidance can sharpen positive behavior but may produce aggressive boundary actions; do not present CFG as mandatory RECAP inference.

## Evidence and boundary

- Official paper: `https://arxiv.org/abs/2511.14759`
- Official PDF: `https://www.physicalintelligence.company/download/pistar06.pdf`
- Official project page: `https://www.pi.website/blog/pistar06`
- Official repository: `https://github.com/Physical-Intelligence/openpi`

Paper-supported results include improvements in throughput and failure rate on laundry folding, box assembly, and espresso making. They are author-reported real-system results, not proof that a public checkpoint or third-party reconstruction reproduces the system.

On 2026-08-27 the official OpenPI README listed π0, π0-FAST, and π0.5, and stated that public π0.5 supports the Flow Matching head. It did not document a complete official π0.6/π*0.6 RECAP training release. Treat similarly named forks as third-party until provenance is verified.

## Falsifiable checks

- **Architecture claim:** inspect the active official config and parameter tree for Gemma 3 4B and the 860M expert; do not infer from a paper diagram alone.
- **Advantage sensitivity:** fix observation, state, subtask, checkpoint, and Flow Matching noise; flip only positive/negative and compare action chunks.
- **Policy improvement:** compare base π0.6, offline-RL π*0.6, SFT, and final RECAP under the same task contract, seeds, intervention rules, and throughput/success metrics.
- **Value validity:** test whether value rises with real progress, drops at failures, and remains calibrated across task lengths; a plausible curve is not sufficient evidence of causal action quality.

## Limitations

- The value estimator uses observations as a Markov state approximation and a V-function-based n-step estimate rather than a fully off-policy Q estimator.
- Binary labels discard advantage magnitude and depend on task-specific thresholds.
- Forced-positive human interventions inherit teleoperator quality and timing errors.
- Training on mixed historical policies changes the meaning of the reference behavior distribution.
- Success and throughput gains on reported tasks do not establish universal cross-embodiment compatibility or safe deployment.
