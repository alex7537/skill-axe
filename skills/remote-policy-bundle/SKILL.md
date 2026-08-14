---
name: remote-policy-bundle
description: Export one or more remote robot-policy training checkpoints into self-contained deployment bundles over SSH, pull the archives into the current local repository, and verify archive contents, manifest provenance, internal file hashes, and remote/local SHA256 equality. Use when the user asks to 拉取 bundle 到本地, package a remote ckpt for rollout, download raw/EMA policy artifacts, collect several best/periodic checkpoints for testing, or prepare deployable `.tgz` files from a TI-ONE/development machine.
---

# Remote Policy Bundle

Use the bundled runner for the fragile export-transfer-verify sequence. Keep training checkpoints remote; deliver only self-contained deployment archives unless the user explicitly asks for full resumable `.ckpt` files.

## Inputs

Resolve these from the conversation or ask only for missing required values:

- SSH host or alias.
- One or more remote `.ckpt` paths.
- Raw or EMA weights for each checkpoint.
- Local repository/output directory when the current repository is not the desired destination.

Accept checkpoint specifications as:

```text
/remote/run/best_action_mse.ckpt
raw-best=/remote/run/best_action_mse.ckpt
ema-best:ema=/remote/run/best_ema_action_mse.ckpt
```

An omitted variant uses `--weights-variant`, whose default is `raw`.

## Run

From the target local repository:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/remote-policy-bundle/scripts/pull_remote_policy_bundle.py" \
  --host <ssh-host-or-alias> \
  --checkpoint '<label>:<raw-or-ema>=<remote-checkpoint>' \
  --local-repo "$PWD"
```

Repeat `--checkpoint` for multiple candidates. Add `--remote-repo` or `--remote-python` only if automatic discovery fails. Add `--local-output` only when the user names a destination. Forward model-specific exporter values with `--execute-horizon`, `--num-inference-steps`, `--data-version`, or `--checkpoint-selection` when required.

The script performs read-only checkpoint inspection plus a temporary remote export. It:

1. verifies passwordless SSH and every checkpoint;
2. finds the remote repository and Python environment;
3. exports each archive in a unique remote temporary directory;
4. downloads to a `.partial` local file;
5. compares remote and local archive SHA256;
6. validates required bundle files, manifest fields, and internal hashes;
7. atomically renames the verified local archive;
8. writes `download_manifest.json` and removes only its unique remote temporary directory.

## Verify and deliver

Read the generated `download_manifest.json`. Report:

- clickable absolute paths to every `.tgz`;
- label, raw/EMA variant, source epoch and step;
- archive SHA256;
- manifest checkpoint-selection criterion;
- any path normalization or explicit overrides.

Do not claim success when only a `.partial` file exists.

## Gotchas

- A deployment bundle is not a resumable training checkpoint: it normally omits Adam, scheduler, RNG, and full EMA training state.
- Prefer `best_action_mse.ckpt`, `best_ema_action_mse.ckpt`, or an explicitly selected periodic checkpoint over `latest.ckpt`; never assume the final epoch is best.
- `weights_variant=ema` requires a checkpoint containing EMA weights. Let the exporter fail rather than silently falling back to raw.
- Require passwordless SSH because transfers run non-interactively.
- Never overwrite an existing verified archive. Choose a new output directory or label.
- On failure, retain `.partial` and the exact remote temporary directory for diagnosis. Never broadly delete `/tmp`, a run directory, or shared storage.
- An absent remote `git` binary is acceptable only when the repository exporter safely records `git_sha: null`.
- Do not store SSH keys, API keys, W&B credentials, signed URLs, or raw session transcripts in this skill or generated manifests.
