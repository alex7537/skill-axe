#!/usr/bin/env python3
"""Validate the portable structure of an A2D model-swap baseline manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TOKEN = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")
PLACEHOLDER = re.compile(r"REPLACE_ME|^0+$")


def nonempty(value: Any, field: str, errors: list[str], allow_placeholders: bool) -> None:
    if value is None or value == "" or value == []:
        errors.append(f"{field}: must be non-empty")
    elif not allow_placeholders and isinstance(value, str) and PLACEHOLDER.search(value):
        errors.append(f"{field}: placeholder value is not allowed")


def hex_value(value: Any, field: str, pattern: re.Pattern[str], errors: list[str], allow_placeholders: bool) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        errors.append(f"{field}: invalid hexadecimal identity")
    elif not allow_placeholders and PLACEHOLDER.fullmatch(value):
        errors.append(f"{field}: zero placeholder identity is not allowed")


def validate(payload: Any, *, allow_placeholders: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root: expected object"]
    if payload.get("schema_version") != "a2d-model-swap-baseline/v1":
        errors.append("schema_version: expected a2d-model-swap-baseline/v1")
    for field in ("baseline_id", "workspace_root"):
        nonempty(payload.get(field), field, errors, allow_placeholders)
    hex_value(payload.get("repository_commit"), "repository_commit", HEX40, errors, allow_placeholders)

    protected = payload.get("protected_files")
    if not isinstance(protected, list) or not protected:
        errors.append("protected_files: expected non-empty array")
        protected = []
    seen_paths: set[str] = set()
    for index, item in enumerate(protected):
        prefix = f"protected_files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: expected object")
            continue
        file_path = item.get("path")
        nonempty(file_path, f"{prefix}.path", errors, allow_placeholders)
        if isinstance(file_path, str):
            pure = PurePosixPath(file_path)
            if pure.is_absolute() or ".." in pure.parts:
                errors.append(f"{prefix}.path: must be workspace-relative without '..'")
            if file_path in seen_paths:
                errors.append(f"{prefix}.path: duplicate path {file_path!r}")
            seen_paths.add(file_path)
        hex_value(item.get("sha256"), f"{prefix}.sha256", HEX64, errors, allow_placeholders)

    environment = payload.get("environment")
    if not isinstance(environment, dict):
        errors.append("environment: expected object")
        environment = {}
    for field in ("type", "name", "identity"):
        nonempty(environment.get(field), f"environment.{field}", errors, allow_placeholders)

    argv = payload.get("command_argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
        errors.append("command_argv: expected non-empty string array")
        argv = []
    allowed = payload.get("allowed_placeholders")
    if not isinstance(allowed, list) or not allowed or any(not isinstance(item, str) for item in allowed):
        errors.append("allowed_placeholders: expected non-empty string array")
        allowed = []
    if len(allowed) != len(set(allowed)):
        errors.append("allowed_placeholders: duplicates are not allowed")
    used = [match for item in argv for match in TOKEN.findall(item)]
    unknown = sorted(set(used) - set(allowed))
    unused = sorted(set(allowed) - set(used))
    if unknown:
        errors.append("command_argv: unknown placeholder(s): " + ", ".join(unknown))
    if unused:
        errors.append("allowed_placeholders: unused placeholder(s): " + ", ".join(unused))
    if used.count("MODEL_BUNDLE") != 1:
        errors.append("command_argv: expected exactly one {MODEL_BUNDLE} placeholder")

    write_roots = payload.get("allowed_write_roots")
    if not isinstance(write_roots, list) or not write_roots:
        errors.append("allowed_write_roots: expected non-empty array")
    else:
        for index, value in enumerate(write_roots):
            nonempty(value, f"allowed_write_roots[{index}]", errors, allow_placeholders)

    runtime = payload.get("runtime_contract")
    if not isinstance(runtime, dict):
        errors.append("runtime_contract: expected object")
        runtime = {}
    for field in ("observation_schema", "action_schema", "preprocessing_revision", "normalization_revision", "success_profile"):
        nonempty(runtime.get(field), f"runtime_contract.{field}", errors, allow_placeholders)
    for field in ("execute_horizon", "max_actions"):
        value = runtime.get(field)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"runtime_contract.{field}: expected positive integer")
    rate = runtime.get("action_rate_hz")
    if not isinstance(rate, (int, float)) or rate <= 0:
        errors.append("runtime_contract.action_rate_hz: expected positive number")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"manifest: {exc}"]
    else:
        errors = validate(payload, allow_placeholders=args.allow_placeholders)
    result = {"valid": not errors, "errors": errors, "manifest": str(args.manifest)}
    if args.json:
        print(json.dumps(result, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print(f"Valid A2D model-swap baseline: {args.manifest}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
