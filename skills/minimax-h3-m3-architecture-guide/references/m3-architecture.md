# MiniMax M3 architecture

Verified against the official release artifacts on 2026-08-27.

## Mental model

M3 is a decoder-style native-multimodal language model whose main trunk combines:

1. a vision encoder and projector that turn images/video into language-width tokens;
2. a 60-layer language backbone, with three dense layers followed by MoE layers;
3. MiniMax Sparse Attention (MSA) in the layers after the initial dense prefix;
4. an autoregressive output head used for text, reasoning, tool calls, and agent actions represented as tokens.

```text
text tokens -------------------------------------------------------+
image/video -> dynamic tiling -> vision encoder -> merge/project --+--> one multimodal token stream
                                                                    |
                                      dense prefix -> MSA + MoE backbone -> next-token distribution
```

“Native multimodal” is a training claim: MiniMax says mixed modalities were present from the start of training. Architecturally, the release still has a distinct vision encoder and projector feeding a shared language backbone.

## Vision path

The checked-in config describes a CLIP-style vision Transformer with:

- 32 layers;
- hidden size `1280`;
- 16 attention heads;
- FFN size `5120`;
- patch size `14`;
- dynamic resolutions up to configured grid points of `2016 x 2016`;
- spatial patch merge size `2`;
- temporal patch size `2` for video;
- projection to the language hidden width `6144`;
- dedicated image and video special-token IDs.

Images/videos become projected embeddings that occupy positions in the same sequence as text. Three-dimensional RoPE in the vision tower preserves spatial/temporal relationships before projection. The shared language model can therefore reason over visual tokens with its normal autoregressive computation.

## Language and MoE backbone

Key checked-in values:

- roughly `428B` total parameters and roughly `23B` activated per token;
- 60 layers, hidden width `6144`;
- 64 query heads, 4 key/value heads, head dimension `128`;
- vocabulary size `200064`;
- maximum configured positions `1,048,576`;
- first 3 layers dense, remaining 57 layers MoE;
- 128 routed local experts, top 4 selected per token;
- 1 shared expert;
- routed expert intermediate width `3072`, dense-layer width `12288`, shared-expert width `3072`.

For token representation `h`, the routed MoE can be taught schematically as:

```text
scores = sigmoid(W_gate h + routing_bias)
S = TopK(scores, k=4)
y = shared_expert(h) + sum(i in S) alpha_i * expert_i(h)
```

The actual implementation includes routing scaling, normalization and communication details. The important distinction is:

- **compute per token** touches a small expert subset;
- **weight residency/storage** still includes all experts unless some are offloaded;
- expert parallelism distributes those weights and all-to-all token traffic across devices.

Therefore “23B activated” predicts arithmetic better than minimum memory.

## MiniMax Sparse Attention

### Dense baseline

For a query token `q`, dense causal attention scores every visible key:

```text
Attention(q) = sum(j <= q) softmax(q K_j^T / sqrt(d))_j V_j
```

At long sequence length `L`, this has quadratic score work in `L` and a large KV-memory traffic cost.

### MSA mechanism

MSA groups keys/values into blocks and separates retrieval from exact attention:

1. **Index Branch** cheaply represents/scans candidate KV blocks.
2. It assigns group-specific scores and selects Top-k blocks for each GQA group.
3. **Main Branch** performs normal exact softmax attention only over tokens in selected blocks, plus required local/causal blocks.

Released M3 config exposes:

- sparse block size `128` tokens;
- `16` selected blocks;
- index dimension `128`;
- `4` sparse index heads;
- score aggregation type `max`;
- a mandatory local block;
- sparse attention disabled for the first 3 layers and enabled in the remaining layers.

Conceptually, for GQA group `g`:

```text
S_g(q) = TopK_b IndexScore_g(q, block_b)
MSA_g(q) = ExactAttention(q, K[S_g(q)], V[S_g(q)])
```

The paper's kernel uses block-granular access, exp-free Top-k selection, and a KV-outer execution strategy to turn algorithmic sparsity into hardware speedup.

### What MSA changes and does not change

MSA reduces the amount of historical context consulted by the expensive main branch and can reduce attention compute/KV traffic at very long context. It does not:

- shrink the MoE expert weights;
- make the KV cache free;
- guarantee speedup in a runtime that falls back to dense/SDPA attention;
- guarantee perfect retrieval at 1M tokens;
- replace the need for tensor, expert and data parallelism.

Published speedups are tied to particular sequence lengths, accelerators and optimized kernels. Quote the experimental setup with the number.

## Long-context behavior

The config limit is a capacity boundary, not a quality or throughput guarantee. Practical 1M serving depends on:

- MSA kernel availability;
- KV-cache precision and block layout;
- multimodal token count;
- tensor/expert parallel topology;
- prefill/decode batching;
- available GPU memory and interconnect bandwidth;
- the inference engine's implementation of M3-specific parsers and attention.

Test retrieval quality across positions and multi-step agent behavior rather than relying on a maximum-position field.

## Agent and coding capability

The backbone predicts tokens; repository editing, terminal execution, browsing, retries and state management come from an external agent harness. Benchmark results therefore combine at least:

```text
model weights + reasoning mode + system prompt + tool schema + harness + sampling parameters
```

Do not attribute scaffold behavior to the bare checkpoint without checking the benchmark protocol. M3 exposes `enabled`, `adaptive`, and `disabled` thinking modes in official serving interfaces, but runtime parity should be verified locally.

## Primary sources

- https://github.com/MiniMax-AI/MiniMax-M3
- https://huggingface.co/MiniMaxAI/MiniMax-M3
- https://huggingface.co/MiniMaxAI/MiniMax-M3/blob/main/config.json
- https://arxiv.org/abs/2606.13392
- https://github.com/MiniMax-AI/MSA
- https://huggingface.co/docs/transformers/model_doc/minimax_m3_vl
