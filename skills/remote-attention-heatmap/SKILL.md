---
name: remote-attention-heatmap
description: Run the current repository's ViT attention heatmap script against one or more remote PSI policy checkpoints over SSH, pull all outputs to the current local repository, and create original-versus-model and multi-model stitched comparison images. Use whenever the user asks to 一键跑 heatmap, compare newly trained remote models, provide checkpoint paths plus a test-image directory and development-machine/SSH address, pull heatmap results locally, or 拼接原图和 attention 结果做对比.
---

# Remote Attention Heatmap

Use the bundled deterministic runner to turn remote checkpoint heatmap evaluation into one command. Keep the remote repository unchanged: the runner uploads the current local `visualization/attention_heatmap.py` to a unique remote temporary directory, executes it with the checkpoint's repository on `PYTHONPATH`, pulls a complete result bundle, and then removes only that temporary directory after a successful transfer.

## Required inputs

Collect these values from the user when they are not already present:

1. SSH host or alias for the development machine.
2. One or more checkpoint paths. Accept optional labels such as `flowmatch=/path/latest.ckpt`; otherwise derive labels from experiment directory names.
3. Remote test-image directory.

Do not ask for optional settings unless automatic discovery fails. Default to the current repository as `--local-repo`, encoder index `0`, automatic CUDA/CPU selection, and a timestamped local directory under `data/attention_heatmaps`.

## Run

From the target PSI policy repository, execute:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/remote-attention-heatmap/scripts/run_remote_attention_heatmap.py" \
  --host <ssh-host-or-alias> \
  --checkpoint '<label-1>=<remote-checkpoint-1>' \
  --checkpoint '<label-2>=<remote-checkpoint-2>' \
  --image-dir '<remote-image-directory>' \
  --local-repo "$PWD"
```

Add `--local-output <path>` only when the user names a destination. Add `--encoder-index N`, `--device cuda|cpu`, or `--remote-python <path>` only when required. Use `--keep-remote` only for debugging.

The runner requires passwordless SSH because it uses `BatchMode=yes`. It validates dependencies, checkpoint paths, image inputs, and inferred remote repository roots before model execution.

## Verify and deliver

After completion:

1. Read `manifest.json` and confirm every requested model has a successful log and the expected number of `.npy`, heatmap, and overlay files.
2. Inspect `comparisons/overview_original_and_all_models.png` with an image viewer. Also inspect one per-model pair image when alignment is important.
3. Give the user clickable absolute links to the bundle, report, all-model overview, and per-model overview images.
4. State whether CUDA or CPU was selected and mention any checkpoint-path normalization.

The bundle contains copied inputs, per-model raw heatmaps and overlays, logs, stitched comparisons, `manifest.json`, and `README.md`.

## Gotchas

- The input directory is intentionally non-recursive because the repository heatmap CLI consumes immediate image files. Stop and report an empty top level instead of silently selecting nested images.
- Normalize known TI-ONE mount spelling only after the exact path fails: `/share_data_prj/` may be mounted as `/share_data/`, and `worksapce` may actually be `workspace`. Record original and resolved paths in the manifest.
- Infer each remote repository from its checkpoint ancestors. Do not edit, pull, switch branches, or clean that repository.
- Upload the current local heatmap script on every run so local uncommitted fixes, including preprocessing corrections, are actually exercised.
- A 3-view model may share one encoder across all RGB keys. Encoder index `0` is correct for that configuration; do not assume three keys imply three separate ViTs.
- An unauthenticated Hugging Face warning is not a failure when the checkpoint finishes loading and outputs are generated.
- Automatic device selection falls back to CPU when the development machine exposes no CUDA device.
- On failure, the runner keeps its exact remote temporary directory and prints it. Do not broadly delete `/tmp` or any shared-data directory.
