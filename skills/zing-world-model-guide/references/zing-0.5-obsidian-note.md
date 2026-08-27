---
title: Zing-0.5 Interactive World Model
aliases:
  - zing-world-model
  - Zing 0.5
tags:
  - world-model
  - video-generation
  - causal-inference
  - dmd
  - wan
source: https://github.com/seedleap/zing-world-model
source_commit: 8dd446798f2dec160351c17484c53e8deaaf7ef4
reviewed: 2026-08-26
evidence_status: inference-code-verified
---

# Zing-0.5 Interactive World Model

## 核心判断

Zing-0.5 是一个面向交互式视觉世界展开的、Wan 系视频 latent 生成器。它不是传统“先规划状态、再渲染”的显式 world model；公开实现直接在视频 latent 空间中，按时间块因果生成未来画面，并用文本切换世界语义、用八维键盘动作改变运动与交互。

公开仓库是推理版本：能确定运行机制，不能确定训练数据、训练损失、DMD 蒸馏细节或完整 benchmark。

## 一张心智图

```text
初始文本 ──UMT5──┐
                 ├─ cross-attention ───────────────┐
参考图像 ─Wan VAE─┴─ 已知首帧 latent                │
                                                     ▼
噪声未来 latent → 每块最多 4 latent 帧 → 30 层 DiT → 四步 DMD → clean latent
                         ▲                 ▲                           │
                         │                 │                           ▼
              W/A/S/D/I/J/K/L      causal KV cache ─────────→ 下一时间块
                                                                   │
                                                                   ▼
                                                             Wan VAE → MP4
```

## 关键机制

### 1. 时间不是逐 RGB 帧生成

Wan VAE 以 4 倍压缩时间。总像素帧数必须符合 `1+4N`。典型的 121 帧 T2V 和“1 张参考图 + 120 个新帧”的 TI2V，都会变成 31 个 latent 帧。

模型通常先单独处理第一个 latent 帧，再以最多 4 个 latent 帧为一块继续生成。每个 latent 帧代表首帧之后约四个像素帧的时间跨度。

### 2. 因果性由块级调度和 cache 实现

FlashAttention 调用本身不是 token-level causal mask。真正的因果约束来自：生成当前块时，cache 里只有过去块；未来块尚未进入 K/V。

当前块的四次去噪会反复覆盖“临时 K/V”，最终用时间步 0 的 clean latent 再前向一次，才把稳定历史交给下一块。这是理解其长序列推理的关键。

### 3. 文本和动作走两条不同条件通路

- 文本：UMT5 编码后进入每层 cross-attention。prompt 切换时清空 text K/V cache。
- 动作：8 维 W/A/S/D/I/J/K/L 序列经正弦编码和因果 Conv1d，投影为 3072 维 residual，加到对应时间的所有空间 token 上。

所以文本更像“改变场景语义/未来事件”，动作更像“给生成动态施加局部控制”，两者可以同时存在。

### 4. 长程记忆是受控压缩，不是完整记忆

默认 `97/9` 或低显存 `33/5` 会保留：开头 sink、最近 tail，以及 prompt 切换后一个可选 pinned block。它用有限显存换取长时展开，但被丢弃的中远程细节无法继续通过 self-attention 直接访问。

`-1/0` 可以保留完整历史，但 cache 随序列增长。

## 模型规格（公开配置）

| 项目 | 数值 |
|---|---:|
| 视频 latent 通道 | 48 |
| VAE 空间压缩 | 16× |
| VAE 时间压缩 | 4× |
| 3D patch | `[1,2,2]` |
| Transformer width | 3072 |
| 层数 / 头数 | 30 / 24 |
| FFN width | 14336 |
| 文本输入维度 | 4096 |
| 每块 latent 帧 | 4 |
| DMD 推理步 | 4 |
| 输出帧率 | 24 fps |

## 与机器人 world model 的关系

它证明了“动作条件 + 视频 latent + 因果 cache”可以组成紧凑的交互世界展开器，但公开接口仍以键盘动作和视频观感为中心。若迁移到机器人，需要重新回答：动作是否对应真实控制量、状态/本体感如何进入、物理一致性如何评估、闭环误差如何抑制，以及模型是否学习了接触和动力学而非视觉相关性。

因此它更适合作为以下研究参照：

- blockwise video rollout 与 cache 设计；
- action conditioning 如何注入视觉生成 token；
- prompt 事件如何切换长期语义；
- 少步生成如何支撑交互延迟。

它不能直接证明机器人控制能力。

## 值得复现实验

1. 固定 seed、prompt、checkpoint，对比 full history、`97/9`、`33/5` 的峰值显存、每块延迟和长程漂移。
2. 固定噪声，只改变单个动作维度，检查动作的方向性、一致性、延迟和释放后的惯性。
3. 在相同 latent 边界切换 prompt，比较是否 pin 新 prompt 首块对后续语义保持的影响。
4. 记录 prompt 边界从 pixel frame snap 到 latent frame 后的真实切换时刻，避免把输入时间和模型时间混为一谈。

## 已知边界与未知项

- CLI 是离线消费完整 JSONL 后输出视频，不是现成的实时事件服务器。
- 必须使用 CUDA、FlashAttention、bfloat16 路径；README 的显存建议需要在实际硬件上复测。
- 权重必须是严格匹配的 bare state dict。
- 技术报告在该 commit 尚未发布。
- 训练数据、loss、teacher/student DMD、评测定义均未知。

## 源码入口

- `src/zing_v0_5/main.py`：CLI 与总流程
- `src/zing_v0_5/processor.py`：JSONL、时间轴、动作与 prompt 合约
- `src/zing_v0_5/pipeline.py`：分块生成、四步采样、cache 生命周期
- `src/zing_v0_5/model/modeling.py`：Wan-style DiT 主体
- `src/zing_v0_5/model/kv_cache.py`：sink/tail/pin 与 active/final cache
- `src/zing_v0_5/model/action.py`：动作条件编码
- `src/zing_v0_5/scheduler.py`：四步 DMD 更新

## 关联笔记建议

- [[World Model]]
- [[Video World Model]]
- [[Diffusion Distillation]]
- [[Causal KV Cache]]
- [[Action-conditioned Video Generation]]
- [[Wan Video Model]]
