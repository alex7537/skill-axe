# Robot ML lifecycle contract

## Phase gates and owners

| Phase | Primary owner(s) | Minimum evidence to resolve |
|---|---|---|
| `frame` | `adaptive-task-coach` | objective, acceptance criteria, constraints, terminal phase |
| `source` | `sync-follow-branch` or Git inspection | repository, branch, full commit, dirty-state decision |
| `understand` | `understand-codebase`, `code-understanding-coach`, `math-principles-coach` | execution path/hypothesis plus verification plan or result |
| `labels` | `seg-label-audit` | label contract, quarantine/valid-frame manifest and gate |
| `split` | `dataset-split-protocol` | role manifests, hashes, exposure state and gate |
| `train_plan` | `plan-training-run` | resolved sample/step/LR/evaluation/checkpoint plan |
| `infrastructure` | `tcr-image-publish`, `tione`, `tione-ssh-diagnose` | image digest and/or verified compute endpoint/task payload |
| `train` | `tione` plus repository trainer | task/instance ID, resolved config, logs, checkpoint provenance |
| `evaluate` | repository evaluator plus dataset exposure contract | frozen eval contract, per-checkpoint metrics, decision |
| `package` | `remote-policy-bundle` | verified archive, manifest and remote/local SHA256 equality |
| `release` | `publish-model-release` | Git/HF revisions, file hashes, model card, load smoke test |
| `capture` | `capture-session-to-skill`, `skill-authoring` | captured/updated Skill or explicit no-capture decision |

Phases may be `skipped` when they genuinely do not apply. Example: skip `labels` for a dataset with no label trust question, or `package` when the terminal outcome is an internal evaluation. Record why.

## Handoff contract

Pass artifacts, not conversational conclusions. Every handoff should identify:

```text
producer skill
artifact path or remote identifier
artifact schema/version when applicable
SHA256 or immutable revision
gate status
limitations and unresolved questions
consumer skill
```

Prefer these durable artifacts:

- label decision/quarantine and valid-frame manifests;
- role/split manifest and exposure ledger;
- resolved training plan and configuration hash;
- Docker manifest digest;
- TI-ONE task and instance IDs;
- checkpoint path, selection rule, raw/EMA role, and hash;
- evaluation manifest with dataset/split/metric identities;
- deployment bundle manifest and archive hash;
- GitHub commit and Hugging Face immutable revision.

## Routing decisions

### Where a failed evaluation loops

Return to the earliest phase whose assumption is invalidated:

- label semantics or annotation holes → `labels`;
- leakage, imbalance, exposure, or domain coverage → `split`;
- insufficient/incorrect step or LR schedule → `train_plan`;
- implementation, shape, preprocessing, or objective bug → `understand`;
- infrastructure/runtime-only failure → `infrastructure` or `train`;
- metric/evaluator bug → `evaluate`.

Do not restart at `frame` unless the objective or acceptance criteria changed.

### Promotion gate

Promote a checkpoint only when:

1. checkpoint provenance and load behavior are verified;
2. evaluation dataset/split and exposure state are explicit;
3. primary and safety/failure metrics meet the frozen rule;
4. comparison baselines use a defensible contract;
5. checkpoint selection did not consume an alleged sealed holdout;
6. known limitations are recorded.

### External write gates

Require explicit confirmation for:

- Git push, PR, tag, or release;
- TI-ONE create/start/stop/modify/delete;
- TCR upload or publication;
- opening a sealed holdout;
- Hugging Face repo creation, upload, visibility change, or deletion;
- deletion of remote checkpoints, bundles, images, logs, or manifests.

Authentication and previously approved read-only inspection do not imply approval for these writes.

## Lifecycle state versus task state

Use the `adaptive-task-coach` task state for milestones, blockers, user learning, and delivery progress. Use the lifecycle ledger for immutable experiment provenance and phase gates. Cross-reference their paths when both exist; do not duplicate all fields in both files.
