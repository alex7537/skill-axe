#!/usr/bin/env python3

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import audit_model_release


class AuditModelReleaseTest(unittest.TestCase):
    def make_release(self, root: Path) -> None:
        files = {
            "README.md": "# Test model\n\nLicense: Apache-2.0\n",
            "model.safetensors": "test weights\n",
            "config.yaml": "architecture: test-policy\n",
            "normalization_stats.json": '{"method": "identity"}\n',
        }
        for name, content in files.items():
            (root / name).write_text(content, encoding="utf-8")

        def digest(name: str) -> str:
            return hashlib.sha256((root / name).read_bytes()).hexdigest()

        manifest = {
            "schema_version": 1,
            "model_id": "example/test-policy",
            "release": "v1.0.0",
            "artifact_type": "finetune",
            "source": {
                "git_url": "https://github.com/example/test-policy",
                "git_commit": "1" * 40,
            },
            "weights": [
                {
                    "path": "model.safetensors",
                    "sha256": digest("model.safetensors"),
                    "role": "policy",
                    "variant": "ema",
                    "format": "safetensors",
                }
            ],
            "config": {"path": "config.yaml", "sha256": digest("config.yaml")},
            "normalization": {
                "path": "normalization_stats.json",
                "sha256": digest("normalization_stats.json"),
            },
            "license": "apache-2.0",
        }
        (root / "release_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def args(self, root: Path) -> SimpleNamespace:
        return SimpleNamespace(
            release_dir=root,
            intent="finetune",
            require_normalization=True,
            skip_hashes=False,
        )

    def test_valid_release_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_release(root)
            payload, exit_code = audit_model_release.audit(self.args(root))
            self.assertEqual(exit_code, 0, payload)
            self.assertEqual(payload["status"], "pass")

    def test_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_release(root)
            (root / "model.safetensors").write_text("changed", encoding="utf-8")
            payload, exit_code = audit_model_release.audit(self.args(root))
            self.assertEqual(exit_code, 1)
            self.assertTrue(any(f["code"] == "hash-mismatch" for f in payload["findings"]))

    def test_secret_pattern_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_release(root)
            (root / "notes.txt").write_text("token=hf_abcdefghijklmnopqrstuvwxyz", encoding="utf-8")
            payload, exit_code = audit_model_release.audit(self.args(root))
            self.assertEqual(exit_code, 1)
            self.assertTrue(any(f["code"] == "secret-pattern" for f in payload["findings"]))


if __name__ == "__main__":
    unittest.main()
