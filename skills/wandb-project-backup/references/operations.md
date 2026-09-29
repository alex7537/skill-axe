# Commands and verified evidence

Run commands from the skill directory. Substitute the user-approved entity, projects and output directory; do not infer scope from examples.

```bash
python3 -m venv /tmp/wandb-backup-venv
/tmp/wandb-backup-venv/bin/python -m pip install 'wandb==0.30.0'
/tmp/wandb-backup-venv/bin/wandb login --cloud --verify

/tmp/wandb-backup-venv/bin/python scripts/backup.py inventory \
  --root /path/to/local-backups --snapshot snapshot-id \
  --entity team-slug --project project-a --project project-b

/tmp/wandb-backup-venv/bin/python scripts/backup.py export \
  --root /path/to/local-backups --snapshot snapshot-id \
  --entity team-slug --project project-a --project project-b

python3 scripts/finalize.py \
  --snapshot /path/to/local-backups/snapshot-id \
  --archive /path/to/local-backups/snapshot-id.zip
```

Keep the same entity/project order on resume. Inventory refuses to overwrite an existing inventory. Use distinct snapshot names. The finalizer uses only Python's standard library, requires no W&B login and must not be run with `python -O` (its invariant checks use assertions). Source files and SHA256SUMS remain in the snapshot after packaging. The archive is an offline data export, not a native W&B database restore image.

The API credential stays in the local W&B credential store. Avoid recording command transcripts containing tokens. The generic helper pins the cloud API host and does not implement self-hosted servers; adapt explicitly when requested.

## Dated evidence: 2026-09-29

The originating cloud export was verified on macOS using Python 3.14 and W&B SDK 0.30.0. Three selected projects yielded 45 Runs (two projects empty), 102,228 unsampled metric rows, 350 uploaded files and 59 Artifact versions (50 history, 9 events). No model checkpoint was found among the enumerated JSON/YAML/log/text files and history/event Artifacts. Export errors were zero; file checksums, Artifact verification, JSONL counts and ZIP integrity passed.

These are historical acceptance evidence, not defaults for another account. No account identifiers, experiment names, raw payloads or credentials belong in this portable reference. Parameterized scripts retain the proven API operations; offline revalidation exercises the exported snapshot, while another account/network still requires a live run.

## Primary references

- [Project visibility and access](https://docs.wandb.ai/guides/hosting/iam/access-management/restricted-projects/)
- [Export run data and unsampled history](https://docs.wandb.ai/models/track/public-api-guide)
- [Artifact download and verification](https://docs.wandb.ai/models/artifacts/download-and-use-an-artifact)

Consult current documentation and installed source when behavior changes; historical evidence does not establish current platform policy.
