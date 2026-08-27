#!/usr/bin/env python3
"""Preview and safely checkpoint a Git-versioned Obsidian vault."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL_DIR / "config.json"

DENIED_PREFIXES = (".git", ".claudian", ".trash")
DENIED_NAMES = {".env", ".netrc", "credentials.json"}
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("tencent-secret-id", re.compile(r"\bAKID[A-Za-z0-9]{20,}\b")),
    ("auth-token-url", re.compile(r"[?&](?:authToken|access_token|token)=[^\s&#]+", re.I)),
)


@dataclass(frozen=True)
class Candidate:
    path: str
    tracked: bool
    exists: bool
    category: str


def run_git(vault: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(vault), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def load_config(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}; copy config.example.json to config.json and set the Vault policy"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config must be a JSON object")
    return payload


def resolve_settings(args: argparse.Namespace) -> tuple[Path, str, str, dict]:
    config = load_config(Path(args.config).expanduser().resolve())
    vault = Path(args.vault or config.get("vault_path", "")).expanduser().resolve()
    remote = str(args.remote or config.get("remote", "origin"))
    branch = str(args.branch or config.get("branch", "main"))
    if not vault.is_dir() or not (vault / ".obsidian").is_dir():
        raise ValueError(f"Not an Obsidian Vault root: {vault}")
    root = Path(run_git(vault, "rev-parse", "--show-toplevel")).resolve()
    if root != vault:
        raise ValueError(f"Git root {root} does not equal configured Vault root {vault}")
    return vault, remote, branch, config


def path_is_denied(path: str) -> str | None:
    posix = Path(path).as_posix().lstrip("./")
    parts = Path(posix).parts
    if not parts:
        return "empty path"
    if parts[0] in DENIED_PREFIXES or parts[0].startswith(".backup_"):
        return f"denied prefix {parts[0]}"
    if Path(posix).name in DENIED_NAMES:
        return f"denied filename {Path(posix).name}"
    if posix.startswith(".obsidian/workspace") and posix.endswith(".json"):
        return "machine-local Obsidian workspace"
    if posix.startswith(".obsidian/plugins/"):
        return "Obsidian plugin data"
    return None


def changed_paths(vault: Path) -> list[Candidate]:
    tracked_names = set(run_git(vault, "ls-files").splitlines())
    modified = set(run_git(vault, "diff", "--name-only", "HEAD", "--").splitlines())
    staged = set(run_git(vault, "diff", "--cached", "--name-only", "--").splitlines())
    untracked = set(run_git(vault, "ls-files", "--others", "--exclude-standard").splitlines())
    result: list[Candidate] = []
    for name in sorted(modified | staged | untracked):
        if not name:
            continue
        path = vault / name
        result.append(
            Candidate(
                path=name,
                tracked=name in tracked_names,
                exists=path.exists(),
                category="untracked" if name in untracked else "tracked",
            )
        )
    return result


def select_candidates(
    vault: Path,
    candidates: list[Candidate],
    config: dict,
    include_obsidian_config: bool,
    include_untracked_binary: bool,
) -> tuple[list[Candidate], list[tuple[Candidate, str]]]:
    text_ext = {str(x).lower() for x in config.get("text_extensions", [])}
    binary_ext = {str(x).lower() for x in config.get("binary_extensions", [])}
    max_bytes = int(float(config.get("max_file_mib", 50)) * 1024 * 1024)
    selected: list[Candidate] = []
    excluded: list[tuple[Candidate, str]] = []
    for item in candidates:
        denied = path_is_denied(item.path)
        if denied:
            excluded.append((item, denied))
            continue
        if item.path.startswith(".obsidian/") and not include_obsidian_config:
            excluded.append((item, "stable .obsidian config requires explicit opt-in"))
            continue
        suffix = Path(item.path).suffix.lower()
        if item.exists:
            size = (vault / item.path).stat().st_size
            if size > max_bytes:
                excluded.append((item, f"file exceeds {config.get('max_file_mib', 50)} MiB"))
                continue
        if suffix in text_ext:
            selected.append(item)
        elif suffix in binary_ext:
            if item.tracked or include_untracked_binary:
                selected.append(item)
            else:
                excluded.append((item, "new binary requires explicit opt-in"))
        elif not item.exists and item.tracked:
            selected.append(item)
        else:
            excluded.append((item, f"extension {suffix or '<none>'} is not allowlisted"))
    return selected, excluded


def scan_secrets(vault: Path, selected: list[Candidate], config: dict) -> list[str]:
    text_ext = {str(x).lower() for x in config.get("text_extensions", [])}
    findings: list[str] = []
    for item in selected:
        path = vault / item.path
        if not item.exists or path.suffix.lower() not in text_ext:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{item.path}: text-allowlisted file is not UTF-8")
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{item.path}: {label}")
    return findings


def print_plan(
    vault: Path,
    remote: str,
    branch: str,
    behind: int,
    ahead: int,
    selected: list[Candidate],
    excluded: list[tuple[Candidate, str]],
    findings: list[str],
) -> None:
    print(f"Vault: {vault}")
    print(f"Remote branch: {remote}/{branch}")
    print(f"Drift: behind={behind} ahead={ahead}")
    print(f"Selected ({len(selected)}):")
    for item in selected:
        print(f"  {item.category:9s} {item.path}")
    print(f"Excluded ({len(excluded)}):")
    for item, reason in excluded:
        print(f"  {item.category:9s} {item.path} :: {reason}")
    print(f"Sensitive findings ({len(findings)}):")
    for finding in findings:
        print(f"  {finding}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--vault")
    parser.add_argument("--remote")
    parser.add_argument("--branch")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--message", default="backup: checkpoint Obsidian vault")
    parser.add_argument("--include-obsidian-config", action="store_true")
    parser.add_argument("--include-untracked-binary", action="store_true")
    parser.add_argument("--allow-existing-staged", action="store_true")
    args = parser.parse_args()

    if (args.commit or args.push) and not args.execute:
        parser.error("--commit/--push require --execute")
    if args.push and not args.commit:
        parser.error("--push requires --commit")

    try:
        vault, remote, branch, config = resolve_settings(args)
        if remote not in set(run_git(vault, "remote").splitlines()):
            raise ValueError(f"Configured remote does not exist: {remote}")
        current = run_git(vault, "branch", "--show-current")
        if current != branch:
            raise ValueError(f"Current branch {current!r} does not match configured branch {branch!r}")
        run_git(vault, "fetch", "--prune", remote)
        upstream = f"{remote}/{branch}"
        run_git(vault, "rev-parse", "--verify", upstream)
        drift = run_git(vault, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
        behind, ahead = (int(x) for x in drift.split())
        if behind:
            raise RuntimeError(
                f"Local branch is behind/diverged from {upstream}; reconcile manually before backup"
            )
        staged = run_git(vault, "diff", "--cached", "--name-only", "--").splitlines()
        if args.execute and staged and not args.allow_existing_staged:
            raise RuntimeError(
                "Existing staged changes detected; review or use --allow-existing-staged explicitly"
            )
        candidates = changed_paths(vault)
        selected, excluded = select_candidates(
            vault,
            candidates,
            config,
            include_obsidian_config=args.include_obsidian_config
            or bool(config.get("include_obsidian_config", False)),
            include_untracked_binary=args.include_untracked_binary
            or bool(config.get("include_untracked_binary", False)),
        )
        findings = scan_secrets(vault, selected, config)
        print_plan(vault, remote, branch, behind, ahead, selected, excluded, findings)
        if findings:
            raise RuntimeError("Sensitive-content gate failed")
        if not args.execute:
            print("PLAN ONLY: no staging, commit, or push performed.")
            return 0
        if not selected:
            print("NOOP: no policy-allowed changes selected.")
            return 0
        for item in selected:
            run_git(vault, "add", "-A", "--", item.path)
        print("Staged changes:")
        print(run_git(vault, "diff", "--cached", "--name-status", "--"))
        if not args.commit:
            print("STAGE COMPLETE: review the staged diff before committing.")
            return 0
        run_git(vault, "commit", "-m", args.message)
        commit = run_git(vault, "rev-parse", "HEAD")
        print(f"COMMIT COMPLETE: {commit}")
        if args.push:
            run_git(vault, "push", remote, f"HEAD:refs/heads/{branch}")
            run_git(vault, "fetch", remote)
            remote_head = run_git(vault, "rev-parse", f"{remote}/{branch}")
            if remote_head != commit:
                raise RuntimeError(f"Remote verification failed: local={commit} remote={remote_head}")
            print(f"PUSH VERIFIED: {remote}/{branch}={remote_head}")
        remaining = run_git(vault, "status", "--short")
        print("Remaining worktree changes:")
        print(remaining or "  clean")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
