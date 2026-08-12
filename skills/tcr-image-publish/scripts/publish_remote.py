#!/usr/bin/env python3
"""Plan or execute docker load, tag, push, and manifest verification over SSH."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time


DIGEST_RE = re.compile(r"digest:\s*(sha256:[0-9a-f]{64})", re.IGNORECASE)


def remote_cmd(target: str, argv: list[str], *, stream: bool = False) -> tuple[int, str]:
    command = " ".join(shlex.quote(part) for part in argv)
    if not stream:
        result = subprocess.run(
            ["ssh", target, command],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return result.returncode, result.stdout

    process = subprocess.Popen(
        ["ssh", target, command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        output.append(line)
    return process.wait(), "".join(output)


def valid_destination(reference: str) -> bool:
    if "/" not in reference or reference.startswith(("http://", "https://")):
        return False
    registry = reference.split("/", 1)[0]
    if "." not in registry and ":" not in registry and registry != "localhost":
        return False
    last = reference.rsplit("/", 1)[-1]
    return ":" in last or "@sha256:" in last


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ssh_target", help="Verified SSH alias or user@host")
    parser.add_argument("remote_archive", help="Absolute remote image archive path")
    parser.add_argument("source_image", help="Image reference produced by docker load")
    parser.add_argument("destination", help="Fully qualified TCR image reference with tag")
    parser.add_argument("--skip-load", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Publish the exact destination")
    return parser.parse_args()


def fail(step: str, output: str, code: int) -> int:
    print(output.rstrip(), file=sys.stderr)
    lower = output.lower()
    if "insufficient_scope" in lower or "push access denied" in lower or "denied" in lower:
        print("Classification: effective repository push scope is missing or the path is wrong.", file=sys.stderr)
    elif "broken pipe" in lower or "connection reset" in lower:
        print("Classification: upload path/connection failed; prefer a same-region relay or multi-layer rebuild.", file=sys.stderr)
    print(f"Failed step: {step} (exit {code})", file=sys.stderr)
    return code or 1


def main() -> int:
    args = parse_args()
    if not args.remote_archive.startswith("/"):
        print("remote_archive must be absolute", file=sys.stderr)
        return 2
    if not valid_destination(args.destination):
        print("destination must be a fully qualified registry/repository:tag reference", file=sys.stderr)
        return 2

    print(f"SSH target: {args.ssh_target}")
    print(f"Remote archive: {args.remote_archive}")
    print(f"Source image: {args.source_image}")
    print(f"Destination: {args.destination}")
    print(f"Load archive: {'no' if args.skip_load else 'yes'}")
    if not args.execute:
        print("PLAN ONLY: rerun with --execute after authorizing this exact registry write.")
        return 0

    code, output = remote_cmd(args.ssh_target, ["docker", "version", "--format", "{{.Server.Version}}"])
    if code != 0:
        return fail("docker preflight", output, code)

    if not args.skip_load:
        preflight_script = (
            'set -eu; test -r "$1"; '
            'docker_root=$(docker info --format "{{.DockerRootDir}}"); '
            'printf "Archive and Docker filesystem capacity (KiB):\\n"; '
            'df -Pk -- "$1" "$docker_root"'
        )
        code, output = remote_cmd(
            args.ssh_target,
            ["sh", "-lc", preflight_script, "tcr-publish-preflight", args.remote_archive],
        )
        if code != 0:
            return fail("archive and Docker storage preflight", output, code)
        print(output.rstrip())

    if not args.skip_load:
        code, output = remote_cmd(
            args.ssh_target,
            ["docker", "load", "--input", args.remote_archive],
            stream=True,
        )
        if code != 0:
            return fail("docker load", output, code)

    code, output = remote_cmd(
        args.ssh_target,
        ["docker", "image", "inspect", "--format", "{{.Os}}/{{.Architecture}}", args.source_image],
    )
    if code != 0:
        return fail("source image inspect", output, code)
    platform = output.strip().splitlines()[-1]
    print(f"Source platform: {platform}")

    code, output = remote_cmd(args.ssh_target, ["docker", "tag", args.source_image, args.destination])
    if code != 0:
        return fail("docker tag", output, code)

    started = time.monotonic()
    code, push_output = remote_cmd(args.ssh_target, ["docker", "push", args.destination], stream=True)
    elapsed = time.monotonic() - started
    if code != 0:
        return fail("docker push", push_output, code)
    matches = DIGEST_RE.findall(push_output)
    if not matches:
        print("Push returned success but no manifest digest was found; refusing to report completion.", file=sys.stderr)
        return 7
    digest = matches[-1].lower()

    code, verify_output = remote_cmd(
        args.ssh_target,
        ["docker", "manifest", "inspect", args.destination],
    )
    if code != 0:
        return fail("independent manifest readback", verify_output, code)

    print("Publication verified")
    print(f"Destination: {args.destination}")
    print(f"Platform: {platform}")
    print(f"Manifest digest: {digest}")
    print(f"Push elapsed: {elapsed:.1f} seconds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
