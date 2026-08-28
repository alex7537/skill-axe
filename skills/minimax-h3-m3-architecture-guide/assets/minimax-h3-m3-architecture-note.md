---
title: MiniMax H3 与 M3：架构原理、开放边界与部署现实
aliases:
  - MiniMax H3 M3 Architecture
  - MiniMax 架构笔记
tags:
  - ai/model-architecture
  - multimodal
  - video-generation
  - mixture-of-experts
  - sparse-attention
source_status: official-release-plus-code-inference
verified: 2026-08-27
---

# MiniMax H3 与 M3：架构原理、开放边界与部署现实

> [!summary]
> H3 与 M3 不是同一模型的两个代际。H3 是把视频 latent 和音频 latent 放进同一个 Transformer 联合生成的音视频模型；M3 是把视觉 token、MoE 和块稀疏注意力结合起来的 coding/agent 大语言模型。两者都发布了权重，但都使用自定义社区许可证；H3 的完整 2K 商用流水线也没有全部本地开放。

## 一张表先分清楚

| 维度 | MiniMax H3 | MiniMax M3 |
|---|---|---|
| 主要任务 | 文本/图片/视频/音频条件下生成视频与立体声音频 | 文本、图片、视频理解；coding、agent、tool use |
| 核心结构 | Dense H3-Omni-Transformer + Visual VAE + Audio VAE | 视觉编码器 + 60 层 MoE LLM + MiniMax Sparse Attention |
| 参数 | Omni Transformer 约 33B，另含 Qwen3-VL-32B 编码器 | 总参数约 428B，每 token 激活约 23B |
| 关键创新 | 音频与视频 latent 在同一 Transformer 中联合预测 | 每个 GQA group 先检索 KV blocks，再做精确稀疏注意力 |
| 本地开放 | H3-Base、FL2VA、Ref2VA | BF16、MXFP8、第三方 NVFP4 等权重 |
| 未完全开放 | Context-IR、Regenerate-2K、初版 native sparse attention | 完整训练数据/配方和官方 agent 产品全栈 |

## H3：声音为什么能和画面一起生成

### 端到端数据流

```text
文本 ------------------------------> Qwen3-VL-32B 语义编码 ----+
图片/视频 -> Qwen3-VL 语义编码 + Visual VAE 像素 latent -----+--> packed sequence
音频 ------------------------------> Audio VAE latent --------+      + 3D MM-RoPE
                                                                    |
噪声或中间状态的 video/audio latent -------------------------------+
                                                                    v
                                                       H3-Omni-Transformer
                                                          |              |
                                                       视频 latent     音频 latent
                                                          |              |
                                                       Visual VAE     Audio VAE
                                                          +-------> 视频 + 双声道音频
```

核心不是“先生成视频，再调用另一个音频模型配音”，而是让两种 latent 进入共享 Transformer。视频 token 能关注音频 token，音频 token 也能关注动作、人物和场景条件，因此模型有机会学习：撞击发生在哪一帧、人物什么时候开口、音乐在哪个镜头变化。

这是一种结构上的同步条件，不代表输出必然做到音素级对齐，也不保证物理规律和角色声音始终正确。

### Visual VAE

官方结构给出的压缩比例：

- 空间压缩 `16x`；
- 时间压缩 `4x`；
- latent 通道 `24`；
- 进入 Transformer 前再用 `(1, 2, 2)` patchify。

因此输入 `T x H x W` 的视频大致变成：

```text
(T/4) x (H/16) x (W/16) x 24
```

patchify 后，Transformer 看到的视觉 token 在空间上等效约 `32x` 下采样，时间仍约 `4x` 下采样。这样能显著减少序列长度，否则十几秒视频的 dense attention 代价会难以承受。

### Audio VAE

- 采样率 `32 kHz`；
- 双声道；
- 左右声道独立处理但共享 VAE 权重；
- latent 时间率约 `40 Hz`；
- 公开配置中 audio latent width 为 `32`。

音频和视频使用不同 VAE，因为波形时间结构与视频空间结构不同；它们最终在 Transformer 里融合，而不是在 codec 层强行统一。

### H3-Omni-Transformer

公开配置的重要值：

- 约 `33B` dense 参数；
- `50` 层；
- hidden size `5376`；
- `56` 个 attention heads；
- FFN hidden size `14336`；
- 约 `13B` 参数属于 AdaLN 分支，推理时部分调制结果可预计算缓存。

AdaLN 的教学化表达是：

```math
h' = \gamma(c,t) \odot \mathrm{Norm}(h) + \beta(c,t)
```

其中 `c` 包含条件和模态信息，`t` 表示生成时间步。真实代码还包含 gate 和更复杂的投影。

H3 使用三维 MM-RoPE 表示 `(time, height, width)`。这让模型不只知道 token 的线性序号，还能区分视频中的时间与二维位置。

### FL2VA 与 Ref2VA

- `FL2VA`：文本生成音视频，以及首帧、尾帧或首尾帧控制。
- `Ref2VA`：使用图片、视频、音频作为参考条件。

二者是独立的任务专用 checkpoint。公开版本被描述为 CFG-distilled，但官方尚未公开足以重建完整训练目标、噪声计划和蒸馏损失的材料，所以不应仅凭 DiT 外观断言它使用某一种具体 diffusion 或 Flow Matching 配方。

### H3 完整产品为何不等于公开权重

```text
H3-Context-IR（未本地开放）
        ↓ 结构化多模态上下文
H3-Base（已开放）
        ↓ 768p-class 基础结果
H3-Regenerate-2K（未本地开放）
        ↓
完整 2K 输出
```

Context-IR 负责把自由形式参考资料转成 H3-Base 更容易遵循的结构；Regenerate-2K 不是普通超分辨率网络，而是让基础模型在原始上下文中重新生成高分辨率结果。因此只下载 H3-Base，不能声称复现了官方完整 2K 系统。

## M3：MoE 与百万上下文如何组合

### 多模态 token 流

```text
图片/视频 -> dynamic resolution/temporal patches
          -> 32 层 vision encoder
          -> patch merge + projector(6144)
          -> 与文本 token 插入同一序列
          -> 60 层语言模型
          -> 下一个 token / tool call / reasoning 输出
```

Vision config 的关键值包括：hidden `1280`、32 层、patch size `14`、spatial merge `2`、video temporal patch `2`，然后投影到语言模型 hidden width `6144`。

“原生多模态”主要是训练阶段从早期就混合多模态数据的主张；从结构上看，它仍然有独立视觉编码器，然后把视觉 embedding 对齐到语言 token 空间。

### MoE：23B 激活不等于只需存 23B

M3 主干配置：

- 60 层，前 3 层 dense，后 57 层 MoE；
- 128 个 routed experts；
- 每个 token 选择 4 个 experts；
- 另有 1 个 shared expert；
- 总参数约 428B，单 token 激活约 23B。

教学化路由公式：

```math
s = \mathrm{sigmoid}(W_{gate}h + b), \quad S=\mathrm{TopK}(s,4)
```

```math
y = E_{shared}(h) + \sum_{i\in S}\alpha_iE_i(h)
```

MoE 省下的是每个 token 需要执行的矩阵计算，而不是让没有被选中的专家从 checkpoint 中消失。全部专家权重通常仍需放在 GPU、CPU 或统一内存里，所以 23B active 不能直接换算成 23B 模型的显存。

### MSA：先找 block，再精确 attention

普通 causal attention 对每个 query 查看全部历史 key：

```math
\mathrm{Attention}(q)=\sum_{j\le q}\mathrm{softmax}(qK_j^T/\sqrt d)_jV_j
```

当序列到几十万或一百万 token 时，计算量和 KV 读取都会非常昂贵。

MSA 将过程拆成两步：

1. Index Branch 低成本扫描/表示历史 KV blocks；
2. 每个 GQA group 选出自己的 Top-k blocks；
3. Main Branch 只在选中的 token 上做标准、精确的 softmax attention。

公开配置中：

- block size `128` tokens；
- Top-k `16` blocks；
- index dimension `128`；
- 4 个 sparse index heads；
- 保留 local block；
- 前 3 层不用 sparse attention，后续层启用。

可以写成：

```math
S_g(q)=\mathrm{TopK}_b\;\mathrm{IndexScore}_g(q,B_b)
```

```math
\mathrm{MSA}_g(q)=\mathrm{ExactAttention}(q,K[S_g(q)],V[S_g(q)])
```

这里最容易误解的是：算法写成稀疏并不自动带来真实加速。必须有匹配 block layout、Top-k 和内存访问方式的 kernel。官方论文的速度来自 exp-free Top-k、KV-outer CUDA kernel 和特定 GPU；如果 llama.cpp、Transformers 或其他 runtime 回退到 dense/SDPA，就不会自动继承同样收益。

### 一百万 context 的正确理解

`max_position_embeddings = 1,048,576` 只说明位置容量。真实能否使用一百万 token 还取决于：

- MSA kernel 是否启用；
- KV cache 精度和布局；
- 图像/视频占用多少 token；
- GPU 显存、卡间带宽、TP/EP 配置；
- prefill 与 decode 批处理；
- 长上下文检索质量是否稳定。

因此应测试“信息位于不同位置时能否正确取回”和“长程 agent 是否持续完成任务”，而不只是看能否成功加载 1M tokens。

### 模型能力与 agent 脚手架

M3 checkpoint 本身只做下一 token 预测。实际 coding agent 成绩还依赖：

```text
模型 + thinking mode + system prompt + tool schema + agent harness + sampling 参数
```

终端执行、浏览器操作、重试、文件修改和长期状态管理属于外部 harness。比较 benchmark 时必须同步这些条件。

## 权重与部署现实

2026-08-27 对 HF file tree 的审计结果：

| 仓库/目录 | 文件体积（十进制约值） |
|---|---:|
| H3 单个 FL2VA 或 Ref2VA 任务目录 | 144 GB |
| H3 完整 HF 仓库（包含重复格式/两个任务） | 498.5 GB |
| M3 BF16 | 854 GB |
| M3 MXFP8 | 444 GB |
| NVIDIA M3 NVFP4 | 250 GB |

这些不是最低显存数字：运行还需要 activation、KV cache 和框架 workspace；CPU/offload 又可以用速度换显存。

## 开放与许可证边界

更准确的称呼是“开放权重”，而不是 OSI 意义的开源软件。

H3 的自定义许可证尤其需要注意：

- 2026-08-02 版本排除美国、欧盟、英国和韩国；
- 年收入超过 2000 万美元的商业产品需事先书面授权；
- 商业 UI 需要展示 `MiniMax H3`；
- 不得用 H3 或其输出改进 H3 以外的其他 AI 模型。

最后一条会直接影响合成数据、蒸馏和 evaluator/reward model 训练。

M3 同样不是标准 Apache/MIT：商业使用涉及 `Built with MiniMax M3` 标识、一次通知或高收入场景的事先授权，并包含军事用途等限制。

> [!warning]
> 许可证会变化。本笔记不是法律意见；商业使用、再分发或训练其他模型前，应重新阅读对应 checkpoint 当前的 LICENSE。

## 我对两个模型的研究判断

H3 最值得研究的是：

1. 不同时间尺度的 video/audio latent 如何在单流 Transformer 对齐；
2. 语义视觉特征与像素 VAE latent 为什么要双路输入；
3. joint generation 是否真的改善事件级、语音级和音乐级同步；
4. Context-IR 带来的收益有多少能由开源 prompt compiler 替代。

M3 最值得研究的是：

1. Index Branch 在百万上下文中选择了哪些 blocks；
2. sparse recall 与最终任务正确率之间的关系；
3. MoE expert specialization 是否按代码语言、工具类型或视觉任务分化；
4. MSA kernel、KV cache 和 expert parallel 的系统瓶颈如何互相转移。

## 可证伪实验

### H3

- 固定 prompt/seed，只改变是否提供音频参考，比较画面动作和音频事件的帧级对齐。
- 同一条件分别走结构化 prompt 和普通自然语言 prompt，测 Context-IR 风格结构化输入的增益。
- 固定总 latent token 数，分别增加空间分辨率或视频长度，观察 attention/activation 峰值。

### M3

- 把关键事实放在 1%、25%、50%、75%、99% 上下文位置，测试检索正确率和延迟。
- 同一 checkpoint 对比原生 MSA kernel 与 dense fallback，分别记录 prefill、decode、峰值显存和答案质量。
- 固定 prompt 和工具 schema，对比 thinking enabled/adaptive/disabled 的工具调用成功率与 token 成本。

## 官方来源

- [MiniMax H3 GitHub](https://github.com/MiniMax-AI/MiniMax-H3)
- [MiniMax H3 Hugging Face](https://huggingface.co/MiniMaxAI/MiniMax-H3)
- [H3 开放说明](https://www.minimax.io/news/minimax-h3-open-source)
- [MiniMax M3 GitHub](https://github.com/MiniMax-AI/MiniMax-M3)
- [MiniMax M3 Hugging Face](https://huggingface.co/MiniMaxAI/MiniMax-M3)
- [MiniMax Sparse Attention 论文](https://arxiv.org/abs/2606.13392)
- [MSA kernel](https://github.com/MiniMax-AI/MSA)
- [Transformers MiniMax M3 文档](https://huggingface.co/docs/transformers/model_doc/minimax_m3_vl)

## 更新记录

- 2026-08-27：基于官方 GitHub、HF config、LICENSE、H3 release note、MSA 论文和上游 runtime 文档建立初版。
