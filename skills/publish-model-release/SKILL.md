---
name: publish-model-release
description: Design, prepare, audit, publish, and maintain reproducible machine-learning model releases with source code on GitHub and weights/artifacts on Hugging Face Hub. Use when the user asks where checkpoints, deployment bundles, configs, normalization statistics, evaluation scripts, or model cards should live; wants to upload or version a model; wants others to fine-tune, resume, evaluate, or deploy it; or needs a GitHub-to-Hugging-Face release contract. For remote robot-policy checkpoint export, use $remote-policy-bundle first and consume its verified output here.
---

# Publish Model Release

Treat a model release as a traceable link between source code, immutable weights, runtime contracts, and evidence—not as a lone checkpoint upload.

## Establish the release intent

Determine which consumer must work:

- `finetune`: weights plus architecture, configuration, preprocessing, normalization, and training interface;
- `resume`: full training state including optimizer, scheduler, step, scaler, and RNG where applicable;
- `deploy`: self-contained inference artifact plus input/output and runtime contracts;
- `evaluate`: loadable artifact plus dataset/split identity, metric definitions, and evaluation command.

Allow one release to support multiple intents, but name one primary intent. Do not claim resumability from a deployment bundle or fine-tune readiness from weights alone.

Read [references/architecture.md](references/architecture.md) when deciding repository ownership, release boundaries, versioning, or maintenance policy. Read [references/release-contract.md](references/release-contract.md) before creating or auditing release files.

## Inspect before preparing

Resolve from the repository and artifacts before asking the user:

- source repository URL and exact Git commit;
- candidate checkpoint or verified deployment bundle;
- model architecture/config and preprocessing entry points;
- normalization or calibration statistics;
- evaluation command, split identity, and reported metrics;
- target GitHub/Hugging Face repository IDs, visibility, and license.

Keep inspection read-only. Never load an untrusted pickle checkpoint merely to inspect it. Prefer manifest/state-dict metadata, safe tensor inspection, or the project's own trusted exporter.

## Apply the ownership boundary

Use GitHub as the canonical home for reviewable source:

- model definitions, training/data/evaluation code;
- environment and configuration schemas;
- tests, CI, documentation, and migration logic.

Use one Hugging Face model repository as the canonical home for one primary released checkpoint:

- weights or a verified deployment archive;
- resolved model/configuration and preprocessing contract;
- normalization statistics required to reproduce outputs;
- release manifest and model card;
- compact evaluation results and a link to the exact GitHub commit.

Do not duplicate a live source tree into the model repository unless custom loading genuinely requires it. Do not publish datasets, raw training checkpoints, caches, logs, secrets, or optimizer state by default.

## Prepare a staged release

Copy `assets/model-release-template/` into a new staging directory; never edit a training run directory in place. Replace every placeholder and remove examples that do not apply.

Create an immutable release identity with:

- GitHub repository URL and full commit SHA;
- artifact role and weight variant such as raw or EMA;
- SHA256 for every published weight/archive;
- configuration and normalization identity;
- training-data provenance that reveals no private paths or credentials;
- evaluation dataset/split and metric definitions;
- compatibility and license constraints.

Prefer `safetensors` for portable weight-only publication when the project supports lossless export and verified reload. Preserve `.ckpt` only when exact training resume is an explicit requirement. Keep ONNX/TensorRT artifacts as target-specific variants, not the only canonical trainable release.

## Audit locally

Run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/publish-model-release/scripts/audit_model_release.py" \
  <staging-directory> \
  --intent <finetune|resume|deploy|evaluate> \
  --require-normalization
```

Omit `--require-normalization` only when the model mathematically and operationally has no learned/data-derived normalization. Resolve all errors; explain any remaining warnings. For machine-readable output, add `--json`.

The audit is necessary but not sufficient. Also run the documented loader/inference smoke test in a clean environment when feasible.

## Publish through explicit write gates

Before any external write, show:

- exact GitHub and Hugging Face destinations;
- public/private visibility and license;
- staged file list and total size;
- audit result and smoke-test evidence;
- commands to run and whether a repository will be created.

Require explicit user approval before creating repositories, uploading files, changing visibility, publishing a release/tag, deleting remote files, or overwriting a mutable alias. Authentication alone is not publication authorization.

After approval, publish code through the installed GitHub workflow and artifacts with the locally supported `hf upload` syntax. Derive commands from `hf upload --help`; do not expose tokens in arguments or logs.

## Verify the remote release

Do not stop at a successful upload process. Verify:

1. remote files and visibility match the approved scope;
2. remote revision resolves to the intended release;
3. a fresh download matches the recorded SHA256;
4. the documented load or inference command succeeds;
5. GitHub commit, Hugging Face revision, model card, license, data provenance, and metrics cross-reference each other.

Report exact repository URLs, revisions, hashes, supported intents, and known limitations.

## Maintain releases

- Create a new model repository when architecture, training dataset, task contract, or independently meaningful checkpoint identity changes substantially.
- Use immutable tags/revisions for released artifacts; never silently replace a published weight under the same release identity.
- Keep experimental periodic checkpoints private or in a clearly non-release area.
- Deprecate with a model-card notice and successor link; do not delete a public artifact without explicit approval and impact review.
- Re-run the audit and smoke test whenever weights, config, normalization, loader code, or dependency constraints change.

## Gotchas

- A Hub repository accepts arbitrary files; upload success does not imply loadability, fine-tune readiness, or reproducibility.
- A `.ckpt` extension has no standard internal contract and may contain unsafe pickle data.
- Missing normalization, camera order, action representation, horizon, or control frequency can make robot-policy weights unusable even when loading succeeds.
- Optimizer/scheduler state is for exact resume, not a default public release requirement.
- Model metrics are invalid without the dataset version, split identity, metric definition, and evaluation commit.
- Public visibility and an explicit license are separate decisions; public files without clear licensing are not automatically reusable.
- Never store access tokens, SSH keys, signed URLs, private absolute paths, raw session transcripts, or proprietary dataset samples in release artifacts.
