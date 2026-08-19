#!/usr/bin/env python3
"""Run one read-only L1 lifecycle control-plane tick.

This runner never invokes an executor and never writes the lifecycle ledger.
It owns only its local lock, runner state, run log, and escalation inbox.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNNER_SCHEMA_VERSION = 1


class RunnerError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_state(path: Path, control_node: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": RUNNER_SCHEMA_VERSION,
            "control_node": control_node,
            "status": "active",
            "consecutive_noops": 0,
            "backoff_level": 0,
            "last_ledger_sha256": None,
            "last_run_id": None,
            "updated_at": None,
        }
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerError(f"Cannot read runner state {path}: {exc}") from exc
    if state.get("schema_version") != RUNNER_SCHEMA_VERSION:
        raise RunnerError(f"Unsupported runner state schema: {state.get('schema_version')}")
    if state.get("control_node") != control_node:
        raise RunnerError(
            "Single-writer boundary violation: runner state belongs to "
            f"{state.get('control_node')!r}, current control node is {control_node!r}"
        )
    return state


def run_ledger_command(ledger_cli: Path, *arguments: str, accepted_codes: set[int]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ledger_cli), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in accepted_codes:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no diagnostic output"
        raise RunnerError(f"Ledger command failed ({completed.returncode}): {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RunnerError(f"Ledger command did not return JSON: {completed.stdout[:300]}") from exc


def ledger_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise RunnerError(f"Cannot fingerprint ledger {path}: {exc}") from exc


def requested_decision(breaker: dict[str, Any]) -> str:
    trigger = breaker.get("trigger")
    if trigger == "paused":
        return "Confirm whether to keep the lifecycle paused or explicitly resume it."
    if trigger in {"attempt-cap", "no-progress", "stagnation"}:
        return "Choose whether to revise the hypothesis/configuration, start a new bounded cycle, or stop."
    if trigger in {"token-budget", "cost-budget"}:
        return "Choose whether to stop or approve a new explicit budget; do not silently raise the current limit."
    if trigger == "runner-noop-pause":
        return "Inspect the event source/cadence, then explicitly reset runner state before scheduling another run."
    return "Review the breaker evidence and provide the exact bounded decision required to continue."


def render_escalation(path: Path, run: dict[str, Any], context: dict[str, Any]) -> None:
    breaker = context["breaker"]
    lines = [
        "# Robot ML lifecycle escalation",
        "",
        f"- Run: `{run['run_id']}`",
        f"- Project: `{context['project']}`",
        f"- Cycle / phase: `{context['active_cycle']}` / `{context['next_phase']}`",
        f"- Trigger: `{breaker['trigger']}`",
        f"- Reason: {breaker['reason']}",
        f"- Attempts / tokens / cost: `{breaker['attempts']}` / `{breaker['tokens']}` / `{breaker['cost']}`",
        "",
        "## Exact decision requested",
        "",
        requested_decision(breaker),
        "",
        "The runner did not modify the lifecycle ledger and did not invoke an executor.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def one_tick(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    control_node = args.control_node or socket.gethostname()
    lock_name = hashlib.sha256(str(args.ledger.resolve()).encode("utf-8")).hexdigest()[:16]
    lock_path = args.lock or Path(tempfile.gettempdir()) / f"robot-ml-runner-{lock_name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RunnerError(f"Another run owns the local control-node lock: {lock_path}") from exc

        state = read_state(args.state, control_node)
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        started_at = now()
        ledger_hash = ledger_sha256(args.ledger)
        breaker = run_ledger_command(
            args.ledger_cli,
            "check",
            "--path",
            str(args.ledger),
            "--json",
            accepted_codes={0, 2},
        )
        context = run_ledger_command(
            args.ledger_cli,
            "context",
            "--path",
            str(args.ledger),
            "--window",
            str(args.context_window),
            accepted_codes={0},
        )

        outcome = "ready"
        exit_code = 0
        if state["status"] == "paused":
            outcome = "paused"
            exit_code = 2
        elif breaker["decision"] == "ESCALATE":
            outcome = "escalate"
            exit_code = 2
        elif breaker["decision"] == "COMPLETE":
            outcome = "complete"
            state["consecutive_noops"] = 0
            state["backoff_level"] = 0
        elif state["last_ledger_sha256"] == ledger_hash:
            outcome = "noop"
            state["consecutive_noops"] += 1
            threshold = args.max_consecutive_noops
            if state["consecutive_noops"] >= threshold * (args.max_backoffs + 1):
                state["status"] = "paused"
                outcome = "paused"
                exit_code = 2
            elif state["consecutive_noops"] % threshold == 0:
                state["backoff_level"] += 1
        else:
            state["consecutive_noops"] = 0
            state["backoff_level"] = 0

        if outcome == "paused" and breaker["decision"] != "ESCALATE":
            breaker = {
                **breaker,
                "decision": "ESCALATE",
                "trigger": "runner-noop-pause",
                "reason": (
                    "Runner paused after "
                    f"{state['consecutive_noops']} unchanged polls and {state['backoff_level']} backoff rounds"
                ),
            }
            context["breaker"] = breaker

        run = {
            "schema_version": 1,
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": now(),
            "control_node": control_node,
            "outcome": outcome,
            "cycle": context["active_cycle"],
            "phase": context["next_phase"],
            "breaker": breaker,
            "ledger_sha256": ledger_hash,
            "consecutive_noops": state["consecutive_noops"],
            "backoff_level": state["backoff_level"],
            "cadence_multiplier": 2 ** state["backoff_level"],
        }

        state["last_ledger_sha256"] = ledger_hash
        state["last_run_id"] = run_id
        state["updated_at"] = run["finished_at"]
        atomic_write_json(args.state, state)
        append_jsonl(args.run_log, run)
        if outcome in {"escalate", "paused"}:
            render_escalation(args.inbox, run, context)

        result = {"run": run, "context": context if outcome == "ready" else None}
        return result, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument(
        "--ledger-cli",
        type=Path,
        default=Path(__file__).with_name("lifecycle_ledger.py"),
    )
    parser.add_argument("--state", type=Path)
    parser.add_argument("--run-log", type=Path)
    parser.add_argument("--inbox", type=Path)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--control-node")
    parser.add_argument("--context-window", type=int, default=5)
    parser.add_argument("--max-consecutive-noops", type=int, default=3)
    parser.add_argument("--max-backoffs", type=int, default=2)
    return parser


def resolve_defaults(args: argparse.Namespace) -> None:
    base = args.ledger.parent
    args.state = args.state or base / "robot-ml-runner-state.json"
    args.run_log = args.run_log or base / "robot-ml-run-log.jsonl"
    args.inbox = args.inbox or base / "robot-ml-inbox.md"
    if args.context_window < 1 or args.max_consecutive_noops < 1 or args.max_backoffs < 1:
        raise RunnerError("context window, noop threshold, and max backoffs must be positive")


def main() -> int:
    args = build_parser().parse_args()
    try:
        resolve_defaults(args)
        result, exit_code = one_tick(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return exit_code
    except RunnerError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
