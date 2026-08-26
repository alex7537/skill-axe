# Evidence Ledger

Use this file to prevent paper claims, public code, local notes, and experiments from collapsing into one level of certainty.

## Source priority

1. active repository/config/checkpoint and live runtime evidence;
2. current official OpenPI README and source;
3. official π0.5/π0 papers;
4. immutable local run artifacts and hashes;
5. dated Obsidian or Feishu analyses;
6. teaching inference or proposed hypothesis.

## Official sources

- π0.5 paper: `https://arxiv.org/abs/2504.16054`
- π0.5 official PDF: `https://www.physicalintelligence.company/download/pi05.pdf`
- OpenPI: `https://github.com/Physical-Intelligence/openpi`
- π0 paper: `https://arxiv.org/abs/2410.24164`

Paper-supported claims:

- heterogeneous co-training includes multiple robots, high-level semantic prediction, web data, and verbal instructions;
- the full system predicts a semantic subtask and then a low-level action chunk;
- the same unified model is used for high- and low-level inference;
- pre-training uses discrete action tokens and post-training introduces the Flow Matching expert.

Public-code-supported boundary:

- tested `README.md` line 8 states that OpenPI currently supports only the Flow Matching head for π0.5 training and inference;
- therefore an ordinary `policy.infer()` action call must not be described as the paper's complete hierarchical runtime.

## Local source snapshots

- live re-check date: `2026-08-26`;
- tested/deployed commit: `15a9616a00943ada6c20a0f158e3adb39df2ccac`;
- later local source snapshot observed: `215abfb217dbac7d5f1273282331b9b1866c0479`.

Always replace these with the active commit when answering a current-code question.

## Local knowledge sources

Relevant Obsidian titles include:

- `pi_0.5_Vision-Language-Action_Model_with_Open-World_Generalization.md`;
- `对于目前模型VA的理解.md`;
- `VLA_World_Model_WAM三大架构对比解析.md`;
- `具身智能模仿学习统一白皮书_VLA_WAM.md`.

The July 2026 π0.5 note is valuable for paper recipe, critique, and research questions, but its “code not open” statement did not incorporate the September 2025 OpenPI π0.5 release information present in the current checkout. Reconcile by source authority and observed repository state rather than deleting the historical note.

## Local run evidence

- Project task record: `openpi-pi05-droid-smoke-test.json` under a project-local `.codex/task-coach` directory.
- Persistent remote project was organized under a personal `openpi-pi05-droid` root with checkpoint, scripts, logs, and diagnostics.
- Stored smoke logs and the visual/language probe are evidence for infrastructure and sensitivity only.

Do not copy private SSH endpoints, credentials, raw session transcripts, checkpoints, or full private data into this skill. Resolve machine-specific paths live when execution is requested.

## Confidence labels

- **verified-current:** checked in the active checkout/runtime during this task;
- **verified-snapshot:** checked at a recorded commit/date;
- **paper-claim:** reported by authors but not reproduced locally;
- **local-diagnostic:** observed under a limited non-qualified experiment;
- **hypothesis:** plausible mechanism awaiting a falsifying experiment.

Use these labels when the distinction affects a decision.
