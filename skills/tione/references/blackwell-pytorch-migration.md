# TI-ONE GPU and PyTorch image migration

Use this runbook when a persistent TI-ONE workspace moves between GPU
architectures or custom Docker images. Treat storage continuity, process
continuity, SSH identity, CUDA driver visibility, PyTorch kernel support, Python
dependency compatibility, and model behavior as separate gates.

## Why an image rebuild is safer than in-place Torch replacement

Prefer a coherent PyTorch/CUDA/cuDNN image when the new GPU architecture is not
compiled into the old Torch binary. Installing a new `torch` over a base image
can leave an old `torchvision`, Triton, NCCL, cuDNN binding, or custom CUDA
extension on `sys.path`.

For Blackwell `sm_120`, use PyTorch 2.7 or newer built with CUDA 12.8 or newer.
The minimum-change reference image is:

```text
pytorch/pytorch:2.7.1-cuda12.8-cudnn9-devel
```

An NVIDIA `cuda:*cudnn-devel*` image is only a toolkit base; it is not a
PyTorch environment until matching Torch and torchvision are installed.

Primary compatibility reference:
[PyTorch 2.7 Blackwell support](https://pytorch.org/blog/pytorch-2-7/).

## Gate sequence

### 1. Resolve machine identity

- Confirm the new Notebook endpoint through TI-ONE or explicit user evidence.
- Run `$tione-ssh-diagnose` before login.
- A rebuild may change host keys even when the IP and forwarded port stay the
  same. Never delete the entire `known_hosts` file.

### 2. Separate driver, runtime, and compiled architecture

Record:

```text
nvidia-smi GPU name, memory, driver, compute capability
torch.__version__ and torch.version.cuda
torch.cuda.get_device_capability(0)
torch.cuda.get_arch_list()
torch.backends.cudnn.version()
```

For a Blackwell RTX PRO device with capability `(12, 0)`, require `sm_120` or
`compute_120` in the Torch architecture list and run real BF16 matmul and
Conv2d kernels. Do not accept visibility-only checks.

```bash
python scripts/probe_pytorch_gpu.py \
  --expected-capability 12.0 \
  --require-package torchvision
```

### 3. Audit persistent venv inheritance

Persistent storage survives a container rebuild; processes and the base Python
environment do not. For every reused venv inspect:

```bash
cat /path/to/venv/pyvenv.cfg
/path/to/venv/bin/python -c \
  'import sys,torch; print(sys.prefix,sys.base_prefix,torch.__file__)'
/path/to/venv/bin/python -m pip check
```

If `include-system-site-packages=true`, the venv may intentionally inherit the
new container's Torch while keeping project packages from persistent storage.
This can be accepted only after import and model-level tests. Prefer a new
versioned venv for long-lived reproducibility when Python patch versions,
binary wheels, or dependency constraints drift.

Reinstall every custom CUDA extension against the new Torch/CUDA stack. Do not
copy `flash-attn`, xFormers, bitsandbytes, fused optimizer, or custom-op wheels
from an older CUDA environment.

### 4. Verify repository contracts

Use the smallest relevant sequence:

1. import required packages and report their file locations;
2. run the actual visual encoder on CUDA;
3. read one real HDF5 batch;
4. strictly load an old checkpoint;
5. run finite forward and backward;
6. save and resume optimizer, scheduler, sampler, and RNG state;
7. compare a deterministic validation result within the declared tolerance;
8. only then launch a long run.

PyTorch 2.6+ changed the default behavior of `torch.load`; loaders for trusted
full training checkpoints may need an explicit `weights_only=False`, while
deployment state dicts should prefer `weights_only=True`.

### 5. Rebudget rather than blindly copying A800 settings

Learning rate, warmup, epochs, and data semantics do not change merely because
the GPU changes. Batch size, throughput, memory headroom, DataLoader workers,
and custom-kernel availability must be remeasured. A nominally newer GPU is not
automatically faster than an A800 for the complete input pipeline.

## Verified incident: A800 image to Blackwell image

Evidence captured 2026-09-14 on a TI-ONE Notebook after moving from an A800
image to an NVIDIA RTX PRO 5000 72GB Blackwell:

```text
Old: PyTorch 2.4.1+cu121, compiled through sm_90
Observed failure: no kernel image is available for execution on the device

New: PyTorch 2.7.1+cu128, torchvision 0.22.1+cu128, cuDNN 9.7.1
Device: capability 12.0; arch list includes sm_120 and compute_120
```

Verified on the new image:

- BF16 matmul and Conv2d were finite;
- the existing timm ViT completed a real CUDA forward;
- a real A2D HDF5 sample loaded;
- frozen SigLIP plus RDT-170M completed a masked real-data backward with finite
  gradients and zero inactive-action-row gradient;
- the exact Wan2.2 VAE checkpoint encoded nine `224x224` frames into finite
  `[48,3,14,14]` latents, using about 3.18 GB peak CUDA allocation in that
  bounded probe.

These results establish environment compatibility, not equal training speed,
rollout quality, or bitwise equivalence across GPU architectures.
