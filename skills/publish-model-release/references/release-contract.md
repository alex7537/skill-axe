# Model release contract

## Required files

Every release must contain:

- `README.md`: model card with intended use, limitations, provenance, load/evaluate instructions, metrics, and license;
- `release_manifest.json`: machine-readable identity and file hashes;
- at least one weight or deployment artifact;
- a resolved model configuration, either as its own file or a clearly versioned built-in configuration.

Robot policies and other normalized control models must also contain normalization statistics unless normalization is provably absent. Include observation keys/order, image preprocessing, action representation, horizon, and control frequency in config or the model card.

## Recommended manifest shape

```json
{
  "schema_version": 1,
  "model_id": "owner/model-name",
  "release": "v1.0.0",
  "artifact_type": "finetune",
  "source": {
    "git_url": "https://github.com/owner/repository",
    "git_commit": "0000000000000000000000000000000000000000"
  },
  "weights": [
    {
      "path": "model.safetensors",
      "sha256": "64 lowercase hexadecimal characters",
      "role": "policy",
      "variant": "ema",
      "format": "safetensors"
    }
  ],
  "config": {
    "path": "config.yaml",
    "sha256": "64 lowercase hexadecimal characters"
  },
  "normalization": {
    "path": "normalization_stats.json",
    "sha256": "64 lowercase hexadecimal characters"
  },
  "data": {
    "id": "dataset repository/revision or governed dataset ID",
    "split": "training split identity"
  },
  "evaluation": {
    "dataset_id": "dataset/revision",
    "split": "test",
    "command": "python -m package.evaluate --config config.yaml",
    "metrics": {}
  },
  "compatibility": {
    "python": ">=3.10",
    "framework": "pytorch",
    "framework_version": "replace-me"
  },
  "license": "replace-me"
}
```

Use real file hashes before publishing. Do not put tokens, credentials, private paths, signed URLs, or confidential dataset samples in any manifest value.

## Model card acceptance criteria

The model card must let a new consumer answer:

1. What does this model do, and what must it not be used for?
2. Which exact source commit, base model, data revision, and checkpoint-selection rule produced it?
3. How are inputs preprocessed and outputs interpreted?
4. How can it be loaded, fine-tuned, evaluated, or deployed—and which of these are unsupported?
5. Which metrics were computed with what implementation and split?
6. What license, access, safety, hardware, and dependency constraints apply?

For custom architectures, link the GitHub source and provide a minimal executable loader. A weight filename alone is not a loader contract.

## Visibility and licensing

Choose visibility and license separately:

- private: access is restricted, but provenance and licensing still matter internally;
- gated: require an explicit access workflow where supported and appropriate;
- public: anyone can download, but reuse rights still depend on the license and upstream dependencies.

Check source-code, base-model, dataset, and third-party component licenses before publication. Stop for user/legal review when rights are unclear.
