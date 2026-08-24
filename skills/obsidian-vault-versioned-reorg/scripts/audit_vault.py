#!/usr/bin/env python3
import argparse
import collections
import hashlib
import json
import re
import urllib.parse
from pathlib import Path

WIKI_RE = re.compile(r"!?\[\[([^\]]+)\]\]")
MD_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hidden_part(rel):
    return any(part.startswith(".") for part in rel.parts)


def protected_tree(vault, requested):
    result = {}
    for raw in requested:
        path = (vault / raw).resolve()
        try:
            relative = path.relative_to(vault)
        except ValueError as exc:
            raise SystemExit(f"Protected path escapes vault: {raw}") from exc
        if not path.exists():
            raise SystemExit(f"Protected path does not exist: {raw}")
        members = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        digest = hashlib.sha256()
        for member in members:
            member_rel = member.relative_to(vault).as_posix()
            digest.update(member_rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(sha256(member).encode("ascii"))
            digest.update(b"\n")
        result[relative.as_posix()] = {
            "files": len(members),
            "sha256": digest.hexdigest(),
        }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--output", required=True)
    ap.add_argument("--protected", action="append", default=[], help="Vault-relative protected path; repeatable.")
    args = ap.parse_args()
    vault = Path(args.vault).resolve()
    if not vault.is_dir():
        raise SystemExit(f"Vault directory does not exist: {vault}")
    files = [p for p in vault.rglob("*") if p.is_file()]
    dirs = [p for p in vault.rglob("*") if p.is_dir()]
    rel = {p: p.relative_to(vault) for p in files}
    content_files = [p for p in files if not is_hidden_part(rel[p])]
    notes = [p for p in content_files if p.suffix.lower() == ".md"]
    assets = [p for p in content_files if p.suffix.lower() != ".md"]

    ext = collections.Counter((p.suffix.lower() or "[no extension]") for p in content_files)
    top = {}
    roots = sorted({r.parts[0] if len(r.parts) > 1 else "[root]" for r in map(rel.get, content_files)})
    for root in roots:
        group = [p for p in content_files if (rel[p].parts[0] if len(rel[p].parts) > 1 else "[root]") == root]
        top[root] = {
            "files": len(group),
            "markdown": sum(p.suffix.lower() == ".md" for p in group),
            "attachments": sum(p.suffix.lower() != ".md" for p in group),
            "bytes": sum(p.stat().st_size for p in group),
        }

    hashes = collections.defaultdict(list)
    for p in content_files:
        if p.stat().st_size:
            hashes[(p.stat().st_size, sha256(p))].append(rel[p].as_posix())
    dup_groups = [sorted(v) for v in hashes.values() if len(v) > 1]
    dup_groups.sort(key=lambda g: (-len(g), g))

    zero_files = sorted(rel[p].as_posix() for p in content_files if p.stat().st_size == 0)
    empty_dirs = []
    for d in dirs:
        dr = d.relative_to(vault)
        if is_hidden_part(dr):
            continue
        try:
            next(d.iterdir())
        except StopIteration:
            empty_dirs.append(dr.as_posix())
    empty_dirs.sort()

    stem_map = collections.defaultdict(list)
    exact_name_map = collections.defaultdict(list)
    canonical_map = collections.defaultdict(list)
    for p in notes:
        stem_map[p.stem.casefold()].append(p)
        exact_name_map[p.name.casefold()].append(p)
        canonical = re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", p.stem.casefold())
        canonical_map[canonical].append(p)
    ambiguous_names = {
        k: sorted(rel[p].as_posix() for p in v)
        for k, v in exact_name_map.items() if len(v) > 1
    }
    similar_names = []
    for k, vals in canonical_map.items():
        names = {p.stem.casefold() for p in vals}
        if k and len(names) > 1:
            similar_names.append(sorted(rel[p].as_posix() for p in vals))
    similar_names.sort(key=lambda g: (-len(g), g))

    rel_lookup = {rel[p].as_posix().casefold(): p for p in content_files}
    basename_lookup = collections.defaultdict(list)
    for p in content_files:
        basename_lookup[p.name.casefold()].append(p)
        if p.suffix.lower() == ".md":
            basename_lookup[p.stem.casefold()].append(p)

    incoming = collections.Counter()
    outgoing = collections.Counter()
    broken = []
    referenced_assets = set()

    def resolve(target, source, wiki=False):
        target = urllib.parse.unquote(target.strip().strip("<>"))
        if not target or target.startswith(("http://", "https://", "mailto:", "obsidian://", "data:")):
            return [], "external"
        target = target.split("#", 1)[0].split("|", 1)[0].strip()
        if not target:
            return [], "heading"
        candidates = []
        direct = (source.parent / target).resolve()
        try:
            direct_rel = direct.relative_to(vault).as_posix().casefold()
            if direct_rel in rel_lookup:
                candidates.append(rel_lookup[direct_rel])
            if not Path(target).suffix:
                md_rel = (direct_rel + ".md")
                if md_rel in rel_lookup:
                    candidates.append(rel_lookup[md_rel])
        except ValueError:
            pass
        if wiki:
            vault_direct = (vault / target).resolve()
            try:
                vault_rel = vault_direct.relative_to(vault).as_posix().casefold()
                if vault_rel in rel_lookup:
                    candidates.append(rel_lookup[vault_rel])
                if not Path(target).suffix and (vault_rel + ".md") in rel_lookup:
                    candidates.append(rel_lookup[vault_rel + ".md"])
            except ValueError:
                pass
        if wiki and not candidates:
            key = Path(target).name.casefold()
            candidates.extend(basename_lookup.get(key, []))
            if not Path(target).suffix:
                candidates.extend(basename_lookup.get((key + ".md"), []))
        unique = list(dict.fromkeys(candidates))
        return unique, "ok" if len(unique) == 1 else ("ambiguous" if unique else "missing")

    for source in notes:
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = source.read_text(encoding="utf-8", errors="replace")
        for kind, regex in (("wiki", WIKI_RE), ("markdown", MD_RE)):
            for raw in regex.findall(text):
                targets, status = resolve(raw, source, wiki=(kind == "wiki"))
                if status in ("external", "heading"):
                    continue
                if len(targets) == 1:
                    target = targets[0]
                    outgoing[rel[source].as_posix()] += 1
                    incoming[rel[target].as_posix()] += 1
                    if target.suffix.lower() != ".md":
                        referenced_assets.add(target)
                else:
                    broken.append({
                        "source": rel[source].as_posix(),
                        "target": raw,
                        "kind": kind,
                        "status": status,
                        "candidates": sorted(rel[p].as_posix() for p in targets),
                    })

    isolated_notes = sorted(
        rel[p].as_posix() for p in notes
        if incoming[rel[p].as_posix()] == 0 and outgoing[rel[p].as_posix()] == 0
    )
    no_incoming = sorted(rel[p].as_posix() for p in notes if incoming[rel[p].as_posix()] == 0)
    unreferenced_assets = sorted(rel[p].as_posix() for p in assets if p not in referenced_assets)

    naming_issues = []
    for p in content_files:
        name = p.name
        reasons = []
        if name != name.strip(): reasons.append("leading/trailing whitespace")
        if "  " in name: reasons.append("repeated spaces")
        if re.search(r"(?: copy|副本|\(\d+\)|_copy)(?=\.[^.]+$|$)", name, re.I): reasons.append("copy/version suffix")
        if re.search(r"[<>:\\|?*]", name): reasons.append("cross-platform unsafe character")
        if reasons:
            naming_issues.append({"path": rel[p].as_posix(), "reasons": reasons})

    result = {
        "vault": str(vault),
        "protected": protected_tree(vault, args.protected),
        "summary": {
            "all_files_including_hidden": len(files),
            "content_files": len(content_files),
            "markdown": len(notes),
            "attachments": len(assets),
            "content_bytes": sum(p.stat().st_size for p in content_files),
            "hidden_files": len(files) - len(content_files),
            "duplicate_groups": len(dup_groups),
            "zero_files": len(zero_files),
            "empty_dirs": len(empty_dirs),
            "ambiguous_note_names": len(ambiguous_names),
            "similar_name_groups": len(similar_names),
            "broken_or_ambiguous_links": len(broken),
            "isolated_notes": len(isolated_notes),
            "notes_without_incoming": len(no_incoming),
            "unreferenced_attachments": len(unreferenced_assets),
        },
        "extensions": dict(ext.most_common()),
        "top_level": top,
        "duplicate_groups": dup_groups,
        "zero_files": zero_files,
        "empty_dirs": empty_dirs,
        "ambiguous_note_names": ambiguous_names,
        "similar_name_groups": similar_names,
        "naming_issues": naming_issues,
        "broken_or_ambiguous_links": broken,
        "isolated_notes": isolated_notes,
        "notes_without_incoming": no_incoming,
        "unreferenced_attachments": unreferenced_assets,
    }
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
