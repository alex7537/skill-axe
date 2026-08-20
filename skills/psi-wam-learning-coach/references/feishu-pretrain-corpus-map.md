# Feishu World Model Pretraining corpus map

## Review boundary

- Root: `World Model` → `World Model Pretraining`
- Read snapshot: 2026-08-20, user identity, read-only operations
- Wiki/Docx traversal: 40 pages, maximum observed depth 6, zero fetch failures
- Additional embedded resource: one spreadsheet named `真机Dataset`, five worksheets inspected read-only
- No images, videos, attachments, signed media links, comments, permissions, or document content were modified

This file is an index and coverage record, not a copy of the source corpus. Re-fetch the live tree when revisions matter.

## Page tree reviewed

```text
World Model
└── World Model Pretraining
    ├── 架构
    └── 训练｜测评
        ├── RoboTwin训练+WorldArena测评
        │   ├── World Arena测评标准
        │   │   ├── World Arena测评标准2026-05-25
        │   │   ├── World Arena测评标准2026-07-13更新与2026-05-25 diff
        │   │   ├── World Arena测评中的一些问题
        │   │   ├── 适配World Arena 2026-07-13测评标准自有测评流程
        │   │   ├── 自有测评流程与World Arena官方测评的区别
        │   │   └── WorldArena测评指标计算方法
        │   ├── RoboTwin+WorldArena 训练测评记录
        │   │   ├── 2026-05-25
        │   │   ├── 2026-06-05
        │   │   ├── 2026-06-18
        │   │   ├── 2026-06-23
        │   │   ├── 2026-06-25
        │   │   ├── 2026-07-06（旧版本worldarena）
        │   │   ├── 2026-07-06（新版本worldarena）
        │   │   ├── 2026-07-20
        │   │   └── 2026-07-27
        │   ├── 训练 insight
        │   │   ├── Robotwin训练和worldarena测评 视频 fps 对比
        │   │   ├── 模型结构优化
        │   │   ├── 2026-07-19训练与模型结构优化
        │   │   └── 使用Wan2.2 A14B的world model
        │   └── 数据
        │       └── RoboTwin 2.0
        ├── psi-world-model-benchmark
        │   └── Psi-WMBench-GT1
        │       ├── Psi-WMBench-GT1 测评标准与执行流程
        │       └── Mix混训模型测评记录
        │           └── 2026年8月6日
        ├── 训练insight
        │   └── 分布式训练
        │       └── FSDP vs HSDP
        ├── Mix混训
        │   ├── HG Wan Dojo Mix 数据集
        │   └── 真机Dataset（Spreadsheet）
        └── 海光集群训练节点分配
```

## Content classification

| Class | Pages/resources | How to use |
|---|---|---|
| Directory/placeholder | root/index pages, `架构`, empty dated pages | Prove coverage; do not invent content |
| Architecture/code contract | model optimization and 2026-07-19 contract pages | Compare against current branch before acting |
| Training history | dated RoboTwin runs | Extract trends and failure modes; do not compare incompatible metric schemas |
| Evaluation contract | WorldArena and Psi-WMBench pages | Freeze version, profile, coverage, preprocessing, and aggregation |
| Data contract | RoboTwin, Mix dataset, embedded spreadsheet | Validate FPS, resolution, action fields, labels, masks, and sampling weights |
| Infrastructure | distributed training and node allocation | Keep performance lessons; exclude machine addresses and mutable allocations |
| External architecture research | A14B and open-source model comparison | Treat as design evidence, not proof for PSI's current model |

## Known coverage caveats

- Some dated pages are empty or contain only media; they contribute no textual conclusion.
- Training-record tables contain historical paths, checkpoints, rollout media, and partial schemas. The skill keeps only decision-relevant conclusions.
- The node-allocation page is operational inventory; addresses are deliberately excluded.
- The spreadsheet contains mutable internal dataset inventory and collection plans. Preserve schema and lessons, not internal paths or project-level rows.
- Psi-WMBench's v2 page explicitly says newer runs must follow the v3 remediation workflow. Never silently use v1/v2 counts or anchors for a current run.
