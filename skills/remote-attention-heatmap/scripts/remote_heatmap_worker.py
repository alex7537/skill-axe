#!/usr/bin/env python3
"""Remote worker used by run_remote_attention_heatmap.py."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-b64", required=True)
    return parser.parse_args()


def resolve_remote_path(raw: str, *, kind: str) -> tuple[Path, list[str]]:
    candidates: list[str] = []

    def add(value: str) -> None:
        if value not in candidates:
            candidates.append(value)

    add(raw)
    add(raw.replace("/share_data_prj/", "/share_data/"))
    for value in list(candidates):
        add(value.replace("/worksapce/", "/workspace/"))
    for value in candidates:
        path = Path(value).expanduser()
        if kind == "file" and path.is_file():
            return path.resolve(), candidates
        if kind == "dir" and path.is_dir():
            return path.resolve(), candidates
    raise FileNotFoundError(f"remote {kind} not found; tried: {candidates}")


def infer_repo(checkpoint: Path) -> Path:
    for parent in checkpoint.parents:
        if (parent / "psi_policy").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    raise FileNotFoundError(f"could not infer PSI repository from checkpoint: {checkpoint}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tee_process(command: list[str], *, cwd: Path, env: dict[str, str], log_path: Path) -> None:
    print("[run]", " ".join(command))
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
        return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)


def choose_device(requested: str) -> str:
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but CUDA is unavailable")
    return requested


def write_report(bundle: Path, manifest: dict[str, object]) -> None:
    models = manifest["models"]
    lines = [
        "# Remote attention heatmap run",
        "",
        f"- Host: `{manifest['host']}`",
        f"- Device: `{manifest['device']}`",
        f"- Input: `{manifest['image_dir_resolved']}`",
        f"- Images: `{manifest['image_count']}`",
        f"- Heatmap script SHA-256: `{manifest['heatmap_script_sha256']}`",
        "",
        "## Models",
        "",
    ]
    for model in models:
        lines.append(f"- `{model['label']}`: `{model['checkpoint_resolved']}`")
    lines.extend(
        [
            "",
            "## Stitched comparisons",
            "",
            "- [Original and all models](comparisons/overview_original_and_all_models.png)",
        ]
    )
    for model in models:
        lines.append(
            f"- [Original vs {model['label']}](comparisons/{model['label']}/overview_original_vs_{model['label']}.png)"
        )
    lines.extend(
        [
            "",
            "Per-frame comparisons are in the corresponding subdirectories. Raw model outputs and logs are under `results/`.",
            "",
        ]
    )
    (bundle / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    config = json.loads(base64.urlsafe_b64decode(args.config_b64.encode("ascii")))
    work_dir = Path(config["work_dir"]).resolve()
    if not str(work_dir).startswith("/tmp/remote-attention-heatmap."):
        raise RuntimeError(f"unexpected work directory: {work_dir}")
    bundle = work_dir / "bundle"
    results_root = bundle / "results"
    inputs_out = bundle / "inputs"
    results_root.mkdir(parents=True)
    inputs_out.mkdir(parents=True)

    image_dir, image_candidates = resolve_remote_path(config["image_dir"], kind="dir")
    images = sorted(
        path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images:
        raise ValueError(f"image directory has no supported top-level images: {image_dir}")
    for image in images:
        shutil.copy2(image, inputs_out / image.name)

    heatmap_script = work_dir / "attention_heatmap.py"
    compositor = work_dir / "compose_heatmap_comparisons.py"
    device = choose_device(config["device"])
    model_records: list[dict[str, object]] = []

    for model in config["models"]:
        checkpoint, checkpoint_candidates = resolve_remote_path(model["checkpoint"], kind="file")
        repo = infer_repo(checkpoint)
        label = model["label"]
        output_dir = results_root / label
        output_dir.mkdir()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
        env["MPLCONFIGDIR"] = str(work_dir / f"matplotlib_{label}")
        command = [
            sys.executable,
            str(heatmap_script),
            "--checkpoint",
            str(checkpoint),
            "--encoder-index",
            str(config["encoder_index"]),
            "--image-dir",
            str(image_dir),
            "--output-dir",
            str(output_dir),
            "--device",
            device,
        ]
        log_path = results_root / f"{label}.log"
        tee_process(command, cwd=repo, env=env, log_path=log_path)
        raw_count = len(list(output_dir.rglob("*__attention.npy")))
        heatmap_count = len(list(output_dir.rglob("*__attention_heatmap.png")))
        overlay_count = len(list(output_dir.rglob("*__attention_overlay.png")))
        expected = len(images)
        if (raw_count, heatmap_count, overlay_count) != (expected, expected, expected):
            raise RuntimeError(
                f"incomplete outputs for {label}: raw={raw_count}, heatmap={heatmap_count}, "
                f"overlay={overlay_count}, expected={expected}"
            )
        stat = checkpoint.stat()
        model_records.append(
            {
                "label": label,
                "checkpoint_original": model["checkpoint"],
                "checkpoint_resolved": str(checkpoint),
                "checkpoint_candidates": checkpoint_candidates,
                "checkpoint_size": stat.st_size,
                "checkpoint_mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "remote_repo": str(repo),
                "raw_count": raw_count,
                "heatmap_count": heatmap_count,
                "overlay_count": overlay_count,
                "log": f"results/{label}.log",
            }
        )

    subprocess.run(
        [
            sys.executable,
            str(compositor),
            "--inputs",
            str(inputs_out),
            "--results",
            str(results_root),
            "--output",
            str(bundle / "comparisons"),
            "--labels-json",
            json.dumps([record["label"] for record in model_records]),
        ],
        check=True,
    )

    manifest: dict[str, object] = {
        "created_at": datetime.now().astimezone().isoformat(),
        "host": config["host"],
        "device": device,
        "encoder_index": config["encoder_index"],
        "image_dir_original": config["image_dir"],
        "image_dir_resolved": str(image_dir),
        "image_dir_candidates": image_candidates,
        "image_count": len(images),
        "images": [image.name for image in images],
        "heatmap_script_sha256": sha256(heatmap_script),
        "models": model_records,
    }
    (bundle / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(bundle, manifest)
    print(f"[done] remote bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

