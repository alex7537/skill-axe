---
name: minimax-h3-m3-architecture-guide
description: Explain, trace, compare, or audit MiniMax H3 and MiniMax M3 architecture, multimodal data flow, sparse attention, MoE routing, open-weight boundaries, licenses, and realistic local-deployment requirements. Use when the user mentions MiniMax H3/M3, H3-Base, FL2VA, Ref2VA, H3-Omni-Transformer, MiniMax Sparse Attention/MSA, M3 million-token context, or asks whether the GitHub/Hugging Face releases reproduce the hosted systems. Do not use for unrelated MiniMax API billing or ordinary video prompting without an architecture question.
---

# MiniMax H3 / M3 Architecture Guide

Treat H3 and M3 as different model families before answering:

- **H3** is an omni-modal audio-video generation system. Read [references/h3-architecture.md](references/h3-architecture.md) for its input encoders, video/audio latent spaces, packed sequence, joint generator, and hosted 2K stages.
- **M3** is a native-multimodal coding/agent MoE language model. Read [references/m3-architecture.md](references/m3-architecture.md) for vision-token injection, expert routing, MiniMax Sparse Attention, and million-token behavior.
- For GitHub/Hugging Face artifacts, license terms, model sizes, and what remains hosted, read [references/release-and-license.md](references/release-and-license.md).
- When the user wants a durable note, adapt or copy [assets/minimax-h3-m3-architecture-note.md](assets/minimax-h3-m3-architecture-note.md). Preserve its `verified` date and refresh unstable facts first.

## Evidence discipline

Separate every material claim into one of these levels:

1. **Official release fact** — model card, checked-in config/code, license, technical report, or framework recipe.
2. **Direct inference** — a conclusion derived from those artifacts; label it as an inference.
3. **Community observation** — hardware, speed, quality, or quantization result from a third party; name the environment and do not generalize it.

Browse current official sources whenever the question concerns availability, repository contents, supported runtimes, license, benchmark status, or hardware support. These facts change quickly. Prefer MiniMax GitHub/Hugging Face and technical reports, then upstream Transformers/SGLang/vLLM/ComfyUI documentation. Do not use search snippets as the only evidence for a consequential claim.

## Explanation contract

Start from the end-to-end data flow, then zoom into the mechanism the user asked about. Always distinguish:

- training from inference;
- total parameters from activated or resident parameters;
- model architecture from serving kernels and agent scaffolding;
- open weights from a fully reproducible hosted product;
- advertised context/resolution from the locally validated path.

Use shapes and equations only when they clarify token flow, attention selection, MoE routing, latent compression, or memory scaling. Mark unknown training details as unknown rather than reconstructing them from analogy.

## Gotchas

- H3 and M3 are not successive versions and should not be ranked as one family.
- H3 local weights reproduce H3-Base, not the complete hosted Context-IR + Base + Regenerate-2K system.
- H3's audio-video synchrony comes from joint latent prediction; it does not prove perfect speech, physics, or semantic synchronization.
- M3's roughly 23B activated parameters do not mean only 23B parameters must be stored. MoE reduces per-token computation, not the full expert-weight footprint.
- A 1M position limit does not mean every runtime efficiently serves 1M tokens. The MSA kernel, KV cache, quantization, parallelism, and serving configuration matter.
- MSA acceleration numbers measured on a specific kernel and accelerator do not transfer automatically to dense-attention fallbacks or consumer runtimes.
- Both releases use custom MiniMax community licenses. Say **open-weight** unless the exact meaning of “open source” has been defined.
- Do not call an HF parameter count the download size; duplicated formats, task checkpoints, quantization metadata, and auxiliary encoders change repository size.
