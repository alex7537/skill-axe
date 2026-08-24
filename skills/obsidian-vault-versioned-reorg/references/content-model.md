# Content model for research vaults

Use metadata and maps of content (MOCs) before large physical moves. A directory can express only one dimension, while a note may have a topic, lifecycle, source, and audience simultaneously.

## Common roles

| Role | Meaning | Typical treatment |
|---|---|---|
| `paper-source` | Raw clipping or imported paper material | Protect; preserve provenance |
| `paper-note` | Structured reading result | Link back to source and forward to ideas |
| `idea` | Falsifiable insight proposed for a pipeline | Track pending/applied/rejected evidence |
| `knowledge` | Long-lived technical understanding | Link from topic MOCs |
| `method` | Repeatable way to do something | Keep principles in notes; executable form may become a skill |
| `status` | Time-sensitive project state | Archive by date; do not treat as current truth |
| `log` | Learning or work history | Preserve, but remove from daily navigation |
| `external` | Weekly report, Feishu export, delivery document | Record audience/date; avoid duplicate internal truth |
| `reference` | Environment and tool notes | Keep concise and deduplicate |

Minimal optional frontmatter:

```yaml
---
type: knowledge
status: stable
topic:
  - world-model
reviewed: YYYY-MM-DD
---
```

Avoid bulk-inserting metadata into every historical note. Add it when a note is touched or indexed.

## Research flow

```text
paper source → structured reading → idea → smallest validation → applied/rejected result
```

An Idea record should contain source, core claim, target module, expected metric, validation design, cost, result, and rejection reason when applicable. Project completion percentages do not belong in the Idea layer.

