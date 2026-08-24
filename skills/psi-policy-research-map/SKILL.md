---
name: psi-policy-research-map
description: "Teach, compare, and turn PSI robot-policy research notes into falsifiable experiments across Diffusion Policy, Flow Matching, IMLE/RS-IMLE, implicit world models, V-JEPA/FLARE/TD-MPC2, VLM value learning, retrieval-weighted imitation, and Recovery/Correction. Use when reviewing the Feishu PsiPolicy learning record, comparing policy families, choosing a research direction, or separating paper claims from PSI implementation hypotheses. Do not use as proof of original-paper results or as a map of the current WAM codebase."
---

# PSI Policy Research Map

Use this skill to navigate robot-policy research ideas and convert them into explicit, testable decisions. It is a literature-and-hypothesis map, not a replacement for reading current code or primary papers.

## Evidence boundary

This skill was distilled from the Feishu page `PsiPolicy学习记录 - yunlong`, revision 2923, under the [技术分享 Wiki](https://psi-robot.feishu.cn/wiki/Ayg5wZAXti7oK0kv8eLc210tnOf), reviewed read-only on 2026-08-21.

The page exposed detailed notes, equations, reported metrics, implementation sketches, and 11 public arXiv links, but no embedded PDF attachment. The original PDF bodies were not fetched in the capture session.

Label every substantive statement as one of:

- **Primary-paper verified:** checked against the actual paper or official implementation.
- **Feishu paper note:** reported by the learning record but not independently verified.
- **PSI implementation fact:** observed in current code/config/tests.
- **PSI proposal:** a planned architecture or experiment, not current behavior.
- **Teaching hypothesis:** a plausible explanation that still needs a falsification test.

Never promote a Feishu metric or generated code sketch to primary evidence without checking the paper and experiment protocol.

## Route the question

- Read [references/research-landscape.md](references/research-landscape.md) for the method families and how they connect.
- Read [references/comparison-contract.md](references/comparison-contract.md) before comparing Diffusion, Flow Matching, IMLE, world-model, retrieval, or recovery approaches.
- Read [references/experiment-queue.md](references/experiment-queue.md) when choosing the next PSI experiment or converting a paper idea into a controlled ablation.
- Use `$psi-wam-learning-coach` for current WAM repository paths, tensor shapes, objectives, training recipes, and benchmark semantics.
- Use `$math-principles-coach` for derivations of Flow Matching, IMLE, value learning, or gradients.
- Use `$code-understanding-coach` when validating an implementation against the claimed method.

## Build the explanation

For any method or comparison:

1. State the problem it is trying to solve.
2. Identify its generated/predicted object: action, trajectory, future latent, video, value, or recovery behavior.
3. Write the conditioning variables and training target.
4. Separate training-time and inference-time computation.
5. State the mechanism that is supposed to improve coverage, efficiency, robustness, or planning.
6. List what the method does not guarantee.
7. Identify the closest PSI baseline and the minimum controlled ablation.
8. Define success metrics and a counterexample that would reject the hypothesis.

## Preserve these distinctions

- Multi-modality, sample efficiency, one-step inference, RL compatibility, and closed-loop robustness are different claims and need different evidence.
- Predicting a future latent is not automatically a useful world model; test action-conditioned controllability and rollout utility.
- A VLM progress score is not automatically a reward or value function; test temporal consistency, task grounding, and ranking of success versus failure.
- Retrieval weighting changes the effective training distribution; compare it with unweighted behavior cloning under the same data and optimizer budget.
- Recovery and Correction are different intervention segments. Recovery returns to a familiar state; Correction advances the task after recovery.
- Training on more data does not replace missing failure, recovery, or minority-mode coverage.

## Deliverable

Return the smallest useful combination of:

- method family and role;
- paper-note claim versus verified evidence;
- comparison table with matched assumptions;
- PSI relevance and current implementation gap;
- one to three falsifiable experiments;
- risks, confounders, and stopping criteria.

## Gotchas

- The Feishu page mixes paper summaries, PSI architecture discussion, future TODOs, personal reflection, and generated pseudo-code.
- Reported success rates and inference speeds are not comparable without the original dataset, seed, evaluation, hardware, and checkpoint protocol.
- “One-step” can describe the policy output path while other encoders, samplers, or search still dominate latency.
- Better mode coverage in a toy task does not establish safer robot behavior.
- A causal or predictive representation objective does not prove the learned latent contains controllable dynamics.
- An arXiv link in a document is evidence that a source was cited, not evidence that its PDF was read.
- TRAP and COLLAGE were present as research directions but the reviewed excerpts did not contain enough detail to assert their mechanisms.

