# Success-video gallery packaging

Use this reference only for the `Report/package` mode when rollout videos must become a traceable GIF/MP4 showcase. It does not authorize a new evaluation, change the success contract, or turn a visual gallery into benchmark evidence.

## Select defensible clips

1. Start from evaluator-produced success assets whose experiment and success profile are known. Exclude `.pending_*`, truncated, undecodable, infrastructure-invalid, and contaminated videos.
2. Freeze the success tier before viewing model outcomes. Do not silently mix 5 cm and 10 cm successes; a strict 10 cm gallery should select only filenames and records validated at that tier.
3. Balance the gallery across the intended model and execute-horizon categories. Within each category, select deterministically across ordered episode/seed values instead of taking the first or most visually dramatic clips.
4. Keep the exact basename, model, horizon, episode, seed, grid cell, selection method, and render parameters in a machine-readable manifest. Do not store a personal absolute source path.
5. State that the gallery is a showcase. Balanced clip counts do not imply equal success rates because the denominator and failures are absent.

The bundled `scripts/build_success_grid.py` implements the verified v17 layout:

```text
100 strict 10 cm clips
25 clips per model
per model: H4 × 8, H8 × 8, H16 × 9

top-left:     best EMA
top-right:    epoch-100 raw
bottom-left:  latest raw
bottom-right: RGB-only final raw
```

Blue, green, and orange borders identify H4, H8, and H16. Adapt the selector when future filename prefixes or model groups differ; do not rename inputs just to make an incompatible collection pass.

## Choose the visible time window

Inspect representative clips from every model at multiple timestamps before encoding. A success video can lift the object out of frame in its later half, so using the full duration may make a successful grid look empty. Prefer one common window that includes approach, contact, and visible lift across categories.

The verified v17 gallery used:

```text
start:      0.5 seconds
duration:   6.0 seconds
frame rate: 5 FPS
tile:       96 × 72
grid:       960 × 720
GIF palette: 128 colors
```

Treat these as proven defaults for that collection, not universal evaluation constants.

## Build

Provide an FFmpeg binary explicitly. A temporary `imageio-ffmpeg` install is sufficient when the host has no global FFmpeg and does not require changing project dependencies:

```bash
python3 -m pip install --target /tmp/a2d-video-tools imageio-ffmpeg
FFMPEG=$(PYTHONPATH=/tmp/a2d-video-tools python3 -c \
  'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')

python3 scripts/build_success_grid.py \
  --source <verified-success-video-directory> \
  --ffmpeg "$FFMPEG" \
  --gif <output>/grasp_success_grid_10x10.gif \
  --mp4 <output>/grasp_success_grid_10x10.mp4 \
  --manifest <output>/grasp_success_grid_10x10_sources.json
```

Use a separate Git worktree when the main repository has unrelated uncommitted changes. Creating assets locally does not authorize a commit or push; publish only when the user explicitly requests the remote change.

## Verify before publishing

- exactly 100 selected clips and 100 unique cells;
- expected counts for every model/horizon category;
- no pending, 5 cm, missing, or duplicate source entries;
- full MP4 and GIF decode succeeds;
- GIF includes the `NETSCAPE2.0` infinite-loop marker;
- a representative frame visibly contains grasp activity across all quadrants;
- GIF is below GitHub's hard file limit and preferably below 10 MB for README loading;
- every relative README link resolves locally;
- `git diff --check` passes;
- after publishing, remote branch SHA matches local and every asset returns HTTP 200 with the expected byte size.

Keep the MP4 even when the GIF is compact: it preserves better motion quality at much lower size. Keep original per-rollout videos outside Git unless the user explicitly requests and the repository storage policy permits them.

## Gotchas

- `100×75` looks natural for a 1000×750 grid, but the odd tile height can be chroma-rounded to 76 and make FFmpeg padding fail. Prefer even tile dimensions such as `96×72`.
- A late-only segment may show empty tables after successful objects leave the camera view. Confirm time windows visually before bulk rendering.
- A filename containing `success` or `10cm` is not enough when provenance is unclear. Reconcile it with the evaluator collection or manifest before presenting it as verified success.
- Four equal quadrants can look like a controlled comparison, but the gallery omits failures and denominators. Link the real evaluation report for performance claims.
