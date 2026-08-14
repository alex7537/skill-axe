#!/usr/bin/env python3
"""Maintain a bounded, append-preserving robot-ML lifecycle ledger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
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
OUTCOMES = ("success", "failure", "noop")
LEVELS = ("L0", "L1", "L2", "L3")
DECISIONS = ("approved", "rejected", "revoked")


class LedgerError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_control() -> dict[str, Any]:
    return {
        "autonomy_level": "L1",
        "cadence": "manual",
        "paused": False,
        "pause_reason": None,
        "max_cycles": 10,
        "max_attempts_per_phase": 3,
        "max_consecutive_failures": 3,
        "stagnation_threshold": 3,
        "token_budget": None,
        "cost_budget": None,
    }


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
        "attempts": [],
        "events": [],
    }


def migrate_ledger(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise LedgerError("Ledger must contain a JSON object")
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        return data
    if version != 1:
        raise LedgerError(f"Unsupported or missing schema_version; expected 1 or {SCHEMA_VERSION}")
    migrated = deepcopy(data)
    migrated["schema_version"] = SCHEMA_VERSION
    migrated["control"] = default_control()
    migrated["decisions"] = []
    for cycle in migrated.get("cycles", []):
        cycle.setdefault("attempts", [])
    return migrated


def read_ledger(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LedgerError(f"Ledger does not exist: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerError(f"Cannot read ledger {path}: {exc}") from exc
    data = migrate_ledger(raw)
    validate_ledger(data)
    return data


def positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise LedgerError(f"{field} must be a positive integer")
    return value


def validate_ledger(data: Any) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise LedgerError(f"Unsupported or missing schema_version; expected {SCHEMA_VERSION}")
    control = data.get("control")
    if not isinstance(control, dict) or control.get("autonomy_level") not in LEVELS:
        raise LedgerError("control.autonomy_level is invalid")
    if not isinstance(control.get("paused"), bool):
        raise LedgerError("control.paused must be boolean")
    for field in ("max_cycles", "max_attempts_per_phase", "max_consecutive_failures", "stagnation_threshold"):
        positive_int(control.get(field), f"control.{field}")
    for field in ("token_budget", "cost_budget"):
        value = control.get(field)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0):
            raise LedgerError(f"control.{field} must be null or a positive number")

    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise LedgerError("decisions must be a list")
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
        if not isinstance(cycle.get("attempts"), list) or not isinstance(cycle.get("events"), list):
            raise LedgerError("cycle attempts and events must be lists")
        in_progress = 0
        for phase, entry in phases.items():
            if not isinstance(entry, dict) or entry.get("status") not in STATUSES:
                raise LedgerError(f"invalid status for phase {phase}")
            in_progress += entry.get("status") == "in_progress"
        if in_progress > 1:
            raise LedgerError("a cycle may have at most one in_progress phase")
        for attempt in cycle["attempts"]:
            if not isinstance(attempt, dict) or attempt.get("phase") not in PHASES or attempt.get("outcome") not in OUTCOMES:
                raise LedgerError("invalid attempt entry")


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


def next_phase(cycle: dict[str, Any]) -> tuple[str | None, str]:
    for phase in PHASES:
        status = cycle["phases"][phase]["status"]
        if status not in RESOLVED:
            return phase, status
    return None, "complete"


def normalize_signature(value: str) -> str:
    value = value.lower()
    value = re.sub(r"https?://\S+", "<url>", value)
    value = re.sub(r"(?:[a-zA-Z]:)?[/\\][^\s:]+", "<path>", value)
    value = re.sub(r"\b(?:0x)?[0-9a-f]{8,}\b", "<id>", value)
    value = re.sub(r"\d+", "#", value)
    return re.sub(r"\s+", " ", value).strip()


def trailing_failures(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for attempt in reversed(attempts):
        if attempt["outcome"] != "failure":
            break
        result.append(attempt)
    return list(reversed(result))


def breaker_decision(data: dict[str, Any]) -> dict[str, Any]:
    control = data["control"]
    cycle = active_cycle(data)
    phase, status = next_phase(cycle)
    attempts = cycle["attempts"]
    total_tokens = sum(item.get("tokens", 0) for item in attempts)
    total_cost = round(sum(item.get("cost", 0.0) for item in attempts), 6)

    def result(decision: str, trigger: str, reason: str) -> dict[str, Any]:
        return {
            "decision": decision,
            "trigger": trigger,
            "reason": reason,
            "cycle": cycle["number"],
            "phase": phase,
            "phase_status": status,
            "attempts": len(attempts),
            "tokens": total_tokens,
            "cost": total_cost,
            "autonomy_level": control["autonomy_level"],
        }

    if control["paused"]:
        return result("ESCALATE", "paused", control.get("pause_reason") or "Loop is paused")
    if phase is None:
        return result("COMPLETE", "complete", "All lifecycle phases are resolved")

    phase_attempts = [item for item in attempts if item["phase"] == phase]
    failures = trailing_failures(phase_attempts)
    threshold = control["stagnation_threshold"]
    if len(failures) >= threshold:
        last_signature = normalize_signature(failures[-1].get("error", ""))
        repeated = 0
        for item in reversed(failures):
            if normalize_signature(item.get("error", "")) == last_signature:
                repeated += 1
            else:
                break
        if last_signature and repeated >= threshold:
            return result("ESCALATE", "stagnation", f"Same normalized failure repeated {repeated} times")
    if len(failures) >= control["max_consecutive_failures"]:
        return result("ESCALATE", "no-progress", f"{len(failures)} consecutive failures in phase {phase}")
    if len(phase_attempts) >= control["max_attempts_per_phase"] and (not phase_attempts or phase_attempts[-1]["outcome"] != "success"):
        return result("ESCALATE", "attempt-cap", f"Attempt cap reached for phase {phase}")
    if control["token_budget"] is not None and total_tokens >= control["token_budget"]:
        return result("ESCALATE", "token-budget", "Active-cycle token budget reached")
    if control["cost_budget"] is not None and total_cost >= control["cost_budget"]:
        return result("ESCALATE", "cost-budget", "Active-cycle monetary budget reached")
    return result("CONTINUE", "ok", "Within configured controls")


def command_init(args: argparse.Namespace) -> int:
    if args.path.exists():
        raise LedgerError(f"Refusing to overwrite existing ledger: {args.path}")
    timestamp = now()
    control = default_control()
    control.update(
        {
            "autonomy_level": args.level,
            "cadence": args.cadence,
            "max_cycles": args.max_cycles,
            "max_attempts_per_phase": args.max_attempts_per_phase,
            "max_consecutive_failures": args.max_consecutive_failures,
            "stagnation_threshold": args.stagnation_threshold,
            "token_budget": args.token_budget,
            "cost_budget": args.cost_budget,
        }
    )
    data = {
        "schema_version": SCHEMA_VERSION,
        "project": args.project,
        "objective": args.objective,
        "created_at": timestamp,
        "updated_at": timestamp,
        "control": control,
        "active_cycle": 1,
        "cycles": [new_cycle(1, "initial cycle")],
        "decisions": [],
    }
    write_ledger(args.path, data)
    print(f"Initialized lifecycle ledger: {args.path}")
    return 0


def command_record(args: argparse.Namespace) -> int:
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
    cycle["phases"][args.phase].update(
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
            "kind": "phase-transition",
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
    return 0


def command_attempt(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    cycle = active_cycle(data)
    expected_phase, _ = next_phase(cycle)
    if expected_phase is None:
        raise LedgerError("Lifecycle is complete; no execution attempt is allowed")
    if args.phase != expected_phase:
        raise LedgerError(f"Attempt phase must match the next unresolved phase: {expected_phase}")
    if args.outcome == "failure" and not args.error:
        raise LedgerError("Failure attempts require --error")
    if args.tokens < 0 or args.cost < 0:
        raise LedgerError("Attempt tokens and cost cannot be negative")
    timestamp = now()
    attempt = {
        "number": len(cycle["attempts"]) + 1,
        "at": timestamp,
        "phase": args.phase,
        "action": args.action,
        "outcome": args.outcome,
        "error": args.error,
        "tokens": args.tokens,
        "cost": args.cost,
        "evidence": args.evidence,
    }
    cycle["attempts"].append(attempt)
    cycle["events"].append({"at": timestamp, "kind": "attempt", **attempt})
    data["updated_at"] = timestamp
    write_ledger(args.path, data)
    print(f"Recorded attempt {attempt['number']}: {args.phase} {args.outcome}")
    return 0


def command_new_cycle(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    previous = active_cycle(data)
    if data["control"]["paused"]:
        raise LedgerError("Cannot start a new cycle while the loop is paused")
    if len(data["cycles"]) >= data["control"]["max_cycles"]:
        raise LedgerError("Cycle cap reached; escalate instead of starting another cycle")
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
    return 0


def command_decision(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    timestamp = now()
    data["decisions"].append(
        {
            "at": timestamp,
            "cycle": data["active_cycle"],
            "gate": args.gate,
            "decision": args.decision,
            "evidence": args.evidence,
        }
    )
    data["updated_at"] = timestamp
    write_ledger(args.path, data)
    print(f"Recorded human gate {args.gate}: {args.decision}")
    return 0


def command_pause(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    data["control"]["paused"] = True
    data["control"]["pause_reason"] = args.reason
    data["updated_at"] = now()
    write_ledger(args.path, data)
    print(f"Paused: {args.reason}")
    return 0


def command_resume(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    if not data["control"]["paused"]:
        raise LedgerError("Loop is not paused")
    data["control"]["paused"] = False
    data["control"]["pause_reason"] = None
    data["decisions"].append(
        {
            "at": now(),
            "cycle": data["active_cycle"],
            "gate": "resume-loop",
            "decision": "approved",
            "evidence": args.evidence,
        }
    )
    data["updated_at"] = now()
    write_ledger(args.path, data)
    print("Resumed loop")
    return 0


def command_level(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    old = data["control"]["autonomy_level"]
    if LEVELS.index(args.level) > LEVELS.index(old) and not args.human_approved:
        raise LedgerError("Increasing autonomy requires --human-approved")
    data["control"]["autonomy_level"] = args.level
    data["decisions"].append(
        {
            "at": now(),
            "cycle": data["active_cycle"],
            "gate": "autonomy-level",
            "decision": "approved",
            "evidence": f"{old} -> {args.level}: {args.evidence}",
        }
    )
    data["updated_at"] = now()
    write_ledger(args.path, data)
    print(f"Autonomy level: {old} -> {args.level}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    decision = breaker_decision(data)
    if args.json:
        print(json.dumps(decision, indent=2, ensure_ascii=False))
    else:
        print(f"{decision['decision']} [{decision['trigger']}] — {decision['reason']}")
    return 2 if decision["decision"] == "ESCALATE" else 0


def compact_attempt(attempt: dict[str, Any]) -> dict[str, Any]:
    result = dict(attempt)
    error = result.get("error")
    if error:
        lines = error.splitlines()
        result["error"] = "\n".join(lines[:3])[:500]
        if len(lines) > 3 or len(error) > 500:
            result["error"] += "\n… pruned"
    return result


def command_context(args: argparse.Namespace) -> int:
    if args.window < 1:
        raise LedgerError("Context window must be a positive integer")
    data = read_ledger(args.path)
    cycle = active_cycle(data)
    phase, status = next_phase(cycle)
    payload = {
        "project": data["project"],
        "objective": data["objective"],
        "control": data["control"],
        "active_cycle": cycle["number"],
        "cycle_reason": cycle["reason"],
        "next_phase": phase,
        "next_phase_status": status,
        "phase_statuses": {name: entry["status"] for name, entry in cycle["phases"].items()},
        "recent_attempts": [compact_attempt(item) for item in cycle["attempts"][-args.window :]],
        "recent_decisions": data["decisions"][-args.window :],
        "breaker": breaker_decision(data),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def command_next(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    cycle = active_cycle(data)
    phase, status = next_phase(cycle)
    print(json.dumps({"cycle": cycle["number"], "phase": phase, "status": status}, ensure_ascii=False))
    return 0


def command_show(args: argparse.Namespace) -> int:
    data = read_ledger(args.path)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    cycle = active_cycle(data)
    control = data["control"]
    print(f"Project: {data['project']}")
    print(f"Objective: {data['objective']}")
    print(f"Control: {control['autonomy_level']} cadence={control['cadence']} paused={control['paused']}")
    print(f"Active cycle: {cycle['number']} ({cycle['reason']})")
    for phase in PHASES:
        entry = cycle["phases"][phase]
        skill = f" via {entry['skill']}" if entry["skill"] else ""
        print(f"- {phase}: {entry['status']}{skill}")
    print(f"Attempts: {len(cycle['attempts'])}  Decisions: {len(data['decisions'])}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a new lifecycle ledger")
    init.add_argument("--path", type=Path, required=True)
    init.add_argument("--project", required=True)
    init.add_argument("--objective", required=True)
    init.add_argument("--level", choices=LEVELS, default="L1")
    init.add_argument("--cadence", default="manual")
    init.add_argument("--max-cycles", type=int, default=10)
    init.add_argument("--max-attempts-per-phase", type=int, default=3)
    init.add_argument("--max-consecutive-failures", type=int, default=3)
    init.add_argument("--stagnation-threshold", type=int, default=3)
    init.add_argument("--token-budget", type=int)
    init.add_argument("--cost-budget", type=float)
    init.set_defaults(handler=command_init)

    record = subparsers.add_parser("record", help="Record a phase status and evidence")
    record.add_argument("--path", type=Path, required=True)
    record.add_argument("--phase", choices=PHASES, required=True)
    record.add_argument("--status", choices=STATUSES[:-1], required=True)
    record.add_argument("--skill")
    record.add_argument("--evidence")
    record.add_argument("--artifact", action="append", default=[])
    record.set_defaults(handler=command_record)

    attempt = subparsers.add_parser("attempt", help="Append one bounded execution attempt")
    attempt.add_argument("--path", type=Path, required=True)
    attempt.add_argument("--phase", choices=PHASES, required=True)
    attempt.add_argument("--action", required=True)
    attempt.add_argument("--outcome", choices=OUTCOMES, required=True)
    attempt.add_argument("--error")
    attempt.add_argument("--tokens", type=int, default=0)
    attempt.add_argument("--cost", type=float, default=0.0)
    attempt.add_argument("--evidence")
    attempt.set_defaults(handler=command_attempt)

    cycle = subparsers.add_parser("new-cycle", help="Start a retry cycle from a chosen phase")
    cycle.add_argument("--path", type=Path, required=True)
    cycle.add_argument("--from-phase", choices=PHASES, required=True)
    cycle.add_argument("--reason", required=True)
    cycle.set_defaults(handler=command_new_cycle)

    decision = subparsers.add_parser("decision", help="Record a human gate decision")
    decision.add_argument("--path", type=Path, required=True)
    decision.add_argument("--gate", required=True)
    decision.add_argument("--decision", choices=DECISIONS, required=True)
    decision.add_argument("--evidence", required=True)
    decision.set_defaults(handler=command_decision)

    pause = subparsers.add_parser("pause", help="Activate the kill switch")
    pause.add_argument("--path", type=Path, required=True)
    pause.add_argument("--reason", required=True)
    pause.set_defaults(handler=command_pause)

    resume = subparsers.add_parser("resume", help="Resume after a recorded human decision")
    resume.add_argument("--path", type=Path, required=True)
    resume.add_argument("--evidence", required=True)
    resume.set_defaults(handler=command_resume)

    level = subparsers.add_parser("level", help="Record an autonomy-level change")
    level.add_argument("--path", type=Path, required=True)
    level.add_argument("--level", choices=LEVELS, required=True)
    level.add_argument("--evidence", required=True)
    level.add_argument("--human-approved", action="store_true")
    level.set_defaults(handler=command_level)

    check = subparsers.add_parser("check", help="Run the deterministic circuit breaker")
    check.add_argument("--path", type=Path, required=True)
    check.add_argument("--json", action="store_true")
    check.set_defaults(handler=command_check)

    context = subparsers.add_parser("context", help="Emit compact context for the next run")
    context.add_argument("--path", type=Path, required=True)
    context.add_argument("--window", type=int, default=5)
    context.set_defaults(handler=command_context)

    next_command = subparsers.add_parser("next", help="Show the next unresolved phase")
    next_command.add_argument("--path", type=Path, required=True)
    next_command.set_defaults(handler=command_next)

    show = subparsers.add_parser("show", help="Show current lifecycle state")
    show.add_argument("--path", type=Path, required=True)
    show.add_argument("--json", action="store_true")
    show.set_defaults(handler=command_show)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.handler(args) or 0)
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
