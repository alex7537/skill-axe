#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import lifecycle_ledger


class LifecycleLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "ledger.json"
        lifecycle_ledger.command_init(
            SimpleNamespace(path=self.path, project="psi-policy", objective="verified policy release")
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

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
        self.assertEqual(tuple(data["cycles"][0]["phases"]), lifecycle_ledger.PHASES)
        self.assertEqual(data["active_cycle"], 1)

    def test_cannot_jump_unresolved_phase(self) -> None:
        with self.assertRaises(lifecycle_ledger.LedgerError):
            self.record("train", "passed")

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


if __name__ == "__main__":
    unittest.main()
