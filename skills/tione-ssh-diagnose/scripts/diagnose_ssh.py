#!/usr/bin/env python3
"""Read-only SSH endpoint, host-key, and optional authentication diagnostic."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile


def run(cmd: list[str], *, input_text: str | None = None, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def ssh_config(target: str) -> dict[str, str]:
    result = run(["ssh", "-G", target])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ssh -G failed for {target}")
    wanted = {"hostname", "port", "user"}
    config: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition(" ")
        if key in wanted and key not in config:
            config[key] = value.strip()
    return config


def fingerprint(key_line: str) -> tuple[str, str] | None:
    fields = key_line.split()
    if len(fields) < 3:
        return None
    result = run(["ssh-keygen", "-lf", "-"], input_text=key_line + "\n")
    if result.returncode != 0:
        return None
    parts = result.stdout.split()
    if len(parts) < 4:
        return None
    return fields[-2], parts[1]


def key_map(lines: list[str]) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for line in lines:
        if not line or line.startswith("#"):
            continue
        item = fingerprint(line)
        if item:
            algorithm, sha256 = item
            found.setdefault(algorithm, set()).add(sha256)
    return found


def known_host_lines(host: str, port: int, known_hosts: Path) -> list[str]:
    lookup = f"[{host}]:{port}" if port != 22 else host
    result = run(["ssh-keygen", "-F", lookup, "-f", str(known_hosts)])
    return [line for line in result.stdout.splitlines() if line and not line.startswith("#")]


def scan_host_lines(host: str, port: int, timeout_seconds: int) -> list[str]:
    result = run(
        ["ssh-keyscan", "-T", str(timeout_seconds), "-p", str(port), host],
        timeout=timeout_seconds + 3,
    )
    return [line for line in result.stdout.splitlines() if line and not line.startswith("#")]


def show_map(label: str, values: dict[str, set[str]]) -> None:
    print(label)
    if not values:
        print("  (none)")
        return
    for algorithm in sorted(values):
        for sha256 in sorted(values[algorithm]):
            print(f"  {algorithm}: {sha256}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="SSH alias or hostname")
    parser.add_argument("--port", type=int, help="Override the SSH port")
    parser.add_argument("--timeout", type=int, default=5, help="Network timeout in seconds")
    parser.add_argument("--known-hosts", type=Path, default=Path.home() / ".ssh" / "known_hosts")
    parser.add_argument("--auth-test", action="store_true", help="Test public-key authentication")
    parser.add_argument(
        "--endpoint-verified",
        action="store_true",
        help="Confirm the endpoint was verified through TI-ONE or by the user",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.auth_test and not args.endpoint_verified:
        print("Refusing auth test: add --endpoint-verified only after checking the endpoint.", file=sys.stderr)
        return 5

    try:
        config = ssh_config(args.target)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"SSH config resolution failed: {exc}", file=sys.stderr)
        return 4

    host = config.get("hostname", args.target)
    port = args.port or int(config.get("port", "22"))
    user = config.get("user", os.environ.get("USER", ""))
    print(f"Endpoint: {user}@{host}:{port} (target: {args.target})")

    try:
        with socket.create_connection((host, port), timeout=args.timeout):
            print("TCP: reachable")
    except OSError as exc:
        print(f"TCP: unreachable ({exc})")
        return 3

    try:
        scanned_lines = scan_host_lines(host, port, args.timeout)
    except subprocess.TimeoutExpired:
        print("Host-key scan: timed out")
        return 3
    current = key_map(scanned_lines)
    stored = key_map(known_host_lines(host, port, args.known_hosts)) if args.known_hosts.exists() else {}
    show_map("Stored known_hosts fingerprints:", stored)
    show_map("Current server fingerprints:", current)

    if not current:
        print("Host-key status: UNKNOWN (server returned no keys)")
        return 3

    statuses: list[str] = []
    for algorithm in sorted(set(stored) | set(current)):
        if algorithm not in stored:
            status = "NEW"
        elif algorithm not in current:
            status = "NOT_OFFERED"
        elif stored[algorithm] & current[algorithm]:
            status = "MATCH"
        else:
            status = "CHANGED"
        statuses.append(status)
        print(f"Host-key status [{algorithm}]: {status}")

    changed = "CHANGED" in statuses
    if args.auth_test:
        host_field = f"[{host}]:{port}" if port != 22 else host
        with tempfile.NamedTemporaryFile("w", prefix="tione-ssh-hostkeys-", delete=True) as temp:
            for line in scanned_lines:
                fields = line.split()
                if len(fields) >= 3:
                    temp.write(f"{host_field} {fields[-2]} {fields[-1]}\n")
            temp.flush()
            result = run(
                [
                    "ssh",
                    "-o", "BatchMode=yes",
                    "-o", f"ConnectTimeout={args.timeout}",
                    "-o", "StrictHostKeyChecking=yes",
                    "-o", f"UserKnownHostsFile={temp.name}",
                    args.target,
                    "true",
                ],
                timeout=args.timeout + 8,
            )
        if result.returncode == 0:
            print("Public-key authentication: SUCCESS")
        else:
            detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "ssh exited nonzero"
            print(f"Public-key authentication: FAILED ({detail})")
            return 4

    return 2 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
