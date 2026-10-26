#!/usr/bin/env python3
"""Validate the structure and internal consistency of a claim/source CSV ledger.

This performs no network access and cannot establish source existence or claim entailment.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = (
    "claim_id", "claim_text", "language", "source_id", "title", "authors",
    "year", "identifier_type", "identifier", "landing_url", "source_kind",
    "locator", "support_type", "evidence_status", "verified_at",
    "status_checked_at", "notes",
)
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
ARXIV_RE = re.compile(r"^(?:\d{4}\.\d{4,5}|[a-z-]+/\d{7})(?:v\d+)?$", re.IGNORECASE)
SUPPORT_TYPES = {"direct", "partial", "contextual", "counterevidence", "inference"}
EVIDENCE_STATUSES = {
    "primary-fulltext", "primary-metadata", "official-supplement",
    "secondary-only", "unresolved",
}
LANGUAGES = {"zh", "en", "bilingual", "other"}
SOURCE_KINDS = {"journal", "conference", "preprint", "review", "thesis", "dataset", "code", "other"}
IDENTIFIER_TYPES = {"doi", "arxiv", "url", "other"}


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def issue(bucket: list[str], row_number: int, message: str) -> None:
    bucket.append(f"row {row_number}: {message}")


def validate(path: Path, schema_only: bool = False) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [name for name in REQUIRED if name not in headers]
        extra = [name for name in headers if name not in REQUIRED]
        if missing:
            errors.append("missing columns: " + ", ".join(missing))
        if extra:
            warnings.append("extra columns: " + ", ".join(extra))
        if missing or schema_only:
            return errors, warnings, 0

        rows = list(reader)

    if not rows:
        errors.append("ledger contains no evidence rows")
        return errors, warnings, 0

    seen_pairs: set[tuple[str, str, str]] = set()
    source_fingerprints: dict[str, tuple[str, str, str, str]] = {}

    for row_number, raw in enumerate(rows, start=2):
        row = {key: (value or "").strip() for key, value in raw.items() if key is not None}
        for field in ("claim_id", "claim_text", "source_id", "title", "authors", "year", "identifier_type", "identifier", "landing_url", "source_kind", "support_type", "evidence_status", "verified_at", "status_checked_at"):
            if not row[field]:
                issue(errors, row_number, f"{field} is required")

        for field in ("claim_id", "source_id"):
            if row[field] and not ID_RE.fullmatch(row[field]):
                issue(errors, row_number, f"{field} has an invalid identifier: {row[field]!r}")

        if row["language"] not in LANGUAGES:
            issue(errors, row_number, f"language must be one of {sorted(LANGUAGES)}")
        if row["support_type"] not in SUPPORT_TYPES:
            issue(errors, row_number, f"support_type must be one of {sorted(SUPPORT_TYPES)}")
        if row["evidence_status"] not in EVIDENCE_STATUSES:
            issue(errors, row_number, f"evidence_status must be one of {sorted(EVIDENCE_STATUSES)}")
        if row["source_kind"] not in SOURCE_KINDS:
            issue(errors, row_number, f"source_kind must be one of {sorted(SOURCE_KINDS)}")
        if row["identifier_type"] not in IDENTIFIER_TYPES:
            issue(errors, row_number, f"identifier_type must be one of {sorted(IDENTIFIER_TYPES)}")

        if row["year"] and (not row["year"].isdigit() or not 1500 <= int(row["year"]) <= date.today().year + 1):
            issue(errors, row_number, "year must be a four-digit publication year no later than next year")
        for field in ("verified_at", "status_checked_at"):
            if row[field] and not valid_iso_date(row[field]):
                issue(errors, row_number, f"{field} must use YYYY-MM-DD")
        if row["landing_url"] and not valid_url(row["landing_url"]):
            issue(errors, row_number, "landing_url must be an http(s) URL")

        identifier_type = row["identifier_type"]
        identifier = row["identifier"].removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        if identifier_type == "doi" and identifier and not DOI_RE.fullmatch(identifier):
            issue(errors, row_number, "identifier is not a plausible DOI")
        elif identifier_type == "arxiv" and identifier and not ARXIV_RE.fullmatch(identifier.removeprefix("arXiv:")):
            issue(errors, row_number, "identifier is not a plausible arXiv ID")
        elif identifier_type == "url" and identifier and not valid_url(identifier):
            issue(errors, row_number, "URL identifier must be an http(s) URL")

        if row["support_type"] in {"direct", "partial", "counterevidence"} and row["evidence_status"] in {"primary-fulltext", "official-supplement"} and not row["locator"]:
            issue(errors, row_number, "full-text support requires a page/section/table/figure/equation locator")
        if row["support_type"] == "direct" and row["evidence_status"] in {"primary-metadata", "secondary-only", "unresolved"}:
            issue(errors, row_number, "direct support is stronger than the recorded evidence status")

        pair = (row["claim_id"], row["source_id"], row["support_type"])
        if pair in seen_pairs:
            issue(warnings, row_number, f"duplicate claim/source/support row: {pair}")
        seen_pairs.add(pair)

        fingerprint = (row["title"].casefold(), row["year"], row["identifier_type"].casefold(), identifier.casefold())
        prior = source_fingerprints.setdefault(row["source_id"], fingerprint)
        if prior != fingerprint:
            issue(errors, row_number, f"source_id {row['source_id']!r} has inconsistent title/year/identifier metadata")

    return errors, warnings, len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--schema-only", action="store_true", help="check headers without requiring data rows")
    args = parser.parse_args()

    if not args.ledger.is_file():
        print(f"ERROR: ledger not found: {args.ledger}")
        return 2

    try:
        errors, warnings, count = validate(args.ledger, args.schema_only)
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: could not read ledger: {exc}")
        return 2

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    print(f"SUMMARY: rows={count} errors={len(errors)} warnings={len(warnings)}")
    print("NOTE: structural validation does not verify source existence, publication status, or claim entailment.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
