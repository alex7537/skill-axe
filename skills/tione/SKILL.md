---
name: tione
description: "Use this skill for Tencent Cloud TI-ONE / Tione task-style modeling, Notebook/development-machine, and online service work: querying running training tasks, task details, pods, pod login URLs, logs, development machines, billing/resource groups, and summarizing or drafting CreateTrainingTask/CreateNotebook/CreateModelService payloads. Also use when the user says 任务式建模, 开发机, Notebook, TI-ONE, Tione, 在线服务, CreateTrainingTask, DescribeTrainingTasks, DescribeNotebooks, or asks to inspect Tione jobs/dev machines."
---

# TI-ONE / Tione

## Scope

Use this skill for Tencent Cloud TI-ONE API 3.0 operations around:

- Task-style modeling / training tasks: list, describe, pods, pod URL, logs.
- Notebook / development machines: list, describe, presigned URL, summarize creation parameters.
- Resource lookup: billing specs and resource groups.
- Online services: summarize or draft custom-image service payloads.

Prefer read-only calls unless the user explicitly asks to create, start, stop, modify, or delete a resource. Never print Tencent Cloud secrets, W&B keys, image secrets, or auth tokens.

## Credentials

Credential lookup order:

1. Environment variables: `TENCENTCLOUD_SECRET_ID`, `TENCENTCLOUD_SECRET_KEY`, `TENCENTCLOUD_REGION`
2. Local config file: `~/.codex/skills/tione/config.json` or `~/.codex/tione.json`
3. macOS Keychain fallback

Do not hardcode secrets in commands. Existing macOS Keychain entries are still supported:

```text
codex:tencentcloud:secret-id
codex:tencentcloud:secret-key
codex:tencentcloud:region
```

Default region in this workspace is usually `ap-shanghai`.

## Quick Commands

Use the bundled script when possible:

```bash
python3 ~/.codex/skills/tione/scripts/tione_api.py list --status RUNNING --name-contains liyueheng
python3 ~/.codex/skills/tione/scripts/tione_api.py describe train-...
python3 ~/.codex/skills/tione/scripts/tione_api.py pods train-...
python3 ~/.codex/skills/tione/scripts/tione_api.py logs --service TRAIN --service-id train-... --pod-name 'train-...*'
python3 ~/.codex/skills/tione/scripts/tione_api.py notebooks --creator liyueheng
python3 ~/.codex/skills/tione/scripts/tione_api.py notebook nb-...
python3 ~/.codex/skills/tione/scripts/tione_api.py encode-start-cmd --worker-start-cmd @launch.sh
python3 ~/.codex/skills/tione/scripts/tione_api.py raw CreateTrainingTask --payload @payload.json
python3 ~/.codex/skills/tione/scripts/tione_api.py raw StartTrainingTask --payload '{"Id":"train-..."}'
```

The script signs Tencent Cloud API 3.0 requests directly with stdlib Python, reads credentials from env/config/keychain, and redacts common sensitive fields.

## Workflow

For "查运行中的任务":

1. Call `list --status RUNNING`.
2. If the user gives a name/person, filter by task name, resource group, and creator fields. If creator is not visible in list output, call `describe` on candidates and inspect `SubUinName`.
3. Report task id, name, status, creator, resource group, start time in CST, runtime, and message/failure reason if present.

For "完整参数":

1. Call `describe <task-id>`.
2. Summarize `ResourceConfigInfos`, `ImageInfo`, `StartCmdInfo`, `DataConfigs`, `Output`, `LogEnable`, `ExposeNetworkConfig`, `Envs`, `TuningParameters`, and `LatestInstanceId`.
3. If the user needs the final Hydra/runtime config, inspect the task's mounted run directory over SSH or from logs; `DescribeTrainingTask` only returns the submitted launch configuration.

For logs:

1. Get `LatestInstanceId` from `describe`.
2. Get pod names from `pods`.
3. Call `logs --service TRAIN --service-id <LatestInstanceId> --pod-name '<pod>*'`.

For "查开发机 / Notebook":

1. Call `notebooks`; add `--creator liyueheng`, `--status Running`, or `--name-contains ...` when the user gives a filter.
2. For creation parameters, call `notebook <nb-id>` or use `notebooks --details` and summarize `ResourceConf`, `ImageInfo`, `DataConfigs`, `VolumeSourceType`, `VpcId`, `SubnetId`, `RootAccess`, `DirectInternetAccess`, `AutoStopping`, `SSHConfig`, `ExposePortConfig`, `SystemDiskConfig`, `LogEnable`, and timestamps.
3. Do not print `PublicKey`, image secrets, or presigned URLs with `authToken` unredacted.

For "创建任务式建模 / CreateTrainingTask":

1. Read `references/api-reference.md` section `CreateTrainingTask` before drafting the payload.
2. Draft first; do not call `CreateTrainingTask` until the user explicitly confirms the exact payload or intended task.
3. Prefer deriving resource group, image, VPC/subnet, data mounts, and SSH/port exposure from a known-good task via `describe <train-id>` or `notebook <nb-id>`.
4. Required fields are `Name`, `ChargeType`, and `ResourceConfigInfos`. Usually also include `TrainingMode`, `ResourceGroupId`, `ImageInfo`, `DataConfigs`, `VpcId`, `SubnetId`, and `EncodedStartCmdInfo`.
5. Use `EncodedStartCmdInfo` for multiline shell scripts. It is base64 of JSON shaped like `{"StartCmd":"","PsStartCmd":"","WorkerStartCmd":"bash ..."}`. Avoid embedding long-lived secrets in launch commands; if unavoidable, never print them unredacted.
6. After creation, record the returned `Id`, then use `StartTrainingTask` only if the created task is not already starting/running and the user asked to start it.
7. Verify with `describe <train-id>`, `pods <train-id>`, and logs using `LatestInstanceId`.

For online service planning:

1. Prefer `CreateModelService` over training tasks for persistent web services.
2. Use custom image, `ServicePort`, `CommandBase64`, `VolumeMount(s)`, health probe, manual replicas, and logging.
3. For dataset labeling Flask service, remember the path issue: expose data at both `/share_data/hetianjia/psi-dc-prod-data` and `/mnt/cos/psi-dc-prod-data` or create a symlink at startup.

## References

Read [references/api-reference.md](references/api-reference.md) when drafting payloads, checking field names, or needing official source links.
