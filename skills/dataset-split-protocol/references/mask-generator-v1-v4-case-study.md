# Mask Generator V1–V4 case study

This is evidence for the protocol, not a source of default model or hyperparameter values.

| Version | Controlled focus | Evidence discovered | Decision |
|---|---|---|---|
| V1 | Prove RGB-to-mask training works | Useful overlap, but zero GT included missing labels; old evaluation was exposed; midpoint sampling hid temporal failures | Stop architecture tuning and repair data/evaluation contracts |
| V2 | Quarantine confirmed missing labels and build grouped roles | Wrong negative gradients removed; sealed holdout excluded every viewed group; full-sequence audit exposed poor early/late performance | Cleaning is necessary but cannot fix temporal distribution mismatch |
| V3 | Replace fixed midpoint training with valid-frame phase coverage | Early/late quality improved substantially while middle stayed stable | Sampling distribution was higher leverage than a larger model |
| V4 | Audit and ingest a new source while preserving old roles | No hard group/sample/resource overlap; old-domain protection remained stable; gains became small and localized regressions concentrated in weak-cue early frames | Freeze the unconditioned model near its plateau |
| Calibration ablation | Change only positive BCE weighting | Lower weighting moved the selected threshold toward the center and produced small, consistent cross-role gains | Select the better-calibrated checkpoint; do not expect it to solve target identity |

## Lessons

- All-zero labels require semantic audit before split or metrics.
- Viewed test data becomes diagnostic.
- Sampling and evaluation must cover deployment time, not only an easy midpoint.
- Incremental training requires old val, new val, diagnostic, and sealed holdout to remain distinct.
- Mean gains require paired regression analysis.
- Threshold drift motivates controlled calibration experiments, not arbitrary threshold reuse.
- If target identity came from a teacher prompt but the student sees only RGB, extra unconditioned data cannot recover that missing information.
