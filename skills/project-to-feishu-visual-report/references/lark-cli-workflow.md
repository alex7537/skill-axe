# CLI publishing and verification

Use when the authenticated `lark-cli` is available. These command shapes were verified in a completed project-summary task; re-read installed help because flags and authoring requirements can change.

## Discover and author

```bash
lark-cli whoami
lark-cli docs --help
lark-cli skills read lark-doc
lark-cli skills read lark-doc references/lark-doc-create-workflow.md
```

Follow the current authoring workflow, including its genre selection, presentation decision, draft initialization and profile check. Read XML and create references before writing. Choose the knowledge/reference genre for project orientation when appropriate; do not force that genre on a research report.

The CLI draft initializer returns a unique workspace and `draft_path`. Keep CWD stable. Content/media file arguments use `@./relative/path` inside CWD; absolute `@/path` is rejected. Use a file or literal heredoc for multi-line content to prevent shell substitutions.

Common XML forms:

```xml
<title>Project overview</title>
<h1 seq="auto">Data routes</h1>
<whiteboard type="svg" path="@./TASK_WORKSPACE/routes.svg"/>
<img path="@./images/sample.jpg" caption="Actual sample; explain coverage"/>
<table><thead><tr><th><p>Input</p></th><th><p>Output</p></th></tr></thead>
<tbody><tr><td><p>Source schema</p></td><td><p>Result</p></td></tr></tbody></table>
<pre lang="bash"><code>example-command --input /path/to/input</code></pre>
```

Escape text content, not XML tags. Read the current whiteboard guide before constructing diagrams. For small flow diagrams, a self-contained SVG with text, shapes and connectors is sufficient; no model-generated image is needed to convey exact technical relations. Do not embed external SVG resources.

```bash
lark-cli docs +script --command parse --content @./TASK_WORKSPACE/draft.xml --format json
lark-cli docs +create --as user --doc-format xml \
  --content @./TASK_WORKSPACE/draft.xml --parent-position my_library
```

Replace `TASK_WORKSPACE` with the initializer's actual path. Parse completion means success only when `data.assessment.status` passes. Review facts and XML separately; the parser does not establish factual correctness or server acceptance. The create command is a real write and requires the user's creation request.

## Verify the created result

Capture the returned URL/document ID, warnings and `new_blocks` tokens. Do not expose unrelated account metadata.

```bash
lark-cli docs +fetch --as user --doc DOCUMENT_ID --detail with-ids
lark-cli whiteboard +export --as user \
  --whiteboard-token BOARD_TOKEN --output-type preview \
  --output ./TASK_WORKSPACE/diagram-preview
```

Use live returned IDs, never example tokens. Inspect the fetched content for expected headings, tables, image/board references and the document ending. Open downloaded previews with an image-viewing tool.

**Verified failure mode:** a board preview response may be JPEG. An explicit `.png` output then fails with `preview response is .jpg but output path has extension .png`. Retry the read-only export with `.jpg` or no extension; do not recreate the document or board.

If create succeeded but a media resource failed, read the update guide, check the target's ownership and effective permission as required, patch only the failed resource, and fetch again. A lack of edit authorization is not permission to replace the whole document.

After verification, remove only the exact temporary workspace returned by initialization. Never delete source images referenced from outside that workspace. No test document, probe write, notification or permission change is needed for ordinary delivery.
