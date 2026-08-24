#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


METRICS = (
    "markdown",
    "attachments",
    "broken_or_ambiguous_links",
    "ambiguous_note_names",
    "isolated_notes",
    "notes_without_incoming",
    "duplicate_groups",
    "zero_files",
    "empty_dirs",
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Compare two Obsidian audit JSON files.")
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument(
        "--allow-content-count-change",
        action="store_true",
        help="Allow Markdown or attachment counts to decrease after an intentional removal.",
    )
    args = parser.parse_args()
    before = load(args.before)
    after = load(args.after)

    failures = []
    print(f"{'metric':32} {'before':>8} {'after':>8} {'delta':>8}")
    for key in METRICS:
        old = before["summary"][key]
        new = after["summary"][key]
        print(f"{key:32} {old:8d} {new:8d} {new-old:8d}")

    if after["summary"]["broken_or_ambiguous_links"] > before["summary"]["broken_or_ambiguous_links"]:
        failures.append("broken_or_ambiguous_links increased")
    if after["summary"]["ambiguous_note_names"] > before["summary"]["ambiguous_note_names"]:
        failures.append("ambiguous_note_names increased")
    if not args.allow_content_count_change:
        if after["summary"]["markdown"] < before["summary"]["markdown"]:
            failures.append("Markdown count decreased")
        if after["summary"]["attachments"] < before["summary"]["attachments"]:
            failures.append("attachment count decreased")

    old_protected = before.get("protected", {})
    new_protected = after.get("protected", {})
    if old_protected != new_protected:
        failures.append("protected folder hashes or membership changed")

    if failures:
        print("\nGATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("\nGATE: PASS")


if __name__ == "__main__":
    main()
