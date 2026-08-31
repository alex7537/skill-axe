#!/usr/bin/env python3
"""Read-only candidate search across personal skills and an Obsidian vault."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


HIDDEN_PARTS = {".git", ".obsidian", ".claudian", ".system", ".trash", ".Trash"}


def readable_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def score(text: str, terms: list[str]) -> int:
    folded = text.casefold()
    return sum(folded.count(term.casefold()) for term in terms)


def frontmatter_value(text: str, key: str) -> str:
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return ""
    value = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?(.*?)[\"']?\s*$", match.group(1))
    return value.group(1).strip() if value else ""


def note_title(text: str, fallback: str) -> str:
    title = frontmatter_value(text, "title")
    if title:
        return title
    heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return heading.group(1).strip() if heading else fallback


def allowed_markdown(path: Path) -> bool:
    return path.suffix.casefold() == ".md" and not any(part in HIDDEN_PARTS for part in path.parts)


def scan_skills(roots: list[Path], terms: list[str]) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for entrypoint in root.rglob("SKILL.md"):
            skill_dir = entrypoint.parent.resolve()
            if skill_dir in seen or any(part in HIDDEN_PARTS for part in skill_dir.parts):
                continue
            seen.add(skill_dir)
            entry_text = readable_text(entrypoint)
            matched_files: list[str] = []
            total = score(entry_text, terms)
            if total:
                matched_files.append("SKILL.md")
            for candidate in skill_dir.rglob("*.md"):
                if candidate == entrypoint or not allowed_markdown(candidate):
                    continue
                candidate_score = score(readable_text(candidate), terms)
                if candidate_score:
                    total += candidate_score
                    matched_files.append(candidate.relative_to(skill_dir).as_posix())
            if total:
                found.append(
                    {
                        "name": frontmatter_value(entry_text, "name") or skill_dir.name,
                        "description": frontmatter_value(entry_text, "description"),
                        "path": str(skill_dir),
                        "score": total,
                        "matched_files": sorted(matched_files),
                    }
                )
    return sorted(found, key=lambda item: (-int(item["score"]), str(item["name"])))


def scan_vault(vault: Path | None, terms: list[str]) -> list[dict[str, object]]:
    if vault is None or not vault.is_dir():
        return []
    found: list[dict[str, object]] = []
    for path in vault.rglob("*.md"):
        if not allowed_markdown(path):
            continue
        text = readable_text(path)
        total = score(path.name, terms) * 3 + score(text, terms)
        if total:
            found.append(
                {
                    "path": path.relative_to(vault).as_posix(),
                    "title": note_title(text, path.stem),
                    "score": total,
                }
            )
    return sorted(found, key=lambda item: (-int(item["score"]), str(item["path"])))


def default_skill_roots() -> list[Path]:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return [codex_home / "skills", Path.home() / ".agents" / "skills"]


def default_vault() -> Path | None:
    candidate = Path.home() / "Documents" / "Obsidian Vault"
    return candidate if (candidate / ".obsidian").is_dir() else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", required=True, help="Discriminating term; repeat 2-6 times.")
    parser.add_argument("--skills-root", action="append", type=Path, help="Personal skill root; repeat as needed.")
    parser.add_argument("--vault", type=Path, help="Exact Obsidian Vault root containing .obsidian/.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum matches per category.")
    args = parser.parse_args()

    roots = [path.expanduser().resolve() for path in (args.skills_root or default_skill_roots())]
    vault = args.vault.expanduser().resolve() if args.vault else default_vault()
    if vault is not None and not (vault / ".obsidian").is_dir():
        parser.error(f"Not an Obsidian Vault root: {vault}")

    result = {
        "queries": args.query,
        "skill_roots": [str(path) for path in roots],
        "vault": str(vault) if vault else None,
        "skills": scan_skills(roots, args.query)[: args.limit],
        "notes": scan_vault(vault, args.query)[: args.limit],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
