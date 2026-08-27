---
name: zing-world-model-guide
description: Explain, trace, review, or prepare inference inputs for seedleap Zing-0.5 (zing-world-model), including JSONL prompt/action timelines, Wan-based video latent generation, four-step DMD sampling, causal KV-cache sliding windows, prompt switching, and T2V/TI2V runtime constraints. Use when the user mentions Zing-0.5, zing-world-model, its inference code, control schema, cache behavior, or wants to compare this released runtime with another world model. Do not use as evidence for unreleased training data, objectives, or benchmark claims.
---

# Zing World Model Guide

Build an evidence-backed explanation of the public Zing-0.5 inference release. Treat the checked-out source at the requested revision as authoritative; this skill's bundled notes describe upstream commit `8dd446798f2dec160351c17484c53e8deaaf7ef4` from 2026-08-26.

## Route the request

- Read [references/architecture.md](references/architecture.md) for architecture, tensors, conditioning, DMD, or causal-cache questions.
- Read [references/input-runtime.md](references/input-runtime.md) before creating JSONL, checking frame/action lengths, choosing cache windows, loading checkpoints, or diagnosing startup/runtime errors.
- Read [references/zing-0.5-obsidian-note.md](references/zing-0.5-obsidian-note.md) when the user wants a concise research summary, comparison note, or Obsidian-ready artifact.

If the user supplies a checkout or asks about a newer revision, inspect that source first and report the commit. Do not silently apply the pinned notes to changed code.

## Evidence contract

Separate conclusions into:

- **Observed:** directly supported by source, configuration, or released examples.
- **Inference:** a plausible interpretation of the implementation; say what evidence would verify it.
- **Unknown:** absent from this inference-only release.

Use repository `path:line` evidence when a checkout is available. Otherwise link to the pinned GitHub source. Prefer the runtime wiring over README wording when they differ.

## Working model

Trace the main execution path as:

`JSONL line → MessageProcessor → InferenceRequest → text/image encoding → blockwise latent denoising → causal KV-cache finalization → Wan VAE decode → PNG/MP4`

Keep these distinctions explicit:

- Pixel-frame time and VAE latent time are different: temporal compression is `4`, so valid total pixel frames follow `1 + 4N`.
- The generator operates on 48-channel video latents, not RGB pixels.
- The first image frame, when present, is a known latent protected by a mask; generated positions start as noise.
- A block is denoised four times while its provisional KV entries are updated in place. Only the final clean pass commits stable history for later blocks.
- Keyboard action is a causal additive conditioning path. Text is cross-attention context. They are distinct conditioning mechanisms.
- Prompt switching resets cached text K/V and can pin the first new-prompt block in a bounded attention window; it does not reset the generated visual history.

## Boundaries

- This repository releases inference, examples, and the model interface. Do not claim it reveals the training loop, dataset, loss composition, DMD teacher/student procedure, or reported benchmark methodology.
- Do not call the runtime truly online merely because it is causal. The CLI consumes a complete JSONL request and writes output only after generation; a live application must adapt events to the same schema or modify orchestration.
- Do not promise hardware compatibility below the published guidance. Initialization requires CUDA, uses FlashAttention, and defaults to `bfloat16`; actual memory depends on resolution, duration, window, library build, and GPU.
- Preserve the exact checkpoint contract: a `.pt` file containing a bare tensor state dict, loaded strictly. Wrapped or partially compatible checkpoints are rejected.

## Gotchas

- `output.frames` excludes the reference image, while the written TI2V video includes it.
- T2V action rows equal `output.frames - 1`; TI2V action rows equal `output.frames`.
- Height and width must align with VAE scale `16` and spatial patch `2`, hence multiples of `32` for the released config.
- Prompt intervals use pixel-frame `[start, end)` boundaries, are snapped to latent boundaries, and must become gap-free, ordered, non-empty latent spans through the tail.
- `local_attn_size` and `sink_size` are expressed in latent frames but rounded to block geometry (`frames_per_block=4`) for validation and retention.
- A seed does not guarantee cross-platform bitwise identity; FlashAttention determinism is separately configurable and defaults to false.
- The four configured scheduler values are implementation facts. A full theoretical description of the training-side DMD method is not present in this repository.
