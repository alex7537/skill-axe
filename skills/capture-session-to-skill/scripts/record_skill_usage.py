#!/usr/bin/env python3
"""Increment machine-local usage counters for installed personal Codex skills."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def load_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def load_config() -> dict[str, str]:
    path = Path(__file__).resolve().parent.parent / "config.json"
    return load_object(path)


def manifest_baseline(config: dict[str, str], name: str) -> int:
    checkout = Path(config.get("checkout_dir", "~/.codex/skill-repos/skill-axe")).expanduser()
    manifest = checkout / config.get("manifest_name", "skills-manifest.json")
    entry = load_object(manifest).get("skills", {}).get(name, {})
    if not isinstance(entry, dict):
        return 0
    try:
        count = max(0, int(entry.get("usage_count", 0)))
    except (TypeError, ValueError):
        count = 0
    return count


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills", nargs="+", help="Installed personal skill names")
    parser.add_argument("--count", type=int, default=1, help="Increment per skill (default: 1)")
    parser.add_argument(
        "--stats-file",
        type=Path,
        default=Path(config.get("usage_stats_file", "~/.codex/skill-usage.json")),
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(config.get("source_skills_dir", "~/.codex/skills")),
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    source = args.source.expanduser().resolve()
    stats_path = args.stats_file.expanduser().resolve()
    state = load_object(stats_path)
    entries = state.setdefault("skills", {})
    if not isinstance(entries, dict):
        raise SystemExit(f"Invalid skills object: {stats_path}")
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    updated: list[str] = []
    for name in dict.fromkeys(args.skills):
        if not (source / name / "SKILL.md").is_file():
            raise SystemExit(f"Not an installed personal skill: {name}")
        baseline_count = manifest_baseline(config, name)
        entry = entries.get(name, {})
        if not isinstance(entry, dict):
            entry = {}
        try:
            local_count = max(0, int(entry.get("usage_count", 0)))
        except (TypeError, ValueError):
            local_count = 0
        entry["usage_count"] = max(local_count, baseline_count) + args.count
        entry["last_used_at"] = now
        entries[name] = entry
        updated.append(f"{name}={entry['usage_count']}")
    state["format_version"] = 1
    atomic_write_json(stats_path, state)
    print(f"Updated {stats_path}: {', '.join(updated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
