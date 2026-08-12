#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate a comparable training budget")
    parser.add_argument("--samples", type=int, required=True, help="Effective train samples")
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--epochs", type=float, required=True)
    parser.add_argument("--warmup-ratio", type=float, default=0.05)
    parser.add_argument("--drop-last", action="store_true")
    parser.add_argument("--old-samples", type=int)
    parser.add_argument("--old-batch-size", type=int)
    parser.add_argument("--old-epochs", type=float)
    args = parser.parse_args()

    if args.samples < 1 or args.batch_size < 1 or args.epochs <= 0:
        parser.error("samples and batch-size must be positive; epochs must be > 0")
    if not 0.0 <= args.warmup_ratio < 1.0:
        parser.error("warmup-ratio must be in [0, 1)")

    steps_per_epoch = (
        args.samples // args.batch_size
        if args.drop_last
        else math.ceil(args.samples / args.batch_size)
    )
    total_steps = round(steps_per_epoch * args.epochs)
    payload: dict[str, int | float | dict[str, int | float]] = {
        "effective_samples": args.samples,
        "batch_size": args.batch_size,
        "drop_last": int(args.drop_last),
        "steps_per_epoch": steps_per_epoch,
        "epochs": args.epochs,
        "total_steps": total_steps,
        "warmup_ratio": args.warmup_ratio,
        "warmup_steps": round(total_steps * args.warmup_ratio),
        "sample_presentations": round(args.samples * args.epochs),
    }

    old_values = (args.old_samples, args.old_batch_size, args.old_epochs)
    if any(value is not None for value in old_values):
        if not all(value is not None for value in old_values):
            parser.error("old-samples, old-batch-size, and old-epochs must be provided together")
        assert args.old_samples is not None
        assert args.old_batch_size is not None
        assert args.old_epochs is not None
        old_steps_per_epoch = math.ceil(args.old_samples / args.old_batch_size)
        old_total_steps = round(old_steps_per_epoch * args.old_epochs)
        payload["baseline_equivalence"] = {
            "old_steps_per_epoch": old_steps_per_epoch,
            "old_total_steps": old_total_steps,
            "equivalent_new_epochs": old_total_steps / steps_per_epoch,
            "planned_step_ratio": total_steps / old_total_steps,
        }

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
