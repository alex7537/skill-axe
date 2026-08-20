# WAM evidence ledger

Use this ledger to avoid mixing repository facts, dated experiment evidence, benchmark contracts, and hypotheses.

| Claim | Evidence class | Confidence | Boundary |
|---|---|---:|---|
| Current default WAM uses Wan VAE latent plus shared DiT and video/action heads | `Wam_Pre_Train` code/config snapshot | High for recorded commit | Re-resolve current Hydra config |
| 9 history + 16 future maps to 3 known + 4 predicted latent time steps | code/VAE geometry | High | Verify active VAE stride/padding |
| Earlier action contract truncated pose and masked gripper | Feishu code audit and repair commits | High historically | Old checkpoints only; inspect current branch |
| UNI_STATE v2 and 85/5/5/5 conditioning require fresh training | Feishu repair record/tests | High | Do not resume incompatible v1 checkpoint |
| W220 was poorly matched to full valid futures and episode starts | dataset audit | High for audited selection | Recompute after dataset/sampler changes |
| Action Following measures diversity, not correctness | metric implementation audit | High | Pair with instruction/semantic/counterfactual tests |
| WorldArena live score is 15-item while paper describes 16 | versioned implementation audit | High for recorded revisions | Recheck current leaderboard code |
| Local and official preprocessing can yield different numbers | evaluator audit plus small drift tests | High qualitatively | Full 1000-episode dual-run was not completed in the cited audit |
| HSDP improved throughput ~38% over FSDP | one recorded 150-node comparison | Medium | Hardware/config/run-specific, not general law |
| Text-Action > Action > Text in later GT1 result snapshot | same-benchmark result tables | High descriptively | Tracks differ; causal attribution requires paired intervention |
| Epoch 6 captured most gain, later epochs smaller gains | same-run checkpoint curve | Medium-high | Not a universal stopping rule |
| 5B is a better immediate optimization target than A14B | public-model audit plus PSI bottlenecks | Medium | A prioritization judgment, not an architectural theorem |
| Slot-valid masks will improve learning | spreadsheet plan and failure analysis | Hypothesis | Requires no-mask/strict/soft ablation |
| Action cross-attention will improve controllability | external model comparison | Hypothesis | Requires matched PSI ablation |

## Source precedence

When evidence conflicts, prefer:

1. current resolved config, code, tests, manifests, and actual run artifacts;
2. frozen benchmark source-of-truth files and hashes;
3. later correction/remediation documents over earlier reports;
4. complete same-schema evaluations over partial aggregates;
5. controlled experiments over visual impressions;
6. documented hypotheses only as experiment proposals.

## Provenance rule

For any important recommendation, state:

```text
claim -> source class -> version/date -> applicable configuration
      -> supporting metric/test -> known confounder -> next verification
```

Do not store expiring media URLs, internal node addresses, credentials, mutable allocation lists, or raw document transcripts in this skill.
