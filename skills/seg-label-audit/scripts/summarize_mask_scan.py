#!/usr/bin/env python3
"""Summarize frame-level mask measurements from JSONL without reading images."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--group-key", default="group_id")
    parser.add_argument("--sample-key", default="sample_id")
    parser.add_argument("--frame-key", default="frame_idx")
    parser.add_argument("--foreground-key", default="foreground_pixels")
    parser.add_argument("--ids-key", default="nonzero_ids")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def empty_runs(frames: list[int], empty: set[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    start = previous = None
    for frame in frames:
        if frame not in empty:
            if start is not None:
                runs.append([start, previous])
                start = previous = None
            continue
        if start is None or previous is None or frame != previous + 1:
            if start is not None:
                runs.append([start, previous])
            start = frame
        previous = frame
    if start is not None:
        runs.append([start, previous])
    return runs


def main() -> None:
    config = args()
    records = [json.loads(line) for line in config.input.read_text().splitlines() if line.strip()]
    by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    groups: dict[str, str] = {}
    for record in records:
        sample = str(record[config.sample_key])
        group = str(record[config.group_key])
        if sample in groups and groups[sample] != group:
            raise ValueError(f"sample {sample!r} appears under multiple groups")
        groups[sample] = group
        by_sample[sample].append(record)

    summaries = []
    counts: Counter[str] = Counter()
    for sample, items in sorted(by_sample.items()):
        frames = [int(item[config.frame_key]) for item in items]
        if len(frames) != len(set(frames)):
            raise ValueError(f"duplicate frame identity in sample {sample!r}")
        frames.sort()
        empty = {int(item[config.frame_key]) for item in items if int(item[config.foreground_key]) == 0}
        unreadable = sum(not bool(item.get("readable", True)) for item in items)
        multi_id = sum(len(item.get(config.ids_key, [])) > 1 for item in items)
        if unreadable:
            classification = "contains_unreadable_frames"
        elif len(empty) == len(items):
            classification = "whole_sample_empty_observation"
        elif empty:
            classification = "partial_empty_observation"
        else:
            classification = "nonempty_observation"
        counts[classification] += 1
        summaries.append({
            "group_id": groups[sample],
            "sample_id": sample,
            "frame_count": len(items),
            "frame_min": min(frames),
            "frame_max": max(frames),
            "empty_frame_count": len(empty),
            "empty_runs": empty_runs(frames, empty),
            "multi_id_frame_count": multi_id,
            "unreadable_frame_count": unreadable,
            "observation": classification,
        })
    report = {"status": "scan-complete", "frames": len(records), "samples": len(summaries), "counts": counts, "samples_detail": summaries}
    text = json.dumps(report, indent=2) + "\n"
    if config.output:
        config.output.parent.mkdir(parents=True, exist_ok=True)
        config.output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
