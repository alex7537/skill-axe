---
name: tcr-image-publish
description: Publish local Docker/OCI image archives or existing Docker images to Tencent Cloud TCR safely, optionally relaying large images through a nearby TI-ONE development machine. Use when the user asks to 上传镜像, 推送镜像到 TCR, docker load/tag/push, move a .tar image through a development machine, diagnose push access denied, insufficient_scope, Waiting, broken pipe, expiring Registry tokens, oversized or squashed layers, verify SHA256 transfer integrity, or confirm the remote manifest digest.
---

# TCR Image Publish

Publish an image without exposing credentials or mistaking a successful byte transfer for a completed registry publication. Treat this as an infrastructure operation with explicit write gates.

## Defaults

Read `config.json` for this user's non-secret registry and relay defaults. If it is absent after restoring the exported skill, copy `config.example.json` to `config.json` and fill machine-local values. Never store passwords, tokens, Docker `auth`, or temporary login URLs in the skill.

## Workflow

1. Identify the source archive or local image, exact destination reference, expected platform, archive size, and whether the image is squashed into a very large layer.
2. Choose the route:
   - Push directly only for a reasonably sized image on a stable, fast path.
   - For a large/squashed image or a prior `Waiting`/`broken pipe` failure, relay through a Linux machine close to the TCR region. Prefer a Shanghai TI-ONE/CVM machine for `ap-shanghai`; the GPU is irrelevant to publishing.
3. Resolve and verify the relay endpoint using the installed `tione` skill or a confirmed SSH alias. Check Docker availability and free space. Budget at least archive size plus unpacked Docker storage, normally more than twice the archive size.
4. Transfer and verify the archive. Preview first, then execute only after the user authorizes remote upload:

   ```bash
   python3 scripts/transfer_archive.py IMAGE.tar SSH_TARGET REMOTE_DIR
   python3 scripts/transfer_archive.py IMAGE.tar SSH_TARGET REMOTE_DIR --execute
   ```

   The script prefers resumable `rsync` and falls back to SFTP `reput`; it compares local and remote SHA256 before success.
5. Authenticate interactively on the machine that will push:

   ```bash
   ssh -t SSH_TARGET 'docker login REGISTRY --username USERNAME'
   ```

   Enter the password only at the hidden prompt. Never use `--password`, echo a password into logs, copy credentials from a chat transcript, or display Docker credential-helper output. A username ending in `rw` does not prove the issued token contains `push` scope.
6. Preview the remote load/tag/push plan. Execute only after the user explicitly authorizes publishing the exact destination reference:

   ```bash
   python3 scripts/publish_remote.py SSH_TARGET REMOTE_ARCHIVE SOURCE_IMAGE DESTINATION
   python3 scripts/publish_remote.py SSH_TARGET REMOTE_ARCHIVE SOURCE_IMAGE DESTINATION --execute
   ```

   Use `--skip-load` only after verifying the source image already exists remotely.
7. Keep one push process. Monitor its existing session and network activity instead of starting duplicate pushes. On completion, require both a push digest and an independent readable-manifest check.
8. Report the destination reference, platform, transfer SHA256, manifest digest, elapsed time, and remaining remote artifacts. Delete archives, images, or credentials only with separate explicit approval.

## Failure Classification

- `denied`, `push access denied`, `insufficient_scope`: repository path or effective service-account scope is wrong; relogging does not create missing permissions.
- Long `Waiting` with a giant single layer: Docker may be preparing/compressing or transmitting without granular CLI progress. Inspect the existing process and network bytes before declaring a stall.
- `broken pipe`, upload ends without manifest, or a retry starts from zero: the route is unsuitable for the layer size or token/connection lifetime. Move the push closer to TCR or rebuild as multiple layers; do not loop the same failed push.
- Successful archive upload but different SHA256: do not run `docker load`; resume or retransmit until hashes match.
- Successful `docker push` but unreadable manifest: publication is incomplete; do not report success.

## Gotchas

- Docker login persistence and Registry Bearer-token lifetime are different. A persistent service password can still mint short-lived upload tokens.
- A `.tar` archive, a loaded local image, a pushed blob, and a committed manifest are four distinct states.
- A squashed 18+ GB layer removes Docker's normal multi-layer retry advantage.
- TI-ONE custom-image execution belongs to the `tione` skill; this skill ends after verified publication.
- Read `references/large-layer-incident.md` only when diagnosing a large single-layer upload.
