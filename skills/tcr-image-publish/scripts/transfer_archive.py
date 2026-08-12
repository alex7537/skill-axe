#!/usr/bin/env python3
"""Plan or execute a resumable archive transfer and verify remote SHA256."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shlex
import shutil
import subprocess
import sys


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quote_sftp(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("paths may not contain newlines")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("ssh_target", help="Verified SSH alias or user@host")
    parser.add_argument("remote_dir", help="Absolute destination directory")
    parser.add_argument("--execute", action="store_true", help="Perform the remote write")
    parser.add_argument("--minimum-space-factor", type=float, default=2.2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive = args.archive.expanduser().resolve()
    if not archive.is_file():
        print(f"Archive not found: {archive}", file=sys.stderr)
        return 2
    if not args.remote_dir.startswith("/"):
        print("remote_dir must be absolute", file=sys.stderr)
        return 2
    if args.minimum_space_factor < 1:
        print("minimum-space-factor must be at least 1", file=sys.stderr)
        return 2

    remote_path = str(PurePosixPath(args.remote_dir) / archive.name)
    size = archive.stat().st_size
    local_hash = sha256_file(archive)
    print(f"Local archive: {archive}")
    print(f"Size: {size} bytes")
    print(f"Local SHA256: {local_hash}")
    print(f"Remote target: {args.ssh_target}:{remote_path}")
    print(f"Required free space: {int(size * args.minimum_space_factor)} bytes")

    if not args.execute:
        print("PLAN ONLY: rerun with --execute after authorizing this remote upload.")
        return 0

    remote_dir_q = shlex.quote(args.remote_dir)
    prep = run(
        [
            "ssh",
            args.ssh_target,
            f"mkdir -p -- {remote_dir_q} && df -Pk -- {remote_dir_q} | tail -1 | awk '{{print $4}}'",
        ],
        capture=True,
    )
    if prep.returncode != 0:
        print(prep.stderr.strip() or "remote directory preflight failed", file=sys.stderr)
        return 3
    try:
        free_bytes = int(prep.stdout.strip().splitlines()[-1]) * 1024
    except (ValueError, IndexError):
        print("could not parse remote free space", file=sys.stderr)
        return 3
    if free_bytes < int(size * args.minimum_space_factor):
        print(f"Insufficient remote space: {free_bytes} bytes available", file=sys.stderr)
        return 3

    remote_rsync = run(["ssh", args.ssh_target, "command -v rsync >/dev/null 2>&1"])
    if shutil.which("rsync") and remote_rsync.returncode == 0:
        print("Transfer method: rsync --partial --append-verify")
        transfer = run(
            [
                "rsync",
                "-ah",
                "--partial",
                "--append-verify",
                "--info=progress2",
                str(archive),
                f"{args.ssh_target}:{shlex.quote(remote_path)}",
            ]
        )
    else:
        print("Transfer method: SFTP reput (resumable fallback)")
        batch = f"reput {quote_sftp(str(archive))} {quote_sftp(remote_path)}\nbye\n"
        transfer = run(["sftp", "-b", "-", args.ssh_target], input_text=batch)
    if transfer.returncode != 0:
        print("Transfer failed; rerun the same command to resume.", file=sys.stderr)
        return 4

    remote_path_q = shlex.quote(remote_path)
    remote_digest = run(
        ["ssh", args.ssh_target, f"sha256sum -- {remote_path_q} | awk '{{print $1}}'"],
        capture=True,
    )
    if remote_digest.returncode != 0:
        print(remote_digest.stderr.strip() or "remote SHA256 failed", file=sys.stderr)
        return 5
    remote_hash = remote_digest.stdout.strip().splitlines()[-1]
    print(f"Remote SHA256: {remote_hash}")
    if remote_hash != local_hash:
        print("SHA256 MISMATCH: do not run docker load.", file=sys.stderr)
        return 6
    print("Transfer verified: SHA256 MATCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
