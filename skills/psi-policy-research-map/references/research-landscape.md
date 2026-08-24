# PSI Policy Research Landscape

This map organizes the reviewed learning record by the problem each method attacks. Treat it as a navigation layer over primary sources and current PSI implementation evidence.

## 1. Action generation baseline

### Diffusion Policy

Role: generate action trajectories through conditional denoising.

The Feishu note treats Diffusion Policy as the conceptual base of Psi-C1. Its strengths are expressive trajectory generation and multimodal behavior, while its costs include iterative denoising latency and a more difficult policy-gradient/RL path.

Primary source identifier in the note: arXiv `2303.04137`.

### Immiscible Diffusion

Role: improve diffusion training through noise-to-sample assignment rather than arbitrary mixing.

The note claims this can accelerate training and improve generation with little downside. Verify the matching objective, assignment cost, batch-size sensitivity, and whether gains transfer from image generation to action trajectories before adopting it as a universal improvement.

Primary source identifier in the note: arXiv `2406.12303`.

### Flow Matching

Role: learn a conditional vector field transporting noise to an action distribution.

The note uses one-step Flow Matching as a speed and modality-coverage comparator. Do not reduce Flow Matching to “fast Diffusion”: compare interpolation, target vector field, integration steps, conditioning, and the evaluation protocol.

## 2. Coverage and sample efficiency

### IMLE Policy and Conditional RS-IMLE

Role: cover real-data modes by matching each real trajectory to an appropriate generated candidate.

The learning record highlights four expected benefits:

- minority-mode and multimodal coverage;
- improved low-data behavior;
- action generation without a diffusion-style multi-step denoising path;
- easier integration with RL and HIL because the policy directly emits actions.

It reports Push-T, UR3 block-push, shoe-racking, and inference-speed comparisons. These are Feishu paper-note claims until checked against arXiv `2502.12371` and its official evaluation code.

PSI hypothesis: RS-IMLE can be the action-generation objective while a shared model also predicts future representation and return. This is a proposal unless verified in the active repository.

## 3. Implicit world modeling

### FLARE

Role: align policy representations with future visual-language features while predicting actions.

The note treats FLARE as evidence that action learning and future-latent prediction can share a model. It also distinguishes the PSI proposal: RS-IMLE action output plus JEPA-style future-latent/return prediction is similar in motivation but not identical in objective or architecture.

Primary source identifier: arXiv `2505.15659`.

### V-JEPA 2

Role: learn predictive video representations for understanding, prediction, and planning without reconstructing every pixel.

Transferable question for PSI: does a future-feature target improve action learning or closed-loop planning relative to action-only and generative-video supervision?

Primary source identifier: arXiv `2506.09985`.

### TD-MPC2

Role: combine latent dynamics, value learning, and planning.

Use it as a reference for task-relevant latent prediction and planning, not as proof that any future-latent auxiliary loss yields model-based control.

Primary source identifier: arXiv `2310.16828`.

### Action-free pretraining

The note proposes using non-robot video to pretrain an implicit world model. This requires a clear transfer contract: which representation is learned without actions, how robot actions are attached later, and whether the representation captures controllable rather than merely predictable factors.

## 4. VLM as value or reward

### In-context value learning / GVL

Role: use a VLM to estimate task progress or rank trajectory quality.

The reviewed mechanism has three parts:

1. autoregressive progress prediction to encourage global consistency;
2. shuffled frames with an initial-frame anchor to reduce reliance on chronological shortcuts;
3. in-context frame/progress examples for cross-task or cross-embodiment transfer.

This is promising for trajectory ranking, HIL filtering, and return supervision. It is not a valid reward until it distinguishes success, regress, recovery, visually similar failure, and reversed task direction under controlled tests.

## 5. Retrieval and data weighting

### R3M and graph-search retrieval

Role: embed observations, construct state/trajectory relations, estimate reachability or value, and reweight imitation data.

The note describes a pipeline of representation fine-tuning, graph construction, neighbor retrieval, value estimation, and weighted behavior cloning. Some included code is explicitly a simplified approximation; do not treat it as a faithful paper implementation.

Primary source identifier for R3M: arXiv `2203.12601`.

### TRAP and COLLAGE

The titles appear as related sub-trajectory retrieval and adaptive fusion directions. The reviewed excerpts did not provide enough evidence to summarize their algorithms. Read the primary papers before comparing them with graph-search weighting or using their names in an experiment plan.

TRAP identifier recorded in the note: arXiv `2412.15182`.

## 6. Recovery and Correction

### RaC

Role: improve long-horizon robustness through structured human intervention data.

- **Recovery:** move from a likely failure/OOD state back toward a familiar in-distribution state.
- **Correction:** complete or advance the subtask after recovery.

The note's key lesson is that data composition matters: successful demonstrations alone do not teach failure recovery. It also argues that standardized intervention rules avoid mixing incompatible human behaviors.

PSI reflection in the note:

- action OOD may be recoverable by returning to a familiar state;
- object/environment OOD may require correction or new task knowledge;
- rollback ability can be more practical than demanding perfect one-shot execution.

Primary source identifier: arXiv `2509.07953`.

## 7. One coherent PSI research hypothesis

The document suggests—but does not prove—the following progression:

```text
expressive action generation
  -> better mode coverage and one-step action output
  -> future-latent and return prediction
  -> VLM-based trajectory/value assessment
  -> retrieval/reweighting of useful experience
  -> structured recovery and correction data
  -> RL/HIL for long-horizon robustness
```

Each arrow is an empirical hypothesis. Test components independently before composing them into one large system.

