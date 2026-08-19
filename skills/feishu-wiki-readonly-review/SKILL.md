---
name: feishu-wiki-readonly-review
description: "Read and summarize nested Feishu/Lark Wiki or Docx pages through the authenticated lark-cli when a user provides a /wiki/ or /docx/ link and asks to review experiments, training methods, evaluations, decisions, or lessons. Use especially when live permission state must be verified or browser access is unavailable. Read-only: do not use for editing, comments, permission changes, Drive organization, or broad document search."
---

# Feishu Wiki Read-only Review

Use the installed `lark-cli` and its embedded `lark-doc` / `lark-shared` skills. The outcome is an evidence-backed synthesis of the relevant page tree, with permission state and metric-version caveats stated explicitly.

## Safety boundary

- Treat every Feishu resource as read-only. Use only `auth status`, `auth check`, `skills read`, and `docs +fetch`.
- Never call create, update, delete, move, copy, comment, permission, member, or sharing commands under this skill.
- Do not request new OAuth scopes unless the user separately asks to change authorization. If read scope or resource ACL is missing, report the exact blocker.
- A token containing `docx:document:readonly` is not necessarily globally read-only. Inspect the complete live scope set before making that claim, and mention materially relevant write/delete scopes without dumping unrelated scopes.
- Do not reproduce expiring `authcode` URLs, access tokens, media download URLs, or raw authentication output in the final report.

## Workflow

1. Confirm `lark-cli` exists. Read its current embedded instructions before the first live operation:

   ```bash
   lark-cli skills read lark-doc
   lark-cli skills read lark-doc references/lark-doc-fetch.md
   ```

   Read `lark-shared` as well when the task asks about identity/scopes or when authentication fails.

2. Verify the effective user identity and actual read grant:

   ```bash
   lark-cli auth status
   lark-cli auth check --scope docx:document:readonly
   ```

   Prefer explicit `--as user` for the whole traversal. Preserve the originating identity if a token came from a bot workflow.

3. Discover the nested page tree before loading large bodies. Use the bundled script from the skill directory:

   ```bash
   python3 scripts/fetch_wiki_tree.py '<wiki-or-docx-url>' --max-depth 8
   ```

   This follows `sub-page-list` Docx/Wiki children only. Add `--include-cites` only when cited pages are genuinely part of the requested evidence. Add `--include-content` only when a bounded tree is small enough to inspect directly.

4. Select pages by title and relevance. Fetch the smallest sufficient scope with `docs +fetch`: outline first for an unknown substantial page, then section/keyword/full content as needed. Directory pages often contain only a title plus `sub-page-list`, so an empty outline does not mean the Wiki is empty.

5. Build the synthesis around stable comparisons:

   - method or training recipe;
   - data, conditioning, model, and infrastructure changes;
   - evaluation protocol and exact metric schema;
   - quantitative outcome and checkpoint selection;
   - failure modes, confounders, and reusable lessons.

   Keep facts from different revisions, datasets, profiles, and metric schemas separate. Explicitly label partial metrics such as EWM7/EWM10 versus official or later schemas.

6. Verify completion: report the root title, the relevant page titles actually read, the live identity/read-scope result, and any skipped resource types or inaccessible pages. Link the original user-provided Wiki URL; do not expose internal media URLs.

## Detailed guidance

Read [references/lark-cli-review-workflow.md](references/lark-cli-review-workflow.md) when handling a multi-level Wiki, permission ambiguity, embedded non-Docx resources, large experiment tables, or versioned benchmark results.

## Gotchas

- `lark-cli auth scopes` may describe app-available scopes; use `auth status` plus `auth check --scope ...` for the effective user grant.
- `--detail with-ids` is ignored with Markdown output. Use XML when block IDs are needed.
- Do not follow every `<cite>` by default; citations can escape the intended subtree and explode scope.
- Empty placeholder pages and infrastructure-only pages should be identified, not padded into the summary.
- More training steps, lower train loss, or a higher partial aggregate do not by themselves establish a better world model. Preserve evaluation coverage and checkpoint-selection evidence.
