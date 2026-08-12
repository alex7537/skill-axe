#!/usr/bin/env python3
"""Safely stage, commit, and optionally push personal Codex skills to Git."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


SKIP_DIRS = {".git", ".system", "__pycache__", ".pytest_cache", ".mypy_cache"}
SKIP_NAMES = {".DS_Store", "auth.json", "hooks.json"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".sqlite", ".sqlite-shm", ".sqlite-wal"}
SENSITIVE_FILENAMES = {
    ".env",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "known_hosts",
    "docker-config.json",
}
SENSITIVE_JSON_KEYS = {
    "access_token",
    "api_key",
    "auth",
    "authorization",
    "client_secret",
    "password",
    "private_key",
    "secret",
    "secret_id",
    "secret_key",
    "token",
}
PLACEHOLDERS = {
    "",
    "...",
    "akidexample",
    "changeme",
    "example",
    "example_secret_key",
    "placeholder",
    "replace-me",
    "your-value",
}
TOKEN_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKID[A-Za-z0-9]{16,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
]
STRUCTURED_SECRET_RE = re.compile(
    r"^\s*(access[_-]?token|api[_-]?key|auth|authorization|client[_-]?secret|password|private[_-]?key|secret|secret[_-]?id|secret[_-]?key|token)\s*[:=]\s*[\"']?([^\"'#\s][^#]*)",
    re.IGNORECASE | re.MULTILINE,
)


def run(cmd: list[str], *, cwd: Path | None = None, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )


def load_config() -> dict[str, str]:
    path = Path(__file__).resolve().parent.parent / "config.json"
    return json.loads(path.read_text())


def parse_args(config: dict[str, str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(config["source_skills_dir"]))
    parser.add_argument("--repo-url", default=config["repository_url"])
    parser.add_argument("--checkout", type=Path, default=Path(config["checkout_dir"]))
    parser.add_argument("--managed-subdir", default=config["managed_subdir"])
    parser.add_argument("--manifest", default=config["manifest_name"])
    parser.add_argument("--execute", action="store_true", help="Clone/copy skills into the checkout")
    parser.add_argument("--commit", action="store_true", help="Commit managed changes")
    parser.add_argument("--push", action="store_true", help="Push HEAD to origin")
    parser.add_argument("--prune", action="store_true", help="Remove stale skill directories from the checkout")
    parser.add_argument("--message", default="Sync personal Codex skills")
    return parser.parse_args()


def is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in PLACEHOLDERS or text.startswith(("<", "${", "your_", "example_"))


def sensitive_json(value: Any, key: str = "") -> bool:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            normalized = str(child_key).strip().lower().replace("-", "_")
            if normalized in SENSITIVE_JSON_KEYS and not is_placeholder(child_value):
                return True
            if sensitive_json(child_value, normalized):
                return True
    elif isinstance(value, list):
        return any(sensitive_json(item, key) for item in value)
    return False


def contains_sensitive_json_key(value: Any) -> bool:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            normalized = str(child_key).strip().lower().replace("-", "_")
            if normalized in SENSITIVE_JSON_KEYS or contains_sensitive_json_key(child_value):
                return True
    elif isinstance(value, list):
        return any(contains_sensitive_json_key(item) for item in value)
    return False


def sensitive_reason(path: Path) -> str | None:
    lower_name = path.name.lower()
    if lower_name in SENSITIVE_FILENAMES or lower_name.startswith(".env."):
        return "sensitive filename"
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return "private credential file type"
    if path.is_symlink():
        return "symlink excluded"
    try:
        data = path.read_bytes()
    except OSError as exc:
        return f"unreadable: {exc}"
    if any(pattern.search(data) for pattern in TOKEN_PATTERNS):
        return "credential-like content"
    if path.suffix.lower() in {".env", ".ini", ".toml", ".yaml", ".yml"}:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        for match in STRUCTURED_SECRET_RE.finditer(text):
            if not is_placeholder(match.group(2).strip().strip("\"'")):
                return "non-placeholder secret field in structured config"
    if path.suffix.lower() == ".json":
        try:
            parsed = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        if parsed is not None:
            if path.name == "config.json" and contains_sensitive_json_key(parsed):
                return "runtime config contains credential fields"
            if sensitive_json(parsed):
                return "non-placeholder secret field in JSON"
    return None


def discover(source: Path) -> tuple[dict[str, list[Path]], dict[str, str]]:
    skills: dict[str, list[Path]] = {}
    excluded: dict[str, str] = {}
    for skill_dir in sorted(source.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name in SKIP_DIRS or not (skill_dir / "SKILL.md").is_file():
            continue
        accepted: list[Path] = []
        for path in sorted(skill_dir.rglob("*")):
            relative = path.relative_to(source)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if path.is_dir():
                continue
            if path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES:
                excluded[str(relative)] = "generated/local state"
                continue
            reason = sensitive_reason(path)
            if reason:
                excluded[str(relative)] = reason
                continue
            accepted.append(path)
        skills[skill_dir.name] = accepted
    return skills, excluded


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_manifest(source: Path, skills: dict[str, list[Path]], excluded: dict[str, str]) -> dict[str, Any]:
    entries: dict[str, Any] = {}
    for name, paths in skills.items():
        entries[name] = {
            "files": {
                str(path.relative_to(source / name)): file_sha256(path)
                for path in paths
            }
        }
    return {
        "format_version": 1,
        "skills": entries,
        "excluded_files": excluded,
    }


def ensure_checkout(repo_url: str, checkout: Path) -> None:
    if checkout.exists():
        if not (checkout / ".git").is_dir():
            raise RuntimeError(f"checkout exists but is not a Git repository: {checkout}")
        origin = run(["git", "remote", "get-url", "origin"], cwd=checkout)
        if origin.returncode != 0 or origin.stdout.strip() != repo_url:
            raise RuntimeError("checkout origin does not match configured repository")
        dirty = run(["git", "status", "--porcelain"], cwd=checkout)
        if dirty.stdout.strip():
            raise RuntimeError("checkout has uncommitted changes; review them before syncing")
        fetched = run(["git", "fetch", "origin"], cwd=checkout)
        if fetched.returncode != 0:
            raise RuntimeError(f"git fetch failed:\n{fetched.stdout}")
        upstream = run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], cwd=checkout)
        if upstream.returncode == 0:
            pulled = run(["git", "pull", "--ff-only"], cwd=checkout)
            if pulled.returncode != 0:
                raise RuntimeError(f"fast-forward pull failed:\n{pulled.stdout}")
        return
    checkout.parent.mkdir(parents=True, exist_ok=True)
    cloned = run(["git", "clone", repo_url, str(checkout)])
    if cloned.returncode != 0:
        raise RuntimeError(f"git clone failed:\n{cloned.stdout}")


def copy_snapshot(
    source: Path,
    checkout: Path,
    managed_subdir: str,
    manifest_name: str,
    skills: dict[str, list[Path]],
    manifest: dict[str, Any],
    prune: bool,
) -> None:
    managed = (checkout / managed_subdir).resolve()
    checkout_resolved = checkout.resolve()
    if checkout_resolved not in managed.parents:
        raise RuntimeError("managed directory escapes checkout")
    managed.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="skill-sync-") as temp_dir:
        staging = Path(temp_dir)
        for name, paths in skills.items():
            target = staging / name
            for path in paths:
                relative = path.relative_to(source / name)
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
        for name in skills:
            destination = managed / name
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(staging / name, destination)
    if prune:
        for existing in managed.iterdir():
            if existing.is_dir() and existing.name not in skills:
                shutil.rmtree(existing)
    manifest_path = checkout / manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    config = load_config()
    args = parse_args(config)
    if (args.commit or args.push or args.prune) and not args.execute:
        print("--commit, --push, and --prune require --execute", file=sys.stderr)
        return 2
    if args.push and not args.commit:
        print("--push requires --commit", file=sys.stderr)
        return 2
    source = args.source.expanduser().resolve()
    checkout = args.checkout.expanduser().resolve()
    if not source.is_dir():
        print(f"Source skills directory not found: {source}", file=sys.stderr)
        return 2

    skills, excluded = discover(source)
    manifest = make_manifest(source, skills, excluded)
    print(f"Repository: {args.repo_url}")
    print(f"Checkout: {checkout}")
    print(f"Managed path: {args.managed_subdir}/")
    print(f"Skills selected ({len(skills)}): {', '.join(skills)}")
    print(f"Files selected: {sum(len(paths) for paths in skills.values())}")
    if excluded:
        print("Excluded files:")
        for path, reason in sorted(excluded.items()):
            print(f"  {path}: {reason}")
    else:
        print("Excluded files: none")

    if not args.execute:
        print("PLAN ONLY: no checkout, copy, commit, or push was performed.")
        return 0
    try:
        ensure_checkout(args.repo_url, checkout)
        copy_snapshot(
            source,
            checkout,
            args.managed_subdir,
            args.manifest,
            skills,
            manifest,
            args.prune,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    status = run(["git", "status", "--short"], cwd=checkout)
    print("Git changes:")
    print(status.stdout.rstrip() or "  (none)")
    if not args.commit:
        print("COPY COMPLETE: review the checkout diff before committing.")
        return 0

    run(["git", "add", "--", args.managed_subdir, args.manifest], cwd=checkout)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=checkout)
    if staged.returncode == 0:
        print("No staged changes; nothing to commit or push.")
        return 0
    committed = run(["git", "commit", "-m", args.message], cwd=checkout)
    if committed.returncode != 0:
        print(f"git commit failed:\n{committed.stdout}", file=sys.stderr)
        return 4
    print(committed.stdout.rstrip())
    if not args.push:
        print("COMMIT COMPLETE: remote repository was not changed.")
        return 0
    pushed = run(["git", "push", "-u", "origin", "HEAD"], cwd=checkout, capture=False)
    if pushed.returncode != 0:
        print("git push failed", file=sys.stderr)
        return 5
    print("PUSH COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
