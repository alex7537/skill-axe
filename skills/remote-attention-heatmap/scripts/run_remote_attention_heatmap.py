#!/usr/bin/env python3
"""Orchestrate remote PSI checkpoint attention heatmaps and pull a result bundle."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


SKILL_DIR = Path(__file__).resolve().parent.parent
REMOTE_WORKER = SKILL_DIR / "scripts" / "remote_heatmap_worker.py"
COMPOSITOR = SKILL_DIR / "scripts" / "compose_heatmap_comparisons.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local repository's heatmap script on remote checkpoints over SSH."
    )
    parser.add_argument("--host", required=True, help="SSH host or configured alias.")
    parser.add_argument(
        "--checkpoint",
        action="append",
        required=True,
        help="Remote checkpoint path, optionally LABEL=PATH. Repeat for multiple models.",
    )
    parser.add_argument("--image-dir", required=True, help="Remote directory containing immediate image files.")
    parser.add_argument("--local-repo", default="", help="Local PSI repository; defaults to discovery from cwd.")
    parser.add_argument("--local-output", default="", help="New local output directory; must not already exist.")
    parser.add_argument("--encoder-index", type=int, default=0)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--remote-python", default="", help="Remote Python executable override.")
    parser.add_argument("--keep-remote", action="store_true", help="Keep the remote temporary directory.")
    return parser.parse_args()


def run(command: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=capture,
    )


def ssh_command(host: str, argv: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    remote_command = shlex.join(argv)
    return run(["ssh", "-o", "BatchMode=yes", host, remote_command], capture=capture, check=check)


def discover_local_repo(raw: str) -> Path:
    candidates = [Path(raw).expanduser()] if raw else [Path.cwd(), *Path.cwd().parents]
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "visualization" / "attention_heatmap.py").is_file():
            return candidate
    raise FileNotFoundError(
        "could not find visualization/attention_heatmap.py; pass --local-repo from the PSI repository"
    )


def sanitize_label(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return clean or "model"


def parse_models(values: list[str]) -> list[dict[str, str]]:
    models: list[dict[str, str]] = []
    used: dict[str, int] = {}
    for value in values:
        if "=" in value and "/" not in value.split("=", 1)[0]:
            raw_label, path = value.split("=", 1)
            label = sanitize_label(raw_label)
        else:
            path = value
            checkpoint = Path(path)
            label = sanitize_label(checkpoint.parents[1].name if len(checkpoint.parents) > 1 else checkpoint.stem)
        count = used.get(label, 0) + 1
        used[label] = count
        if count > 1:
            label = f"{label}_{count}"
        models.append({"label": label, "checkpoint": path})
    return models


def discover_remote_python(host: str, override: str) -> str:
    candidates = [override] if override else [
        "/opt/conda/envs/psipolicy-env/bin/python",
        "/opt/conda/bin/python",
        "python3",
    ]
    probe = (
        "import hydra,dill,timm,matplotlib,PIL,torch; "
        "print('ok', torch.__version__, torch.cuda.is_available())"
    )
    failures: list[str] = []
    for candidate in candidates:
        result = ssh_command(host, [candidate, "-c", probe], capture=True, check=False)
        if result.returncode == 0:
            print(f"[remote] python: {candidate} ({result.stdout.strip()})")
            return candidate
        failures.append(f"{candidate}: {result.stderr.strip() or result.stdout.strip()}")
    raise RuntimeError("no usable remote Python environment found:\n" + "\n".join(failures))


def default_output(repo: Path, image_dir: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_name = sanitize_label(Path(image_dir.rstrip("/")).name)
    return repo / "data" / "attention_heatmaps" / f"remote_{timestamp}_{input_name}"


def validate_host(host: str) -> None:
    if not host or host.startswith("-") or any(char.isspace() for char in host):
        raise ValueError(f"invalid SSH host: {host!r}")
    if shutil.which("ssh") is None or shutil.which("scp") is None:
        raise RuntimeError("ssh and scp are required")


def main() -> int:
    args = parse_args()
    validate_host(args.host)
    local_repo = discover_local_repo(args.local_repo)
    heatmap_script = local_repo / "visualization" / "attention_heatmap.py"
    models = parse_models(args.checkpoint)
    local_output = Path(args.local_output).expanduser().resolve() if args.local_output else default_output(local_repo, args.image_dir)
    if local_output.exists():
        raise FileExistsError(f"local output already exists: {local_output}")

    print(f"[local] repository: {local_repo}")
    print(f"[local] output: {local_output}")
    remote_python = discover_remote_python(args.host, args.remote_python)
    mktemp = ssh_command(
        args.host,
        ["mktemp", "-d", "/tmp/remote-attention-heatmap.XXXXXX"],
        capture=True,
    )
    remote_dir = mktemp.stdout.strip()
    if not re.fullmatch(r"/tmp/remote-attention-heatmap\.[A-Za-z0-9]+", remote_dir):
        raise RuntimeError(f"refusing unexpected remote temporary path: {remote_dir!r}")
    print(f"[remote] temporary directory: {remote_dir}")

    success = False
    try:
        run(
            [
                "scp",
                "-q",
                str(heatmap_script),
                str(REMOTE_WORKER),
                str(COMPOSITOR),
                f"{args.host}:{remote_dir}/",
            ]
        )
        config = {
            "host": args.host,
            "work_dir": remote_dir,
            "image_dir": args.image_dir,
            "models": models,
            "encoder_index": args.encoder_index,
            "device": args.device,
        }
        encoded = base64.urlsafe_b64encode(json.dumps(config).encode("utf-8")).decode("ascii")
        ssh_command(
            args.host,
            [remote_python, f"{remote_dir}/remote_heatmap_worker.py", "--config-b64", encoded],
        )

        local_output.mkdir(parents=True)
        run(["scp", "-qr", f"{args.host}:{remote_dir}/bundle/.", str(local_output)])
        success = True
    finally:
        if success and not args.keep_remote:
            ssh_command(args.host, ["rm", "-rf", "--", remote_dir], check=True)
            print(f"[remote] removed temporary directory: {remote_dir}")
        elif not success:
            print(f"[remote] run failed; retained for debugging: {remote_dir}", file=sys.stderr)

    print(f"[done] bundle: {local_output}")
    print(f"[done] report: {local_output / 'README.md'}")
    print(f"[done] all-model overview: {local_output / 'comparisons' / 'overview_original_and_all_models.png'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
