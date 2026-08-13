#!/usr/bin/env python3
"""Validate semantic label decisions and evidence fields in JSONL."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ALLOWED = {
    "valid_nonempty", "true_empty", "confirmed_missing", "partial_annotation_hole",
    "boundary_ambiguous", "multi_instance_ambiguous", "corrupt_or_unreadable",
}
REQUIRES_EVIDENCE = ALLOWED - {"valid_nonempty"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    config = parser.parse_args()
    records = [json.loads(line) for line in config.input.read_text().splitlines() if line.strip()]
    failures: list[str] = []
    identities: set[tuple[str, str]] = set()
    counts: Counter[str] = Counter()
    for index, record in enumerate(records):
        identity = (str(record.get("group_id", "")), str(record.get("sample_id", "")))
        classification = record.get("classification")
        if not all(identity): failures.append(f"row {index}: missing group_id/sample_id")
        if identity in identities: failures.append(f"row {index}: duplicate decision for {identity}")
        identities.add(identity)
        if classification not in ALLOWED:
            failures.append(f"row {index}: unsupported classification {classification!r}")
            continue
        counts[classification] += 1
        if classification in REQUIRES_EVIDENCE and not record.get("evidence_ref"):
            failures.append(f"row {index}: {classification} requires evidence_ref")
        if classification in {"partial_annotation_hole", "boundary_ambiguous"} and not record.get("affected_ranges"):
            failures.append(f"row {index}: {classification} requires affected_ranges")
        if classification in {"confirmed_missing", "boundary_ambiguous", "multi_instance_ambiguous"} and not record.get("confidence"):
            failures.append(f"row {index}: {classification} requires confidence")
    report = {"status": "pass" if not failures else "block", "records": len(records), "counts": counts, "failures": failures}
    text = json.dumps(report, indent=2) + "\n"
    if config.output:
        config.output.parent.mkdir(parents=True, exist_ok=True)
        config.output.write_text(text)
    print(text, end="")
    raise SystemExit(0 if not failures else 2)


if __name__ == "__main__":
    main()
