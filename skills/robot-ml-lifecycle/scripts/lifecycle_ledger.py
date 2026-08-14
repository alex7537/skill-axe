#!/usr/bin/env python3
"""Maintain an append-preserving robot-ML lifecycle ledger."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PHASES = (
    "frame",
    "source",
    "understand",
    "labels",
    "split",
    "train_plan",
    "infrastructure",
    "train",
    "evaluate",
    "package",
    "release",
    "capture",
)
STATUSES = ("pending", "in_progress", "passed", "diagnostic-only", "blocked", "skipped", "carried")
RESOLVED = {"passed", "diagnostic-only", "skipped", "carried"}


class LedgerError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def blank_phase() -> dict[str, Any]:
    return {
        "status": "pending",
        "skill": None,
        "evidence": None,
        "artifacts": {},
        "updated_at": None,
    }


def new_cycle(number: int, reason: str) -> dict[str, Any]:
    return {
        "number": number,
        "created_at": now(),
        "reason": reason,
        "phases": {phase: blank_phase() for phase in PHASES},
        "events": [],
    }


def read_ledger(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LedgerError(f"Ledger does not exist: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerError(f"Cannot read ledger {path}: {exc}") from exc
    validate_ledger(data)
    return data


def validate_ledger(data: Any) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise LedgerError(f"Unsupported or missing schema_version; expected {SCHEMA_VERSION}")
    cycles = data.get("cycles")
    active = data.get("active_cycle")
    if not isinstance(cycles, list) or not cycles:
        raise LedgerError("cycles must be a non-empty list")
    if not isinstance(active, int) or not 1 <= active <= len(cycles):
        raise LedgerError("active_cycle is out of range")
    for expected_number, cycle in enumerate(cycles, start=1):
        if cycle.get("number") != expected_number:
            raise LedgerError("cycle numbers must be contiguous and one-based")
        phases = cycle.get("phases")
        if not isinstance(phases, dict) or tuple(phases) != PHASES:
            raise LedgerError("cycle phases do not match the lifecycle schema")
        in_progress = 0
        for phase, entry in phases.items():
            if not isinstance(entry, dict) or entry.get("status") not in STATUSES:
                raise LedgerError(f"invalid status for phase {phase}")
            in_progress += entry.get("status") == "in_progress"
        if in_progress > 1:
            raise LedgerError("a cycle may have at most one in_progress phase")


def write_ledger(path: Path, data: dict[str, Any]) -> None:
    validate_ledger(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def active_cycle(data: dict[str, Any]) -> dict[str, Any]:
    return data["cycles"][data["active_cycle"] - 1]


def parse_artifacts(values: list[str]) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise LedgerError(f"Artifact must be KEY=VALUE: {value}")
        key, item = value.split("=", 1)
        key = key.strip()
        if not key or not item:
            raise LedgerError(f"Artifact must have a non-empty key and value: {value}")
        if key in artifacts:
            raise LedgerError(f"Duplicate artifact key: {key}")
        artifacts[key] = item
    return artifacts


def unresolved_prerequisites(cycle: dict[str, Any], phase: str) -> list[str]:
    index = PHASES.index(phase)
    return [name for name in PHASES[:index] if cycle["phases"][name]["status"] not in RESOLVED]


def command_init(args: argparse.Namespace) -> None:
    if args.path.exists():
        raise LedgerError(f"Refusing to overwrite existing ledger: {args.path}")
    timestamp = now()
    data = {
        "schema_version": SCHEMA_VERSION,
        "project": args.project,
        "objective": args.objective,
        "created_at": timestamp,
        "updated_at": timestamp,
        "active_cycle": 1,
        "cycles": [new_cycle(1, "initial cycle")],
    }
    write_ledger(args.path, data)
    print(f"Initialized lifecycle ledger: {args.path}")


def command_record(args: argparse.Namespace) -> None:
    data = read_ledger(args.path)
    cycle = active_cycle(data)
    if args.status in {"in_progress", "passed", "diagnostic-only"}:
        unresolved = unresolved_prerequisites(cycle, args.phase)
        if unresolved:
            raise LedgerError(
                f"Resolve earlier phases before {args.phase}: {', '.join(unresolved)}. "
                "Record an explicit skipped status when a phase does not apply."
            )
    if args.status != "pending" and not args.evidence:
        raise LedgerError(f"Status {args.status} requires --evidence")
    if args.status == "in_progress":
        running = [name for name, entry in cycle["phases"].items() if entry["status"] == "in_progress" and name != args.phase]
        if running:
            raise LedgerError(f"Phase already in progress: {running[0]}")

    artifacts = parse_artifacts(args.artifact)
    timestamp = now()
    before = deepcopy(cycle["phases"][args.phase])
    entry = cycle["phases"][args.phase]
    entry.update(
        {
            "status": args.status,
            "skill": args.skill,
            "evidence": args.evidence,
            "artifacts": artifacts,
            "updated_at": timestamp,
        }
    )
    cycle["events"].append(
        {
            "at": timestamp,
            "phase": args.phase,
            "from_status": before["status"],
            "to_status": args.status,
            "skill": args.skill,
            "evidence": args.evidence,
            "artifacts": artifacts,
        }
    )
    data["updated_at"] = timestamp
    write_ledger(args.path, data)
    print(f"Cycle {data['active_cycle']} {args.phase}: {before['status']} -> {args.status}")


def command_new_cycle(args: argparse.Namespace) -> None:
    data = read_ledger(args.path)
    previous = active_cycle(data)
    index = PHASES.index(args.from_phase)
    cycle = new_cycle(len(data["cycles"]) + 1, args.reason)
    timestamp = now()
    for phase in PHASES[:index]:
        old = previous["phases"][phase]
        if old["status"] not in RESOLVED:
            raise LedgerError(f"Cannot carry unresolved phase into new cycle: {phase} ({old['status']})")
        cycle["phases"][phase] = {
            "status": "carried",
            "skill": old["skill"],
            "evidence": f"Carried from cycle {previous['number']}: {old['evidence']}",
            "artifacts": deepcopy(old["artifacts"]),
            "updated_at": timestamp,
        }
    data["cycles"].append(cycle)
    data["active_cycle"] = cycle["number"]
    data["updated_at"] = timestamp
    write_ledger(args.path, data)
    print(f"Started cycle {cycle['number']} from phase {args.from_phase}")


def command_next(args: argparse.Namespace) -> None:
    data = read_ledger(args.path)
    cycle = active_cycle(data)
    for phase in PHASES:
        status = cycle["phases"][phase]["status"]
        if status not in RESOLVED:
            print(json.dumps({"cycle": cycle["number"], "phase": phase, "status": status}, ensure_ascii=False))
            return
    print(json.dumps({"cycle": cycle["number"], "phase": None, "status": "complete"}, ensure_ascii=False))


def command_show(args: argparse.Namespace) -> None:
    data = read_ledger(args.path)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    cycle = active_cycle(data)
    print(f"Project: {data['project']}")
    print(f"Objective: {data['objective']}")
    print(f"Active cycle: {cycle['number']} ({cycle['reason']})")
    for phase in PHASES:
        entry = cycle["phases"][phase]
        skill = f" via {entry['skill']}" if entry["skill"] else ""
        print(f"- {phase}: {entry['status']}{skill}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a new lifecycle ledger")
    init.add_argument("--path", type=Path, required=True)
    init.add_argument("--project", required=True)
    init.add_argument("--objective", required=True)
    init.set_defaults(handler=command_init)

    record = subparsers.add_parser("record", help="Record a phase status and evidence")
    record.add_argument("--path", type=Path, required=True)
    record.add_argument("--phase", choices=PHASES, required=True)
    record.add_argument("--status", choices=STATUSES[:-1], required=True)
    record.add_argument("--skill")
    record.add_argument("--evidence")
    record.add_argument("--artifact", action="append", default=[])
    record.set_defaults(handler=command_record)

    cycle = subparsers.add_parser("new-cycle", help="Start a retry cycle from a chosen phase")
    cycle.add_argument("--path", type=Path, required=True)
    cycle.add_argument("--from-phase", choices=PHASES, required=True)
    cycle.add_argument("--reason", required=True)
    cycle.set_defaults(handler=command_new_cycle)

    next_phase = subparsers.add_parser("next", help="Show the next unresolved phase")
    next_phase.add_argument("--path", type=Path, required=True)
    next_phase.set_defaults(handler=command_next)

    show = subparsers.add_parser("show", help="Show current lifecycle state")
    show.add_argument("--path", type=Path, required=True)
    show.add_argument("--json", action="store_true")
    show.set_defaults(handler=command_show)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
