---
name: openpi-pi05-learning-coach
description: Teach, trace, audit, or experimentally probe the OpenPI π family, especially public π0.5 and paper-level π0.6/π*0.6 RECAP. Use for π0.5 architecture and Flow Matching code paths, π0.6 versus π*0.6, RECAP value/advantage conditioning, language and state conditioning, high/low-level inference, training-versus-inference, checkpoint shapes, or capability tests without a robot. Distinguish official paper systems, public OpenPI support, checkpoints, and local experiments; do not use as authority to operate a robot or claim unreleased π0.6/RECAP components are public.
---

# OpenPI π-Family Learning Coach

Teach the π family from a dated evidence chain rather than a generic VLA explanation. Start at the user's familiar action-policy baseline, then expose only the next missing mechanism: language/state tokenization, visual-language prefix, action expert, Flow Matching, hierarchical paper system, value/advantage conditioning, or evaluation.

## Establish the evidence boundary

1. Prefer the live OpenPI checkout and active config. Record repository commit, checkpoint role, adapter, normalization assets, and runtime before asserting shapes or behavior.
2. Distinguish four layers explicitly:
   - **paper system**: heterogeneous co-training plus high-level semantic subtask generation and low-level continuous action inference; π*0.6 additionally reports RECAP training with a separate value model and advantage conditioning;
   - **public OpenPI**: verify the live README before claiming model support; the official repository checked on 2026-08-27 listed π0, π0-FAST, and π0.5, not a full π0.6/π*0.6 RECAP release;
   - **checkpoint/adapter**: e.g. `pi05_base`, `pi05_droid`, or `pi05_libero`, each with different observation/action contracts;
   - **local experiment**: smoke, fixed-noise diagnostic, simulator, or robot rollout.
3. Treat local Obsidian notes and stored run records as dated analysis. Correct them when current source or official documentation supersedes them.
4. Never infer action compatibility from equal dimensions. Verify semantic names, order, units, normalization, control mode, frequency, horizon, masks, and camera roles.
5. Keep repositories, Obsidian, Data Lake, and remote model assets read-only unless the user explicitly requests a scoped write. This skill does not authorize robot motion.

## Route the question

- Read [references/current-openpi-map.md](references/current-openpi-map.md) for architecture, tensors, source paths, π0 versus π0.5 differences, and the comparison with a familiar action-only Flow Matching policy.
- Read [references/training-recipe-and-math.md](references/training-recipe-and-math.md) for the paper recipe, public-code objective, gradients, randomness, and training-versus-inference differences.
- Read [references/pi06-recap.md](references/pi06-recap.md) for π0.6 versus π*0.6, the distributional value model, advantage labeling, policy extraction, iterative robot-data loop, and open-source boundary.
- Read [references/inference-and-language-conditioning.md](references/inference-and-language-conditioning.md) for preprocessing order, prompt/state tokens, attention, Flow Matching sampling, DROID adaptation, hierarchical inference, and runtime gotchas.
- Read [references/evaluation-and-experiment-lessons.md](references/evaluation-and-experiment-lessons.md) for smoke gates, fixed-noise interventions, verified local results, cross-embodiment limits, and the next falsifiable experiment.
- Read [references/evidence-ledger.md](references/evidence-ledger.md) when a claim needs a source, date, confidence level, or Obsidian/live-code conflict resolved.

Do not load every reference for a narrow question.

## Explanation loop

For each request:

1. State the corrected mechanism in one sentence.
2. Trace the shortest real path from raw input to output with source locations.
3. Give a shape ledger using `B` (batch), `V` (camera slots), `L` (language length), `H` (action horizon), and `D_a` (internal action dimension).
4. Give the minimum useful equation and map each term to code.
5. Mark learned, frozen, sampled, masked, padded, normalized, and gradient-receiving quantities.
6. Separate what the evidence proves from what it does not.
7. End with one prediction or intervention that could falsify the explanation.

Use `$code-understanding-coach` for function-level tracing and `$math-principles-coach` for deeper derivations. Use `$robot-benchmark-loop` only when turning diagnostics into a formal benchmark.

## Non-negotiable distinctions

- Language-conditioned action generation is VLA-like, but it is not automatically high-level planning.
- π0.6 is the supervised base VLA; π*0.6 is the advantage-conditioned model trained with RECAP. Do not use the names interchangeably.
- RECAP is offline/iterative RL whose policy update retains supervised token and Flow Matching objectives; reward affects the update through value-derived advantage labels rather than a direct reward gradient through the VLA.
- The value model is principally a training-time labeler. Ordinary β=1 inference fixes the indicator to positive and does not require evaluating the value model at every action step; optional CFG is a separate inference choice.
- The paper's high-level subtask is an autoregressively generated text action; the public `policy.infer()` path accepts a supplied prompt and directly generates a continuous action chunk.
- π0.5 is end-to-end within the policy boundary, not from camera electronics to motor current; preprocessing, transport, safety, and the servo controller remain external.
- The internal action tensor may be padded to 32 dimensions while an adapter returns fewer physical dimensions.
- A random-observation smoke test proves infrastructure validity, not task competence.
- A prompt ablation proves sensitivity only when visual input, state, checkpoint, preprocessing, and Flow Matching noise are fixed. Sensitivity is not semantic correctness.
- Offline action similarity is invalid when the source robot and DROID action contracts differ.

## Gotchas

- In the tested OpenPI snapshot, `pi05_droid` config predicts `(15, 32)` internally and `DroidOutputs` returns `(15, 8)`, while the example DROID client still asserts `(10, 8)`. Re-check the live checkout before rollout.
- π0.5 tokenizes normalized state into the language prefix; zero or guessed state is not a neutral omission.
- The third DROID camera slot exists in the model tensor but is zero-filled and masked. Passing another raw camera key does not create three-camera fusion.
- The official paper's hybrid discrete pre-training and hierarchical runtime are not reproduced by merely fine-tuning the public Flow Matching head.
- Cross-GPU bfloat16/JAX results can be stable per machine yet differ slightly across architectures. Compare tolerances and behavior, not only hashes.
- Obsidian notes written before the September 2025 OpenPI release may say π0.5 code is closed; preserve that as historical context, not current truth.
- Third-party repositories that add `pi0.6` or `RECAP` code are implementations or reconstructions unless provenance proves they are an official Physical Intelligence release.

## Deliverable

Return the smallest useful subset of: corrected mental model, code path, tensor table, equation-to-code mapping, open-source boundary, verified evidence, one key limitation, and the next experiment. For a repository audit, attach `path:line` evidence from the active checkout.
