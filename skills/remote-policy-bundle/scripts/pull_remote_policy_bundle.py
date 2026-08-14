#!/usr/bin/env python3
"""Export remote policy checkpoints and pull verified deployment bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "README.md",
    "ckpt.pt",
    "config.yaml",
    "data_split.json",
    "manifest.json",
    "norm_stats.json",
}


@dataclass(frozen=True)
class CheckpointSpec:
    label: str
    variant: str
    path: str


def run(
    command: list[str],
    *,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        capture_output=capture,
        check=check,
    )


def ssh_command(host: str, script: str) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        host,
        f"bash -lc {shlex.quote(script)}",
    ]


def remote(host: str, script: str) -> str:
    result = run(ssh_command(host, script))
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    if not label:
        raise ValueError(f"label has no safe characters: {value!r}")
    return label[:96]


def parse_checkpoint(value: str, default_variant: str) -> CheckpointSpec:
    if "=" in value:
        raw_label, path = value.split("=", 1)
    else:
        path = value
        checkpoint = Path(path)
        raw_label = f"{checkpoint.parent.name}-{checkpoint.stem}"
    variant = default_variant
    if raw_label.endswith(":raw") or raw_label.endswith(":ema"):
        raw_label, variant = raw_label.rsplit(":", 1)
    if variant not in {"raw", "ema"}:
        raise ValueError(f"unsupported weights variant: {variant}")
    if not path.startswith("/"):
        raise ValueError(f"remote checkpoint must be an absolute path: {path}")
    return CheckpointSpec(safe_label(raw_label), variant, path)


def discover_remote_runtime(
    host: str,
    checkpoint: str,
    remote_repo: str | None,
    remote_python: str | None,
) -> tuple[str, str]:
    checkpoint_q = shlex.quote(checkpoint)
    repo_override = shlex.quote(remote_repo) if remote_repo else "''"
    python_override = shlex.quote(remote_python) if remote_python else "''"
    script = f"""
set -e
checkpoint={checkpoint_q}
test -s "$checkpoint"
repo={repo_override}
if [ -n "$repo" ]; then
  test -f "$repo/flow_matching_test/export_bundle.py"
else
  cursor=$(dirname "$checkpoint")
  repo=''
  for _ in 1 2 3 4 5 6; do
    if [ -f "$cursor/flow_matching_test/export_bundle.py" ]; then repo="$cursor"; break; fi
    if [ -f "$cursor/code/flow_matching_test/export_bundle.py" ]; then repo="$cursor/code"; break; fi
    parent=$(dirname "$cursor")
    [ "$parent" != "$cursor" ] || break
    cursor="$parent"
  done
fi
[ -n "$repo" ] && test -f "$repo/flow_matching_test/export_bundle.py"
python={python_override}
if [ -n "$python" ]; then
  test -x "$python"
elif [ -x "$repo/../venv/bin/python" ]; then
  python="$repo/../venv/bin/python"
elif [ -x "$repo/venv/bin/python" ]; then
  python="$repo/venv/bin/python"
else
  python=$(command -v python3)
fi
printf 'REPO=%s\nPYTHON=%s\n' "$(readlink -f "$repo")" "$(readlink -f "$python")"
"""
    values: dict[str, str] = {}
    for line in remote(host, script).splitlines():
        key, separator, item = line.partition("=")
        if separator:
            values[key] = item
    if not values.get("REPO") or not values.get("PYTHON"):
        raise RuntimeError("could not discover remote repository and Python environment")
    return values["REPO"], values["PYTHON"]


def archive_manifest(path: Path, expected_variant: str) -> dict[str, Any]:
    with tarfile.open(path, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers() if member.isfile()}
        by_basename = {Path(name).name: name for name in members}
        missing = sorted(REQUIRED_FILES - set(by_basename))
        if missing:
            raise ValueError(f"bundle archive is missing files: {missing}")
        manifest_file = archive.extractfile(members[by_basename["manifest.json"]])
        if manifest_file is None:
            raise ValueError("could not read manifest.json")
        manifest = json.load(manifest_file)
        if manifest.get("weights_variant") != expected_variant:
            raise ValueError(
                "manifest weights_variant mismatch: "
                f"expected {expected_variant}, got {manifest.get('weights_variant')}"
            )
        declared_files = manifest.get("files", {})
        for filename, metadata in declared_files.items():
            member_name = by_basename.get(filename)
            if member_name is None:
                raise ValueError(f"manifest references missing file: {filename}")
            source = archive.extractfile(members[member_name])
            if source is None:
                raise ValueError(f"could not read archived file: {filename}")
            digest = hashlib.sha256()
            size = 0
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
            if digest.hexdigest() != metadata.get("sha256"):
                raise ValueError(f"internal SHA256 mismatch: {filename}")
            if size != int(metadata.get("bytes", -1)):
                raise ValueError(f"internal size mismatch: {filename}")
    return manifest


def remote_sha256(host: str, path: str) -> str:
    path_q = shlex.quote(path)
    script = f"""
set -e
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum {path_q} | cut -d ' ' -f1
else
  shasum -a 256 {path_q} | cut -d ' ' -f1
fi
"""
    return remote(host, script).splitlines()[-1].strip()


def remove_remote_temp(host: str, path: str) -> None:
    """Remove only a directory created by this script under remote /tmp."""
    path_q = shlex.quote(path)
    script = f"""
set -e
target={path_q}
case "$target" in
  /tmp/remote-policy-bundle.*) rm -rf -- "$target" ;;
  *) printf 'refusing unsafe cleanup target: %s\n' "$target" >&2; exit 2 ;;
esac
"""
    remote(host, script)


def export_one(
    *,
    host: str,
    spec: CheckpointSpec,
    repo: str,
    python: str,
    remote_temp: str,
    local_dir: Path,
    execute_horizon: int,
    num_inference_steps: int | None,
    data_version: str,
    checkpoint_selection: str | None,
) -> dict[str, Any]:
    remote_out = f"{remote_temp}/{spec.label}"
    command = [
        python,
        "-m",
        "flow_matching_test.export_bundle",
        "--ckpt",
        spec.path,
        "--out",
        remote_out,
        "--execute-horizon",
        str(execute_horizon),
        "--data-version",
        data_version,
        "--weights-variant",
        spec.variant,
        "--archive",
    ]
    if num_inference_steps is not None:
        command.extend(["--num-inference-steps", str(num_inference_steps)])
    if checkpoint_selection:
        command.extend(["--checkpoint-selection", checkpoint_selection])
    rendered = " ".join(shlex.quote(item) for item in command)
    remote_archive = f"{remote_out}.tgz"
    script = (
        "set -e\n"
        f"cd {shlex.quote(repo)}\n"
        f"PYTHONPATH={shlex.quote(repo)} {rendered}\n"
        f"test -s {shlex.quote(remote_archive)}\n"
        f"printf '%s\\n' {shlex.quote(remote_archive)}"
    )
    remote(host, script)
    expected_sha = remote_sha256(host, remote_archive)

    final_path = local_dir / f"{spec.label}-{spec.variant}.tgz"
    partial_path = final_path.with_suffix(final_path.suffix + ".partial")
    if final_path.exists() or partial_path.exists():
        raise FileExistsError(f"refusing to overwrite local artifact: {final_path}")
    run(
        [
            "scp",
            "-q",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            f"{host}:{remote_archive}",
            str(partial_path),
        ],
        capture=False,
    )
    actual_sha = sha256_file(partial_path)
    if actual_sha != expected_sha:
        raise ValueError(
            f"archive SHA256 mismatch for {spec.label}: "
            f"remote={expected_sha} local={actual_sha}"
        )
    manifest = archive_manifest(partial_path, spec.variant)
    os.replace(partial_path, final_path)
    return {
        "label": spec.label,
        "weights_variant": spec.variant,
        "remote_checkpoint": spec.path,
        "remote_archive": remote_archive,
        "local_archive": str(final_path.resolve()),
        "archive_sha256": actual_sha,
        "train_epoch": manifest.get("train_epoch"),
        "train_step": manifest.get("train_step"),
        "source_checkpoint_selection": manifest.get("source_checkpoint_selection"),
        "source_checkpoint_sha256": manifest.get("source_checkpoint_sha256"),
        "policy_type": manifest.get("policy_type"),
        "data_version": manifest.get("data_version"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="Passwordless SSH host or alias")
    parser.add_argument("--checkpoint", action="append", required=True)
    parser.add_argument("--weights-variant", choices=("raw", "ema"), default="raw")
    parser.add_argument("--local-repo", type=Path, default=Path.cwd())
    parser.add_argument("--local-output", type=Path)
    parser.add_argument("--remote-repo")
    parser.add_argument("--remote-python")
    parser.add_argument("--execute-horizon", type=int, default=16)
    parser.add_argument("--num-inference-steps", type=int)
    parser.add_argument("--data-version", default="remote-policy-bundle")
    parser.add_argument("--checkpoint-selection")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.execute_horizon < 1:
        raise ValueError("execute horizon must be positive")
    specs = [parse_checkpoint(value, args.weights_variant) for value in args.checkpoint]
    labels = [spec.label for spec in specs]
    if len(labels) != len(set(labels)):
        raise ValueError("checkpoint labels must be unique")
    local_repo = args.local_repo.expanduser().resolve()
    if not local_repo.is_dir():
        raise FileNotFoundError(f"local repository does not exist: {local_repo}")
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    local_dir = (
        args.local_output.expanduser().resolve()
        if args.local_output
        else local_repo / "output" / "bundles" / f"remote_policy_bundle_{timestamp}"
    )
    if local_dir.exists() and any(local_dir.iterdir()):
        raise FileExistsError(f"local output directory is not empty: {local_dir}")
    local_dir.mkdir(parents=True, exist_ok=True)

    remote(args.host, "true")
    repo, python = discover_remote_runtime(
        args.host,
        specs[0].path,
        args.remote_repo,
        args.remote_python,
    )
    for spec in specs[1:]:
        other_repo, other_python = discover_remote_runtime(
            args.host,
            spec.path,
            args.remote_repo or repo,
            args.remote_python or python,
        )
        if (other_repo, other_python) != (repo, python):
            raise ValueError("all checkpoints in one invocation must share a repository/runtime")

    remote_temp = remote(
        args.host,
        "mktemp -d /tmp/remote-policy-bundle.XXXXXX",
    ).splitlines()[-1]
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": args.host,
        "remote_repo": repo,
        "remote_python": python,
        "remote_temp": remote_temp,
        "artifacts": [],
    }
    try:
        for spec in specs:
            receipt["artifacts"].append(
                export_one(
                    host=args.host,
                    spec=spec,
                    repo=repo,
                    python=python,
                    remote_temp=remote_temp,
                    local_dir=local_dir,
                    execute_horizon=args.execute_horizon,
                    num_inference_steps=args.num_inference_steps,
                    data_version=args.data_version,
                    checkpoint_selection=args.checkpoint_selection,
                )
            )
        receipt["status"] = "verified"
        receipt_path = local_dir / "download_manifest.json"
        remove_remote_temp(args.host, remote_temp)
        receipt["remote_temp_removed"] = True
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
        return 0
    except Exception:
        receipt["status"] = "failed"
        receipt["remote_temp_retained"] = True
        (local_dir / "download_manifest.failed.json").write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Remote temporary directory retained: {remote_temp}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
