#!/usr/bin/env python3
"""Plan or install the managed milestone-capture block in global AGENTS.md."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


START = "<!-- capture-session-to-skill:start -->"
END = "<!-- capture-session-to-skill:end -->"
BLOCK = f"""{START}
# Reusable workflow capture

- When using one or more personal skills, record each skill at most once per session with `python3 ~/.codex/skills/capture-session-to-skill/scripts/record_skill_usage.py <skill-name> [...]`.
- When a non-trivial task reaches a verified milestone or completes, assess whether it produced a repeatable workflow, difficult diagnosis, non-obvious constraint, reusable script, or valuable failure mode.
- If it did, finish the requested work first, then add one concise optional question asking whether to capture the result by creating or updating a skill with `capture-session-to-skill` and back it up to `skill-axe`.
- Do not ask for trivial answers, unresolved work, or tasks already creating, updating, reviewing, or syncing a skill.
- Never copy secrets or raw session transcripts into a skill or Git repository.
{END}
"""


def render(existing: str) -> tuple[str, str]:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
    if pattern.search(existing):
        return pattern.sub(BLOCK, existing, count=1), "update"
    prefix = existing.rstrip()
    return ((prefix + "\n\n") if prefix else "") + BLOCK, "append"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-file", type=Path, default=Path.home() / ".codex" / "AGENTS.md")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    path = args.agents_file.expanduser().resolve()
    existing = path.read_text() if path.exists() else ""
    updated, action = render(existing)
    changed = updated != existing
    print(f"Global instructions: {path}")
    print(f"Action: {action if changed else 'none'}")
    if not args.execute:
        print("PLAN ONLY: rerun with --execute to install the managed reminder block.")
        return 0
    if not changed:
        print("Reminder already current.")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated)
    print("Reminder installed. It will load in newly started Codex sessions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
