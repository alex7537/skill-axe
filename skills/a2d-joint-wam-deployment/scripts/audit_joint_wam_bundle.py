#!/usr/bin/env python3
"""Audit a Joint WAM archive and optionally its external Wan runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path


REQUIRED = {
    "README.md",
    "ckpt.pt",
    "config.yaml",
    "data_split.json",
    "manifest.json",
    "norm_stats.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_member(
    archive: tarfile.TarFile,
    members: dict[str, tarfile.TarInfo],
    name: str,
) -> bytes:
    stream = archive.extractfile(members[name])
    if stream is None:
        raise ValueError(f"could not read {name}")
    return stream.read()


def audit(
    bundle: Path,
    *,
    bundle_only: bool,
    wan_vae: Path | None,
    wan_runtime_repo: Path | None,
) -> dict:
    with tarfile.open(bundle, "r:gz") as archive:
        members = {
            Path(item.name).name: item
            for item in archive.getmembers()
            if item.isfile()
        }
        missing = sorted(REQUIRED - set(members))
        if missing:
            raise ValueError(f"missing bundle members: {missing}")
        manifest = json.loads(read_member(archive, members, "manifest.json"))
        if manifest.get("policy_type") != "joint_latent_wam":
            raise ValueError("policy_type is not joint_latent_wam")
        if int(manifest.get("schema_version", -1)) != 3:
            raise ValueError("Joint WAM manifest schema_version must be 3")
        for name, metadata in manifest.get("files", {}).items():
            if name not in members:
                raise ValueError(f"manifest references missing member: {name}")
            payload = read_member(archive, members, name)
            if hashlib.sha256(payload).hexdigest() != metadata.get("sha256"):
                raise ValueError(f"internal SHA256 mismatch: {name}")
            if len(payload) != int(metadata.get("bytes", -1)):
                raise ValueError(f"internal byte-count mismatch: {name}")

    expected_vae_sha = str(
        manifest.get("external_artifacts", {}).get("wan_vae", {}).get("sha256", "")
    )
    if len(expected_vae_sha) != 64:
        raise ValueError("manifest has no valid external Wan VAE SHA256")
    result = {
        "bundle_valid": True,
        "bundle": str(bundle.resolve()),
        "bundle_sha256": sha256_file(bundle),
        "weights_variant": manifest.get("weights_variant"),
        "checkpoint_selection": manifest.get("source_checkpoint_selection"),
        "train_epoch": manifest.get("train_epoch"),
        "train_step": manifest.get("train_step"),
        "expected_wan_vae_sha256": expected_vae_sha,
        "runtime_valid": False,
        "ready_for_model_load": False,
    }
    if bundle_only:
        result["status"] = "bundle-valid-external-unchecked"
        return result
    if wan_vae is None or wan_runtime_repo is None:
        raise ValueError("external audit requires --wan-vae and --wan-runtime-repo")
    if not wan_vae.is_file():
        raise FileNotFoundError(f"Wan VAE not found: {wan_vae}")
    actual_vae_sha = sha256_file(wan_vae)
    if actual_vae_sha != expected_vae_sha:
        raise ValueError(
            f"Wan VAE SHA256 mismatch: expected={expected_vae_sha} actual={actual_vae_sha}"
        )
    module = wan_runtime_repo / "wan" / "modules" / "vae2_2.py"
    if not module.is_file():
        raise FileNotFoundError(f"Wan runtime module not found: {module}")
    result.update(
        {
            "runtime_valid": True,
            "ready_for_model_load": True,
            "wan_vae": str(wan_vae.resolve()),
            "wan_vae_sha256": actual_vae_sha,
            "wan_runtime_repo": str(wan_runtime_repo.resolve()),
            "status": "bundle-and-runtime-valid",
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-only", action="store_true")
    parser.add_argument("--wan-vae", type=Path)
    parser.add_argument("--wan-runtime-repo", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(
        args.bundle.expanduser().resolve(),
        bundle_only=args.bundle_only,
        wan_vae=args.wan_vae.expanduser().resolve() if args.wan_vae else None,
        wan_runtime_repo=(
            args.wan_runtime_repo.expanduser().resolve()
            if args.wan_runtime_repo
            else None
        ),
    ), indent=2))


if __name__ == "__main__":
    main()
