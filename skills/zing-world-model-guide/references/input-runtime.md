# Zing-0.5 input and runtime contract

This reference describes upstream commit `8dd446798f2dec160351c17484c53e8deaaf7ef4`.

## Required model layout

```text
Zing-0.5/
├── generator/
│   └── model.pt
└── pretrained/
    ├── text_encoder/
    ├── tokenizer/
    └── vae/
```

`model.pt` must be an existing `.pt` file whose top-level object is a non-empty mapping from string names directly to tensors. `load_state_dict(..., strict=True, assign=True)` requires exact names and shapes.

## Minimal T2V JSONL line

```json
{"sample_id":"demo","messages":[{"role":"user","type":"text","content":"A quiet lake at sunrise"},{"role":"target","type":"video","reference_frame_count":0,"output":{"frames":121,"height":480,"width":832},"controls":[]}]}
```

Each nonblank JSONL line is an independent rollout and must contain exactly one `user/text` and one `target/video` message. Unknown top-level metadata is tolerated, but forbidden `frames` or `latent` fields directly on the target are rejected.

## TI2V differences

- Set `reference_frame_count` to `1`.
- Set `uri` to an existing local image. It is converted to RGB and bicubic-resized to the output dimensions.
- `output.frames` is the number of newly generated frames; the recorded result prepends the reference image.

## Dimension and time equations

For released config, spatial dimensions must be multiples of `VAE scale 16 × generator patch 2 = 32`.

Let `R` be `reference_frame_count` and `G` be `output.frames`:

```text
total_pixel_frames = R + G
(total_pixel_frames - 1) mod 4 = 0
total_latent_frames = 1 + (total_pixel_frames - 1) / 4
```

Because temporal patch size is one, every resulting latent-frame count is patch-aligned. Examples: T2V commonly uses `G=121`; TI2V commonly uses `G=120`; both produce 31 latent frames.

## Keyboard actions

Control type: `keyboard_direction_frame_interval`.

- Shape is `[N,8]`, ordered W/A/S/D/I/J/K/L.
- Values must be finite in `[0,1]`; simultaneous/fractional values pass validation.
- T2V expects `N=G-1`; TI2V expects `N=G`.
- The processor inserts any reference transition offset, then reshapes every four pixel transitions into one latent action window `[1,F_lat,4,8]`.
- At most one action control is allowed.

`action_keys` appears in examples but is not read by the runtime; column order is fixed by contract, not dynamically derived from that field.

## Prompt switching

Control type: `text_prompt_interval`, containing `segments` with `start`, `end`, and non-empty `text`.

- Boundaries are pixel-frame `[start,end)` indices.
- They are snapped to the nearest valid `1+4N` pixel boundary and converted to latent indices.
- After conversion, spans must be non-empty, ordered, gap-free, non-overlapping, and reach the final latent frame.
- A leading gap is allowed and uses the initial `user/text` prompt.
- At most one prompt-interval control is allowed.

Inspect the converted latent spans when exact switch timing matters; two different pixel boundaries can snap to the same latent boundary.

## Chunking

Hard boundaries are start/end, latent frame 1, the reference boundary, and prompt boundaries. Each region is split into chunks of at most `frames_per_block=4`. Thus the usual 31-latent-frame rollout becomes a first one-frame chunk followed by blocks of up to four, with extra splits at prompt changes.

## Cache-window modes

| CLI values | Intended use | Behavior |
|---|---|---|
| `97/9` | Published offline default; README recommends H100 or ≥80 GB | Keeps sink, prompt pin when applicable, and a larger recent tail. |
| `33/5` | Lower memory / online-oriented setting | Same policy with a shorter tail. |
| `-1/0` | Full history | Never prunes self-attention history; may grow substantially. |

Validation rounds frame counts up to four-frame blocks and requires at least two non-sink local blocks. These options change runtime cache behavior, not checkpoint parameter names.

## Launch

```bash
CUDA_VISIBLE_DEVICES=0 \
ZING_PYTHON=/path/to/python \
bash run.sh \
  --pretrained-dir /path/to/Zing-0.5/pretrained \
  --checkpoint /path/to/Zing-0.5/generator/model.pt \
  --messages examples/case3_action_t2v.jsonl \
  --output-dir outputs/case3 \
  --seed 0
```

The launcher adds `src` to `PYTHONPATH`, enables expandable CUDA allocation unless already configured, and runs `python -m zing_v0_5`. Configuration is always loaded from repository `config/zing.yaml`; only cache window values have CLI overrides.

## Diagnostic order

1. Confirm Linux, CUDA, compatible NVIDIA GPU, Python 3.11, exact pinned dependencies, and a working FlashAttention build.
2. Confirm the three pretrained directories and bare `.pt` checkpoint.
3. Validate JSON syntax and one-request-per-line structure.
4. Check `32`-pixel spatial alignment and `1+4N` total-frame structure.
5. Check T2V/TI2V action row count and prompt interval conversion.
6. For OOM, reduce cache from `97/9` to `33/5`, resolution, or duration; measure rather than assuming cache alone is the cause.
7. For prompt-switch discontinuity, inspect snapped boundaries, cross-cache reset, and whether the new-prompt anchor has reached pin eligibility.

## Reproducibility caveat

The CLI seeds Python, NumPy, CPU Torch, and all CUDA generators. This makes repeated runs more controlled, but `deterministic_attention` defaults to false and no global deterministic-algorithm mode is enabled. Report seed plus hardware, CUDA/Torch/FlashAttention versions, config, commit, and checkpoint hash for comparisons.
