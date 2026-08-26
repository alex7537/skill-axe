---
name: robot-model-knowledge-dashboard
description: Inventory, classify, and summarize personal robot-model architecture skills, then generate or refresh a linked Obsidian dashboard of learned routes, evidence status, gaps, and current expansion candidates. Use when the user asks what robot/VLA/WAM/value models have been studied, wants 模型知识版图/学习看板/路线统计, needs to classify a new model skill, or wants the Obsidian model dashboard updated. Do not use as the canonical source for live training status or to reorganize unrelated Vault content.
---

# Robot Model Knowledge Dashboard

Treat this as a data-fetching and analysis skill. Codex skills are the executable summaries; Obsidian is the semantic navigation layer. Keep model knowledge, support workflows, and unstudied candidates distinct.

## Canonical ownership

- Codex skill: reusable model-specific explanation, audit, experiment, and gates.
- Obsidian dashboard: route map, counts, decisions, gaps, and links to canonical notes.
- Repository: executable source/config/tests.
- Run infrastructure: logs, metrics, checkpoints.
- Data platform: raw data and split membership.

Never copy checkpoints, logs, raw data, full source, or raw session transcripts into the dashboard.

## Refresh workflow

1. Read `config.json`; if absent, copy `config.example.json` and resolve the exact personal skill root, Vault root, and dashboard path.
2. Confirm the Vault root via `.obsidian/` and inspect Git status. Preserve existing user changes; this skill writes only the configured generated dashboard.
3. Read [references/model-routes.json](references/model-routes.json). Treat registered model skills as curated classification and installed metadata as live availability.
4. Run the generator in dry-run mode first:

   ```bash
   python3 scripts/update_dashboard.py --dry-run
   ```

5. Review counts, untracked model-like skills, links, and candidate freshness. Then write only when requested:

   ```bash
   python3 scripts/update_dashboard.py --write
   ```

6. Re-read the dashboard, validate every Wiki link target that is expected to exist, and inspect `git diff -- <dashboard>` without staging or committing unrelated Vault changes.

## Classification rules

- **Core model route:** changes what is predicted, how conditioning enters, or how actions/futures/values are represented and learned.
- **Integration route:** adds a learned representation or branch to a core policy.
- **Supporting workflow:** data, training budget, evaluation, packaging, release, or infrastructure; never count it as a learned model architecture.
- **Candidate:** an official model/paper selected for future study; never count it as summarized merely because a link exists.

One skill may inform multiple concepts, but give it one primary route in the dashboard to avoid double-counting.

## Latest-model refresh

When the user asks for latest models, browse current official project pages, official repositories, or original papers. Update the registry snapshot date and candidate entries only after source verification. Record each candidate's route, why it extends the current map, and the first falsifiable learning question. Do not promote a candidate to `summarized` until a dedicated skill or reviewed canonical note exists.

## Write safety

- The generator refuses to overwrite a dashboard that lacks its generated marker.
- Dashboard paths must remain inside the configured Vault and outside protected roots.
- Do not edit `.obsidian/`, existing notes, indexes, or README files.
- Do not initialize Git, commit, merge, push, or clean the Vault unless separately authorized.
- If the Vault is dirty, add only the dashboard and report its isolated diff.

## Gotchas

- Installed skill count is not learned-model count: generic coaches and evaluation runbooks are supporting capability.
- A paper note is not a verified implementation map; record evidence status.
- Dashboard progress is navigation, not a percentage of scientific understanding.
- A static “latest” list decays quickly; show its source date and refresh gate.
- Avoid duplicate truth: the dashboard links to model notes and skills instead of copying their full content.

## Deliverable

Report route counts, installed model-summary skills, supporting skills, unclassified candidates, newest official expansion candidates, exact dashboard path, source snapshot date, and isolated Vault diff status.
