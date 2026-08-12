# Project-Based Coding Progression

Use this reference only for sustained coaching plans. Keep daily work anchored to the current repository.

## Weeks 1–4: Read and modify

Target evidence:

- Trace a real function from caller to consumer.
- Explain lists, dictionaries, branches, functions, classes, imports, and object state in context.
- Track NumPy/PyTorch shapes through indexing, reshape, transpose, broadcast, and batching.
- Read a traceback from the final exception back to the first incorrect assumption.
- Use logs, breakpoints, focused assertions, and `git diff`.
- Predict one behavioral change before editing, then verify it.

Daily unit:

1. Choose one real function.
2. State input, output, shapes, side effects, and pipeline role.
3. Predict the effect of one change.
4. Run a focused experiment.
5. Rewrite the key 10–30 lines.

## Weeks 5–8: Build a minimum training loop

Require the learner to assemble and explain:

```text
Dataset → DataLoader → Model → Loss → Backward → Optimizer → Evaluation
```

Prefer a small MLP, behavior-cloning, or trajectory-prediction task. Judge success by independent explanation and controlled debugging, not benchmark quality.

Checkpoints:

- batch schema and every tensor shape;
- train/eval mode and gradient ownership;
- loss scalar construction;
- `zero_grad`, `backward`, and `step` ordering;
- overfit-one-batch test;
- held-out evaluation and a deliberately broken baseline.

## Weeks 9–12: Own one real improvement

Choose one bounded deliverable such as:

- trajectory smoothness, jerk, or drift metrics;
- PERCEPTION/DRIFT/JITTER failure taxonomy;
- unified IMLE vs Flow Matching evaluation;
- visual perturbation and robustness reporting;
- alignment of robot video, actions, timestamps, and success labels.

Require a reproducible command, documented metric definition, baseline comparison, failure examples, and a short conclusion separating evidence from speculation.

## Progress rubric

Advance when the learner can:

1. predict before running;
2. explain the relevant data path without reading a generated answer;
3. write or reconstruct the core block;
4. design a test that could falsify the hypothesis;
5. recover from one injected bug using logs or a debugger.
