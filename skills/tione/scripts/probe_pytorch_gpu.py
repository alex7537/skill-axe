#!/usr/bin/env python3
"""Read-only CUDA/PyTorch compatibility probe with real BF16 kernels."""

from __future__ import annotations

import argparse
import importlib
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--expected-capability",
        help="Expected CUDA capability such as 12.0; omit to accept the device value.",
    )
    parser.add_argument("--require-package", action="append", default=[])
    parser.add_argument("--skip-kernels", action="store_true")
    args = parser.parse_args()

    result: dict[str, object] = {
        "python": sys.version.split()[0],
        "packages": {},
        "errors": [],
    }
    try:
        import torch
    except Exception as exc:
        result["errors"].append(f"torch import failed: {type(exc).__name__}: {exc}")
        print(json.dumps(result, indent=2))
        return 1

    result.update({
        "torch": torch.__version__,
        "torch_file": torch.__file__,
        "torch_cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
    })
    if not torch.cuda.is_available():
        result["errors"].append("torch.cuda.is_available() is false")
    else:
        capability = torch.cuda.get_device_capability(0)
        arch = torch.cuda.get_arch_list()
        result.update({
            "device": torch.cuda.get_device_name(0),
            "capability": list(capability),
            "arch_list": arch,
            "bf16_supported_reported": torch.cuda.is_bf16_supported(),
            "cudnn": torch.backends.cudnn.version(),
        })
        if args.expected_capability:
            expected = tuple(int(item) for item in args.expected_capability.split("."))
            if capability != expected:
                result["errors"].append(
                    f"capability mismatch: expected={expected} actual={capability}"
                )
            wanted_arch = f"sm_{expected[0]}{expected[1]}"
            wanted_ptx = f"compute_{expected[0]}{expected[1]}"
            if wanted_arch not in arch and wanted_ptx not in arch:
                result["errors"].append(
                    f"Torch has neither {wanted_arch} nor {wanted_ptx}"
                )
        if not args.skip_kernels:
            try:
                torch.cuda.reset_peak_memory_stats()
                left = torch.randn((256, 256), device="cuda", dtype=torch.bfloat16)
                right = torch.randn((256, 256), device="cuda", dtype=torch.bfloat16)
                product = left @ right
                conv = torch.nn.Conv2d(
                    3, 16, 3, padding=1, device="cuda", dtype=torch.bfloat16
                )
                convolved = conv(torch.randn(
                    (2, 3, 32, 32), device="cuda", dtype=torch.bfloat16
                ))
                torch.cuda.synchronize()
                result["kernels"] = {
                    "bf16_matmul_finite": bool(torch.isfinite(product).all()),
                    "bf16_conv_finite": bool(torch.isfinite(convolved).all()),
                    "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
                }
                if not all(result["kernels"][key] for key in (
                    "bf16_matmul_finite", "bf16_conv_finite"
                )):
                    result["errors"].append("a BF16 kernel returned non-finite output")
            except Exception as exc:
                result["errors"].append(
                    f"CUDA kernel probe failed: {type(exc).__name__}: {exc}"
                )

    for name in args.require_package:
        try:
            module = importlib.import_module(name)
            result["packages"][name] = {
                "version": getattr(module, "__version__", "unknown"),
                "file": getattr(module, "__file__", None),
            }
        except Exception as exc:
            result["packages"][name] = {
                "error": f"{type(exc).__name__}: {exc}"
            }
            result["errors"].append(f"required package import failed: {name}")

    result["status"] = "pass" if not result["errors"] else "fail"
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
