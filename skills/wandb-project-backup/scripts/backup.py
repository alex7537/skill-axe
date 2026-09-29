"""Read-only W&B backup for explicitly selected projects."""
import argparse
import base64
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ENTITY = None
PROJECTS = []
ROOT = None
import wandb


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n")
    tmp.replace(path)


def safe_path(root, name):
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError("Unsafe remote file path")
    return p


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inventory(api, dest):
    result = {"entity": ENTITY, "created_at": datetime.now(timezone.utc).isoformat(),
              "sdk": wandb.__version__, "inventory_complete": False, "projects": []}
    for project in PROJECTS:
        path = f"{ENTITY}/{project}"
        item = {"name": project, "runs": [], "artifacts": []}
        for run in api.runs(path):
            files = [{"name": f.name, "size": f.size, "md5": f.md5} for f in run.files()]
            item["runs"].append({"id": run.id, "name": run.name, "state": run.state, "files": files})
        for kind in api.artifact_types(path):
            for collection in kind.collections():
                for artifact in api.artifacts(kind.name, f"{path}/{collection.name}"):
                    item["artifacts"].append({"name": artifact.name, "type": kind.name,
                                              "size": artifact.size, "digest": artifact.digest})
        result["projects"].append(item)
        save(dest / "inventory.json", result)
        print(json.dumps({"project": project, "runs": len(item["runs"]),
                          "artifacts": len(item["artifacts"]),
                          "artifact_bytes": sum(a["size"] or 0 for a in item["artifacts"])}), flush=True)
    result["inventory_complete"] = True
    save(dest / "inventory.json", result)
    return result


def export(api, dest, inv):
    errors = []
    totals = {"runs": 0, "history_rows": 0, "files": 0, "artifacts": 0}

    def download_file(remote, folder):
        try:
            local = safe_path(folder / "files", remote.name)
            remote.download(root=str(folder / "files"), replace=True, api=api).close()
            if not local.is_file():
                raise ValueError("Downloaded file missing")
            expected = remote.md5
            if expected:
                actual = digest(local, "md5")
                b64 = base64.b64encode(bytes.fromhex(actual)).decode()
                if expected not in (actual, b64):
                    raise ValueError("Remote MD5 mismatch")
            return remote.name, None
        except Exception as exc:
            return remote.name, exc

    def problem(stage, target, exc):
        errors.append({"stage": stage, "target": target, "error_type": type(exc).__name__,
                       "message": str(exc)[:600]})
        save(dest / "errors.json", errors)
        print(f"ERROR {stage} {target}: {type(exc).__name__}", flush=True)

    for project in inv["projects"]:
        pname = project["name"]
        for info in project["runs"]:
            target = f"{ENTITY}/{pname}/{info['id']}"
            folder = dest / pname / "runs" / info["id"]
            marker = folder / "complete.json"
            if marker.exists():
                old = json.loads(marker.read_text())
                totals["runs"] += 1
                totals["history_rows"] += old["history_rows"]
                totals["files"] += old["files"]
                continue
            before = len(errors)
            try:
                run = api.run(target)
                save(folder / "metadata.json", {"id": run.id, "name": run.name, "url": run.url,
                     "state": run.state, "created_at": run.created_at, "tags": run.tags,
                     "notes": run.notes, "group": run.group, "job_type": run.job_type})
                save(folder / "config.json", run.config)
                save(folder / "summary.json", dict(run.summary))
                rows = 0
                with (folder / "history.jsonl.partial").open("w") as f:
                    for row in run.scan_history(page_size=1000, use_cache=False):
                        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
                        rows += 1
                (folder / "history.jsonl.partial").replace(folder / "history.jsonl")
                totals["history_rows"] += rows
                count = 0
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for name, exc in pool.map(lambda f: download_file(f, folder), list(run.files())):
                        if exc:
                            problem("file", target + "/" + name, exc)
                        else:
                            count += 1
                totals["files"] += count
                if len(errors) == before:
                    save(marker, {"history_rows": rows, "files": count})
                    totals["runs"] += 1
                print(f"RUN {info['id']} rows={rows} files={count}", flush=True)
            except Exception as exc:
                problem("run", target, exc)
        for info in project["artifacts"]:
            target = f"{ENTITY}/{pname}/{info['name']}"
            folder = safe_path(dest / pname / "artifacts", info["type"] + "/" + info["name"])
            marker = folder / "complete.json"
            if marker.exists():
                totals["artifacts"] += 1
                continue
            try:
                artifact = api.artifact(target, type=info["type"])
                save(folder / "metadata.json", {**info, "aliases": artifact.aliases,
                                              "metadata": artifact.metadata})
                artifact.download(root=str(folder / "files"), skip_cache=True)
                artifact.verify(str(folder / "files"))
                save(folder / "manifest.json", artifact.manifest.to_manifest_json())
                save(marker, {"verified": True})
                totals["artifacts"] += 1
                print(f"ARTIFACT {info['name']} verified", flush=True)
            except Exception as exc:
                problem("artifact", target, exc)
    save(dest / "errors.json", errors)
    save(dest / "result.json", {"completed_at": datetime.now(timezone.utc).isoformat(),
                               "totals": totals, "errors": len(errors),
                               "complete": not errors})
    checksums = []
    for path in sorted(dest.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            checksums.append(f"{digest(path)}  {path.relative_to(dest)}")
    (dest / "SHA256SUMS").write_text("\n".join(checksums) + "\n")
    print(json.dumps({"totals": totals, "errors": len(errors)}), flush=True)
    return not errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["inventory", "export"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--entity", required=True)
    parser.add_argument("--project", action="append", required=True)
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    ENTITY, PROJECTS = args.entity, args.project
    os.environ.setdefault("WANDB_CACHE_DIR", str(ROOT / ".cache"))
    os.environ.setdefault("WANDB_DATA_DIR", str(ROOT / ".data"))
    if Path(args.snapshot).name != args.snapshot or args.snapshot in (".", ".."):
        parser.error("snapshot must be one directory name")
    dest = safe_path(ROOT, args.snapshot)
    dest.mkdir(parents=True, exist_ok=True)
    api = wandb.Api(overrides={"base_url": "https://api.wandb.ai"}, timeout=60)
    if args.mode == "inventory":
        if (dest / "inventory.json").exists():
            parser.error("inventory already exists; resume export or choose a new snapshot")
        inventory(api, dest)
    else:
        inv = json.loads((dest / "inventory.json").read_text())
        if not inv.get("inventory_complete"):
            parser.error("inventory incomplete; create a fresh snapshot and enumerate again")
        if inv["entity"] != ENTITY or [p["name"] for p in inv["projects"]] != PROJECTS:
            parser.error("entity/project arguments do not match inventory")
        raise SystemExit(0 if export(api, dest, inv) else 1)
