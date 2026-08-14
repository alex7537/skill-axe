#!/usr/bin/env python3

import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import lifecycle_ledger


class LifecycleLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "ledger.json"
        lifecycle_ledger.command_init(self.init_args())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def init_args(self, **overrides):
        values = {
            "path": self.path,
            "project": "psi-policy",
            "objective": "verified policy release",
            "level": "L1",
            "cadence": "manual",
            "max_cycles": 10,
            "max_attempts_per_phase": 3,
            "max_consecutive_failures": 3,
            "stagnation_threshold": 3,
            "token_budget": None,
            "cost_budget": None,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def record(self, phase: str, status: str, evidence: str = "verified") -> None:
        lifecycle_ledger.command_record(
            SimpleNamespace(
                path=self.path,
                phase=phase,
                status=status,
                skill="test-skill",
                evidence=evidence,
                artifact=[f"{phase}_id=value"],
            )
        )

    def test_init_has_expected_phases(self) -> None:
        data = lifecycle_ledger.read_ledger(self.path)
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(tuple(data["cycles"][0]["phases"]), lifecycle_ledger.PHASES)
        self.assertEqual(data["active_cycle"], 1)
        self.assertEqual(data["control"]["autonomy_level"], "L1")
        self.assertEqual(data["cycles"][0]["attempts"], [])

    def test_cannot_jump_unresolved_phase(self) -> None:
        with self.assertRaises(lifecycle_ledger.LedgerError):
            self.record("train", "passed")

    def test_attempt_must_target_next_unresolved_phase(self) -> None:
        with self.assertRaises(lifecycle_ledger.LedgerError):
            lifecycle_ledger.command_attempt(
                SimpleNamespace(
                    path=self.path,
                    phase="train",
                    action="launch task",
                    outcome="failure",
                    error="not ready",
                    tokens=0,
                    cost=0.0,
                    evidence="blocked by prerequisites",
                )
            )

    def test_cycle_preserves_old_evidence_and_carries_prefix(self) -> None:
        for phase in lifecycle_ledger.PHASES[:6]:
            self.record(phase, "passed")
        lifecycle_ledger.command_new_cycle(
            SimpleNamespace(path=self.path, from_phase="train_plan", reason="revise schedule")
        )
        data = lifecycle_ledger.read_ledger(self.path)
        self.assertEqual(len(data["cycles"]), 2)
        self.assertEqual(data["cycles"][0]["phases"]["frame"]["status"], "passed")
        self.assertEqual(data["cycles"][1]["phases"]["frame"]["status"], "carried")
        self.assertEqual(data["cycles"][1]["phases"]["train_plan"]["status"], "pending")

    def test_json_remains_valid_after_transition(self) -> None:
        self.record("frame", "passed")
        parsed = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(parsed["cycles"][0]["phases"]["frame"]["status"], "passed")

    def test_schema_one_is_migrated_in_memory(self) -> None:
        data = lifecycle_ledger.read_ledger(self.path)
        data.pop("control")
        data.pop("decisions")
        data["schema_version"] = 1
        data["cycles"][0].pop("attempts")
        self.path.write_text(json.dumps(data), encoding="utf-8")

        migrated = lifecycle_ledger.read_ledger(self.path)

        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["control"]["autonomy_level"], "L1")
        self.assertEqual(migrated["decisions"], [])
        self.assertEqual(migrated["cycles"][0]["attempts"], [])

    def attempt(self, error: str, tokens: int = 0, cost: float = 0.0) -> None:
        lifecycle_ledger.command_attempt(
            SimpleNamespace(
                path=self.path,
                phase="frame",
                action="inspect repository",
                outcome="failure",
                error=error,
                tokens=tokens,
                cost=cost,
                evidence="command failed",
            )
        )

    def test_repeated_normalized_error_trips_stagnation_breaker(self) -> None:
        for run in range(3):
            self.attempt(f"failed at /tmp/run-{run}/model.ckpt with code {500 + run}")

        decision = lifecycle_ledger.breaker_decision(lifecycle_ledger.read_ledger(self.path))

        self.assertEqual(decision["decision"], "ESCALATE")
        self.assertEqual(decision["trigger"], "stagnation")

    def test_pause_activates_kill_switch_and_resume_records_decision(self) -> None:
        lifecycle_ledger.command_pause(SimpleNamespace(path=self.path, reason="operator stop"))
        paused = lifecycle_ledger.breaker_decision(lifecycle_ledger.read_ledger(self.path))
        self.assertEqual(paused["trigger"], "paused")

        lifecycle_ledger.command_resume(SimpleNamespace(path=self.path, evidence="operator approved"))
        data = lifecycle_ledger.read_ledger(self.path)
        self.assertFalse(data["control"]["paused"])
        self.assertEqual(data["decisions"][-1]["gate"], "resume-loop")

    def test_budget_trips_breaker(self) -> None:
        data = lifecycle_ledger.read_ledger(self.path)
        data["control"]["token_budget"] = 100
        lifecycle_ledger.write_ledger(self.path, data)
        self.attempt("one failure", tokens=100)

        decision = lifecycle_ledger.breaker_decision(lifecycle_ledger.read_ledger(self.path))

        self.assertEqual(decision["trigger"], "token-budget")

    def test_cycle_cap_prevents_another_cycle(self) -> None:
        data = lifecycle_ledger.read_ledger(self.path)
        data["control"]["max_cycles"] = 1
        lifecycle_ledger.write_ledger(self.path, data)
        with self.assertRaises(lifecycle_ledger.LedgerError):
            lifecycle_ledger.command_new_cycle(
                SimpleNamespace(path=self.path, from_phase="frame", reason="retry")
            )

    def test_autonomy_increase_requires_human_approval(self) -> None:
        args = SimpleNamespace(
            path=self.path,
            level="L2",
            evidence="operator approved assisted execution",
            human_approved=False,
        )
        with self.assertRaises(lifecycle_ledger.LedgerError):
            lifecycle_ledger.command_level(args)
        args.human_approved = True
        lifecycle_ledger.command_level(args)
        self.assertEqual(lifecycle_ledger.read_ledger(self.path)["control"]["autonomy_level"], "L2")

    def test_context_is_compact_and_window_is_validated(self) -> None:
        for run in range(3):
            self.attempt(f"failure {run}\nline two\nline three\nline four")
        output = io.StringIO()
        with redirect_stdout(output):
            lifecycle_ledger.command_context(SimpleNamespace(path=self.path, window=2))
        payload = json.loads(output.getvalue())
        self.assertEqual(len(payload["recent_attempts"]), 2)
        self.assertIn("pruned", payload["recent_attempts"][-1]["error"])
        with self.assertRaises(lifecycle_ledger.LedgerError):
            lifecycle_ledger.command_context(SimpleNamespace(path=self.path, window=0))


if __name__ == "__main__":
    unittest.main()
