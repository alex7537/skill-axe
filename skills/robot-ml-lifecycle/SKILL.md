---
name: robot-ml-lifecycle
description: Orchestrate an end-to-end robot-learning or embodied-AI project across source synchronization, repository understanding, label and dataset gates, training-budget design, TI-ONE infrastructure and training, evaluation, checkpoint packaging, Hugging Face release, and reusable-skill capture. Use when the user asks to run or continue a complete training loop, coordinate several installed robot-ML skills, decide the next experiment from evidence, recover a stalled project, or maintain traceability from Git commit and data split through checkpoint and release. Compose the specialized skills; do not replace their domain logic.
---

# Robot ML Lifecycle

Own the lifecycle state and handoffs. Delegate domain decisions and deterministic operations to the specialized Skills that already own them.

## Operating contract

- Use `$adaptive-task-coach` for the user-facing project plan and learning track. Use this Skill's ledger for experiment provenance and phase gates.
- Keep completed evidence immutable. Start a new cycle when a result sends the work back to code, data, or training design.
- Keep at most one phase `in_progress` in a cycle.
- Advance only from observable evidence: manifest, hash, Git commit, task ID, checkpoint, log, metric, digest, or verified artifact.
- Distinguish explanation from authorization. Never infer permission to create cloud resources, start training, open a holdout, publish an image/model, push Git, or delete anything.
- Read [references/lifecycle-contract.md](references/lifecycle-contract.md) for phase gates, handoff artifacts, and routing rules.

## Initialize or resume

For work spanning multiple phases, create a project-local ledger:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/robot-ml-lifecycle/scripts/lifecycle_ledger.py" init \
  --path <project>/.codex/robot-ml-lifecycle.json \
  --project <project-name> \
  --objective '<observable objective>'
```

If the ledger exists, run `show` and reconcile it with current Git, data, TI-ONE, checkpoint, and release state. Do not overwrite it or reconstruct completed evidence from memory.

Use `next` to identify the first unresolved phase. A phase may be explicitly `skipped` only with evidence explaining why it does not apply.

## Route each phase

### 1. Frame and source

- Use `$adaptive-task-coach` to define acceptance criteria and milestones.
- Use `$sync-follow-branch` when the repository must safely follow another branch while preserving local work.
- Record repository URL, branch, full Git commit, dirty-state decision, and relevant environment identity.

### 2. Understand and change

- Use `$understand-codebase` to map an unfamiliar repository or trace an execution path.
- Use `$code-understanding-coach` for function/tensor-level modification and verification.
- Use `$math-principles-coach` when the unresolved question concerns objectives, gradients, probability, train/inference differences, or metrics.
- Keep hypotheses falsifiable and attach each code change to a test or experiment.

### 3. Gate labels and data

- Use `$seg-label-audit` when masks, pseudo-labels, empty annotations, or label semantics are involved.
- Feed its quarantine and valid-frame manifests into `$dataset-split-protocol`.
- Record dataset revision, label-rule hash, split-manifest hash, exposure ledger, holdout state, and gate result.
- Never use heatmaps, failure review, or checkpoint selection on a sealed holdout.

### 4. Plan training

- Use `$plan-training-run` to determine effective samples, steps, epochs, LR schedule, evaluation cadence, and stop/extend rules.
- Bind the plan to the exact Git commit, data/split hashes, resolved configuration, seed, and comparison baseline.

### 5. Prepare infrastructure and run

- Use `$tcr-image-publish` only when a new Docker/OCI image must be published; record the immutable image digest.
- Use `$tione` to inspect or draft the exact task payload. Require approval before create/start/stop/delete operations.
- Use `$tione-ssh-diagnose` only when endpoint, host-key, or user-key authentication fails.
- Record TI-ONE task/instance IDs, image digest, resource configuration, resolved launch config, logs, checkpoints, and termination reason.

### 6. Evaluate and decide

- Freeze checkpoint, dataset/split, preprocessing, metric implementation, and failure policy before evaluation.
- Use repository-native evaluation commands and `$dataset-split-protocol` exposure rules. Use `$remote-attention-heatmap` only as diagnostic evidence.
- Record metrics by checkpoint and data slice, runtime validity, failure taxonomy, checkpoint-selection rule, and decision: `retry`, `promote`, or `stop`.
- If the decision is `retry`, create a new ledger cycle from the earliest invalidated phase. Do not rewrite the old cycle.

### 7. Package and release

- Use `$remote-policy-bundle` to export and verify selected remote robot-policy checkpoints.
- Use `$publish-model-release` to bind GitHub source, Hugging Face artifacts, configs, normalization, evaluation evidence, license, revisions, and hashes.
- Require separate approval for every external publication target.

### 8. Capture learning

- After a verified milestone, use `$capture-session-to-skill` to decide whether a failure mode or workflow should update an existing Skill or create a new one.
- Use `$skill-authoring` only for the actual Skill design/update.
- Keep tokens, private paths, raw sessions, and machine-local config out of portable artifacts.

## Record evidence

Record phase status immediately after verification:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/robot-ml-lifecycle/scripts/lifecycle_ledger.py" record \
  --path <project>/.codex/robot-ml-lifecycle.json \
  --phase train \
  --status passed \
  --skill tione \
  --evidence 'Task completed and selected checkpoint exists' \
  --artifact task_id=train-... \
  --artifact checkpoint=/verified/path/best.ckpt
```

Start a new immutable cycle after a retry decision:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/robot-ml-lifecycle/scripts/lifecycle_ledger.py" new-cycle \
  --path <project>/.codex/robot-ml-lifecycle.json \
  --from-phase train_plan \
  --reason 'Validation regression requires a shorter schedule'
```

## Close

Close only when the requested terminal outcome has evidence. A research iteration may close at `evaluate`; a deployable handoff requires `package`; a public reusable result requires `release`. Report:

- active cycle and terminal phase;
- immutable source/data/config/task/checkpoint/release identities;
- gate outcomes and evaluation decision;
- unresolved risks and exact resume phase;
- reusable findings captured or intentionally left uncaptured.

## Gotchas

- A successful TI-ONE task is not proof of model quality; evaluation is a separate gate.
- A low validation loss is not automatically a promotion decision.
- Diagnostic heatmaps expose data and can invalidate holdout independence.
- A deployment bundle is not an exact-resume checkpoint.
- Upload completion is not release verification.
- Do not embed every specialist procedure here; route to the owner Skill and record its output contract.
