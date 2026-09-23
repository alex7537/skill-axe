# TI-ONE development workspace and shared storage

## Decision to communicate first

Recommend a verified persistent directory as the primary editable source tree when the instance stop dialog says non-mounted paths are cleared. For that configuration, `/share_data/<user>/src/<project>` is the default; `/workspace/<user>` is for disposable environments, build products, caches and temporary run copies. Do not recommend ephemeral storage as the main development directory merely because backup is possible: uncommitted edits and unsaved experiment configuration are normal daily work.

A temporary working copy under `/workspace` is an optional performance optimization only when a relevant bottleneck has been measured and the user has a practical, verified sync/recovery workflow. Git alone does not preserve uncommitted or untracked work. Check capacity and storage backing before promising a benefit.
Keep datasets, pretrained weights, checkpoints, experiment outputs and recovery material on verified persistent storage. Source belongs in version control with an authorized backup; environment lockfiles, image identity and launch configurations must allow reconstruction. Git commits alone on the same ephemeral disk are not a backup. Do not automatically push company code or migrate files from an audit request.

Shared storage is not categorically unsuitable for source. Small projects can work acceptably there, and avoiding loss may matter more than modest latency. Prioritize broken environment dependencies and expensive temporary/cache I/O before wholesale relocation.

## Read-only audit

- Resolve the requested machine, then use `tione-ssh-diagnose` if its host identity changed. Do not treat host-key regeneration as a need to regenerate the user's login key.
- Run `findmnt -T` and `df -hT` on the **exact personal directory**, `/workspace`, `/root` and `/tmp`. A parent such as `/share_data` may be overlay while its child is a separate Lustre mount.
- An overlay mount identifies the container filesystem layer, not its physical medium, performance, quota or persistence. Filesystem-wide capacity is not a personal allocation. Confirm lifecycle using Notebook `SystemDiskConfig`, mounts and current platform documentation; mark persistence unknown if API access fails.
- Inspect names at shallow depth. Classify source, venvs, datasets, weights, outputs, caches and symlinks. Avoid recursive `du`/`find` across large data or package trees by default; do not read credentials, shell history or arbitrary process arguments.
- Inspect `pyvenv.cfg`, `bin/python` link resolution and target existence. Follow up with actual runtime checks only if needed, using the intended interpreter; avoid importing project code during a directory inventory.
- Check current editor/runtime locations rather than assuming an old `.vscode-server` directory in shared storage is active. Keep process inspection scoped and omit unrelated users' details from reports.
- If performance is questioned, time a bounded read-only Git operation twice, for example `git --no-optional-locks -C <repo> status --porcelain --untracked-files=normal`. Summarize timing and change counts without exposing filenames unnecessarily. Use a timeout. Label first and repeated observations; do not claim controlled cold-cache testing or infer training throughput from them.

## Environment failure modes

1. A persistent venv points to `/root/.local/share/uv/python/...`, but the new container lacks that interpreter. The venv directory survives while `bin/python` is broken. Rebuild from the project's pinned dependencies and Python version in the intended runtime; do not blindly redirect symlinks to a different Python.
2. `include-system-site-packages=true` plus `/opt/conda` ties a venv to the base image. A rebuild can change Torch/CUDA packages without changes to the shared venv. Record the image and validate the real runtime before training.
3. Moving a venv can invalidate absolute shebangs and editable-install paths. Recreate it rather than assuming a directory copy is portable.
4. One mutable environment shared by several development machines can couple their dependencies. Prefer per-image/per-project environments or reproducible images; choose based on the actual workflow.

## Suggested layout, not an automatic migration

```text
/workspace/<user>/
  run/<project>/       optional disposable execution copies
  envs/<project>/      reconstructible runtime environments
  cache/               disposable build/runtime caches
  tmp/                 temporary files

/share_data/<user>/
  src/<project>/       primary editable source working copies
  datasets/            persistent training/evaluation inputs
  pretrained/          model weights
  experiments/         run outputs, checkpoints, reports
  reproducibility/     lockfiles, launch configs, source snapshots
```

Respect existing project layouts and hardcoded paths. Keep heavyweight reusable model downloads persistent where useful; not every cache should move locally. Open the specific source directory in the editor, excluding datasets, outputs and venvs from indexing as appropriate.

Before an authorized migration, inventory dirty/untracked source, check active jobs and path references, prepare a recoverable copy and validate a small project first. Never infer permission to delete old directories, alter another user's workspace, start training or change storage configuration.

## Evidence from the September 2026 audit

A personal directory was a Lustre child mount while `/workspace`, `/root` and `/tmp` were overlay. Several persistent venvs had missing uv-managed Python targets; other venvs inherited `/opt/conda`. Three Git status samples took approximately 14.31/0.78 s, 2.01/0.43 s and 0.93/0.20 s on first/repeated calls. These observations support checking runtime portability and cache-sensitive metadata access; they do not establish a universal local-versus-shared speedup. Platform API authentication failed initially. The user's subsequent stop-confirmation screenshot explicitly listed persistent mounts including the personal shared directory and warned that other paths would be cleared; `/workspace` was absent. A fresh SSH check still showed `/workspace` and `/root` on overlay, with the personal directory mounted as Lustre. Therefore revise the recommendation for this configuration: keep primary editable source on the personal persistent mount. No destructive stop test was performed.

Another screenshot showed a different Notebook mounting a personal data source directly at `/root`. This demonstrates that `/root` can be persistent when explicitly mounted, but is not evidence for the inspected Notebook. Match Notebook identity before applying screenshot configuration, and use exact mount targets rather than directory names to decide persistence. Recheck live properties in future sessions.

## Authoritative references

- [TI-ONE create development machine](https://cloud.tencent.com/document/product/851/74128): system disk and persistence options.
- [TI-ONE manage development machine](https://cloud.tencent.com/document/product/851/74130): lifecycle and storage behavior.
- [Lustre metadata service](https://wiki.lustre.org/Lustre_Metadata_Service_%28MDS%29): metadata workload characteristics.

Read current documentation when making platform-specific lifecycle claims. Do not generalize one storage configuration to all TI-ONE instances.
