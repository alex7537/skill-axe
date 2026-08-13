#!/usr/bin/env python3
"""Assign whole groups to roles while approximating sample-weight ratios."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="") as stream: return list(csv.DictReader(stream))
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    raise ValueError("use CSV or JSONL")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--group-key", required=True)
    parser.add_argument("--sample-key", required=True)
    parser.add_argument("--weight-key")
    parser.add_argument("--roles", nargs="+", default=["train", "val", "holdout"])
    parser.add_argument("--ratios", nargs="+", type=float, default=[0.8, 0.1, 0.1])
    parser.add_argument("--seed", type=int, default=42)
    config = parser.parse_args()
    if len(config.roles) != len(config.ratios) or any(r <= 0 for r in config.ratios):
        raise ValueError("roles and positive ratios must have equal length")
    records = load(config.input)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    samples: set[str] = set()
    for record in records:
        sample = str(record[config.sample_key])
        if sample in samples: raise ValueError(f"duplicate sample: {sample}")
        samples.add(sample)
        groups[str(record[config.group_key])].append(record)
    weights = {group: sum(float(row.get(config.weight_key, 1)) if config.weight_key else 1 for row in rows) for group, rows in groups.items()}
    ratios = {role: ratio / sum(config.ratios) for role, ratio in zip(config.roles, config.ratios)}
    targets = {role: sum(weights.values()) * ratios[role] for role in config.roles}
    current = {role: 0.0 for role in config.roles}
    items = list(groups)
    random.Random(config.seed).shuffle(items)
    items.sort(key=lambda group: weights[group], reverse=True)
    assignment: dict[str, str] = {}
    for group in items:
        role = max(config.roles, key=lambda name: (targets[name] - current[name]) / targets[name])
        assignment[group] = role
        current[role] += weights[group]
    config.output_dir.mkdir(parents=True, exist_ok=False)
    handles = {role: (config.output_dir / f"{role}.jsonl").open("w") for role in config.roles}
    try:
        for group, rows in groups.items():
            role = assignment[group]
            for record in rows:
                handles[role].write(json.dumps({**record, "role": role}) + "\n")
    finally:
        for handle in handles.values(): handle.close()
    summary = {"seed": config.seed, "roles": {role: {"groups": sum(value == role for value in assignment.values()), "samples": sum(len(groups[group]) for group, value in assignment.items() if value == role), "weight": current[role]} for role in config.roles}, "group_assignment": assignment}
    (config.output_dir / "split_manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
