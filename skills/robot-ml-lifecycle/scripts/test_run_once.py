#!/usr/bin/env python3

import fcntl
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import lifecycle_ledger


SCRIPT = Path(__file__).with_name("run_once.py")


class RunOnceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "robot-ml-lifecycle.json"
        lifecycle_ledger.command_init(
            SimpleNamespace(
                path=self.ledger,
                project="flow-matching",
                objective="verified evaluation loop",
                level="L1",
                cadence="manual",
                max_cycles=10,
                max_attempts_per_phase=3,
                max_consecutive_failures=3,
                stagnation_threshold=3,
                token_budget=None,
                cost_budget=None,
            )
        )
        self.state = self.root / "runner-state.json"
        self.log = self.root / "run-log.jsonl"
        self.inbox = self.root / "inbox.md"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_once(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--ledger",
                str(self.ledger),
                "--state",
                str(self.state),
                "--run-log",
                str(self.log),
                "--inbox",
                str(self.inbox),
                "--control-node",
                "test-node",
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_first_tick_is_ready_and_does_not_write_ledger(self) -> None:
        before = self.ledger.read_bytes()
        completed = self.run_once()
        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(payload["run"]["outcome"], "ready")
        self.assertEqual(payload["context"]["next_phase"], "frame")
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertEqual(lifecycle_ledger.read_ledger(self.ledger)["cycles"][0]["attempts"], [])

    def test_unchanged_tick_is_runner_noop_not_attempt(self) -> None:
        self.run_once()
        completed = self.run_once()
        payload = json.loads(completed.stdout)

        self.assertEqual(payload["run"]["outcome"], "noop")
        self.assertEqual(payload["run"]["consecutive_noops"], 1)
        self.assertEqual(lifecycle_ledger.read_ledger(self.ledger)["cycles"][0]["attempts"], [])
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 2)

    def test_ledger_change_resets_noop_and_returns_ready(self) -> None:
        self.run_once()
        self.run_once()
        lifecycle_ledger.command_record(
            SimpleNamespace(
                path=self.ledger,
                phase="frame",
                status="passed",
                skill="test",
                evidence="repository identity verified",
                artifact=["commit=abc123"],
            )
        )
        completed = self.run_once()
        payload = json.loads(completed.stdout)

        self.assertEqual(payload["run"]["outcome"], "ready")
        self.assertEqual(payload["run"]["consecutive_noops"], 0)
        self.assertEqual(payload["context"]["next_phase"], "source")

    def test_repeated_noops_backoff_then_pause_runner_only(self) -> None:
        self.run_once("--max-consecutive-noops", "1")
        first = json.loads(self.run_once("--max-consecutive-noops", "1").stdout)
        second = json.loads(self.run_once("--max-consecutive-noops", "1").stdout)
        paused_call = self.run_once("--max-consecutive-noops", "1")
        paused = json.loads(paused_call.stdout)

        self.assertEqual(first["run"]["backoff_level"], 1)
        self.assertEqual(second["run"]["backoff_level"], 2)
        self.assertEqual(paused_call.returncode, 2)
        self.assertEqual(paused["run"]["outcome"], "paused")
        self.assertEqual(paused["run"]["breaker"]["trigger"], "runner-noop-pause")
        self.assertTrue(self.inbox.exists())
        self.assertIn("event source/cadence", self.inbox.read_text(encoding="utf-8"))
        self.assertFalse(lifecycle_ledger.read_ledger(self.ledger)["control"]["paused"])

    def test_ledger_breaker_renders_escalation(self) -> None:
        lifecycle_ledger.command_pause(SimpleNamespace(path=self.ledger, reason="operator stop"))
        completed = self.run_once()
        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(payload["run"]["outcome"], "escalate")
        self.assertIn("Exact decision requested", self.inbox.read_text(encoding="utf-8"))

    def test_control_node_change_is_rejected(self) -> None:
        self.run_once()
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--ledger",
                str(self.ledger),
                "--state",
                str(self.state),
                "--control-node",
                "other-node",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 3)
        self.assertIn("Single-writer boundary violation", completed.stderr)

    def test_overlapping_local_run_is_rejected(self) -> None:
        lock = self.root / "runner.lock"
        with lock.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            completed = self.run_once("--lock", str(lock))

        self.assertEqual(completed.returncode, 3)
        self.assertIn("owns the local control-node lock", completed.stderr)

    def test_result_contracts_are_valid_json_schemas(self) -> None:
        assets = SCRIPT.parent.parent / "assets"
        for name in ("executor-result.schema.json", "verifier-result.schema.json"):
            schema = json.loads((assets / name).read_text(encoding="utf-8"))
            self.assertEqual(schema["type"], "object")
            self.assertTrue(schema["required"])


if __name__ == "__main__":
    unittest.main()
