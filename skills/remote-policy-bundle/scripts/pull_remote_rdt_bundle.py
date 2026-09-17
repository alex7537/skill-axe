#!/usr/bin/env python3
"""Export and pull verified A2D RDT-170M deployment bundles over SSH."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shlex
import sys

from pull_remote_policy_bundle import (
    archive_manifest,
    remote,
    remote_sha256,
    remove_remote_temp,
    run,
    sha256_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--candidate", action="append", choices=(
        "best-raw", "best-ema-at-raw-best", "latest-raw"
    ))
    parser.add_argument("--remote-rdt-source", required=True)
    parser.add_argument("--remote-data-dir", required=True)
    parser.add_argument("--remote-siglip-dir", required=True)
    parser.add_argument("--remote-python", required=True)
    parser.add_argument("--local-repo", type=Path, default=Path.cwd())
    parser.add_argument("--local-output", type=Path)
    args = parser.parse_args()

    candidates = args.candidate or ["best-raw", "latest-raw"]
    if len(candidates) != len(set(candidates)):
        raise ValueError("RDT candidates must be unique")
    local_repo = args.local_repo.expanduser().resolve()
    if not local_repo.is_dir():
        raise FileNotFoundError(local_repo)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    local_dir = (
        args.local_output.expanduser().resolve()
        if args.local_output
        else local_repo / "output" / "bundles" / f"remote_rdt_bundle_{timestamp}"
    )
    if local_dir.exists() and any(local_dir.iterdir()):
        raise FileExistsError(f"local output is not empty: {local_dir}")
    local_dir.mkdir(parents=True, exist_ok=True)

    remote(args.host, "true")
    remote_temp = remote(
        args.host, "mktemp -d /tmp/remote-policy-bundle.XXXXXX"
    ).splitlines()[-1]
    exporter = Path(__file__).with_name("export_rdt_bundle.py")
    run([
        "scp", "-q", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
        str(exporter), f"{args.host}:{remote_temp}/export_rdt_bundle.py",
    ], capture=False)
    receipt: dict[str, object] = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": args.host,
        "source_run": args.run_dir,
        "remote_temp": remote_temp,
        "artifacts": [],
    }
    try:
        for candidate in candidates:
            remote_archive = f"{remote_temp}/rdt170m-a2d-{candidate}.tgz"
            command = [
                args.remote_python,
                f"{remote_temp}/export_rdt_bundle.py",
                "--run-dir", args.run_dir,
                "--candidate", candidate,
                "--rdt-source", args.remote_rdt_source,
                "--data-dir", args.remote_data_dir,
                "--siglip-dir", args.remote_siglip_dir,
                "--out", remote_archive,
            ]
            remote(args.host, " ".join(shlex.quote(item) for item in command))
            expected_sha = remote_sha256(args.host, remote_archive)
            final = local_dir / f"rdt170m-a2d-{candidate}.tgz"
            partial = final.with_suffix(final.suffix + ".partial")
            if final.exists() or partial.exists():
                raise FileExistsError(final)
            run([
                "scp", "-q", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                f"{args.host}:{remote_archive}", str(partial),
            ], capture=False)
            actual_sha = sha256_file(partial)
            if actual_sha != expected_sha:
                raise ValueError(
                    f"remote/local SHA mismatch: remote={expected_sha} local={actual_sha}"
                )
            variant = "ema" if candidate == "best-ema-at-raw-best" else "raw"
            manifest = archive_manifest(partial, variant)
            if manifest.get("policy_type") != "rdt_170m_a2d":
                raise ValueError("archive policy_type is not rdt_170m_a2d")
            partial.replace(final)
            receipt["artifacts"].append({
                "candidate": candidate,
                "weights_variant": variant,
                "remote_archive": remote_archive,
                "local_archive": str(final),
                "archive_sha256": actual_sha,
                "train_step": manifest.get("train_step"),
                "checkpoint_selection": manifest.get("checkpoint_selection"),
                "source_checkpoint_sha256": manifest.get("source_checkpoint_sha256"),
                "data_version": manifest.get("data_version"),
                "policy_type": manifest.get("policy_type"),
            })
        remove_remote_temp(args.host, remote_temp)
        receipt["remote_temp_removed"] = True
        receipt["status"] = "verified"
        (local_dir / "download_manifest.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(receipt, indent=2))
        return 0
    except Exception:
        receipt["status"] = "failed"
        receipt["remote_temp_retained"] = True
        (local_dir / "download_manifest.failed.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Remote temporary directory retained: {remote_temp}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
