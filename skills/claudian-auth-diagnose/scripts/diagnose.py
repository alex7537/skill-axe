#!/usr/bin/env python3
"""Read-only Claudian/Claude Code authentication diagnostics for macOS."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def run(command: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            command,
            124,
            stdout=exc.stdout or "",
            stderr=f"timed out after {timeout}s",
        )


def heading(title: str) -> None:
    print(f"\n## {title}")


def parse_json(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def inspect_plugin(vault: Path | None) -> None:
    heading("Claudian plugin")
    if vault is None:
        print("vault: not supplied")
        return
    manifest = vault / ".obsidian" / "plugins" / "realclaudian" / "manifest.json"
    if not manifest.is_file():
        print(f"manifest: not found under {vault}")
        return
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"manifest: unreadable ({exc})")
        return
    print(f"vault: {vault}")
    print(f"plugin: {data.get('name', 'Claudian')} {data.get('version', 'unknown')}")


def inspect_cli(claude: str) -> dict[str, Any] | None:
    heading("Claude Code CLI")
    print(f"path: {claude}")
    version = run([claude, "--version"])
    print(f"version: {(version.stdout or version.stderr).strip() or 'unknown'}")

    status = run([claude, "auth", "status"])
    payload = parse_json(status.stdout)
    if payload is None:
        print(f"auth status: unreadable (exit {status.returncode})")
        return None
    safe_fields = ("loggedIn", "authMethod", "apiProvider", "subscriptionType")
    safe_status = {key: payload.get(key) for key in safe_fields if key in payload}
    print("auth status: " + json.dumps(safe_status, ensure_ascii=False))
    return payload


def inspect_network() -> bool:
    heading("Network reachability")
    curl = shutil.which("curl")
    if not curl:
        print("curl: unavailable")
        return False
    all_reachable = True
    for url in ("https://api.anthropic.com", "https://platform.claude.com"):
        result = run(
            [
                curl,
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "http=%{http_code} dns=%{time_namelookup}s connect=%{time_connect}s "
                "tls=%{time_appconnect}s total=%{time_total}s",
                "--connect-timeout",
                "8",
                "--max-time",
                "15",
                url,
            ],
            timeout=20,
        )
        line = (result.stdout or result.stderr).strip()
        print(f"{url}: {line or 'failed'}")
        if result.returncode != 0:
            all_reachable = False
    proxy_names = [
        key for key in os.environ if key.lower() in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}
    ]
    print("proxy env: " + (", ".join(sorted(proxy_names)) if proxy_names else "none"))
    return all_reachable


def inspect_keychain() -> None:
    heading("macOS credential metadata")
    security = shutil.which("security")
    if not security:
        print("security: unavailable (non-macOS environment?)")
        return
    result = run([security, "find-generic-password", "-s", "Claude Code-credentials"])
    if result.returncode != 0:
        print("Claude Code-credentials: not found or inaccessible")
        return
    metadata = result.stdout + result.stderr
    for line in metadata.splitlines():
        stripped = line.strip()
        if stripped.startswith('"cdat"') or stripped.startswith('"mdat"'):
            print(stripped)
    print("secret payload: intentionally not read")


def inspect_processes() -> None:
    heading("Relevant processes")
    result = run(["ps", "-axo", "pid,ppid,state,lstart,etime,command"])
    matches = []
    for line in result.stdout.splitlines():
        lower = line.lower()
        if "claude auth login" in lower or ("claude" in lower and "stream-json" in lower):
            matches.append(line.strip())
    print("\n".join(matches) if matches else "none")


def probe(claude: str) -> tuple[bool, str]:
    heading("Real authentication probe")
    print('sending non-sensitive prompt: "Reply only OK"')
    result = run([claude, "-p", "Reply only OK", "--output-format", "json"], timeout=45)
    if result.returncode == 124:
        print("result: timed out after 45s")
        return False, "timeout"
    payload = parse_json(result.stdout)
    if payload is None:
        print(f"result: unreadable (exit {result.returncode})")
        return False, "unreadable"
    if payload.get("is_error"):
        status = payload.get("api_error_status")
        message = str(payload.get("result", "API error"))
        lowered = message.lower()
        if status == 401 or "expired" in lowered or "authenticate" in lowered:
            classification = "oauth_expired_or_refresh_failed"
        else:
            classification = "api_error"
        print(f"result: failure; status={status}; classification={classification}")
        return False, classification
    text = str(payload.get("result", "")).strip()
    print(f"result: success; response={text[:80]!r}")
    return True, "success"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, help="Optional Obsidian vault path")
    parser.add_argument(
        "--probe",
        action="store_true",
        help='Send only "Reply only OK" to verify a real Claude API request',
    )
    args = parser.parse_args()

    claude = shutil.which("claude")
    if not claude:
        print("Claude Code CLI not found on PATH", file=sys.stderr)
        return 2

    inspect_plugin(args.vault)
    status = inspect_cli(claude)
    network_ok = inspect_network()
    inspect_keychain()
    inspect_processes()

    probe_ok: bool | None = None
    probe_class = "not_run"
    if args.probe:
        probe_ok, probe_class = probe(claude)

    heading("Classification")
    if status is not None and not status.get("loggedIn", False):
        print("local_auth_missing")
    elif probe_ok is False and probe_class == "oauth_expired_or_refresh_failed":
        print("local_status_stale: OAuth token expired or refresh failed")
    elif probe_ok is True:
        print("cli_auth_works: if Claudian still fails, inspect plugin/child environment")
    elif not network_ok:
        print("network_unstable: stabilize routing before changing credentials")
    elif probe_ok is False:
        print(f"probe_failed: {probe_class}")
    else:
        print("inconclusive_without_probe: rerun with --probe for server-side verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
