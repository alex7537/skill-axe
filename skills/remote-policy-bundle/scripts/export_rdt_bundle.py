#!/usr/bin/env python3
"""Export a completed A2D RDT-170M run into a portable inference bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone

import torch
import yaml


RDT_SOURCE_COMMIT = "cd79363a1387e8f81c7724d070ef7e45fd23150f"
RDT_BASE_REVISION = "8aa386cac3bbfd9540676c75b3d767cc7f88a10a"
A2D_INDICES = [0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 45]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def candidate(run: Path, name: str) -> tuple[Path, str, int, str]:
    best_path = run / "best_sample_metrics.json"
    best = json.loads(best_path.read_text(encoding="utf-8")) if best_path.is_file() else {}
    if name == "best-raw":
        return (
            run / "best_raw",
            "raw",
            int(best["global_step"]),
            str(best["selection"]),
        )
    if name == "best-ema-at-raw-best":
        return (
            run / "best_ema_at_raw_best",
            "ema",
            int(best["global_step"]),
            "ema_at_raw_overall_avg_sample_mse_best",
        )
    if name == "latest-raw":
        checkpoints = [
            int(match.group(1))
            for path in run.glob("checkpoint-*")
            if (match := re.fullmatch(r"checkpoint-(\d+)", path.name))
        ]
        if not checkpoints:
            raise ValueError("run has no numbered checkpoints")
        return run, "raw", max(checkpoints), "latest"
    raise ValueError(f"unsupported RDT candidate: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--candidate", choices=(
        "best-raw", "best-ema-at-raw-best", "latest-raw"
    ), required=True)
    parser.add_argument("--rdt-source", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--siglip-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    run = args.run_dir.resolve()
    source = args.rdt_source.resolve()
    data = args.data_dir.resolve()
    siglip = args.siglip_dir.resolve()
    output = args.out.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite: {output}")
    status = json.loads((run / "status.json").read_text(encoding="utf-8"))
    if status.get("status") != "completed" or int(status.get("exit_code", -1)) != 0:
        raise ValueError(f"RDT run is not completed successfully: {status}")

    model_dir, variant, step, selection = candidate(run, args.candidate)
    weights = model_dir / "pytorch_model.bin"
    model_config = model_dir / "config.json"
    if not weights.is_file() or not model_config.is_file():
        raise FileNotFoundError(f"incomplete model directory: {model_dir}")
    state = torch.load(weights, map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or not state or not all(
        isinstance(key, str) and torch.is_tensor(value) for key, value in state.items()
    ):
        raise ValueError("pytorch_model.bin is not a plain tensor state dict")

    siglip_weights = siglip / "model.safetensors"
    if not siglip_weights.is_file():
        raise FileNotFoundError(f"SigLIP weights missing: {siglip_weights}")
    required_data = {
        "norm_stats.json": data / "rdt_dataset_stat.json",
        "action_stats.json": data / "rdt_action_stat.json",
        "data_split.json": data / "split_manifest.json",
        "data_manifest.json": data / "rdt_manifest.json",
        "empty_lang_embed.pt": data / "language" / "box.pt",
    }
    for path in required_data.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    runtime_files = [
        "LICENSE",
        "models/hub_mixin.py",
        "models/rdt_runner.py",
        "models/rdt/model.py",
        "models/rdt/blocks.py",
    ]
    for relative in runtime_files:
        if not (source / relative).is_file():
            raise FileNotFoundError(source / relative)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rdt-bundle-", dir=output.parent) as tmp:
        root = Path(tmp) / f"rdt170m-a2d-{args.candidate}"
        root.mkdir()
        shutil.copy2(weights, root / "ckpt.pt")
        for name, path in required_data.items():
            shutil.copy2(path, root / name)

        with tarfile.open(root / "rdt_runtime.tgz", "w:gz") as archive:
            for relative in runtime_files:
                archive.add(source / relative, arcname=f"rdt_runtime/{relative}")

        model = json.loads(model_config.read_text(encoding="utf-8"))
        deployment_config = {
            "schema_version": 4,
            "policy": {
                "type": "rdt_170m_a2d",
                "weights_variant": variant,
                "normalization": "identity_raw_joint_radians",
            },
            "observation": {
                "history_steps": 2,
                "cameras": ["rgb_head", "rgb_right_hand", "missing_background"],
                "image_size": 384,
                "siglip_tokens_per_image": 729,
                "image_condition_tokens": 4374,
                "proprio_dim": 13,
            },
            "action": {
                "chunk_size": 64,
                "unified_dim": 128,
                "active_dim": 13,
                "active_indices": A2D_INDICES,
                "semantics": "arm_executed_hand_commanded_joint_position",
            },
            "sampling": {
                "train_timesteps": 1000,
                "inference_steps": 5,
                "solver": "DPMSolverMultistepScheduler",
                "prediction_type": "sample",
            },
            "model": model,
        }
        (root / "config.yaml").write_text(
            yaml.safe_dump(deployment_config, sort_keys=False), encoding="utf-8"
        )
        write_json(root / "a2d_mapping.json", {
            "state_indices": A2D_INDICES,
            "action_indices": A2D_INDICES,
            "arm_indices": list(range(0, 7)),
            "hand_indices": [10, 11, 12, 13, 14, 45],
            "action_offset_steps": 1,
            "sixth_hand_joint_note": "slot 45 is project-reserved and has no official pretrained semantic",
        })
        (root / "requirements.txt").write_text(
            "torch>=2.7,<3\n"
            "torchvision>=0.22,<1\n"
            "transformers==4.41.0\n"
            "diffusers==0.27.2\n"
            "timm==1.0.3\n"
            "huggingface_hub==0.23.2\n"
            "safetensors\n"
            "numpy\n"
            "opencv-python-headless\n"
            "PyYAML\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            f"A2D RDT-170M {args.candidate} bundle using {variant} weights at step {step}.\n\n"
            "This archive contains the complete RDT action-core state dict and pinned runtime source. "
            "It requires the external frozen SigLIP artifact declared in manifest.json. "
            "Language conditioning is disabled through the bundled official empty embedding. "
            "An online Isaac rollout adapter is not included; bundle validity is not rollout readiness.\n",
            encoding="utf-8",
        )

        files = {}
        for path in sorted(root.iterdir()):
            if path.name == "manifest.json" or not path.is_file():
                continue
            files[path.name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        log_text = (run / "train.log").read_text(encoding="utf-8", errors="ignore")
        urls = re.findall(r"https://wandb\.ai/[^\s]+/runs/[a-z0-9]+", log_text)
        manifest = {
            "schema_version": 4,
            "policy_type": "rdt_170m_a2d",
            "weights_variant": variant,
            "checkpoint_selection": selection,
            "source_checkpoint_selection": selection,
            "train_step": step,
            "train_epoch": None,
            "source_run": str(run),
            "source_checkpoint": str(weights),
            "source_checkpoint_sha256": sha256_file(weights),
            "source_run_status": status,
            "best_sample_metrics": (
                json.loads((run / "best_sample_metrics.json").read_text(encoding="utf-8"))
                if (run / "best_sample_metrics.json").is_file() else None
            ),
            "model_state": {
                "tensor_count": len(state),
                "numel": sum(value.numel() for value in state.values()),
                "tensor_bytes": sum(value.numel() * value.element_size() for value in state.values()),
            },
            "source_identity": {
                "rdt_source_commit": RDT_SOURCE_COMMIT,
                "rdt_base_revision": RDT_BASE_REVISION,
            },
            "data_provenance": json.loads(
                (data / "rdt_manifest.json").read_text(encoding="utf-8")
            ),
            "external_artifacts": {
                "siglip_so400m_patch14_384": {
                    "revision": siglip.name,
                    "model_sha256": sha256_file(siglip_weights),
                    "model_bytes": siglip_weights.stat().st_size,
                }
            },
            "wandb_run": urls[-1] if urls else None,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": files,
        }
        manifest["data_version"] = manifest["data_provenance"].get("data_version")
        write_json(root / "manifest.json", manifest)
        with tarfile.open(output, "w:gz") as archive:
            archive.add(root, arcname=root.name)

    print(json.dumps({
        "status": "RDT_BUNDLE_EXPORTED",
        "archive": str(output),
        "archive_sha256": sha256_file(output),
        "candidate": args.candidate,
        "weights_variant": variant,
        "train_step": step,
        "checkpoint_selection": selection,
    }, indent=2))


if __name__ == "__main__":
    main()
