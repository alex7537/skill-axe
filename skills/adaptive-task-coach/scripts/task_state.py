#!/usr/bin/env python3
"""Create and safely update adaptive-task-coach JSON state."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STEP_STATUSES = {"pending", "in_progress", "completed", "blocked"}
TASK_STATUSES = {"active", "completed", "blocked"}
FEEDBACK_KINDS = {
    "understood",
    "needs_explanation",
    "attempted_success",
    "attempted_failed",
    "blocker",
    "scope_change",
    "preference",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"State file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if data.get("schema_version") != 1:
        raise SystemExit(f"Unsupported schema_version in {path}")
    return data


def save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["revision"] = int(data.get("revision", 0)) + 1
    data["updated_at"] = now()
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def find_step(data: dict[str, Any], step_id: str) -> dict[str, Any]:
    for step in data["steps"]:
        if step["id"] == step_id:
            return step
    raise SystemExit(f"Unknown step id: {step_id}")


def command_init(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing state: {path}")
    timestamp = now()
    data = {
        "schema_version": 1,
        "revision": 0,
        "objective": args.objective,
        "acceptance_criteria": args.acceptance,
        "status": "active",
        "status_reason": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "steps": [],
        "feedback": [],
    }
    save(path, data)


def command_add_step(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    data = load(path)
    if any(step["id"] == args.id for step in data["steps"]):
        raise SystemExit(f"Duplicate step id: {args.id}")
    known_ids = {step["id"] for step in data["steps"]}
    missing = [item for item in args.depends_on if item not in known_ids]
    if missing:
        raise SystemExit(f"Dependencies must already exist: {', '.join(missing)}")
    timestamp = now()
    data["steps"].append(
        {
            "id": args.id,
            "title": args.title,
            "outcome": args.outcome,
            "verification": args.verification,
            "depends_on": args.depends_on,
            "status": "pending",
            "evidence": [],
            "status_reason": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    save(path, data)


def command_transition(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    data = load(path)
    step = find_step(data, args.id)
    old_status = step["status"]
    if old_status == "completed" and args.status != "completed":
        raise SystemExit("Completed steps are immutable; add a superseding step")
    if args.status == "in_progress":
        active = [
            item["id"]
            for item in data["steps"]
            if item["status"] == "in_progress" and item["id"] != args.id
        ]
        if active:
            raise SystemExit(f"Another step is already in_progress: {active[0]}")
        incomplete = [
            dep
            for dep in step["depends_on"]
            if find_step(data, dep)["status"] != "completed"
        ]
        if incomplete:
            raise SystemExit(f"Incomplete dependencies: {', '.join(incomplete)}")
    if args.status == "completed" and not (args.evidence or step["evidence"]):
        raise SystemExit("Completing a step requires --evidence")
    if args.status == "blocked" and not args.reason:
        raise SystemExit("Blocking a step requires --reason")
    if args.evidence:
        step["evidence"].append(args.evidence)
    step["status"] = args.status
    step["status_reason"] = args.reason
    step["updated_at"] = now()
    save(path, data)


def command_feedback(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    data = load(path)
    if args.id:
        find_step(data, args.id)
    data["feedback"].append(
        {
            "timestamp": now(),
            "step_id": args.id,
            "kind": args.kind,
            "message": args.message,
        }
    )
    save(path, data)


def command_set_task_status(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser()
    data = load(path)
    if args.status == "completed":
        incomplete = [
            step["id"] for step in data["steps"] if step["status"] != "completed"
        ]
        if not data["steps"]:
            raise SystemExit("Completing a task requires at least one step")
        if incomplete:
            raise SystemExit(f"Incomplete steps: {', '.join(incomplete)}")
    if args.status == "blocked" and not args.reason:
        raise SystemExit("Blocking a task requires --reason")
    data["status"] = args.status
    data["status_reason"] = args.reason
    save(path, data)


def command_show(args: argparse.Namespace) -> None:
    data = load(Path(args.path).expanduser())
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print(f"Objective: {data['objective']}")
    print(f"Status: {data['status']}  Revision: {data['revision']}")
    print("Acceptance:")
    for criterion in data["acceptance_criteria"]:
        print(f"  - {criterion}")
    print("Steps:")
    for step in data["steps"]:
        dependencies = ",".join(step["depends_on"]) or "-"
        print(f"  [{step['status']:^11}] {step['id']}: {step['title']} (deps: {dependencies})")
    print(f"Feedback entries: {len(data['feedback'])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new state file")
    init_parser.add_argument("--path", required=True)
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--acceptance", action="append", required=True)
    init_parser.set_defaults(handler=command_init)

    add_parser = subparsers.add_parser("add-step", help="Append a pending step")
    add_parser.add_argument("--path", required=True)
    add_parser.add_argument("--id", required=True)
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--outcome", required=True)
    add_parser.add_argument("--verification", required=True)
    add_parser.add_argument("--depends-on", action="append", default=[])
    add_parser.set_defaults(handler=command_add_step)

    transition_parser = subparsers.add_parser(
        "transition", help="Change a step status"
    )
    transition_parser.add_argument("--path", required=True)
    transition_parser.add_argument("--id", required=True)
    transition_parser.add_argument("--status", choices=sorted(STEP_STATUSES), required=True)
    transition_parser.add_argument("--evidence")
    transition_parser.add_argument("--reason")
    transition_parser.set_defaults(handler=command_transition)

    feedback_parser = subparsers.add_parser("feedback", help="Append user feedback")
    feedback_parser.add_argument("--path", required=True)
    feedback_parser.add_argument("--id")
    feedback_parser.add_argument("--kind", choices=sorted(FEEDBACK_KINDS), required=True)
    feedback_parser.add_argument("--message", required=True)
    feedback_parser.set_defaults(handler=command_feedback)

    status_parser = subparsers.add_parser(
        "set-task-status", help="Change overall task status"
    )
    status_parser.add_argument("--path", required=True)
    status_parser.add_argument("--status", choices=sorted(TASK_STATUSES), required=True)
    status_parser.add_argument("--reason")
    status_parser.set_defaults(handler=command_set_task_status)

    show_parser = subparsers.add_parser("show", help="Display current state")
    show_parser.add_argument("--path", required=True)
    show_parser.add_argument("--json", action="store_true")
    show_parser.set_defaults(handler=command_show)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
