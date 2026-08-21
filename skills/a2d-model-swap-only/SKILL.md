---
name: a2d-model-swap-only
description: Test, compare, or validate a different A2D checkpoint or deployment bundle while preserving the established inference and simulation pipeline. Use when the user says 换模型测试, swap checkpoint, compare A2D bundles, or explicitly requires workspace code, preprocessing, action mapping, simulator assets, control parameters, datasets, dependencies, and evaluation criteria to remain unchanged. Do not use when the requested experiment intentionally changes the pipeline or evaluation contract.
---

# A2D Model Swap Only

Apply a strict model-only boundary: vary the selected model bundle and a fresh result namespace, while treating the frozen pipeline contract as immutable.

## Load the baseline contract

Require a reviewed baseline manifest matching [assets/baseline-manifest.template.json](assets/baseline-manifest.template.json). Validate it with `scripts/validate_baseline_manifest.py` and read [references/model-only-contract.md](references/model-only-contract.md).

The runtime baseline manifest may contain local workspace paths and environment names; keep it in the project or private configuration, not in the portable skill. If no approved manifest exists, inspect read-only and produce a proposed contract only when the user asks for one. Do not guess the command or protected hashes.

Use `$remote-policy-bundle` first when a remote checkpoint still needs to be exported, pulled, or hash-verified. Use `$a2d-grasp-evaluation` for the grasp-specific success funnel and `$robot-benchmark-loop` for formal coverage and promotion gates.

## Enforce the model-only boundary

Unless a separate exception is explicitly authorized:

- Do not edit, format, restore, delete, or generate files under protected code/config/data roots.
- Do not install, uninstall, upgrade, downgrade, clone, or reconfigure environments.
- Do not change inference logic, preprocessing, image transforms, normalization, observation fields, action mapping, sampling, seeds, control frequency, execute horizon, RPC mode, scene, assets, dataset, server code, or evaluation criteria.
- Do not replace a default checkpoint inside source code. Supply the bundle through the frozen runtime argument.
- Do not extract or copy the new bundle into a protected workspace.
- Allow writes only inside the manifest's designated fresh result roots and only when executing the frozen test.
- Do not start, stop, kill, or restart the simulator/server unless the user explicitly authorizes that process action.
- Stop when the model cannot be tested without crossing a protected boundary. An observed failure does not authorize a pipeline fix.

## Model-only workflow

1. Resolve the requested bundle read-only and require exactly one file.
2. Record its absolute path, role, size, SHA-256, and archive/manifest identity when available.
3. Validate the baseline manifest and record its hash.
4. Inspect `git status --short` and compare every protected file against the baseline hash. Report drift; never restore it automatically.
5. Confirm that the result namespace is fresh or resume-compatible and is the only intended writable location.
6. Render the frozen argument vector by replacing exactly `{MODEL_BUNDLE}` and any explicitly allowed output placeholder. Show the command before a costly or external run when authorization is not already explicit.
7. Execute only when requested. Preserve argv structure; do not pass it through an extra shell evaluation layer.
8. Record exit state, result artifacts, errors, and unchanged runtime parameters.
9. Recheck protected hashes and workspace status after the run. Report every unexpected mutation and disqualify the comparison until resolved.

## Compare models fairly

- Keep the same baseline manifest, task/layout seeds, result schema, horizon, rate, maximum actions, server, and success profile.
- Use separate output namespaces and record bundle hashes in every result.
- Alternate bundles when time/order drift could bias sequential runs.
- Compare only matched seeds at equal completed counts.
- Treat loading/execution smoke episodes separately from qualified performance evidence.

## Handle requests beyond the boundary

If the user also asks to change a parameter or pipeline file, state that this exits model-only mode. Obtain a separate explicit scope naming the file/parameter/process action, then use the appropriate code, benchmark, or lifecycle skill. Do not silently broaden this skill into a repair or tuning workflow.

## Success criteria

A model-only test is valid when:

- the baseline manifest and protected hashes validated before and after;
- only the bundle identity and approved result namespace differed;
- observation/action schemas and runtime parameters match the baseline;
- the evaluator produced schema-valid results or a precisely attributed compatibility/runtime error;
- no dependency, simulator, dataset, code, or configuration mutation occurred.

## Gotchas

- “Same action dimension” does not prove matching normalization, representation, timing, or observation schema.
- A `.tgz` filename is not bundle identity; use verified internal manifest and SHA-256 when available.
- A dirty workspace is not automatically invalid, but its pre-existing changes must be preserved and included in the baseline/drift assessment.
- Source paths embedded in a downloaded skill are historical evidence, not the current baseline.
- Changing only `--bundle` can still be unfair if the policy adapter auto-selects preprocessing from bundle metadata; record resolved behavior.
- Running a baseline command may write caches or bytecode outside the intended result root. Detect and report them; do not expand the allowed surface after the fact.
- A failed model load is a compatibility result, not permission to patch the loader or environment.
