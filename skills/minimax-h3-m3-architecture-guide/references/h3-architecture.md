# MiniMax H3 architecture

Verified against the official release artifacts on 2026-08-27.

## Mental model

H3 is best understood as a conditional latent audio-video generator with a shared Transformer core. It converts heterogeneous context into a packed sequence, iteratively predicts video and audio latent variables in one network, and decodes them with separate VAEs.

```text
text ------------------------------> H3 Encoder (Qwen3-VL-32B) --+
image/video -> H3 Encoder + Visual VAE --------------------------+--> packed multimodal sequence
audio -----------------------> Audio VAE ------------------------+          + 3D MM-RoPE
                                                                            |
noise / partially noised video+audio latents -------------------------------+
                                                                            v
                                                               H3-Omni-Transformer
                                                                  |              |
                                                          predicted video   predicted audio
                                                              latents          latents
                                                                  |              |
                                                           Visual VAE       Audio VAE
                                                                  +------> video + stereo audio
```

This is a conceptual flow, not a claim that every condition follows an identical preprocessing call in every runtime.

## Context interpretation

The complete hosted product has three conceptual stages:

1. **H3-Context-IR** interprets free-form text, images, video, and audio and serializes them into the structured context expected by H3-Base.
2. **H3-Base** generates audio-video latents and decodes the normal local output.
3. **H3-Regenerate-2K** asks the base model to regenerate its lower-resolution result in context, recovering high-resolution detail.

Only H3-Base is locally open-weight in the initial release. Context-IR and Regenerate-2K remain hosted API stages. Prompt guides approximate the expected structured representation but are not the hidden Context-IR implementation.

## Encoders and latent spaces

### H3 Encoder

- Uses the complete Qwen3-VL-32B weights.
- The official description takes hidden states from Qwen3-VL layer 50 into H3-Omni-Transformer.
- Text is processed by this encoder.
- Visual references are processed both semantically by H3 Encoder and reconstructively by Visual VAE.
- The release supplies its own tokenizer/config because it adds special tokens.

The two visual paths serve different purposes: semantic features answer “what is present and how is it related,” while VAE latents preserve information needed to condition or regenerate pixels over time.

### Visual VAE

- Temporally causal.
- Spatial compression: `16x` before Transformer patchification.
- Temporal compression: `4x`.
- Latent channels: `24`.
- Transformer patch size in latent coordinates: `(time, height, width) = (1, 2, 2)`.

For an input video with approximate shape `T x H x W`, the VAE produces a latent grid close to:

```text
(T/4) x (H/16) x (W/16) x 24
```

Patchifying `1 x 2 x 2` makes the effective spatial token downsampling `32x`, while temporal downsampling remains `4x`. Exact boundary behavior depends on padding and clip conventions.

### Audio VAE

- Input/output sample rate: `32 kHz`.
- Stereo output; left and right channels are processed independently using shared encoder/decoder weights and then recombined.
- Latent rate: `40 Hz` per channel according to the official architecture description.
- Released config exposes `32` audio latent channels.

The separate audio and visual codecs let each modality use a suitable compression geometry. Synchronization is learned in the shared Transformer rather than by forcing audio into the video VAE.

## H3-Omni-Transformer

Official summary and released FL2VA/Ref2VA config:

- approximately `33B` dense parameters;
- approximately `13B` are in AdaLN-related branches whose modulation output can be precomputed and cached for inference;
- `50` Transformer layers;
- hidden size `5376`;
- `56` attention heads with configured head dimension `128`;
- FFN hidden size `14336`;
- text-conditioning dimension `5120`;
- visual latent width `24`, audio latent width `32`;
- modality-specific parameters are concentrated around input/output mappings and AdaLN rather than separate attention/FFN towers.

H3 packs modality tokens into a single sequence. Three-dimensional multimodal RoPE represents temporal and two spatial axes `(t, h, w)`. Shared self-attention then lets video tokens condition audio tokens and vice versa. That coupling is the architectural reason synchronized sound can be generated in the same sampling process.

AdaLN can be viewed schematically as conditioning a normalized hidden state with scale and shift derived from timestep and modality/context signals:

```text
h' = gamma(c, t) * Norm(h) + beta(c, t)
```

The exact implementation has more gates and projected outputs than this teaching equation. Use the released code for implementation-level claims.

## FL2VA and Ref2VA

- **FL2VA** supports text-to-audio-video and optional first frame, last frame, or both.
- **Ref2VA** supports text plus reference images, videos, and/or audio.
- They are separate task-specialized, CFG-distilled checkpoints with the same high-level DiT config but different learned weights/conditioning behavior.

CFG-distilled means the released inference model has absorbed behavior normally obtained through classifier-free guidance. Do not infer the undisclosed training recipe or objective weights from this label alone.

## Training versus inference

Confirmed facts:

- H3 is a latent iterative generator with a DiT-like Transformer.
- The final training stage used native sparse attention.
- The initially released checkpoints are CFG-distilled.

Do not state a precise diffusion, flow-matching, loss, noise schedule, dataset mixture, optimizer, or distillation objective unless a current technical report or code explicitly documents it. The public launch description and inference config are insufficient to reconstruct those details safely.

## Architectural consequences

- Joint generation can improve temporal alignment between picture and sound, but quality must be evaluated separately for speech identity, phoneme timing, effects, music, and physical events.
- Packing long video/audio sequences makes attention a major cost. The open initial release omits H3's native sparse-attention implementation, so public full-attention inference is substantially heavier.
- Local 768p H3-Base and hosted 2K output are different pipelines. A local/base result must not be presented as a reproduction of the complete hosted system.

## Primary sources

- https://github.com/MiniMax-AI/MiniMax-H3
- https://huggingface.co/MiniMaxAI/MiniMax-H3
- https://www.minimax.io/news/minimax-h3-open-source
- https://www.minimax.io/blog/minimax-h3
