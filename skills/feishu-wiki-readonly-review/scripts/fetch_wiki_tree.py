#!/usr/bin/env python3
"""Discover a Feishu/Lark Wiki subtree using read-only lark-cli calls."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from collections import deque
from dataclasses import dataclass
from typing import Any


SUB_PAGE_RE = re.compile(r"<sub-page\b(?P<attrs>[^>]*)/?>", re.IGNORECASE)
CITE_RE = re.compile(r"<cite\b(?P<attrs>[^>]*)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r"([\w-]+)=\"([^\"]*)\"")
SOURCE_RE = re.compile(r"<source\b[^>]*/?>", re.IGNORECASE)
FIGURE_RE = re.compile(r"<figure\b[^>]*>.*?</figure>", re.IGNORECASE | re.DOTALL)
SENSITIVE_ATTR_RE = re.compile(r"\s(?:href|src)=\"[^\"]*\"", re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class PendingPage:
    token: str
    title: str | None
    depth: int
    parent: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recursively discover Docx/Wiki children using only "
            "`lark-cli docs +fetch --as user`."
        )
    )
    parser.add_argument("root", help="Feishu /wiki/ or /docx/ URL, or a document token")
    parser.add_argument("--max-depth", type=int, default=8, help="maximum child depth (default: 8)")
    parser.add_argument(
        "--include-cites",
        action="store_true",
        help="also follow cited Docx/Wiki pages; off by default to bound scope",
    )
    parser.add_argument(
        "--include-content",
        action="store_true",
        help="emit sanitized page content; default output is a compact catalog",
    )
    parser.add_argument(
        "--lark-cli",
        default=shutil.which("lark-cli") or "lark-cli",
        help="path to lark-cli (default: PATH lookup)",
    )
    parser.add_argument("--timeout", type=int, default=120, help="seconds per fetch (default: 120)")
    args = parser.parse_args()
    if args.max_depth < 0:
        parser.error("--max-depth must be >= 0")
    return args


def run_fetch(cli: str, token: str, timeout: int) -> dict[str, Any]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    command = [
        cli,
        "docs",
        "+fetch",
        "--as",
        "user",
        "--doc",
        token,
        "--doc-format",
        "markdown",
        "--detail",
        "simple",
        "--format",
        "json",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"lark-cli not found: {cli}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"fetch timed out after {timeout}s for {token}") from exc

    raw = completed.stdout if completed.stdout.strip() else completed.stderr
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"lark-cli returned non-JSON output for {token} (exit {completed.returncode})"
        ) from exc
    if completed.returncode != 0 or payload.get("ok") is not True:
        error = payload.get("error", {})
        message = error.get("message") or error.get("hint") or "unknown lark-cli error"
        raise RuntimeError(f"fetch failed for {token}: {message}")
    return payload


def attrs(fragment: str) -> dict[str, str]:
    return {key: html.unescape(value) for key, value in ATTR_RE.findall(fragment)}


def links_from(content: str, include_cites: bool) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    patterns = [("sub-page", SUB_PAGE_RE)]
    if include_cites:
        patterns.append(("cite", CITE_RE))
    for relation, pattern in patterns:
        for match in pattern.finditer(content):
            item = attrs(match.group("attrs"))
            token = item.get("doc-id")
            file_type = item.get("file-type", "").lower()
            if not token or file_type not in {"docx", "wiki"}:
                continue
            found.append(
                {
                    "token": token,
                    "title": item.get("title", ""),
                    "file_type": file_type,
                    "relation": relation,
                }
            )
    return found


def sanitized(content: str) -> str:
    content = FIGURE_RE.sub("<figure omitted/>", content)
    content = SOURCE_RE.sub("<source omitted/>", content)
    content = SENSITIVE_ATTR_RE.sub("", content)
    return content.strip()


def inferred_title(content: str) -> str | None:
    match = TITLE_RE.search(content) or HEADING_RE.search(content)
    return html.unescape(match.group(1).strip()) if match else None


def main() -> int:
    args = parse_args()
    queue: deque[PendingPage] = deque([PendingPage(args.root, None, 0, None)])
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    while queue:
        pending = queue.popleft()
        if pending.token in visited or pending.depth > args.max_depth:
            continue
        visited.add(pending.token)
        try:
            payload = run_fetch(args.lark_cli, pending.token, args.timeout)
        except RuntimeError as exc:
            failures.append({"token": pending.token, "error": str(exc)})
            continue

        document = payload["data"]["document"]
        content = document.get("content", "")
        children = links_from(content, args.include_cites)
        page: dict[str, Any] = {
            "token": pending.token,
            "title": pending.title or inferred_title(content),
            "depth": pending.depth,
            "parent": pending.parent,
            "document_id": document.get("document_id"),
            "revision_id": document.get("revision_id"),
            "children": children,
        }
        if args.include_content:
            page["content"] = sanitized(content)
        pages.append(page)

        if pending.depth < args.max_depth:
            for child in children:
                queue.append(
                    PendingPage(
                        token=child["token"],
                        title=child.get("title") or None,
                        depth=pending.depth + 1,
                        parent=document.get("document_id") or pending.token,
                    )
                )

    result = {
        "ok": not failures,
        "root": args.root,
        "identity": "user",
        "page_count": len(pages),
        "failure_count": len(failures),
        "pages": pages,
        "failures": failures,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
