#!/usr/bin/env python3
"""Synchronize applications.json into index.html's fallbackData block."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def sync_block(html: str, data_path: Path, block_id: str) -> str:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"{data_path.name} root must be an array")

    block = re.compile(
        rf'(<script id="{re.escape(block_id)}" type="application/json">)(.*?)(</script>)',
        re.DOTALL,
    )
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    updated, count = block.subn(
        lambda match: f"{match.group(1)}\n{payload}\n  {match.group(3)}",
        html,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"{block_id} block was not found exactly once")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    args = parser.parse_args()

    html_path = args.repository / "index.html"
    html = html_path.read_text(encoding="utf-8")
    html = sync_block(html, args.repository / "applications.json", "fallbackData")
    luh_path = args.repository / "luh.json"
    if luh_path.exists():
        html = sync_block(html, luh_path, "luhFallbackData")
    html_path.write_text(html, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
