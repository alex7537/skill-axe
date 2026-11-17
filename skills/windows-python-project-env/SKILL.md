---
name: windows-python-project-env
description: Audit, create, repair, or explain Windows Python project environments, especially media and ML pipelines using FFmpeg, faster-whisper, CUDA, or OpenAI. Use when deciding what can be shared across projects, whether to create a venv, why a local pipeline fails preflight, or how to establish a reproducible Windows setup. Do not use for Conda-specific workflows unless the project already requires Conda.
---

# Windows Python Project Environment

Build a layered environment: reuse stable machine-level tools and caches, while isolating Python packages per repository. Do not reuse or copy one project's virtual environment into another project.

## Audit before changing anything

Probe the current shell and report evidence before installing or upgrading tools:

```powershell
py -0p
python --version
ffmpeg -version
git --version
gh --version
nvidia-smi
$env:CUDA_PATH
```

Check relevant managers such as `uv`, `conda`, `poetry`, and `pipx`, but do not introduce one when standard `venv` already satisfies the project. Search only the user's stated project roots for `pyvenv.cfg`; avoid broad home-directory scans.

When checking `.env` or API credentials, report only `present` or `missing`. Never print secret values.

## Environment boundary

Treat these as machine-level and reusable:

- installed Python interpreters;
- FFmpeg, Git, and GitHub CLI;
- GPU driver, CUDA toolkit, and compatible cuDNN runtime;
- pip download cache and Hugging Face model cache.

Treat these as project-level and isolated:

- `.venv` and all Python packages;
- dependency declarations and pins;
- `.env`, project configuration, and runtime outputs.

Add `.venv/` and `.env` to `.gitignore`. Do not install project libraries into the base Python interpreter. A project environment is created once and reused across runs; rebuild it only for corruption, a Python-version change, or a deliberate dependency reset.

## Create or repair a project environment

For Windows media/ML projects, prefer Python 3.12 unless the dependency set is verified on a newer interpreter:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Use the venv's explicit Python path in verification commands so success does not depend on shell activation policy. Before rebuilding an existing environment, inspect its `pyvenv.cfg`, interpreter version, installed packages, and failure evidence; do not delete it merely because setup failed once.

## Media and faster-whisper acceptance order

Separate basic pipeline correctness from GPU acceleration:

1. Run compilation, unit tests, URL/config validation, and a no-network dry-run.
2. Verify FFmpeg and Python imports from `.venv`.
3. Run the first transcription with `device: cpu` and `compute_type: int8`.
4. Test GPU transcription separately only after matching the installed CTranslate2 version to its current official CUDA/cuDNN requirements.

An NVIDIA GPU plus `nvcc` is not proof that faster-whisper can use the GPU. Missing or incompatible cuDNN/CUDA DLLs are a distinct runtime gate. Do not downgrade CTranslate2 or replace CUDA globally without showing the compatibility reason and obtaining authorization for that environment change.

Model downloads and API calls are later gates. A dry-run must not download video, fetch a Whisper model, or call a paid API. For copyrighted-media pipelines, preserve the project's explicit rights/permission gate before the first media download.

## Current host baseline

This baseline was observed on 2026-08-25 and is evidence, not a permanent assumption. Re-probe before relying on it:

- Python 3.12.10 and 3.13.0 are installed; use 3.12 for the media pipeline.
- FFmpeg 9.0, Git 2.51, and GitHub CLI 2.98 are installed machine-wide.
- The GPU is an RTX 4060 Laptop GPU with 8 GB VRAM.
- CUDA Toolkit 11.8 is installed; a separate cuDNN installation was not found.
- pip and Hugging Face caches exist and can be reused.
- No Conda, Mamba, Poetry, uv, or pipx installation was found.

## Completion report

State:

- which tools were reused versus installed;
- the exact Python interpreter backing `.venv`;
- whether tests and dry-run passed;
- whether CPU transcription passed;
- GPU compatibility as a separate result;
- remaining blockers such as API credentials or content authorization.

## Gotchas

- A newly installed executable may require rebuilding the current process `PATH` or opening a new terminal.
- `python` can resolve differently from `py -3.12`; prefer the launcher when creating the environment and the venv's explicit interpreter afterward.
- Do not expose credentials while diagnosing environment variables.
- Do not call a dependency installation successful until imports run from the project's `.venv`.
