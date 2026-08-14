# GitHub and Hugging Face release architecture

## Ownership map

| Concern | Canonical home | Release link |
|---|---|---|
| Model architecture and training logic | GitHub | Full Git commit SHA |
| Dataset loader and evaluation implementation | GitHub | Commit plus config path |
| Released weights | Hugging Face model repo | Revision/tag plus SHA256 |
| Resolved model configuration | Hugging Face model repo | Included in release manifest |
| Preprocessing and normalization contract | Hugging Face model repo | Included beside weights |
| Large datasets | Hugging Face dataset repo or governed storage | Immutable dataset revision |
| Interactive demo | Hugging Face Space | Pin model and code revisions |
| Experiment telemetry and raw logs | Experiment tracker/private storage | Link only when access is appropriate |

GitHub explains how the model is built. Hugging Face carries what consumers load. The release manifest binds them.

## Artifact taxonomy

### Fine-tune release

Include weight-only state, architecture/config, preprocessing, normalization, dependency constraints, and a minimal load/train example. Exclude optimizer state unless the consumer explicitly needs exact resume.

### Resume checkpoint

Include model, optimizer, scheduler, global step/epoch, AMP scaler, RNG, and any sampler/data-cursor state needed by the training system. Treat it as environment-sensitive and usually private. Document whether raw and EMA weights are both present.

### Deployment release

Include only the inference graph/weights needed at runtime plus input/output schema, normalization, runtime versions, target hardware, precision, and a validated smoke test. A deployment bundle is not assumed to be trainable.

### Evaluation release

Bind a loadable artifact to exact dataset/split identities, metric implementation, evaluation command, and results. Keep diagnostic data distinct from sealed holdout results.

## Release identity

Use a human-readable release name plus immutable machine identities:

```text
model repo:      owner/model-name
release:         v1.2.0
HF revision:     immutable tag or commit
source commit:   full 40-character Git SHA
weights:         SHA256 per file
data:            dataset repo/revision or governed internal ID
config:          resolved config file plus SHA256
normalization:   file plus SHA256 when applicable
```

Use semantic versions when consumers depend on an interface. Increment:

- major for incompatible observation/action/config or architecture contracts;
- minor for a new compatible checkpoint or capability;
- patch for metadata, documentation, or packaging fixes that do not change numerical model behavior.

If the organization uses date-based releases, retain the same immutable identities and compatibility declaration.

## Repository boundaries

Prefer one primary checkpoint per Hugging Face model repository. Use a distinct repo when the checkpoint represents a different dataset, task, architecture, license, or independently cited model. Use immutable revisions within one repo for compatible packaging iterations of the same model identity.

Keep these paths separate when multiple artifact classes must coexist:

```text
/
├── README.md
├── release_manifest.json
├── config.yaml
├── normalization_stats.json
├── model.safetensors
├── evaluation/
└── deployment/
    ├── onnx/
    └── tensorrt/
```

Do not place a series of training snapshots at the repository root. Use private experiment storage until a checkpoint is selected for release.

## Maintenance lifecycle

1. Select a checkpoint by a declared criterion, not by filename alone.
2. Export into a fresh staging directory.
3. Record source/data/config/normalization identities and hashes.
4. Audit and smoke-test locally.
5. Approve destinations, visibility, license, and file scope.
6. Publish code and artifacts.
7. Download from the remote revision and verify hash plus load behavior.
8. Freeze the release identity and document any successor or deprecation.

Never mutate an immutable release to hide a regression. Publish a corrected revision and preserve provenance.
