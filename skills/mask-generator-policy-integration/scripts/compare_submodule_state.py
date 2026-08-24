#!/usr/bin/env python3
"""Compare a checkpoint submodule with standalone weights tensor by tensor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path, help="Policy or first checkpoint")
    parser.add_argument("right", type=Path, help="Standalone or second checkpoint")
    parser.add_argument("--left-prefix", default="", help="Prefix to select and strip")
    parser.add_argument("--right-prefix", default="", help="Prefix to select and strip")
    parser.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="Absolute tolerance; default requires bitwise-equivalent values",
    )
    return parser.parse_args()


def load_state(path: Path) -> dict[str, torch.Tensor]:
    if path.suffix == ".safetensors":
        try:
            from safetensors.torch import load_file
        except ModuleNotFoundError as exc:
            raise SystemExit("safetensors is required to read .safetensors files") from exc
        raw = load_file(str(path), device="cpu")
    else:
        raw = torch.load(path, map_location="cpu", weights_only=False)

    if isinstance(raw, Mapping):
        for key in ("state_dict", "model_state_dict", "model"):
            nested = raw.get(key)
            if isinstance(nested, Mapping) and nested:
                raw = nested
                break
    if not isinstance(raw, Mapping):
        raise TypeError(f"{path} does not contain a state dict")

    result: dict[str, torch.Tensor] = {}
    for key, value in raw.items():
        if isinstance(value, torch.Tensor):
            result[str(key)] = value.detach().cpu()
    if not result:
        raise ValueError(f"{path} contains no tensors")
    return result


def select_prefix(
    state: Mapping[str, torch.Tensor], prefix: str
) -> dict[str, torch.Tensor]:
    if not prefix:
        return dict(state)
    selected = {
        key[len(prefix) :]: value
        for key, value in state.items()
        if key.startswith(prefix)
    }
    if not selected:
        examples = ", ".join(list(state)[:5])
        raise ValueError(f"prefix {prefix!r} matched no keys; examples: {examples}")
    return selected


def main() -> int:
    args = parse_args()
    left = select_prefix(load_state(args.left), args.left_prefix)
    right = select_prefix(load_state(args.right), args.right_prefix)

    left_keys = set(left)
    right_keys = set(right)
    missing_left = sorted(right_keys - left_keys)
    missing_right = sorted(left_keys - right_keys)
    mismatched: list[tuple[str, str]] = []
    max_abs_diff = 0.0

    for key in sorted(left_keys & right_keys):
        a, b = left[key], right[key]
        if a.shape != b.shape:
            mismatched.append((key, f"shape {tuple(a.shape)} != {tuple(b.shape)}"))
            continue
        dtype_note = f"dtype {a.dtype} != {b.dtype}; " if a.dtype != b.dtype else ""
        if a.numel() == 0:
            diff = 0.0
        elif a.is_floating_point() or b.is_floating_point():
            diff = float((a.to(torch.float64) - b.to(torch.float64)).abs().max())
        else:
            diff = 0.0 if torch.equal(a, b) else float("inf")
        max_abs_diff = max(max_abs_diff, diff)
        if diff > args.atol or dtype_note:
            mismatched.append((key, f"{dtype_note}max_abs_diff={diff:g}"))

    print(f"left_tensors={len(left)} right_tensors={len(right)}")
    print(f"common={len(left_keys & right_keys)} max_abs_diff={max_abs_diff:g}")
    if missing_left:
        print(f"missing_in_left={len(missing_left)} examples={missing_left[:5]}")
    if missing_right:
        print(f"missing_in_right={len(missing_right)} examples={missing_right[:5]}")
    if mismatched:
        print(f"mismatched={len(mismatched)}")
        for key, reason in mismatched[:20]:
            print(f"  {key}: {reason}")

    ok = not missing_left and not missing_right and not mismatched
    print("MATCH" if ok else "DIFFERENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
