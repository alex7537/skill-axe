#!/usr/bin/env python3
"""Check high-signal structural invariants in a blind-box service scaffold."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_SUFFIXES = {
    ".c",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".md",
    ".mjs",
    ".py",
    ".rs",
    ".sql",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {".git", "coverage", "dist", "build", "node_modules", ".next", ".vite"}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Root of the generated project")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def read_files(root: Path) -> dict[Path, str]:
    files: dict[Path, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        try:
            files[path.relative_to(root)] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return files


def contains(corpus: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, corpus, flags=re.IGNORECASE) for pattern in patterns)


def main() -> int:
    args = parse_args()
    root = args.project.expanduser().resolve()
    if not root.is_dir():
        print(f"error: project directory does not exist: {root}", file=sys.stderr)
        return 2

    files = read_files(root)
    corpus = "\n".join(files.values())
    code_corpus = "\n".join(
        text for path, text in files.items() if path.suffix.lower() not in {".md", ".yaml", ".yml", ".sql"}
    )
    web_corpus = "\n".join(
        text for path, text in files.items() if any(part in {"web", "frontend", "storefront", "client"} for part in path.parts)
    )
    code_paths = [path for path in files if path.suffix.lower() not in {".md", ".yaml", ".yml", ".sql"}]
    test_paths = [path for path in code_paths if "test" in path.name.lower() or "spec" in path.name.lower()]

    checks = [
        Check(
            "secure-server-rng",
            contains(code_corpus, [r"crypto\.randomInt", r"randomBytes", r"SecureRandom", r"crypto/rand", r"secrets\."]),
            "server code references a cryptographically secure RNG",
        ),
        Check(
            "idempotency",
            contains(corpus, [r"idempotency[-_ ]?key", r"Idempotency-Key"]),
            "idempotency is represented in code or contract",
        ),
        Check(
            "inventory-boundary",
            contains(corpus, [r"remaining", r"inventory", r"库存"]),
            "inventory or remaining quantity is represented",
        ),
        Check(
            "audit-evidence",
            contains(corpus, [r"audit[_ -]?hash", r"previous[_ -]?hash", r"审计"]),
            "draw audit evidence is represented",
        ),
        Check(
            "pool-version",
            contains(corpus, [r"pool[_ -]?version", r"商品池版本", r"config[_ -]?hash"]),
            "published pool versioning is represented",
        ),
        Check(
            "no-client-math-random",
            not contains(web_corpus, [r"Math\.random\s*\("]),
            "frontend contains no Math.random call",
        ),
        Check(
            "automated-tests",
            bool(test_paths),
            f"found {len(test_paths)} test/spec source file(s)",
        ),
        Check(
            "architecture-contract",
            any("architecture" in str(path).lower() or "架构" in str(path) for path in files),
            "architecture documentation is present",
        ),
        Check(
            "api-contract",
            any("openapi" in str(path).lower() for path in files),
            "OpenAPI contract is present",
        ),
    ]

    if args.as_json:
        print(json.dumps({"project": str(root), "checks": [asdict(check) for check in checks]}, ensure_ascii=False, indent=2))
    else:
        for check in checks:
            mark = "PASS" if check.passed else "FAIL"
            print(f"[{mark}] {check.name}: {check.detail}")

    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
