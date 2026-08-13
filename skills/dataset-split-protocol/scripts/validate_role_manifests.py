#!/usr/bin/env python3
"""Validate disjoint dataset roles from CSV or JSONL manifests."""

from __future__ import annotations

import argparse, csv, hashlib, json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="") as stream: return list(csv.DictReader(stream))
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    raise ValueError("use CSV or JSONL")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""): value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", action="append", required=True, metavar="NAME=PATH")
    parser.add_argument("--group-key", required=True)
    parser.add_argument("--sample-key", required=True)
    parser.add_argument("--resource-key")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--quarantine", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths: dict[str, Path] = {}
    for spec in args.role:
        name, separator, raw = spec.partition("=")
        if not separator or not name or name in paths: raise ValueError(f"invalid role spec: {spec}")
        paths[name] = Path(raw)
    keys = [args.group_key, args.sample_key] + ([args.resource_key] if args.resource_key else [])
    failures: list[str] = []
    sets: dict[str, dict[str, set[str]]] = {}
    report: dict[str, Any] = {"status": "pass", "roles": {}, "intersections": {}, "conservation": None, "failures": failures}
    for role, path in paths.items():
        rows = load(path); per_key = {}
        for key in keys:
            values = [str(row[key]) for row in rows]
            per_key[key] = set(values)
            if key == args.sample_key and len(values) != len(per_key[key]): failures.append(f"duplicate samples in {role}")
        sets[role] = per_key
        report["roles"][role] = {"path": str(path), "sha256": digest(path), "rows": len(rows), "unique": {key: len(value) for key, value in per_key.items()}}
    names = list(paths)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            pair = f"{left}__{right}"; report["intersections"][pair] = {}
            for key in keys:
                overlap = sorted(sets[left][key] & sets[right][key])
                report["intersections"][pair][key] = {"count": len(overlap), "examples": overlap[:20]}
                if overlap: failures.append(f"{left}/{right} overlap on {key}")
    if args.source:
        source = {str(row[args.sample_key]) for row in load(args.source)}
        active = set().union(*(sets[role][args.sample_key] for role in names))
        quarantine = {str(row[args.sample_key]) for row in load(args.quarantine)} if args.quarantine else set()
        missing, unexpected, collision = source-active-quarantine, (active|quarantine)-source, active&quarantine
        report["conservation"] = {"source":len(source),"active":len(active),"quarantine":len(quarantine),"missing":len(missing),"unexpected":len(unexpected),"active_quarantine_overlap":len(collision)}
        if missing or unexpected or collision: failures.append("source conservation failed")
    report["status"] = "pass" if not failures else "block"
    text = json.dumps(report, indent=2) + "\n"
    if args.output: args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text)
    print(text, end="")
    raise SystemExit(0 if not failures else 2)


if __name__ == "__main__": main()
