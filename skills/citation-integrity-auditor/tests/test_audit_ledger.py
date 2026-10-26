import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_ledger.py"
SPEC = importlib.util.spec_from_file_location("audit_ledger", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AuditLedgerTests(unittest.TestCase):
    def write_ledger(self, row):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / "ledger.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MODULE.REQUIRED)
            writer.writeheader()
            writer.writerow(row)
        return temp, path

    def valid_row(self):
        return {
            "claim_id": "C1", "claim_text": "A bounded claim.", "language": "en",
            "source_id": "S1", "title": "Verified Paper", "authors": "A. Author",
            "year": "2025", "identifier_type": "doi", "identifier": "10.1234/example.1",
            "landing_url": "https://doi.org/10.1234/example.1", "source_kind": "journal",
            "locator": "p. 4, Table 2", "support_type": "direct",
            "evidence_status": "primary-fulltext", "verified_at": "2026-10-26",
            "status_checked_at": "2026-10-26", "notes": "",
        }

    def test_accepts_structurally_valid_row(self):
        temp, path = self.write_ledger(self.valid_row())
        self.addCleanup(temp.cleanup)
        errors, warnings, count = MODULE.validate(path)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(count, 1)

    def test_rejects_missing_locator_for_full_text_support(self):
        row = self.valid_row()
        row["locator"] = ""
        temp, path = self.write_ledger(row)
        self.addCleanup(temp.cleanup)
        errors, _, _ = MODULE.validate(path)
        self.assertTrue(any("locator" in error for error in errors))

    def test_rejects_inconsistent_source_metadata(self):
        first = self.valid_row()
        second = self.valid_row()
        second["claim_id"] = "C2"
        second["title"] = "Different Paper"
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "ledger.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=MODULE.REQUIRED)
            writer.writeheader()
            writer.writerows([first, second])
        errors, _, _ = MODULE.validate(path)
        self.assertTrue(any("inconsistent" in error for error in errors))

    def test_rejects_direct_claim_from_metadata_only(self):
        row = self.valid_row()
        row["evidence_status"] = "primary-metadata"
        row["locator"] = ""
        temp, path = self.write_ledger(row)
        self.addCleanup(temp.cleanup)
        errors, _, _ = MODULE.validate(path)
        self.assertTrue(any("stronger than" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
