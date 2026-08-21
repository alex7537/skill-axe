#!/usr/bin/env python3
"""Read-only summary table for A2D evaluation summary JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Summary JSON files")
    parser.add_argument("--eval-dir", type=Path, help="Directory to glob")
    parser.add_argument("--pattern", default="*_summary.json")
    parser.add_argument("--json", action="store_true", help="Emit normalized JSON")
    return parser.parse_args()


def collect(args: argparse.Namespace) -> list[Path]:
    paths = list(args.paths)
    if args.eval_dir:
        paths.extend(sorted(args.eval_dir.glob(args.pattern)))
    unique = sorted({item.expanduser().resolve() for item in paths})
    if not unique:
        raise SystemExit("No summary JSON files selected")
    missing = [str(item) for item in unique if not item.is_file()]
    if missing:
        raise SystemExit("Missing summary file(s): " + ", ".join(missing))
    return unique


def nonnegative_int(value: Any, field: str, source: Path) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source}: {field} must be an integer") from exc
    if result < 0:
        raise ValueError(f"{source}: {field} must be non-negative")
    return result


def normalize(source: Path) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{source}: root must be an object")
    counts = payload.get("funnel_counts") or {}
    if not isinstance(counts, dict):
        raise ValueError(f"{source}: funnel_counts must be an object")
    completed = nonnegative_int(payload.get("completed", 0), "completed", source)
    requested = nonnegative_int(payload.get("requested", 0), "requested", source)
    success_fallback = counts.get("success", 0)
    success_5cm = nonnegative_int(counts.get("grasp_lift_5cm", success_fallback), "grasp_lift_5cm", source)
    success_10cm = nonnegative_int(counts.get("grasp_lift_10cm", 0), "grasp_lift_10cm", source)
    target_contact = nonnegative_int(counts.get("target_contact_ready", 0), "target_contact_ready", source)
    for field, value in (
        ("grasp_lift_5cm", success_5cm),
        ("grasp_lift_10cm", success_10cm),
        ("target_contact_ready", target_contact),
    ):
        if value > completed:
            raise ValueError(f"{source}: {field}={value} exceeds completed={completed}")
    fixed_runtime = payload.get("fixed_runtime") or {}
    if not isinstance(fixed_runtime, dict):
        raise ValueError(f"{source}: fixed_runtime must be an object")
    return {
        "configuration": payload.get("configuration", payload.get("model", source.stem)),
        "horizon": fixed_runtime.get("execute_horizon"),
        "completed": completed,
        "requested": requested,
        "success_5cm": success_5cm,
        "success_10cm": success_10cm,
        "target_contact": target_contact,
        "success_rate_percent": 100.0 * success_5cm / completed if completed else 0.0,
        "failure_stage_counts": payload.get("failure_stage_counts", {}),
        "path": str(source),
    }


def main() -> int:
    args = parse_args()
    try:
        rows = [normalize(item) for item in collect(args)]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    print("configuration\thorizon\tcompleted\t5cm\t10cm\tcontact\tsuccess_rate\tfailures")
    for row in rows:
        failures = json.dumps(row["failure_stage_counts"], ensure_ascii=False, sort_keys=True)
        print(
            f"{row['configuration']}\t{row['horizon']}\t"
            f"{row['completed']}/{row['requested']}\t{row['success_5cm']}\t"
            f"{row['success_10cm']}\t{row['target_contact']}\t"
            f"{row['success_rate_percent']:.2f}%\t{failures}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
