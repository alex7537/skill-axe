---
name: research-project-resume
description: Verify research or engineering project claims against GitHub code, Obsidian notes, experiment reports, and the user's account, then produce concise English resume bullets with traceable evidence and personal contribution boundaries. Use for 项目经历提炼、结合代码和Obsidian写简历、把机器人或机器学习项目写成英文bullets, or ASu-style evidence-based project rewriting. Do not use for resume layout, job applications, running experiments, or generic translation without evidence review.
---

# Research Project Resume

Turn a technical project into defensible resume claims. Treat the user's account as evidence of personal responsibilities; repository ownership and implemented code do not establish sole authorship.

## Scope and inputs

- Start from the named project, the user's responsibilities, available repositories, project notes, and experimental outcomes. Infer a suitable role from context when possible; a missing job description need not block a useful draft.
- Read repositories and notes without modifying their source. Write requested resume artifacts and evidence records in the current deliverables directory. Do not launch training, operate a robot, publish materials, or contact recruiters as part of this skill.
- This is a personal evidence-extraction workflow, not the upstream ASu plugin. If ASu is explicitly requested, locate its installed `great-resume` rules or read the upstream source and relevant claim-ledger reference. Do not claim to have used unavailable rules or silently install a plugin.

## Resolve evidence efficiently

1. Inspect available local checkouts and their remotes, branch, full commit, and working-tree status before downloading another copy. A stale local checkout must not override newer remote evidence.
2. For remote verification, prefer repository APIs and targeted file reads. Resolve the intended branch to a full commit, then fetch README, model, dataset, trainer, relevant configs, changelog, and evaluation reports at that revision. Large repositories rarely need a full clone for resume extraction.
3. Search the narrowest relevant Obsidian project notes and personal skill references. Distinguish project records from unrelated paper summaries and general learning notes. Notes and skills provide leads and historical context, not automatic proof of present implementation or measured outcomes.
4. Trace only claims likely to enter the resume: data provenance and processing; encoder/token/action shapes; learning objective and masks; optimizer and training budget; checkpoint evaluation; iteration rationale and outcome.
5. Read the related inference repository to verify the training/deployment contract. Respect statements such as “I mainly trained and tested the models”; describe evaluation through the existing pipeline unless the user actually designed it.

## Build a compact claim ledger

Use a Markdown table for this standalone workflow; use the upstream schema when an active ASu workflow requires it. Keep candidate claims, not transcripts. Record:

- Original claim and candidate wording.
- Evidence location and revision/date; distinguish inspected code, report, note, and user account.
- Personal role and team boundary.
- Status: supported, user-reported, conflicting, or missing evidence.
- Metric scope, qualification, and unresolved questions.

Separate four kinds of evidence: **code exists**, **a configuration was proposed**, **a run completed**, and **an outcome was measured**. A config alone cannot establish a finished run; a completed run cannot establish a rollout gain. A repository report is documentary evidence unless raw measurements were independently checked.

When sources disagree, look for a version change before treating one as wrong. Preserve both stages and identify which claim each supports. Unresolved conflicts stay outside unqualified final bullets. User-reported achievements can be used at the scope the user supplied, with their evidence status explained outside the copyable text; do not invent missing trial counts, environments, or benchmark definitions.

## Translate technical decisions into bullets

- Prefer action → concrete method/system → reason or difficulty → measured result. Choose details that demonstrate judgment rather than listing every training parameter.
- Distinguish using a standard objective from proposing a new loss. Masking, target semantics, sampling, and training schedules can be substantial engineering contributions without a novelty claim.
- Fold backpropagation into trainable/frozen parameter groups, differential learning rates, or loss-gradient design. Do not list routine `backward()` execution as a separate achievement.
- Express feature adapters and token assembly precisely. Shape arithmetic can clarify a contribution, but do not claim dimension reduction when the adapter is identity or only projects a different branch.
- Separate oversampling, loss weighting, and higher recording FPS. Specify whether a keyframe rule selects frames, windows, or episodes.
- Put unfinished world-model or post-training work in an optional exploration bullet using “explored,” “prototyped,” or “implemented and smoke-tested,” according to evidence.
- Keep qualitative improvements qualitative unless a matched comparison supports a number. Never convert lower validation loss into higher task success.

For robot-policy claims about padding, target/executed actions, deduplication, or success rate, read [references/robot-policy-evidence.md](references/robot-policy-evidence.md).

## Deliver and verify

Deliver a paste-ready project title and approximately 4–6 focused English bullets, adapting length to the user's requested coverage. Add a separate exploration bullet when useful. Keep citations and evidence caveats outside the copyable resume text. Provide a linked evidence note when the investigation contains version conflicts or multiple strong claims; do not force a file for a simple rewrite.

Before delivery, check that:

- Every number has a source and the correct denominator, unit, dataset, baseline, and experimental stage where known.
- Approximate raw-data size is not mislabeled as processed dataset size or personal collection volume.
- Baseline-to-result calculations use the correct direction and distinguish relative percent from percentage points.
- Each strong verb matches the user's responsibility; no implementation in a team repository becomes independent personal ownership by inference.
- Completed results and untested extensions are visibly separated.
- Important gaps are stated concisely, without withholding the supported draft.

## Gotchas

- README and local notes can describe different revisions; inspect executable code and changelog before reconciling them.
- Smaller-data and larger-data encoder ablations can favor different strategies. Preserve dataset scale and experiment budget rather than declaring one globally best.
- A standard loss with padding masking is not a newly invented algorithm; diagnostic loss breakdowns may not contribute gradients.
- A predicted action chunk and the prefix actually executed are different horizons.
- Source retrieval is not fresh runtime verification. Report what was read and what was actually run.
