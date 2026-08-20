# Robbyant LingBot-World comparison notes

Use this reference only when comparing PSI WAM with Robbyant's public world-model work or when designing an experiment inspired by it. It is external evidence, not a map of the PSI repository.

## Evidence snapshot

- Reviewed: 2026-08-20.
- Primary implementation: `Robbyant/lingbot-world-v2`, commit `2648877f763a06cc743bcd919936da4d25f12e7b`.
- Predecessor: `Robbyant/lingbot-world`; its README says it is no longer actively maintained and directs users to v2.
- Adjacent but distinct: `Robbyant/lingbot-vla-v2` uses future perceptual prediction as an auxiliary/distillation signal for an action policy. Do not treat that VLA design as the LingBot-World video simulator or as PSI WAM.
- Public v2 status at review time: 14B causal-fast inference code and weights are released. The 14B causal-pretrained weights, bidirectional model, 1.3B variants, training code, and deployment code are not all publicly released. Claims about those components therefore come from the technical report or README, not a reproducible public training implementation.

Sources:

- Repository: https://github.com/Robbyant/lingbot-world-v2
- Technical report: https://arxiv.org/abs/2607.07534
- Predecessor: https://github.com/Robbyant/lingbot-world
- VLA 2.0: https://github.com/Robbyant/lingbot-vla-v2

## Do not collapse the model roles

| Dimension | LingBot-World 2.0 | PSI WAM orientation snapshot |
|---|---|---|
| Primary output | Future video/world states | Future video latents and robot actions |
| Action/control input | Camera poses plus time-localized text prompts | Robot state, noisy future action tokens, language, and robot identity |
| Action prediction | Not the released simulator's stated objective | Explicit Flow Matching action head |
| Core use | Interactive visual world simulation | Robot-policy learning with auxiliary future-video generation |
| Rollout interface | Autoregressive video chunks with KV cache | Joint video/action sampling and shallow closed-loop policy rollout |

The transferable ideas are about causal conditioning, rollout drift, data alignment, and evaluation. Tensor shapes, action semantics, loss ownership, and deployment behavior are not transferable facts.

## High-signal lessons

### Align training conditions with interactive inference

LingBot-World combines global scene context with chunk-wise local captions because a single global caption does not match an interface whose instruction changes during a rollout. It also uses synthetic/game data when precise, temporally aligned control signals are hard to infer from web video.

For PSI WAM, test whether task-level text is too coarse for within-trajectory state changes. If subtask boundaries or action phases exist, compare global text with time-localized conditioning under the same split and budget. Do not add generated captions without auditing temporal leakage and visual grounding.

### Make causality a training contract

The report factorizes each visual state as conditioned on past visual context and controls up to the current time. It uses causal self-attention and lower-triangular prompt access so future semantics cannot leak into the current prediction. Its MoBA proposal mixes a teacher-forced causal component with a bidirectional component; the authors report that pure teacher forcing can over-rely on a long clean context and degrade generation quality.

For PSI WAM, separately audit video-prefix masking, future-action corruption, text/subtask timestamps, and any full-clip attention path. A causal VAE alone does not prove the joint DiT or conditioning path is leak-free.

### Optimize and evaluate on self-induced states

The reported real-time student combines consistency distillation for few-step sampling with distribution-matching distillation over long student self-rollouts. The important general lesson is not the specific distillation recipe: deployment feeds model outputs back as future inputs, so teacher-forced one-step quality is an incomplete objective and metric.

For PSI WAM, compare teacher-forced, one-step, and recursive rollout performance. Record error versus rollout depth and intervene on actions while holding the visual prefix fixed. If adding self-rollout training, make it a bounded ablation rather than assuming it will improve robot control.

### Separate stability, memory, identity, and physics

The report explicitly says visually stable long rollouts are not genuine long-term memory: content outside the context window may be regenerated rather than recalled. It also lists character/style drift and imperfect collision/geometry as remaining limitations.

Do not label low perceptual drift as memory, object permanence, causal action following, or physical correctness. Evaluate these properties separately.

### Treat cache policy as a bounded-memory design

The released inference code generates latent chunks autoregressively, writes the final denoised chunk into a per-layer KV cache, preserves an initial attention sink, and evicts older non-sink tokens when the local cache fills. This supports bounded compute, but by construction it cannot retain every past detail.

This is relevant to a future streaming PSI WAM runtime, not automatically to the current fixed-horizon training path. Measure latency, memory, action quality, video quality, and revisit consistency before adopting a cache scheme.

### Keep the agentic harness outside the learned dynamics claim

LingBot-World wraps the generator with pilot/director agents that propose character actions and environmental events. This expands planning and interaction orchestration, but it is not evidence that the video generator itself learned planning, durable memory, or physically grounded state.

For PSI WAM, distinguish policy/world-model capability from external planners, prompt generators, safety logic, or task orchestration.

## Candidate PSI experiments

1. **Temporal-condition ablation:** global task text versus phase/subtask-local text, with a leakage audit and matched data.
2. **Causality audit:** perturb future captions/actions and verify earlier predictions are invariant within numerical tolerance.
3. **Rollout-depth curve:** report video, action-block, and task metrics at teacher-forced, one-step, and recursive depths.
4. **Action intervention:** hold prefix and language fixed, change one action block, and measure whether the predicted visual consequence changes in the intended region and time.
5. **Memory-versus-stability test:** leave and revisit a scene/object; score identity retrieval separately from short-range visual smoothness.

## Gotchas

- The repository's one-hour result is a qualitative stress test in the report, not proof of exact state recall or robot-simulation validity.
- The 720p/60-fps claim describes the optimized distilled system; the public repository does not include the full deployment stack.
- `causal-fast` inference code does not expose the full causal pretraining or DMD training implementation, so do not infer unshown optimizer, data mixture, or loss details from inference code.
- Camera poses and semantic prompts are controls, but they are not PSI's 82D robot action targets.
- A fixed attention sink plus recent local context is not the same as learned episodic memory.
