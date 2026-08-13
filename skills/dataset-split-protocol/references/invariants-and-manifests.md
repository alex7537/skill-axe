# Split invariants and manifests

## Required identities

Parameterize field names. Typical levels are:

- group: scene/session/run/episode/volume;
- sample: clip/trajectory item;
- resource: recording, archive, Zarr group, file, or record ID;
- optional temporal identity: timestamp interval.

## Hard invariants

- Every active role pair is group-disjoint and sample-disjoint.
- Underlying resources do not cross roles when resource identity implies correlation.
- Samples are unique within each role.
- Active roles and quarantine are disjoint.
- Active plus quarantine conserve the eligible source set.
- Each sample's parent group owns exactly one role.
- Repaired samples retain historical role ownership.
- Evaluation frames belong to the frozen valid-frame manifest.
- Holdout manifest hash and state match the seal record.

Validate independently of generation so shared assumptions cannot hide a bug.

## Role manifest JSONL

```json
{"group_id":"g1","sample_id":"c1","resource_id":"r1","role":"train","sample_weight":1}
```

## Split summary

```json
{
  "schema_version": 1,
  "source_manifest_sha256": "<sha256>",
  "group_key": "group_id",
  "sample_key": "sample_id",
  "allocation": "sample_weighted_whole_group",
  "seed": 42,
  "roles": {
    "train": {"manifest":"train.jsonl","sha256":"<sha256>","sealed":false},
    "val": {"manifest":"val.jsonl","sha256":"<sha256>","sealed":false},
    "diagnostic": {"manifest":"diagnostic.jsonl","sha256":"<sha256>","sealed":false},
    "holdout": {"manifest":"holdout.jsonl","sha256":"<sha256>","sealed":true}
  },
  "exposure_policy": "seen_once_is_contaminated"
}
```

Store full group lists in role manifests rather than only aggregate counts. Include unavailable checks and soft-overlap risks in the human-readable report.
