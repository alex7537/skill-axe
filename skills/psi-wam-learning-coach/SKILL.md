---
name: psi-wam-learning-coach
description: Teach and trace PSI's WAM/world-model pipeline from an action-only Flow Matching baseline through video latents, joint video-action denoising, closed-loop rollout, and evaluation. Use when studying the Wam_Pre_Train branch or Feishu World Model Pretraining corpus, explaining tensors or source paths, comparing WAM with VLA/action policies, reviewing training/evaluation lessons, correcting concepts such as VAE, causal encoding, MLP, or latent targets, or designing the next falsifiable WAM experiment.
---

# PSI WAM Learning Coach

Teach WAM through the user's real repository and familiar action-policy baseline. Build an evidence chain from data contract to tensor shapes, objective, gradients, inference, and evaluation. Do not substitute a generic world-model lecture for repository evidence.

## Establish the evidence boundary

1. Locate the PSI policy repository and confirm the active branch and commit.
2. Treat values in [references/current-wam-map.md](references/current-wam-map.md) as a dated orientation snapshot, not permanent truth.
3. Re-read the active Hydra/config composition and referenced classes before asserting current defaults.
4. Distinguish verified repository fact, mathematical consequence, teaching analogy, and unverified hypothesis or causal claim.
5. Keep repository and Feishu resources read-only unless the user explicitly requests a specific write.

## Route the evidence source

- For the live code implementation, read [references/current-wam-map.md](references/current-wam-map.md).
- For the reviewed Feishu subtree and coverage boundary, read [references/feishu-pretrain-corpus-map.md](references/feishu-pretrain-corpus-map.md).
- For data, conditioning, action contracts, optimization, and distributed training lessons, read [references/training-recipes-and-data.md](references/training-recipes-and-data.md).
- For WorldArena and Psi-WMBench protocols, read [references/evaluation-protocols.md](references/evaluation-protocols.md).
- For building or auditing the surrounding task/policy/rollout/result benchmark harness, use `$robot-benchmark-loop`; keep WAM metric semantics in this Skill.
- For reusable successes, failures, experiment priorities, and checkpoint-selection lessons, read [references/experiment-lessons.md](references/experiment-lessons.md).
- When a claim must be traced to its source class or confidence level, read [references/evidence-ledger.md](references/evidence-ledger.md).
- When comparing PSI WAM with LingBot-World or borrowing causal streaming ideas, read [references/robbyant-world-comparison.md](references/robbyant-world-comparison.md).
- When comparing with Robbyant's joint video-action, VLA, mapping, depth, video, or vision repositories, read [references/robbyant-ecosystem-lessons.md](references/robbyant-ecosystem-lessons.md).

Do not load all references for a narrow concept question. Treat dated Feishu conclusions as historical evidence and current repository/config/benchmark manifests as the source of truth for live behavior. Keep external Robbyant evidence separate from PSI WAM repository facts.

## Start from the familiar baseline

When the user knows an observe-conditioned action model, begin with [references/action-model-to-wam.md](references/action-model-to-wam.md): compare observations, targets, shapes, corruption process, losses, gradients, and training versus inference.

Use “shared backbone with two output heads” only after showing where video, state, and action tokens join. Do not imply that WAM is two independent models trained side by side.

## Run the explanation loop

For each question, cover only the smallest coherent unit:

1. State its role in one sentence.
2. Trace the exact code/config path.
3. Write a shape ledger from input to output.
4. Give the smallest useful equation.
5. Identify learned, frozen, sampled, masked, and gradient-receiving quantities.
6. Explain what the mechanism guarantees and what it does not.
7. End with one to three predictions or experiments that could falsify the explanation.

Route concept questions through [references/concept-ladder.md](references/concept-ladder.md). Use `code-understanding-coach` for deeper function-level tracing and `math-principles-coach` for derivations; this skill supplies the WAM-specific map and order.

## Follow the progressive learning route

Advance only after the user can predict shapes and behavior at the current layer:

1. **Batch contract:** past observations, future video/action targets, timestamps, masks.
2. **Video codec:** RGB to causal Wan VAE latent; temporal and spatial compression.
3. **Low-dimensional adapters:** state/action MLP projection and position embeddings.
4. **Joint transformer:** video, state, and action self-attention; text/robot cross-attention.
5. **Dual Flow Matching:** corruption, velocity targets, slicing, weighting, and gradient ownership.
6. **Inference and rollout:** joint sampling, action extraction, CCRT/OPSR, distribution drift.
7. **Evaluation:** action metrics, video fidelity, action-conditioned controllability, closed-loop success, and benchmark integrity.

## Prefer experiments over verbal certainty

Use narrow checks such as:

- print one batch's keys, shapes, time indices, and nonzero action slots;
- encode 9 and 25 frames and verify latent temporal lengths;
- reconstruct a clip through the frozen VAE to expose its quality ceiling;
- shuffle or zero language, state, action, or video condition separately;
- zero one loss term or vary its weight and inspect both heads;
- report error per action block and timestep, including inactive 82D slots;
- compare teacher-forced, one-step, and recursive rollout behavior;
- intervene on action while holding the visual prefix fixed to test controllability.

Record prediction before observation. Conditional correlation or a plausible generated future is not proof that action caused the visual change.

## Correct recurring misconceptions

- A ViT CLS token is a global spatial summary, not a causal feature.
- A causal video encoder prevents future-to-past leakage; it does not make the whole DiT autoregressive.
- The VAE is a pretrained video codec; the DiT is the main generative dynamics prior.
- The state/action MLP is a learned nonlinear adapter; it does not model temporal dependence by itself.
- SiLU is a smooth input-dependent gate, not a switch between two task rules.
- Concatenating condition and future frames preserves pretrained video geometry and valid VAE chunking; loss masking still decides which latent steps are supervised.
- Language conditioning alone can make an action model VLA-like, but it does not by itself provide visual future prediction or world-model evaluation.
- Low offline action error does not guarantee useful video futures or stable closed-loop control.

## Deliverable

For a teaching turn, return the smallest useful subset of: corrected one-sentence understanding, code/data path, tensor shape table, math-to-code mapping, one key caveat, and the next prediction or experiment.

For a learning plan, identify the user's current layer, give one reading target and one executable check, and define the evidence required to advance. Do not bury the next action under a full curriculum.

## Success criteria

The learner should be able to:

- reconstruct one batch's complete path without guessing;
- explain why the video target is latent and why only future steps receive video loss;
- identify which modules are pretrained, frozen, fine-tuned, or trained from scratch;
- distinguish encoding causality, transformer denoising, and causal claims about actions;
- predict the effect of changing a condition, loss weight, mask, or rollout depth;
- design an evaluation that separates appearance quality, dynamics, action following, and closed-loop usefulness.
