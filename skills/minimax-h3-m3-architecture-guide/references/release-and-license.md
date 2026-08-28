# Release, deployment, and license boundaries

Snapshot verified 2026-08-27. Refresh official sources before using this file for a current availability, license, or deployment decision.

## H3 public artifacts

- GitHub: `MiniMax-AI/MiniMax-H3` — inference code, task layouts, prompt-writing skills and examples.
- Hugging Face: `MiniMaxAI/MiniMax-H3` — FL2VA and Ref2VA checkpoints plus multiple framework-oriented layouts.
- Public base model: 33B H3-Omni-Transformer, Qwen3-VL-32B encoder, Visual VAE and Audio VAE.
- Official local validation: H3-Base at 768p-class output.
- Not initially public locally: H3-Context-IR implementation, H3-Regenerate-2K implementation, and native sparse-attention implementation.

Repository-size audit on 2026-08-27 using the HF file-tree API:

- one original task family (`FL2VA/` or `Ref2VA/`): about `144 GB` decimal;
- complete HF repository: about `498.5 GB` decimal because it includes two task families and duplicate/repacked component layouts.

The official SGLang example uses four GPUs. Do not infer VRAM per card from that flag alone. Upstream vLLM recipes add CPU offload, text-encoder tensor parallelism and VAE tiling because the Qwen encoder, DiT and VAE create different peak-memory phases.

## M3 public artifacts

- GitHub: `MiniMax-AI/MiniMax-M3` — release/model overview; most executable model artifacts live on HF and in upstream inference frameworks.
- Hugging Face BF16: `MiniMaxAI/MiniMax-M3`.
- Official MXFP8: `MiniMaxAI/MiniMax-M3-MXFP8`.
- NVIDIA NVFP4: `nvidia/MiniMax-M3-NVFP4`.
- MSA paper and kernel: `arXiv:2606.13392` and `MiniMax-AI/MSA`.
- Supported ecosystems include Transformers, SGLang, vLLM and community/offload runtimes; exact feature parity changes over time.

Repository-size audit on 2026-08-27:

- official BF16 repository: about `854 GB` decimal;
- official MXFP8 repository: about `444 GB` decimal;
- NVIDIA NVFP4 repository: about `250 GB` decimal.

These are file-tree totals, not minimum VRAM. Serving additionally needs runtime buffers and KV cache. Conversely, CPU/unified-memory offload can reduce VRAM at a large latency cost.

## Open-weight versus open-source

Use these terms carefully:

- **Open weights**: weights are downloadable and local inference/fine-tuning is permitted subject to a license.
- **Open inference implementation**: sufficient code exists to load and run the published weights.
- **Open training recipe**: training data, objective, schedules and distributed training system are reproducible. Neither release currently satisfies this strong meaning.
- **Fully open product pipeline**: every hosted preprocessing/postprocessing component is public. H3 does not satisfy this because Context-IR and Regenerate-2K remain hosted.
- **OSI open source**: a software license satisfying OSI criteria. Custom use, territory and commercial restrictions mean these MiniMax community licenses should not be described this way.

## License facts that change decisions

This section summarizes official text and is not legal advice.

### H3 Community License

- Applicable territory excludes the United States, European Union, United Kingdom and Republic of Korea in the 2026-08-02 license.
- Commercial products/services above USD 20 million annual revenue require prior written authorization.
- Commercial interfaces must prominently display `MiniMax H3`.
- Distribution requires the prescribed notice.
- Use restrictions and downstream-user safeguards apply.
- H3 works or outputs may not be used to improve another AI model except H3 or its derivatives.

This last condition matters for synthetic training data, distillation, evaluator training and multimodal dataset generation.

### M3 Community License

- Commercial use requires prominent `Built with MiniMax M3` attribution.
- Below the USD 20 million annual-revenue threshold, the license calls for a one-time commercial notice; above it, prior written authorization is required.
- Prohibited uses include military purposes and other enumerated harmful or unlawful uses.

Read the current license file before commercial use or redistribution.

## Deployment decision guide

- Use the hosted API first when evaluating capability without multi-GPU infrastructure.
- For H3 research, download only the required task family or the exact Diffusers/Comfy components rather than the whole repository.
- For M3, choose precision and runtime together. A quantized checkpoint without an optimized MSA path may fit but lose the main long-context efficiency advantage.
- Record checkpoint revision, runtime commit, GPU topology, quantization, context/resolution, offload settings and exact prompt/harness for every benchmark.

## Official links

- https://github.com/MiniMax-AI/MiniMax-H3
- https://huggingface.co/MiniMaxAI/MiniMax-H3
- https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE
- https://github.com/MiniMax-AI/MiniMax-M3
- https://huggingface.co/MiniMaxAI/MiniMax-M3
- https://huggingface.co/MiniMaxAI/MiniMax-M3/blob/main/LICENSE
- https://huggingface.co/MiniMaxAI/MiniMax-M3-MXFP8
- https://huggingface.co/nvidia/MiniMax-M3-NVFP4
- https://arxiv.org/abs/2606.13392
