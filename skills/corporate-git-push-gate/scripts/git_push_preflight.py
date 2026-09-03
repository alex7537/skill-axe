#!/usr/bin/env python3
"""Read-only Git remote-mutation preflight with corporate-target classification."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


CORPORATE_HOSTS = {"code.<internal-domain>"}
PERSONAL_GITHUB_OWNERS = {"<github-owner>"}


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def sanitize_url(raw_url: str) -> str:
    value = raw_url.strip()
    if "://" not in value:
        return value
    parsed = urlsplit(value)
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    safe_netloc = f"{hostname}{port}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, "", ""))


def remote_identity(url: str) -> tuple[str, str]:
    value = sanitize_url(url)
    if "://" in value:
        parsed = urlsplit(value)
        return (parsed.hostname or "").lower(), parsed.path.strip("/")
    match = re.match(r"^(?:[^@]+@)?([^:]+):(.+)$", value)
    if match:
        return match.group(1).lower(), match.group(2).strip("/")
    return "", value.strip("/")


def classify(url: str) -> tuple[str, str]:
    host, path = remote_identity(url)
    lowered_path = path.lower()
    if host in CORPORATE_HOSTS or "dev-algorithm/" in lowered_path:
        return "corporate", f"matched company host/namespace: {host}/{path}"
    parts = [part for part in path.removesuffix(".git").split("/") if part]
    if host == "github.com" and parts and parts[0].lower() in PERSONAL_GITHUB_OWNERS:
        return "personal", f"matched personal GitHub owner: {parts[0]}"
    return "unknown", f"remote is not in the configured corporate/personal map: {host}/{path}"


def optional_git(repo: Path, *args: str) -> str | None:
    try:
        value = git(repo, *args)
    except RuntimeError:
        return None
    return value or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--remote", default="origin")
    parser.add_argument(
        "--operation",
        required=True,
        choices=("push-branch", "delete-branch", "push-tag", "delete-tag", "force-push"),
    )
    parser.add_argument("--target-ref", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    root = Path(git(repo, "rev-parse", "--show-toplevel"))
    remote_url = git(root, "remote", "get-url", "--push", args.remote)
    classification, reason = classify(remote_url)
    branch = optional_git(root, "branch", "--show-current")
    head = git(root, "rev-parse", "HEAD")
    upstream = optional_git(root, "rev-parse", "--abbrev-ref", "@{upstream}")
    status = optional_git(root, "status", "--porcelain=v1")
    commits: list[str] = []
    files: list[str] = []
    if args.operation in {"push-branch", "force-push"}:
        base = upstream
        if base:
            commits_text = optional_git(root, "log", "--oneline", f"{base}..HEAD")
            files_text = optional_git(root, "diff", "--name-status", f"{base}...HEAD")
            commits = commits_text.splitlines() if commits_text else []
            files = files_text.splitlines() if files_text else []
        else:
            commits = [git(root, "log", "-1", "--oneline", "HEAD")]
            files = ["upstream unavailable; resolve the intended base before approval"]
    payload = {
        "requires_explicit_confirmation": classification in {"corporate", "unknown"},
        "operation": args.operation,
        "repository_root": str(root),
        "remote": args.remote,
        "push_url": sanitize_url(remote_url),
        "classification": classification,
        "classification_reason": reason,
        "local_branch": branch,
        "head_sha": head,
        "upstream": upstream,
        "target_ref": args.target_ref,
        "force_or_non_fast_forward": args.operation == "force-push",
        "worktree_dirty": bool(status),
        "uncommitted_status": status.splitlines() if status else [],
        "commits": commits,
        "files": files,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
