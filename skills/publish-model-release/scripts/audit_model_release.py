#!/usr/bin/env python3
"""Read-only audit for a staged GitHub/Hugging Face model release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


WEIGHT_SUFFIXES = {
    ".safetensors",
    ".ckpt",
    ".pt",
    ".pth",
    ".bin",
    ".onnx",
    ".engine",
    ".plan",
    ".tgz",
    ".tar",
    ".gz",
}
CONFIG_NAMES = {
    "config.yaml",
    "config.yml",
    "config.json",
    "model_config.yaml",
    "model_config.yml",
    "model_config.json",
}
NORMALIZATION_HINTS = ("normalization", "normalizer", "norm_stats", "stats")
INFERENCE_HINTS = ("inference", "predict", "serve", "deployment", "runtime")
SENSITIVE_NAME_PARTS = (
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    "credentials",
    "access_token",
    "secret",
)
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".py",
    ".sh",
}
SECRET_PATTERNS = {
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:github_pat_|gh[opusr]_)[A-Za-z0-9_]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "authorization bearer": re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/-]{12,}"),
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
PLACEHOLDER = re.compile(r"(?i)(replace[-_ ]?me|full_git_commit|github_repository_url|owner/model-name)")


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_files(root: Path) -> list[Path]:
    return sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: str(p.relative_to(root)))


def load_manifest(path: Path, findings: list[Finding]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        findings.append(Finding("error", "manifest-invalid", f"Cannot parse {path.name}: {exc}"))
        return None
    if not isinstance(value, dict):
        findings.append(Finding("error", "manifest-shape", "release_manifest.json must contain a JSON object"))
        return None
    return value


def check_manifest(
    root: Path,
    manifest: dict[str, Any],
    intent: str,
    skip_hashes: bool,
    findings: list[Finding],
) -> None:
    required = ("schema_version", "model_id", "release", "artifact_type", "source", "weights", "license")
    for key in required:
        if key not in manifest:
            findings.append(Finding("error", "manifest-field", f"Manifest is missing required field: {key}"))

    artifact_type = manifest.get("artifact_type")
    if artifact_type and artifact_type != intent:
        findings.append(
            Finding("warning", "intent-mismatch", f"Requested intent is {intent!r}, manifest artifact_type is {artifact_type!r}")
        )

    source = manifest.get("source")
    if not isinstance(source, dict):
        findings.append(Finding("error", "source-shape", "Manifest source must be an object"))
    else:
        if not source.get("git_url"):
            findings.append(Finding("error", "source-url", "Manifest source.git_url is missing"))
        commit = source.get("git_commit", "")
        if not isinstance(commit, str) or not GIT_SHA.fullmatch(commit):
            findings.append(Finding("error", "source-commit", "source.git_commit must be a full 40-character Git SHA"))

    weights = manifest.get("weights")
    if not isinstance(weights, list) or not weights:
        findings.append(Finding("error", "weights-shape", "Manifest weights must be a non-empty list"))
    else:
        for index, item in enumerate(weights):
            label = f"weights[{index}]"
            if not isinstance(item, dict):
                findings.append(Finding("error", "weight-entry", f"{label} must be an object"))
                continue
            check_hashed_entry(root, item, label, skip_hashes, findings)
            for key in ("role", "format"):
                if not item.get(key):
                    findings.append(Finding("warning", "weight-metadata", f"{label}.{key} is missing"))

    for key in ("config", "normalization"):
        item = manifest.get(key)
        if item is not None:
            if not isinstance(item, dict):
                findings.append(Finding("error", f"{key}-shape", f"Manifest {key} must be an object"))
            else:
                check_hashed_entry(root, item, key, skip_hashes, findings)

    license_value = manifest.get("license")
    if not isinstance(license_value, str) or not license_value.strip() or PLACEHOLDER.search(license_value):
        findings.append(Finding("error", "license-unresolved", "Manifest license is missing or unresolved"))


def check_hashed_entry(
    root: Path,
    item: dict[str, Any],
    label: str,
    skip_hashes: bool,
    findings: list[Finding],
) -> None:
    rel = item.get("path")
    expected = item.get("sha256")
    if not isinstance(rel, str) or not rel:
        findings.append(Finding("error", "artifact-path", f"{label}.path is missing"))
        return
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        findings.append(Finding("error", "artifact-escape", f"{label}.path escapes the release directory: {rel}"))
        return
    if not target.is_file():
        findings.append(Finding("error", "artifact-missing", f"Manifest references missing file: {rel}"))
        return
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        findings.append(Finding("error", "hash-shape", f"{label}.sha256 must be 64 lowercase hexadecimal characters"))
        return
    if expected == "0" * 64:
        findings.append(Finding("error", "hash-placeholder", f"{label}.sha256 is still a placeholder"))
        return
    if not skip_hashes:
        actual = sha256_file(target)
        if actual != expected:
            findings.append(Finding("error", "hash-mismatch", f"SHA256 mismatch for {rel}: expected {expected}, got {actual}"))


def scan_sensitive_content(root: Path, files: list[Path], findings: list[Finding]) -> None:
    for path in files:
        rel = str(path.relative_to(root))
        lowered = path.name.lower()
        if any(part in lowered for part in SENSITIVE_NAME_PARTS):
            findings.append(Finding("error", "sensitive-filename", f"Potential credential file in release: {rel}"))
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(Finding("error", "secret-pattern", f"Potential {name} found in {rel}"))
        if PLACEHOLDER.search(text):
            findings.append(Finding("error", "placeholder", f"Unresolved placeholder found in {rel}"))


def audit(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    root = args.release_dir.expanduser().resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        findings.append(Finding("error", "directory-missing", f"Release directory does not exist: {root}"))
        return result(root, [], findings), 2

    files = relative_files(root)
    rels = [str(p.relative_to(root)) for p in files]
    names = {p.name for p in files}

    if "README.md" not in names:
        findings.append(Finding("error", "model-card-missing", "README.md model card is required"))
    if "release_manifest.json" not in names:
        findings.append(Finding("error", "manifest-missing", "release_manifest.json is required"))

    weight_files = [p for p in files if any(p.name.lower().endswith(suffix) for suffix in WEIGHT_SUFFIXES)]
    if not weight_files:
        findings.append(Finding("error", "weights-missing", "No recognized weight or deployment artifact found"))

    if not any(p.name.lower() in CONFIG_NAMES for p in files):
        findings.append(Finding("error", "config-missing", "No resolved model config file found"))

    normalization_files = [p for p in files if any(hint in p.name.lower() for hint in NORMALIZATION_HINTS)]
    if args.require_normalization and not normalization_files:
        findings.append(Finding("error", "normalization-missing", "Normalization is required but no statistics/config file was found"))
    elif not normalization_files:
        findings.append(Finding("warning", "normalization-absent", "No normalization file found; confirm the model does not require one"))

    if args.intent == "deploy" and not any(any(hint in str(p.relative_to(root)).lower() for hint in INFERENCE_HINTS) for p in files):
        findings.append(Finding("warning", "inference-entrypoint", "Deploy intent has no obvious inference/runtime entry point"))

    manifest_path = root / "release_manifest.json"
    if manifest_path.is_file():
        manifest = load_manifest(manifest_path, findings)
        if manifest is not None:
            check_manifest(root, manifest, args.intent, args.skip_hashes, findings)

    scan_sensitive_content(root, files, findings)

    if len(files) > 10_000:
        findings.append(Finding("warning", "file-count", f"Release contains {len(files)} files; consolidate generated shards/caches where possible"))

    payload = result(root, rels, findings)
    exit_code = 1 if any(f.severity == "error" for f in findings) else 0
    return payload, exit_code


def result(root: Path, files: list[str], findings: list[Finding]) -> dict[str, Any]:
    return {
        "release_dir": str(root),
        "file_count": len(files),
        "total_bytes": sum((root / p).stat().st_size for p in files) if root.is_dir() else 0,
        "status": "fail" if any(f.severity == "error" for f in findings) else "pass",
        "findings": [asdict(f) for f in findings],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_dir", type=Path, help="Staged model release directory")
    parser.add_argument(
        "--intent",
        choices=("finetune", "resume", "deploy", "evaluate"),
        default="finetune",
        help="Primary supported consumer intent (default: finetune)",
    )
    parser.add_argument("--require-normalization", action="store_true", help="Fail if no normalization statistics/config is found")
    parser.add_argument("--skip-hashes", action="store_true", help="Validate hash fields without reading artifact bytes")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = audit(args)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Model release audit: {payload['status'].upper()}")
        print(f"Directory: {payload['release_dir']}")
        print(f"Files: {payload['file_count']}  Bytes: {payload['total_bytes']}")
        for finding in payload["findings"]:
            print(f"[{finding['severity'].upper()}] {finding['code']}: {finding['message']}")
        if not payload["findings"]:
            print("No findings.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
