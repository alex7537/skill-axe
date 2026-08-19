# lark-cli Wiki review workflow

Use this reference for non-trivial nested Wiki reviews. It captures the failure modes that are easy to miss even when `lark-cli` itself is working.

## Permission interpretation

Check three separate layers:

1. `lark-cli auth status`: effective identity, token state, and granted user scopes.
2. `lark-cli auth check --scope docx:document:readonly`: confirms the required read scope.
3. A real `docs +fetch --as user`: distinguishes scope success from per-resource ACL success.

`needs_refresh` is not automatically a failure; the next user API call may refresh the token. Attempt the requested read once. Do not change identity to bypass an ACL or scope failure.

If the user asks whether access is “read-only,” inspect for write/delete capabilities such as document create/write, space document delete/move, permission management, Wiki writes, or record deletion. Say that the current operation was read-only even when the broader token is not.

## Tree discovery

Feishu Wiki navigation frequently has several layers of index pages:

```text
root Wiki
└── topic index
    └── training/evaluation index
        ├── dated experiment pages
        ├── benchmark pages
        └── insight pages
```

The root may resolve to a Docx whose body is only:

```xml
<sub-page-list ...>
  <sub-page doc-id="..." file-type="docx" title="..."/>
</sub-page-list>
```

An outline request can therefore return an empty fragment. Fetch the simple body and parse the children instead of concluding the document is empty.

Follow `sub-page-list` children by default. Treat `<cite>` and `<synced_reference>` as cross-references: follow only when the requested analysis depends on them. For a synced reference, preserve the source token and source block ID together.

## Resource routing

- Docx or Wiki content: `lark-doc`, `docs +fetch`.
- Sheets/Base embedded data: use the corresponding read-only embedded skill only if necessary for the user's question.
- Files/PDFs: do not download automatically. First determine whether the surrounding page already contains the needed conclusions.
- Images/video: do not download merely to reproduce experiment tables. Preview only when visual judgment is required.

Never turn a read-only review into a write, permission, comment, or Drive-management workflow without a new explicit request.

## Efficient reading

Use the smallest useful scope:

```bash
# Directory discovery
lark-cli docs +fetch --as user --doc '<url-or-token>' \
  --doc-format markdown --detail simple --format json

# Unknown content page
lark-cli docs +fetch --as user --doc '<token>' \
  --scope outline --max-depth 4 --doc-format xml --detail with-ids --format json

# Targeted evidence
lark-cli docs +fetch --as user --doc '<token>' \
  --scope keyword --keyword '结论|短板|配置|EWM|checkpoint' \
  --context-before 1 --context-after 2 --max-depth 3 \
  --doc-format markdown --detail simple --format json
```

Full-page fetches containing large rollout tables may be dominated by `<figure>` and signed media URLs. Prefer keyword/section reads, or sanitize transient output before inspection. The bundled tree script strips `href`/`src` values and source tags from emitted content.

## Experiment synthesis contract

For each comparable run, capture:

| Field | Why it matters |
|---|---|
| Date, revision, commit | Pages evolve and later corrections may invalidate old conclusions |
| Dataset and split | Prevents comparing RoboTwin-only with multi-source Mix as if identical |
| Model/backbone and conditioning | Distinguishes backbone changes from action-contract changes |
| Window, resolution, FPS | Determines temporal and visual comparability |
| Checkpoint/epoch/step | Makes “best model” reproducible |
| Evaluation schema and coverage | Prevents EWM7/EWM10/EWM15/Core/Full conflation |
| Score and uncertainty | Prefer confidence intervals or paired comparisons when available |
| Failure/confounder | OOM, communication timeout, incomplete shards, metric drift, contradictory conditioning |

When a page corrects an earlier report, present the corrected interpretation and briefly note the historical mismatch. Do not average results across condition tracks or benchmark profiles unless the protocol explicitly defines such an aggregate.

## Success criteria

A completed review should make it possible to answer:

- Which methods were actually trained rather than merely proposed?
- What changed between runs?
- Which evaluation protocol produced each number?
- What is the best checkpoint under each stated objective?
- Which conclusions are robust, and which are partial or confounded?
- What should be tried next, and why?

The final answer should also state that the operation was read-only and distinguish that from the breadth of the account's granted scopes.
