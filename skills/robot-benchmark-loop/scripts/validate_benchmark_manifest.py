#!/usr/bin/env python3
"""Validate a robot-benchmark run manifest using only the Python stdlib."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
PLACEHOLDER = re.compile(r"REPLACE_ME|^0+$")


def require_dict(parent: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key}: expected object")
        return {}
    return value


def require_nonempty(value: Any, path: str, errors: list[str], *, allow_placeholders: bool) -> None:
    if value is None or value == "" or value == []:
        errors.append(f"{path}: must be non-empty")
    elif not allow_placeholders and isinstance(value, str) and PLACEHOLDER.search(value):
        errors.append(f"{path}: placeholder value is not allowed")


def require_sha256(value: Any, path: str, errors: list[str], *, allow_placeholders: bool) -> None:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        errors.append(f"{path}: expected 64 lowercase hex characters")
    elif not allow_placeholders and PLACEHOLDER.fullmatch(value):
        errors.append(f"{path}: zero placeholder hash is not allowed")


def validate(data: Any, *, allow_placeholders: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root: expected object"]

    if data.get("schema_version") != "robot-benchmark-run/v1":
        errors.append("schema_version: expected robot-benchmark-run/v1")
    require_nonempty(data.get("run_id"), "run_id", errors, allow_placeholders=allow_placeholders)
    require_nonempty(data.get("output_root"), "output_root", errors, allow_placeholders=allow_placeholders)

    benchmark = require_dict(data, "benchmark", errors)
    for key in ("name", "version", "repository", "asset_release"):
        require_nonempty(benchmark.get(key), f"benchmark.{key}", errors, allow_placeholders=allow_placeholders)
    commit = benchmark.get("git_commit")
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        errors.append("benchmark.git_commit: expected 40 lowercase hex characters")
    elif not allow_placeholders and PLACEHOLDER.fullmatch(commit):
        errors.append("benchmark.git_commit: zero placeholder commit is not allowed")
    for key in ("task_registry_sha256", "capability_registry_sha256", "asset_selection_sha256"):
        require_sha256(benchmark.get(key), f"benchmark.{key}", errors, allow_placeholders=allow_placeholders)

    policy = require_dict(data, "policy", errors)
    for key in (
        "name", "adapter_revision", "protocol", "checkpoint_role", "observation_schema",
        "action_schema", "preprocessing_revision", "normalization_revision",
    ):
        require_nonempty(policy.get(key), f"policy.{key}", errors, allow_placeholders=allow_placeholders)
    require_sha256(policy.get("checkpoint_sha256"), "policy.checkpoint_sha256", errors, allow_placeholders=allow_placeholders)

    environment = require_dict(data, "environment", errors)
    for key in ("simulator", "simulator_version"):
        require_nonempty(environment.get(key), f"environment.{key}", errors, allow_placeholders=allow_placeholders)
    digest = environment.get("container_digest")
    if not isinstance(digest, str) or not SHA256_DIGEST.fullmatch(digest):
        errors.append("environment.container_digest: expected sha256:<64 lowercase hex>")
    elif not allow_placeholders and digest == "sha256:" + "0" * 64:
        errors.append("environment.container_digest: zero placeholder digest is not allowed")
    for key in ("control_hz", "observation_hz"):
        value = environment.get(key)
        if not isinstance(value, (int, float)) or (value <= 0 and not allow_placeholders):
            errors.append(f"environment.{key}: expected positive number")

    sampling = require_dict(data, "sampling", errors)
    seeds = sampling.get("seeds")
    if not isinstance(seeds, list) or not seeds or any(not isinstance(x, int) for x in seeds):
        errors.append("sampling.seeds: expected non-empty integer array")
    elif len(seeds) != len(set(seeds)):
        errors.append("sampling.seeds: duplicate seeds are not allowed")
    tasks = sampling.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("sampling.tasks: expected non-empty task array")
        tasks = []
    task_ids: set[str] = set()
    for index, task in enumerate(tasks):
        path = f"sampling.tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{path}: expected object")
            continue
        task_id = task.get("task_id")
        require_nonempty(task_id, f"{path}.task_id", errors, allow_placeholders=allow_placeholders)
        if isinstance(task_id, str):
            if task_id in task_ids:
                errors.append(f"{path}.task_id: duplicate task_id {task_id!r}")
            task_ids.add(task_id)
        for key in ("dimension", "variant", "embodiment", "success_predicate_version"):
            require_nonempty(task.get(key), f"{path}.{key}", errors, allow_placeholders=allow_placeholders)
        for key in ("required_episodes_per_seed", "max_steps"):
            value = task.get(key)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{path}.{key}: expected positive integer")
        for key in ("config_sha256", "layout_selection_sha256"):
            require_sha256(task.get(key), f"{path}.{key}", errors, allow_placeholders=allow_placeholders)

    metrics = require_dict(data, "metrics", errors)
    require_nonempty(metrics.get("revision"), "metrics.revision", errors, allow_placeholders=allow_placeholders)
    if metrics.get("missing_result_policy") != "disqualify":
        errors.append("metrics.missing_result_policy: official v1 manifests must use 'disqualify'")
    primary = metrics.get("primary")
    if not isinstance(primary, list) or not primary:
        errors.append("metrics.primary: expected non-empty array")
    else:
        names: set[str] = set()
        for index, metric in enumerate(primary):
            path = f"metrics.primary[{index}]"
            if not isinstance(metric, dict):
                errors.append(f"{path}: expected object")
                continue
            name = metric.get("name")
            require_nonempty(name, f"{path}.name", errors, allow_placeholders=allow_placeholders)
            if isinstance(name, str):
                if name in names:
                    errors.append(f"{path}.name: duplicate metric {name!r}")
                names.add(name)
            if metric.get("direction") not in {"higher", "lower"}:
                errors.append(f"{path}.direction: expected 'higher' or 'lower'")
            require_nonempty(metric.get("aggregation"), f"{path}.aggregation", errors, allow_placeholders=allow_placeholders)

    runtime = require_dict(data, "runtime", errors)
    for key in ("parallelism", "timeout_seconds"):
        value = runtime.get(key)
        if not isinstance(value, (int, float)) or value <= 0:
            errors.append(f"runtime.{key}: expected positive number")
    for key in ("max_episode_retries", "max_process_restarts"):
        value = runtime.get(key)
        if not isinstance(value, int) or value < 0:
            errors.append(f"runtime.{key}: expected non-negative integer")
    require_sha256(runtime.get("assignment_manifest_sha256"), "runtime.assignment_manifest_sha256", errors, allow_placeholders=allow_placeholders)

    qualification = require_dict(data, "qualification", errors)
    for key in ("required_coverage", "max_invalid_fraction", "max_abandoned_fraction"):
        value = qualification.get(key)
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            errors.append(f"qualification.{key}: expected number in [0, 1]")
    if qualification.get("required_coverage") != 1.0:
        errors.append("qualification.required_coverage: official v1 manifests require 1.0")
    if qualification.get("allow_partial_official_score") is not False:
        errors.append("qualification.allow_partial_official_score: must be false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true", help="Validate the bundled template structure")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation output")
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"manifest: {exc}"]
    else:
        errors = validate(data, allow_placeholders=args.allow_placeholders)

    payload = {"valid": not errors, "errors": errors, "manifest": str(args.manifest)}
    if args.json:
        print(json.dumps(payload, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print(f"Valid benchmark manifest: {args.manifest}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
