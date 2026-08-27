# Zing-0.5 architecture and execution trace

## Provenance

- Upstream: <https://github.com/seedleap/zing-world-model>
- Pinned commit: `8dd446798f2dec160351c17484c53e8deaaf7ef4`
- Release scope: inference runtime, config, examples, and Apache-2.0 license; no training code or technical report at this revision.

Use permalinks of the form `https://github.com/seedleap/zing-world-model/blob/8dd446798f2dec160351c17484c53e8deaaf7ef4/<path>#Lx-Ly` when a local checkout is unavailable.

## One-sentence model

Zing-0.5 is a causal, block-autoregressive video-latent generator derived from a Wan-style diffusion transformer: it generates four latent frames at a time, conditions on UMT5 text and optional eight-channel keyboard actions, reuses prior attention K/V state, and decodes the completed latent sequence with a Wan VAE.

## End-to-end trace

| Stage | Main symbol | Input → output | Important behavior |
|---|---|---|---|
| CLI | `main.main` | arguments + JSONL → files | Loads fixed YAML, creates one pipeline, processes each JSONL line independently, then writes PNG/MP4. |
| Contract | `MessageProcessor.process` | message object → `InferenceRequest` | Validates dimensions/timing, encodes an optional reference image, constructs known/generated mask, prompt spans, block spans, and action windows. |
| Text | `WanTextEncoder.encode` | prompt strings → UMT5 embeddings + lengths | Pads effective context to at least 512 tokens and zeros padding embeddings. |
| Image | `WanVAE.encode` | uint8 `[B,C,T,H,W]` → normalized latent | Uses deterministic posterior mode, then changes layout to `[B,T,C,H,W]`. |
| Sampling | `InferencePipeline.generate` | request → complete video latent | Initializes unknown positions with noise and processes hard-boundary-aware chunks sequentially. |
| Generator | `WanModel.forward` | latent block + time + conditions + cache → predicted flow | 3D patch embed, action residual, 3D RoPE, 30 transformer blocks, text cross-attention, AdaLN time modulation, then unpatchify. |
| Scheduler | `DmdScheduler.step` | predicted flow + noisy latent → next latent | Computes `x0 = x_t - sigma*v`; re-noises between four configured steps and returns `x0` at the final step. |
| Cache | `CausalKVCache` | current K/V + history → visible causal history | Supports full history or sink + tail + optional prompt-switch pin; updates provisional current-block entries across denoising steps. |
| Decode | `WanVAE.decode` | normalized latent → RGB video tensor | Restores VAE statistics, decodes, maps `[-1,1]` to `[0,1]`, then CPU output is encoded at 24 fps. |

## Tensor map for the released config

Let output video be `F_out × H × W`, reference count `R ∈ {0,1}`, and `F_pixel = R + F_out`.

1. VAE latent time: `F_lat = 1 + (F_pixel - 1) / 4`. The division must be exact.
2. VAE latent space: `clean_latents [1, F_lat, 48, H/16, W/16]`.
3. Known/generated mask: `label_mask [1, F_lat]`; only the optional first reference latent is known.
4. Generator input is permuted to `[B, 48, T, H/16, W/16]`.
5. Patch size `[1,2,2]` produces tokens per latent frame `(H/32) × (W/32)`, each of width `3072`.
6. The released model has 30 transformer blocks and 24 heads, so head width is `128`.
7. Output tokens project back to 48-channel latents and are decoded to video.

Worked example: T2V with `output.frames=121`, `H=704`, `W=1248` gives `F_lat=31`, latent tensor `[1,31,48,44,78]`, and `22×39=858` generator tokens per latent frame. The first chunk is one latent frame; subsequent chunks contain up to four.

## Why the cache is causal

Within one latent block, all spatial tokens for its frames attend to cached earlier blocks plus the current block; `flash_attn` itself is called with `causal=False`. Causality comes from orchestration: future blocks do not exist in the key/value history yet.

For each denoising step, cache mode `active` lets the current block overwrite its provisional K/V slots rather than append duplicates. After the four steps, a timestep-zero `final` forward pass commits clean-block K/V and action history. This makes later blocks condition on a stable representation of the generated past.

With bounded attention, visible history is the union of:

- initial sink blocks;
- recent tail blocks within the local budget;
- after a prompt change, at most one pinned first block from the new prompt era.

The pin preserves a visual anchor for the new semantic regime after that block leaves the ordinary tail. Cross-attention K/V is reset immediately on prompt switch so new text context replaces the old cached context.

## Conditioning paths

### Text

UMT5 embeddings are projected from width 4096 to model width 3072 and used as cross-attention K/V. Each prompt interval selects a context for corresponding latent chunks. Prompt changes affect semantics through cross-attention and cache pinning.

### Keyboard action

Actions are ordered W/A/S/D/I/J/K/L and supplied at pixel-transition resolution. Every group of four transitions maps to one latent frame. The eight values are sinusoidally embedded independently, fused, passed through two causal temporal Conv1d blocks, projected to width 3072, broadcast over spatial tokens, and added to video tokens before transformer blocks. Two convolutional blocks with kernel size three require four latent frames of retained action history.

## Four-step DMD inference

Observed scheduler configuration is `[1000, 750, 500, 250]` over a 1000-step base grid with timestep shift `5.0`. At each selected sigma, the generator predicts a flow/velocity-like tensor `v`; the scheduler estimates clean latent `x0 = x_t - sigma*v`. Unless at the last step, it mixes `x0` with fresh noise at the next sigma.

This explains the runtime's four generator evaluations per generated block, but not how the model was trained to support them. The repository does not expose the teacher, distillation losses, data, or optimization procedure.

## Design trade-offs

- Blockwise causal rollout reduces repeated computation and enables long sequences, but errors accumulate in generated history.
- A bounded cache caps memory growth, but removes most distant context; sink and prompt pinning preserve only selected anchors.
- CPU offloading of UMT5 and VAE lowers steady GPU memory, but creates device-transfer latency.
- Strict checkpoint loading prevents silent architecture mismatch, but blocks adapters, wrapped checkpoints, and partial migrations.
- Full JSONL preprocessing makes validation simple and reproducible, but the public CLI is not itself an event-driven streaming server.

## Verification experiments

- Processor-only: construct small valid/invalid JSONL cases and check frame, dimension, prompt-gap, and action-length errors without model weights by stubbing `encode_reference`.
- Cache-only: feed synthetic block IDs into `_visible_indices` to verify sink/tail/pin retention.
- Scheduler-only: use a zero model output to verify re-noising and final `x0` behavior under a fixed seed.
- GPU integration: compare full-history, `97/9`, and `33/5` on the same prompt/seed while recording peak memory, block latency, and long-horizon drift.

## Unknowns that should remain unknown

- Training dataset and filtering
- Base model initialization beyond code-level Wan compatibility
- Exact DMD distillation recipe and losses
- Training action-label semantics beyond the released W/A/S/D/I/J/K/L order
- Quantitative latency/quality benchmarks and definition of “real-time”
- Whether prompt intervals or action mixtures outside released examples are well represented in training
