# Label-audit manifest contract

## Frame scan JSONL

```json
{"group_id":"g1","sample_id":"c1","frame_idx":12,"foreground_pixels":0,"nonzero_ids":[],"readable":true}
```

The project adapter may add paths, shapes, dtypes, timestamps, or source-record IDs. Stable identity fields and measured facts are mandatory.

## Label decision JSONL

```json
{
  "group_id": "g1",
  "sample_id": "c1",
  "classification": "confirmed_missing",
  "confidence": "confirmed",
  "affected_ranges": [[10, 18]],
  "evidence_ref": "audit/c1_10_18.png",
  "evidence_sha256": "<sha256>",
  "original_role": "train",
  "rules_sha256": "<sha256>",
  "status": "awaiting_relabel"
}
```

## Valid-frame JSONL

```json
{
  "group_id": "g1",
  "sample_id": "c1",
  "frame_start": 0,
  "frame_end": 99,
  "valid_ranges": [[0, 9], [19, 99]],
  "invalid_ranges": [{"range":[10,18],"reason":"partial_annotation_hole"}],
  "true_empty_ranges": []
}
```

Hash the classification rules before generating decisions. Keep evidence references relative and portable. Never store credentials or signed access links.
