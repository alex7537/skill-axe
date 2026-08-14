# TI-ONE API Reference Notes

These notes summarize the official Tencent Cloud TI-ONE API pages used in June 2026. Prefer these notes first; re-check official docs when an API rejects a field, a new field is needed, or the console behavior differs.

## Common API Settings

- Endpoint: `https://tione.tencentcloudapi.com`
- Service name for TC3 signing: `tione`
- API version: `2021-11-11`
- Common request headers: `X-TC-Action`, `X-TC-Version`, `X-TC-Region`, `X-TC-Timestamp`, `Authorization`
- Most relevant rate limits observed in docs: 20 req/s for training/resource/log APIs; some online-service describe APIs allow 50 req/s.

Official sources:

- API intro: https://cloud.tencent.com/document/product/851/75059
- API overview: https://cloud.tencent.com/document/product/851/75060
- Data structures: https://cloud.tencent.com/document/api/851/75051
- Online service intro/deploy docs used earlier: https://cloud.tencent.com/document/product/851/74139 and https://cloud.tencent.com/document/product/851/82291
- Notebook create/manage docs: https://cloud.tencent.com/document/product/851/74128 and https://cloud.tencent.com/document/product/851/74130

## Training Task APIs

### DescribeTrainingTasks

Source: https://cloud.tencent.com/document/api/851/75087

Use to list task-style modeling jobs.

Useful request fields:

```json
{
  "Limit": 50,
  "Offset": 0,
  "Order": "DESC",
  "OrderField": "UpdateTime",
  "Filters": [
    {"Name": "Status", "Values": ["RUNNING"]}
  ]
}
```

Filter names documented/observed: `Name`, `Id`, `Status`, `ResourceGroupId`, `Creator`, `ChargeType`, `CHARGE_STATUS`.

Useful statuses: `SUBMITTING`, `PENDING`, `STARTING`, `RUNNING`, `STOPPING`, `STOPPED`, `FAILED`, `SUCCEED`, `SUBMIT_FAILED`.

List results may not include `SubUinName`; call `DescribeTrainingTask` to verify creator.

### DescribeTrainingTask

Source: https://cloud.tencent.com/document/api/851/75089

Use for full submitted configuration and creator.

Request:

```json
{"Id": "train-..."}
```

Useful response fields:

- Identity/status: `Id`, `Name`, `Status`, `FailureReason`, `Message`
- Creator: `Uin`, `SubUin`, `SubUinName`, `Tags`
- Runtime: `CreateTime`, `StartTime`, `UpdateTime`, `EndTime`, `RuntimeInSeconds`
- Resources: `ChargeType`, `ResourceGroupId`, `ResourceGroupName`, `ResourceConfigInfos`
- Image/code: `ImageInfo`, `CodePackagePath`, `CodeRepos`
- Launch: `StartCmdInfo`, `TuningParameters`, `Envs`
- Data/network/logs: `DataSource`, `DataConfigs`, `Output`, `LogEnable`, `LogConfig`, `VpcId`, `SubnetId`, `ExposeNetworkConfig`
- Logs helper: `LatestInstanceId`

`StartCmdInfo` contains `StartCmd`, `PsStartCmd`, and `WorkerStartCmd`. For DDP worker jobs, the useful launch script is usually `WorkerStartCmd`.

### CreateTrainingTask

Source: https://cloud.tencent.com/document/api/851/117377
Official page checked: 2026-06-11. Tencent page last updated: 2026-04-29.

Use only after explicit user approval. Creates a training task; may not start it automatically in all flows.

Request basics:

- Action: `CreateTrainingTask`
- Version: `2021-11-11`
- Endpoint: `tione.tencentcloudapi.com`
- Rate limit in official docs: 20 req/s

Required request fields:

- Required: `Name`, `ChargeType`, `ResourceConfigInfos`

Common optional fields:

- Workspace/framework: `TiProjectId`, `FrameworkName`, `FrameworkVersion`, `FrameworkEnvironment`, `TrainingMode`
- Resource: `ResourceGroupId`, `ResourceConfigInfos`
- Image/code: `ImageInfo`, `CodePackagePath`, `CodeRepos`
- Launch: `StartCmdInfo` or `EncodedStartCmdInfo` (encoded wins if both present)
- Data: `DataSource`, `DataConfigs` (official docs say count <= 10)
- Network: `VpcId`, `SubnetId`, `ExposeNetworkConfig`
- Output/logging: `Output`, `LogEnable`, `LogConfig`
- Other: `TuningParameters`, `Envs`, `Tags`, `Remark`, `CallbackUrl`

Name constraints from official docs: <= 60 chars; Chinese/English letters, digits, `_`, `-`; must start with Chinese/English letter or digit.

`ChargeType` values used in docs/observed: `PREPAID` for resource-group prepaid, `POSTPAID_BY_HOUR` for pay-as-you-go.

`TrainingMode` examples from official docs: `PS_WORKER`, `DDP`, `MPI`, `HOROVOD`.

`DataSource` examples from official docs: `DATASET`, `COS`, `CFS`, `CFSTurbo`, `HDFS`, `GooseFSx`. In this workspace, mounted public data sources often appear in returned task details as `DataSourceType: PUBLIC_DATA_SOURCE` inside `DataConfigs`.

`ResourceConfigInfos` must describe each role, usually:

```json
[
  {
    "Role": "WORKER",
    "InstanceNum": 1,
    "InstanceType": "TI.S.MEDIUM.POST"
  }
]
```

For prepaid resource groups in this workspace, existing tasks often return explicit `Cpu`, `Memory`, `Gpu`, `GpuType`, `InstanceNum`, and empty `InstanceType`; copying a known-good existing task's `ResourceConfigInfos` can be more reliable than guessing.

`StartCmdInfo` shape:

```json
{
  "StartCmd": "",
  "PsStartCmd": "",
  "WorkerStartCmd": "bash -lc '...'"
}
```

For multiline launch scripts, prefer `EncodedStartCmdInfo`. Official docs state that if both `StartCmdInfo` and `EncodedStartCmdInfo` are configured, only `EncodedStartCmdInfo` takes effect.

Minimal shape for a custom-image DDP worker:

```json
{
  "Name": "job-name",
  "ChargeType": "PREPAID",
  "TrainingMode": "DDP",
  "ResourceGroupId": "rsg-...",
  "ResourceConfigInfos": [
    {"Role": "WORKER", "InstanceNum": 1, "InstanceType": "TI.S..."}
  ],
  "ImageInfo": {
    "ImageType": "TCR",
    "ImageUrl": "registry/repo:tag",
    "RegistryRegion": "ap-shanghai",
    "RegistryId": "tcr-..."
  },
  "EncodedStartCmdInfo": {
    "StartCmdInfo": "base64({\"StartCmd\":\"\",\"PsStartCmd\":\"\",\"WorkerStartCmd\":\"bash ...\"})"
  }
}
```

`EncodedStartCmdInfo.StartCmdInfo` is base64 of the JSON `StartCmdInfo` object, for example:

```bash
python3 - <<'PY'
import base64, json
cmd = {
    "StartCmd": "",
    "PsStartCmd": "",
    "WorkerStartCmd": "bash -lc 'cd /workspace && python train.py'",
}
print(base64.b64encode(json.dumps(cmd, separators=(",", ":")).encode()).decode())
PY
```

Typical create-and-start flow:

1. Draft payload and review it with the user.
2. After explicit confirmation, call:

```bash
python3 ~/.codex/skills/tione/scripts/tione_api.py raw CreateTrainingTask --payload @payload.json
```

3. Capture returned `Id`.
4. If needed and explicitly requested, call:

```bash
python3 ~/.codex/skills/tione/scripts/tione_api.py raw StartTrainingTask --payload '{"Id":"train-..."}'
```

5. Verify with `DescribeTrainingTask`, `DescribeTrainingTaskPods`, and `DescribeLogs`.

Create response:

```json
{
  "Id": "train-...",
  "RequestId": "..."
}
```

Common creation failures to check first: duplicate task name, insufficient resource group quota, inaccessible CFS/GooseFS/COS path, invalid image, invalid VPC/subnet, unsupported framework version, parameter length limit, or unsupported data config for bare-metal resource groups.

### StartTrainingTask

Source: https://cloud.tencent.com/document/api/851/117375

Use only after explicit user approval.

Request:

```json
{"Id": "train-..."}
```

### StopTrainingTask / DeleteTrainingTask

Listed in API overview. Treat as destructive/state-changing and ask for explicit confirmation with the exact task id before using.

### DescribeTrainingTaskPods

Source: https://cloud.tencent.com/document/api/851/75088

Request:

```json
{"Id": "train-..."}
```

Useful response fields: `PodNames`, `PodInfoList[].Name`, `IP`, `Status`, `StartTime`, `EndTime`, `ResourceConfigInfo`.

### DescribeTrainingTaskPodUrl

Source: https://cloud.tencent.com/document/api/851/131906

Request:

```json
{"PodName": "train-...-launcher"}
```

Returns `PodUrl`. This is not the same as the SSH command shown in `ExposeNetworkConfig.SSHConfig.PodSSHInfo`; use task detail when SSH info is needed.

### DescribeLogs

Source: https://cloud.tencent.com/document/api/851/117840

Use for task-style modeling logs, Notebook logs, online service logs, and batch logs.

Training log request:

```json
{
  "Service": "TRAIN",
  "ServiceId": "LatestInstanceId from DescribeTrainingTask",
  "PodName": "pod-name-or-prefix*",
  "StartTime": "2026-06-11T00:00:00+08:00",
  "EndTime": "2026-06-11T23:59:59+08:00",
  "Limit": 100,
  "Order": "DESC",
  "OrderField": "Timestamp",
  "Filters": [{"Name": "Key", "Values": ["ERROR"]}]
}
```

`Service` enum: `TRAIN`, `NOTEBOOK`, `INFER`, `BATCH`. For training, `ServiceId` comes from `TrainingTaskDetail.LatestInstanceId`; `PodName` comes from `DescribeTrainingTaskPods`.

## Resource APIs

### DescribeBillingSpecs

Source: https://cloud.tencent.com/document/api/851/112648

Use to discover valid postpaid/prepaid specs.

Request fields:

```json
{
  "ChargeType": "POSTPAID_BY_HOUR",
  "TaskType": "TRAIN",
  "ResourceType": "GPU"
}
```

`ResourceType` examples: `CALC`, `CPU`, `GPU`, `GPU-SW`.

### DescribeBillingResourceGroups

Source: https://cloud.tencent.com/document/api/851/75065

Use to list resource groups and free/total resources.

Request fields:

```json
{
  "Offset": 0,
  "Limit": 20,
  "SearchWord": "<creator>",
  "DontShowInstanceSet": true
}
```

Useful filters: `ResourceGroupId`, `ResourceGroupName`, `AvailableNodeCount`.

## Notebook / Development Machine APIs

The TI-ONE console's "开发机" feature is represented by Notebook APIs.

API overview source: https://cloud.tencent.com/document/product/851/75060

### DescribeNotebooks

Source: https://cloud.tencent.com/document/api/851/95653

Use to list development machines.

Request shape:

```json
{
  "Offset": 0,
  "Limit": 50,
  "Order": "DESC",
  "OrderField": "UpdateTime",
  "Filters": [
    {"Name": "Status", "Values": ["Running"]}
  ]
}
```

Documented filter names:

- `Name`
- `Id`
- `Status`: `Starting`, `Running`, `Stopped`, `Stopping`, `Failed`, `SubmitFailed`
- `Creator`: creator uin
- `ChargeType`: `PREPAID`, `POSTPAID_BY_HOUR`
- `ChargeStatus`
- `DefaultCodeRepoId`
- `AdditionalCodeRepoId`
- `LifecycleScriptId`

In this workspace, creator filtering has been observed to be unreliable for some calls; prefer paging through notebooks and filtering locally by `SubUinName` or `SubUin`.

Useful list/detail fields:

- Identity/status: `Id`, `Name`, `Status`, `Message`, `FailureReason`
- Creator/operator: `SubUin`, `SubUinName`, `LatestOperatorInfo`
- Resource: `ChargeType`, `ResourceConf`, `ResourceGroupId`, `ResourceGroupName`, `InstanceTypeAlias`
- Runtime: `CreateTime`, `StartTime`, `UpdateTime`, `StopTime`, `RuntimeInSeconds`
- Image/storage/network: `ImageInfo`, `VolumeSourceType`, `VolumeSizeInGB`, `DataConfigs`, `VpcId`, `SubnetId`
- Access: `SSHConfig`, `ExposePortConfig`, `DirectInternetAccess`, `RootAccess`
- Lifecycle: `AutoStopping`, `AutomaticStopTime`, `SystemDiskConfig`, `LifecycleScriptId`

### DescribeNotebook

Source: https://cloud.tencent.com/document/api/851/95662

Request:

```json
{"Id": "nb-..."}
```

Use for the full creation/runtime configuration of one dev machine.

### CreateNotebook

Source: https://cloud.tencent.com/document/api/851/95658

Use only after explicit user approval.

Required fields:

- `Name`
- `ChargeType`
- `ResourceConf`
- `LogEnable`
- `RootAccess`
- `AutoStopping`
- `DirectInternetAccess`

Common optional fields:

- `ResourceGroupId`, `VpcId`, `SubnetId`
- `VolumeSourceType`, `VolumeSizeInGB`, `VolumeSourceCFS`, `VolumeSourceGooseFS`
- `LogConfig`
- `LifecycleScriptId`
- `DefaultCodeRepoId`, `AdditionalCodeRepoIds`
- `AutomaticStopTime`
- `Tags`
- `DataConfigs`
- `ImageInfo`, `ImageType`
- `SSHConfig`
- `Description`

Minimal custom-image shape:

```json
{
  "Name": "dev-name",
  "ChargeType": "PREPAID",
  "ResourceGroupId": "rsg-...",
  "ResourceConf": {
    "Cpu": 10000,
    "Memory": 102400,
    "Gpu": 800,
    "GpuType": "HCC-A800"
  },
  "ImageInfo": {
    "ImageType": "TCR",
    "ImageUrl": "registry/repo:tag",
    "RegistryRegion": "ap-shanghai",
    "RegistryId": "tcr-..."
  },
  "ImageType": "TCR",
  "DataConfigs": [
    {
      "MappingPath": "/share_data/<creator>",
      "DataSourceType": "PUBLIC_DATA_SOURCE",
      "PublicDataSource": {"DataSourceId": "dsrc-...", "SubPath": "/"},
      "ReadOnly": false
    }
  ],
  "RootAccess": true,
  "AutoStopping": false,
  "DirectInternetAccess": true,
  "LogEnable": false
}
```

### StartNotebook / StopNotebook / DeleteNotebook / ModifyNotebook

Listed in the official API overview. These are state-changing; ask for explicit confirmation with the exact `nb-...` id before using.

### CreatePresignedNotebookUrl

Source: https://cloud.tencent.com/document/api/851/104306

Request:

```json
{"Id": "nb-..."}
```

Returns `AuthorizedUrl` containing an `authToken`. Treat it as sensitive; do not print the raw URL unless the user explicitly needs it, and redact `authToken` in normal summaries.

### DescribeBuildInImages

Listed in the API overview. Use to discover system images for Notebook creation.

## Online Service APIs

### CreateModelService

Source: https://cloud.tencent.com/document/product/851/82291

Use only after explicit user approval. Prefer online service for persistent web apps such as labeling services.

Important fields:

- Naming: `ServiceGroupId`, `ServiceGroupName`, `ServiceDescription`, `NewVersion`
- Billing/resources: `ChargeType`, `ResourceGroupId`, `InstanceType`, `Resources`, `ScaleMode`, `Replicas`, `HorizontalPodAutoscaler`
- Runtime: `ImageInfo`, `ModelInfo`, `Env`, `Command`, `CommandBase64`, `ServicePort`
- Storage: `VolumeMount`, `VolumeMounts`
- Network/gateway: `AuthorizationEnable`, `GatewayConfig`, `ServiceEIP`, `GrpcEnable`
- Health/lifecycle: `HealthProbe`, `TerminationGracePeriodSeconds`, `PreStopCommand`, `RollingUpdate`
- Logs/limits: `LogEnable`, `LogConfig`, `GatewayLogConfig`, `ServiceLimit`

For custom-image Flask services:

```json
{
  "ServiceGroupName": "dataset-label-web",
  "ChargeType": "POSTPAID_BY_HOUR",
  "InstanceType": "TI.S.LARGE.POST",
  "ImageInfo": {
    "ImageType": "TCR",
    "ImageUrl": "registry/repo:tag",
    "RegistryRegion": "ap-shanghai",
    "RegistryId": "tcr-..."
  },
  "ScaleMode": "MANUAL",
  "Replicas": 1,
  "ServicePort": 8080,
  "CommandBase64": "base64(bash -lc '...')",
  "LogEnable": true,
  "AuthorizationEnable": false
}
```

For the <application-repository> labeling service, a practical startup command is:

```bash
bash -lc '
set -e
mkdir -p /mnt/cos /share_data/<data-owner>
ln -sfn /share_data/<data-owner>/<dataset> /mnt/cos/<dataset>
cd /root/codes/<application-repository>
exec bash start_web_server.sh 8080
'
```

Use `CommandBase64` if the command contains quotes/newlines.

## Useful Data Structures

Source: https://cloud.tencent.com/document/api/851/75051

- `EnvVar`: `{ "Name": "...", "Value": "..." }`
- `ExposeNetworkConfig`: includes `SSHConfig` and `ExposePortConfig`; training-task port exposure lives here.
- `ExposePortConfig`: `Enable`, `VpcId`, `ClbId`, `ClbHost`, and port elements in returned detail.
- `ExecAction`, `HTTPGetAction`, `HealthProbe`: online-service probes.
- `ImageInfo`: `ImageType`, `ImageUrl`, `RegistryRegion`, `RegistryId`, returned `ImageSecret`.
- `ResourceConfigInfo`: `Role`, `Cpu`, `Memory`, `GpuType`, `Gpu`, `InstanceType`, `InstanceNum`, `RDMAConfig`.

## Safety Rules

- Read-only by default: describe/list/log APIs are OK when the user asks to inspect.
- Confirm before: `CreateTrainingTask`, `StartTrainingTask`, `StopTrainingTask`, `DeleteTrainingTask`, `CreateModelService`, `ModifyModelService`, `DeleteModelService*`, auth token changes.
- Redact: values whose key or content includes `secret`, `token`, `password`, `passwd`, `pwd`, `api_key`, `access_key`, `credential`, `authorization`, `wandb_`, `AKID`.
- If the user pasted a secret into chat, store it in Keychain if asked, then remind them to rotate/disable it.
