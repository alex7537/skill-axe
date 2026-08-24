# Falsifiable Experiment Queue

Run the smallest experiment that distinguishes the proposed mechanism. Do not combine every paper idea in the first run.

## 1. Action generator comparison

Compare action-only Diffusion, Flow Matching, and IMLE/RS-IMLE under matched data, encoder, parameter budget, and optimizer steps.

Measure:

- task success and failure stage;
- conditional mode coverage and minority-mode recall;
- trajectory validity/smoothness;
- training samples and wall time;
- end-to-end inference latency;
- robustness across seeds and initial states.

Reject “IMLE improves multimodality” if additional modes are invalid, unrelated to conditioning, or do not improve rollout success.

## 2. Future-representation ablation

Use three matched policies:

1. action-only;
2. action plus frozen future-feature target;
3. action plus future-feature and return targets.

Measure action performance, future-feature error, gradient interaction, recursive rollout, and closed-loop success. Intervene on action while fixing observation/language/noise; require predicted future features to change in the correct direction.

## 3. Action-free pretraining transfer

Pretrain the future representation on non-robot video, then attach the same action-policy head and robot dataset as a from-scratch baseline.

Keep robot fine-tuning data and compute fixed. Test low-data curves and controllability. Reject the transfer claim if gains disappear after matching total compute or if features predict appearance without action-relevant dynamics.

## 4. VLM progress/value audit

Build paired trajectories:

- success versus failure;
- forward versus reversed order;
- monotonic progress versus regress/recovery;
- visually similar actions with different task outcomes;
- human versus robot execution.

Compare independent-frame prediction, autoregressive prediction, shuffled-frame prompting, and in-context examples. Measure rank correlation, ordering consistency, success discrimination, calibration, and cost/latency.

## 5. Retrieval-weighted behavior cloning

Freeze the encoder and dataset. Compare:

- uniform behavior cloning;
- similarity-only weighting;
- value-only weighting;
- similarity plus value/reachability weighting.

Report effective sample weight distribution, minority/failure coverage, training stability, and rollout success. Reject the method if a small group of near-duplicate states dominates or if offline weight proxies do not correlate with rollout improvement.

## 6. Recovery/Correction dataset composition

Define intervention segments explicitly:

- nominal successful demonstrations;
- recovery only;
- correction only;
- recovery followed by correction.

Inject controlled action and object/environment failures. Measure recovery-to-distribution rate, corrected subtask completion, final task success, human intervention time, and retries. Keep total trajectory time or transition count matched where possible.

## 7. Composition gate

Only compose IMLE, future-latent/return prediction, VLM value, retrieval, and RaC data after each component passes its independent gate. For the composed system, include ablations removing one component at a time and retain the same evaluation contract.

## Experiment record

For every run retain:

- hypothesis and rejection condition;
- source claim and evidence class;
- code commit and resolved config;
- data/split hash and trajectory composition;
- checkpoint-selection rule;
- metric schema, seeds, uncertainty, latency, and compute;
- representative success, failure, and counterexample rollouts.

