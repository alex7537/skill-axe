#!/usr/bin/env python3
"""Validate that a PPTX contains useful, annotated speaker notes."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def natural_key(path: str) -> tuple[int, str]:
    match = re.search(r"notesSlide(\d+)\.xml$", path)
    return (int(match.group(1)) if match else 10**9, path)


def extract_text(archive: zipfile.ZipFile, member: str) -> str:
    root = ET.fromstring(archive.read(member))
    parts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    return "\n".join(part for part in parts if part.strip())


def source_lines(text: str) -> list[str]:
    if "[Sources]" not in text:
        return []
    block = text.split("[Sources]", 1)[1]
    return [line.strip() for line in block.splitlines() if line.strip().startswith("-")]


def validate_note(text: str, args: argparse.Namespace) -> list[str]:
    issues: list[str] = []
    if "[Sources]" not in text:
        issues.append("missing [Sources]")

    sources = source_lines(text)
    if not sources:
        issues.append("no source entries")
    if args.require_annotated_sources:
        unannotated = [line for line in sources if "：" not in line and ": " not in line]
        if unannotated:
            issues.append(f"unannotated source entries: {len(unannotated)}")

    if args.require_accessibility:
        if "[给爷爷奶奶的一句话]" not in text and not re.search(r"\[[^\]]*类比[^\]]*\]", text):
            issues.append("missing accessible analogy")
        if not re.search(r"\[(最小数学|闭环数学|数学原理|最小数值例子|张量和形状)", text):
            issues.append("missing minimum mathematics or numerical example")

    if args.require_timed_scripts:
        if "[5分钟基础稿" not in text:
            issues.append("missing 5-minute base segment")
        if "[10分钟扩展" not in text:
            issues.append("missing 10-minute extension segment")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--expected-slides", type=int)
    parser.add_argument("--require-accessibility", action="store_true")
    parser.add_argument("--require-timed-scripts", action="store_true")
    parser.add_argument("--require-annotated-sources", action="store_true")
    args = parser.parse_args()

    if not args.pptx.is_file():
        print(f"ERROR: file not found: {args.pptx}", file=sys.stderr)
        return 2

    try:
        with zipfile.ZipFile(args.pptx) as archive:
            members = sorted(
                (name for name in archive.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)),
                key=natural_key,
            )
            if args.expected_slides is not None and len(members) != args.expected_slides:
                print(f"ERROR: expected {args.expected_slides} notes slides, found {len(members)}")
                return 1
            if not members:
                print("ERROR: no speaker notes found")
                return 1

            failures = 0
            for index, member in enumerate(members, start=1):
                text = extract_text(archive, member)
                issues = validate_note(text, args)
                if issues:
                    failures += 1
                    print(f"slide {index}: FAIL - {'; '.join(issues)}")
                else:
                    print(f"slide {index}: PASS ({len(text)} chars, {len(source_lines(text))} sources)")

            if failures:
                print(f"FAILED: {failures}/{len(members)} notes slides have issues")
                return 1
            print(f"PASSED: {len(members)} notes slides validated")
            return 0
    except zipfile.BadZipFile:
        print(f"ERROR: not a valid PPTX/ZIP file: {args.pptx}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
