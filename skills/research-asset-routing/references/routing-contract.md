# Research asset routing contract

## Routing table

| Artifact | Canonical home | Obsidian keeps |
|---|---|---|
| Research question / hypothesis | Obsidian | Full concise statement and falsification rule |
| Architecture insight / invariant | Obsidian | Explanation plus source-code pointer |
| Source code / pipeline / config / tests | GitHub | Repository, commit, entry point, one-line role |
| Training task and curves | W&B / TI-ONE | Task/run ID, decisive metric, termination reason |
| Raw/processed dataset and labels | Data platform | Dataset revision, split/label hashes, gate result |
| Periodic or resume checkpoints | Training storage | Selected checkpoint identity only |
| Released model weights | Hugging Face | Repo, immutable revision, SHA256, primary intent |
| Deployment bundle | Artifact storage / HF | Manifest, hash, source commit, runtime contract |
| Repeatable workflow | Codex Skill | Skill name and when it triggers |
| Full report / generated media | Artifact/report store | One conclusion and direct pointer |

## Decision tree

1. Does it explain **why**, change a decision, or define the next hypothesis?
   - Yes → Obsidian.
2. Must a machine execute, test, or review it?
   - Yes → GitHub.
3. Is it a reusable frozen model artifact?
   - Yes → Hugging Face or approved artifact storage.
4. Is it high-volume run telemetry or temporary training state?
   - Yes → W&B / TI-ONE / training storage.
5. Is it raw data, labels, or split membership?
   - Yes → Data platform.
6. Is it a recurring procedure with stable gates?
   - Yes → Skill.

Mixed artifacts should be split, not duplicated. For example, a successful model release produces:

- Obsidian: what was learned and why this checkpoint was promoted;
- GitHub: source/config/eval code at one commit;
- Hugging Face: weights/config/model card at one revision;
- W&B/TI-ONE: full training history;
- Data platform: data and split identity.

## Minimal cross-system identity

```yaml
code:
  repo: owner/name
  commit: full_sha
  entry: path/to/entry
data:
  revision: semantic_id
  split_sha256: hash
run:
  system: wandb_or_tione
  id: immutable_id
checkpoint:
  repo: hf_owner/model
  revision: immutable_revision
  sha256: hash
decision:
  outcome: continue_or_reject_or_promote_or_archive
  next_test: falsifiable_action
```

Omit a block when it does not apply. Never invent missing identities.

## Obsidian pruning test

Before keeping a section, ask:

- Would this still matter after the code is refactored?
- Does it change how future work is chosen?
- Is this the only place where the conclusion is explained?
- Can the payload be replaced by an immutable link and a one-line summary?

If only the last answer is yes, replace the payload with the link.

