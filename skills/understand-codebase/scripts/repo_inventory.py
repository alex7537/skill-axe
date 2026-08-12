#!/usr/bin/env python3
"""Produce a compact, read-only inventory of a source repository."""

from __future__ import annotations

import argparse
import collections
import os
from pathlib import Path
import subprocess


MANIFESTS = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "CMakeLists.txt", "Makefile", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "WORKSPACE", "BUILD", "BUILD.bazel",
}
DOCS = {"README", "CONTRIBUTING", "ARCHITECTURE", "DESIGN", "AGENTS", "CHANGELOG"}
ENTRY_NAMES = {
    "main.py", "app.py", "server.py", "cli.py", "manage.py", "__main__.py",
    "main.go", "main.rs", "main.c", "main.cpp", "index.js", "index.ts",
    "server.js", "server.ts", "app.js", "app.ts", "Program.cs",
}
EXT_LANG = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".c": "C",
    ".h": "C/C++", ".cc": "C++", ".cpp": "C++", ".hpp": "C++",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".scala": "Scala", ".sh": "Shell", ".sql": "SQL", ".lua": "Lua",
}
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "target",
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".next",
}


def git_files(root: Path) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
            check=True, capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return sorted({item.decode("utf-8", "surrogateescape") for item in result.stdout.split(b"\0") if item})


def walk_files(root: Path) -> list[str]:
    files: list[str] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        base = Path(current)
        for name in sorted(names):
            path = base / name
            try:
                files.append(path.relative_to(root).as_posix())
            except ValueError:
                continue
    return files


def is_doc(path: str) -> bool:
    stem = Path(path).stem.upper()
    return any(stem == name or stem.startswith(name + ".") for name in DOCS)


def is_test(path: str) -> bool:
    lowered = path.lower()
    parts = Path(lowered).parts
    name = Path(lowered).name
    return (
        any(part in {"test", "tests", "spec", "specs", "__tests__"} for part in parts)
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
        or name.endswith("_test.go")
        or name.endswith("_test.py")
    )


def print_group(title: str, items: list[str], limit: int) -> None:
    print(f"\n## {title} ({len(items)})")
    for item in items[:limit]:
        print(f"- `{item}`")
    if len(items) > limit:
        print(f"- … {len(items) - limit} more")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument("--limit", type=int, default=30, help="max paths shown per group")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    if args.limit < 1:
        parser.error("--limit must be positive")

    files = git_files(root)
    source = "git ls-files" if files is not None else "filesystem walk"
    files = files if files is not None else walk_files(root)

    languages = collections.Counter(
        EXT_LANG[Path(path).suffix.lower()]
        for path in files
        if Path(path).suffix.lower() in EXT_LANG
    )
    top_dirs = collections.Counter(path.split("/", 1)[0] for path in files if "/" in path)
    manifests = [path for path in files if Path(path).name in MANIFESTS]
    docs = [path for path in files if is_doc(path)]
    entries = [path for path in files if Path(path).name in ENTRY_NAMES]
    tests = [path for path in files if is_test(path)]

    print("# Repository inventory")
    print(f"\n- Root: `{root}`")
    print(f"- Discovery: {source}")
    print(f"- Files: {len(files)}")
    print("- Languages: " + (", ".join(f"{name} {count}" for name, count in languages.most_common()) or "none detected"))
    print("- Top directories: " + (", ".join(f"{name} {count}" for name, count in top_dirs.most_common(15)) or "none"))

    print_group("Instructions and documentation", docs, args.limit)
    print_group("Build and dependency manifests", manifests, args.limit)
    print_group("Entry-point candidates", entries, args.limit)
    print_group("Test files", tests, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
