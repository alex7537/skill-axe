#!/usr/bin/env python3
"""Check proposed incremental train records against protected role manifests."""

from __future__ import annotations

import argparse, csv, json
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="") as stream: return list(csv.DictReader(stream))
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-train", required=True, type=Path)
    parser.add_argument("--protected", action="append", required=True, metavar="ROLE=PATH")
    parser.add_argument("--keys", nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    new = load(args.new_train); failures=[]; report={"status":"pass","checks":{},"unavailable_keys":[]}
    for key in args.keys:
        if any(key not in row or row[key] in (None, "") for row in new): report["unavailable_keys"].append(key)
    for spec in args.protected:
        role, separator, raw = spec.partition("=")
        if not separator: raise ValueError(f"invalid protected spec: {spec}")
        old = load(Path(raw)); report["checks"][role] = {}
        for key in args.keys:
            if key in report["unavailable_keys"] or any(key not in row or row[key] in (None, "") for row in old):
                report["checks"][role][key] = {"status":"unavailable"}; continue
            overlap = sorted({str(row[key]) for row in new} & {str(row[key]) for row in old})
            report["checks"][role][key] = {"status":"clear" if not overlap else "overlap","count":len(overlap),"examples":overlap[:20]}
            if overlap: failures.append(f"new train overlaps {role} on {key}")
    report["failures"] = failures
    report["status"] = "block" if failures else ("diagnostic-only" if report["unavailable_keys"] else "pass")
    text=json.dumps(report,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
    print(text,end="")
    raise SystemExit(2 if failures else 0)


if __name__ == "__main__": main()
