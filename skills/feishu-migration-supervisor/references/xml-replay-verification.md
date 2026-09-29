# XML replay: verified failure modes and acceptance

## Evidence and limits

A 2026-09-29 migration with lark-cli 1.0.87 reconstructed 73 reviewed Docx pages and six target index pages across accounts, reusing one existing target. All target bodies, structure, ownership and library placement were read back. All 220 transferred resources passed source/target SHA256 comparison. Twenty-one attachments above the task-specific 20 MiB threshold were explicitly skipped; 21 embedded sheet views became data snapshots and three boards became static previews. Counts are dated evidence, not defaults or guarantees for another task.

Three pages returned successful writes but lost paragraphs nested directly inside list items. Complete body comparison detected the problem; repair and another readback confirmed recovery. Source revisions were checked before closing. This proved completion of the approved set with declared omissions, not a lossless native clone or coverage of every company-accessible document.

## Nested paragraph loss and repair

Observed problematic input:

```xml
<ul><li>Main point<p>Important detail</p></li></ul>
```

The writer could omit `Important detail` while reporting success. This tested representation preserved the text order by adding a nested bullet:

```xml
<ul><li>Main point<ul><li>Important detail</li></ul></li></ul>
```

Inspect the fetched XML tree, not a regex over arbitrary markup. Preserve text, inline formatting, child order and tail text. Confirm source-to-prepared text equality before uploading. Apply only to direct paragraph children of list items, not paragraphs inside table cells or unrelated blocks. Mixed paragraphs containing media need their own readback check.

For an existing target, diagnose the missing content from the stored source snapshot and current readback. Prefer targeted repair when block boundaries are reliable. Full-body rebuilding was verified only for newly generated, owned migration targets with preserved snapshots and no intervening edits. This is not permission to overwrite unrelated user content, comments or another editor's changes. Recheck current owner, edit permission and content before repair; fetch again afterward. Record the list-format adjustment as a transformation.

## Three-way evidence

Keep immutable source XML plus reference map/revision, prepared target XML plus transformations/omissions, and actual target readback. Check source → prepared for intentional transformations, then prepared → target for write fidelity. Comparing only prepared → target can certify content already lost by the transformation.

Remove original block IDs for new objects. Resolve media references explicitly. Rebuild in-scope document links after target IDs exist. Keep out-of-scope references identified as source links; do not expand migration scope by following them. If cross-app user identities cannot be resolved, use display-name text with a declared limitation instead of emitting incorrect mentions or sending notifications.

## Verification rules

- Compare complete prose streams and investigate differences. Whitespace-normalized equality helps locate missing text but is insufficient for code, formulas, tables or ordering.
- Compare code line order and indentation on nonblank lines. This service version removed trailing whitespace and indentation on blank lines. Tolerate only observed nonsemantic normalization, retaining raw evidence; never strip all code whitespace.
- Check headings, table/row/cell structure, code blocks, checkboxes, formulas and resources. Counts alone do not prove content, order or cell alignment; check those too.
- Compare link destinations and retain raw hrefs in private evidence. Percent encoding, including nested encodings, may be normalized by the service. Decoded-string similarity is diagnostic, not a universal proof of URL equivalence. Do not rewrite signed URLs or query parameters on that basis; review unresolved differences.
- Re-download target images/attachments using the target user and compare SHA256 against source downloads. Readability alone is not byte integrity. If the platform recompresses an image, report hash inequality and validate the conversion separately rather than claiming a hash match.
- Validate actual Wiki node, parent, library space and owner. Default creation can land outside 我的文档库. Reused documents may stay in place and be linked from the new index when this is explicitly planned.
- Compare source revisions at snapshot and final check. Refresh changed documents or report the backed-up revision instead of claiming a current snapshot.

## Large files and embedded resources

When the user allows skipping large files, state a concrete threshold and persist it with the user instruction. Inventory sizes first: a small number of videos can dominate volume. Put filename, size and skip reason at the original content position and in the final report. Do not skip a whole page because one attachment is large.

A board preview preserves a static image, not editable board structure. A sheet snapshot preserves read data, not the original formulas, formatting or synchronization. Read the complete relevant view and check truncation; a Docx table must preserve cells and order. Do not read unrelated workbook tabs just because they share the workbook token. State these limits in the target index and final report. Unmigrated content without an authorized omission remains unresolved.

## Recovery and publication

Create/write sequentially and checkpoint every returned ID. An interrupted `creating` state, like `unknown_write`, requires remote reconciliation before retrying. A local status update is not proof of cloud success.

Keep task executors, raw content, account/resource IDs, receipts and media in private runtime storage. Portable skills contain distilled procedure and synthetic examples only. Report newly created/reused documents, additional index pages, byte-verified resources, authorized skips, static conversions, remaining failures and exact scope. Do not call the result native or lossless when transformations or omitted comments/history remain.
