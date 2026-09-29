"""Independently validate this snapshot, build an index, and package it."""
import argparse
import base64
import hashlib
import json
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--snapshot", type=Path, required=True)
parser.add_argument("--archive", type=Path, required=True)
args = parser.parse_args()
SNAPSHOT = args.snapshot.resolve()
archive = args.archive.resolve()
if archive.is_relative_to(SNAPSHOT):
    parser.error("archive must be outside the snapshot directory")


def read(path):
    return json.loads(path.read_text())


def sha(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


result = read(SNAPSHOT / "result.json")
assert result["complete"] and result["errors"] == 0
assert read(SNAPSHOT / "errors.json") == []
assert not list(SNAPSHOT.rglob("*.partial"))
inv = read(SNAPSHOT / "inventory.json")
assert inv.get("inventory_complete", True), "Incomplete inventory"
counts = {"runs": 0, "files": 0, "history_rows": 0, "artifacts": 0}
lines = ["# 实验记录索引", "", "本地训练记录快照。模型是否已上传须查看 inventory.json 的文件与 Artifact 类型。", ""]
for project in inv["projects"]:
    pname = project["name"]
    lines.extend([f"## {pname}", "", f"Run 数量：{len(project['runs'])}", "",
                  "| Run ID | 实验名称 | 状态 | 历史行数 |", "|---|---|---|---:|"])
    for info in project["runs"]:
        folder = SNAPSHOT / pname / "runs" / info["id"]
        complete = read(folder / "complete.json")
        for name in ["metadata.json", "config.json", "summary.json"]:
            read(folder / name)
        rows = 0
        with (folder / "history.jsonl").open() as f:
            for row in f:
                assert isinstance(json.loads(row), dict)
                rows += 1
        assert rows == complete["history_rows"]
        assert complete["files"] == len(info["files"])
        for remote in info["files"]:
            file = folder / "files" / remote["name"]
            assert file.is_file(), file
            if remote["md5"]:
                actual = sha(file, "md5")
                assert remote["md5"] in (actual, base64.b64encode(bytes.fromhex(actual)).decode()), file
            counts["files"] += 1
        counts["runs"] += 1
        counts["history_rows"] += rows
        name = info["name"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| [{info['id']}]({pname}/runs/{info['id']}/metadata.json) | {name} | {info['state']} | {rows} |")
    lines.append("")
    for info in project["artifacts"]:
        folder = SNAPSHOT / pname / "artifacts" / info["type"] / info["name"]
        assert read(folder / "complete.json")["verified"]
        manifest = read(folder / "manifest.json")
        for name, entry in manifest["contents"].items():
            file = (folder / "files" / name).resolve()
            assert file.is_relative_to((folder / "files").resolve()), name
            assert file.is_file(), file
            if not entry.get("ref"):
                actual = sha(file, "md5")
                assert entry["digest"] in (actual, base64.b64encode(bytes.fromhex(actual)).decode()), file
            # References may use provider-specific digests; SDK verification is
            # retained, but offline MD5 verification applies only to stored bytes.
        counts["artifacts"] += 1
assert counts == result["totals"], (counts, result["totals"])
(SNAPSHOT / "INDEX.md").write_text("\n".join(lines) + "\n")
(SNAPSHOT / "validation.json").write_text(json.dumps({"verified": True, "counts": counts,
    "checks": ["inventory_coverage", "run_file_md5_where_available", "history_json_and_row_counts",
               "artifact_manifest_files_and_md5_for_stored_entries", "no_partial_files"]}, indent=2) + "\n")
paths = sorted(p for p in SNAPSHOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
(SNAPSHOT / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(SNAPSHOT)}\n" for p in paths))
archive.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(SNAPSHOT.rglob("*")):
        if p.is_file():
            z.write(p, SNAPSHOT.name + "/" + str(p.relative_to(SNAPSHOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
checksum = sha(archive)
archive.with_suffix(".zip.sha256").write_text(f"{checksum}  {archive.name}\n")
print(json.dumps({"verified": True, "counts": counts, "archive": str(archive),
                  "archive_bytes": archive.stat().st_size, "sha256": checksum}, indent=2))
