#!/usr/bin/env python3
"""Small Tencent Cloud TI-ONE API helper.

Credential lookup order:
  1. Environment variables
  2. Local Codex JSON config files
  3. macOS Keychain (if `security` is available)

Only uses Python stdlib. Output is redacted by default.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any


SERVICE = "tione"
HOST = "tione.tencentcloudapi.com"
ENDPOINT = f"https://{HOST}"
VERSION = "2021-11-11"

SENSITIVE_KEY = re.compile(
    r"(secret|token|password|passwd|pwd|public[_-]?key|api[_-]?key|access[_-]?key|credential|authorization)",
    re.I,
)
SENSITIVE_VALUE = re.compile(
    r"(wandb_[A-Za-z0-9_\-]+|AKID[A-Za-z0-9]+|authToken=[^&\s]+|(?i:secretid)\s*[:=]\s*\S+|(?i:secretkey)\s*[:=]\s*\S+)"
)

CONFIG_CANDIDATES = [
    Path.home() / ".codex" / "skills" / "tione" / "config.json",
    Path.home() / ".codex" / "tione.json",
]


def keychain(service: str) -> str:
    return subprocess.check_output(
        ["security", "find-generic-password", "-s", service, "-a", "codex", "-w"],
        text=True,
    ).strip()


def load_local_config() -> dict[str, Any]:
    for path in CONFIG_CANDIDATES:
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise SystemExit(f"Config file must be a JSON object: {path}")
        nested = raw.get("tencentcloud")
        if isinstance(nested, dict):
            raw = nested
        return raw
    return {}


def read_credential(
    *,
    env_var: str,
    config: dict[str, Any],
    config_key: str,
    keychain_service: str,
    default: str | None = None,
    required: bool = True,
) -> str:
    value = os.getenv(env_var)
    if value:
        return value
    config_value = config.get(config_key)
    if config_value not in (None, ""):
        return str(config_value)
    if shutil.which("security"):
        try:
            return keychain(keychain_service)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    if default is not None:
        return default
    if required:
        raise SystemExit(
            "Missing Tencent Cloud credential. Set environment variables "
            f"({env_var}) or create ~/.codex/skills/tione/config.json."
        )
    return ""


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


class TioneClient:
    def __init__(self, region: str | None = None) -> None:
        config = load_local_config()
        self.secret_id = read_credential(
            env_var="TENCENTCLOUD_SECRET_ID",
            config=config,
            config_key="secret_id",
            keychain_service="codex:tencentcloud:secret-id",
        )
        self.secret_key = read_credential(
            env_var="TENCENTCLOUD_SECRET_KEY",
            config=config,
            config_key="secret_key",
            keychain_service="codex:tencentcloud:secret-key",
        )
        self.region = region or read_credential(
            env_var="TENCENTCLOUD_REGION",
            config=config,
            config_key="region",
            keychain_service="codex:tencentcloud:region",
            default="ap-shanghai",
            required=False,
        )

    def call(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        timestamp = int(time.time())
        date = dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).strftime("%Y-%m-%d")
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        canonical_request = "\n".join(
            [
                "POST",
                "/",
                "",
                f"content-type:application/json; charset=utf-8\nhost:{HOST}\n",
                "content-type;host",
                hashlib.sha256(body).hexdigest(),
            ]
        )
        credential_scope = f"{date}/{SERVICE}/tc3_request"
        string_to_sign = "\n".join(
            [
                "TC3-HMAC-SHA256",
                str(timestamp),
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )

        secret_date = sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, SERVICE)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            f"TC3-HMAC-SHA256 Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders=content-type;host, Signature={signature}"
        )
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": HOST,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": VERSION,
            "X-TC-Region": self.region,
        }
        request = urllib.request.Request(ENDPOINT, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                wrapper = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            wrapper = json.loads(exc.read().decode("utf-8"))
        response = wrapper.get("Response", wrapper)
        if "Error" in response:
            raise SystemExit(json.dumps(response["Error"], ensure_ascii=False, indent=2))
        return response


def redact(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {k: ("<redacted>" if SENSITIVE_KEY.search(k) else redact(v, k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    if isinstance(value, str):
        if SENSITIVE_KEY.search(key):
            return "<redacted>"
        return SENSITIVE_VALUE.sub("<redacted>", value)
    return value


def iso_to_cst(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S CST")
    except ValueError:
        return value


def human_runtime(seconds: Any) -> str:
    seconds = int(seconds or 0)
    return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m{seconds % 60:02d}s"


def compact_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "Id": task.get("Id"),
        "Name": task.get("Name"),
        "Status": task.get("Status"),
        "SubUinName": task.get("SubUinName"),
        "ResourceGroupName": task.get("ResourceGroupName"),
        "ResourceGroupId": task.get("ResourceGroupId"),
        "TrainingMode": task.get("TrainingMode"),
        "FrameworkName": task.get("FrameworkName"),
        "StartTimeCST": iso_to_cst(task.get("StartTime")),
        "UpdateTimeCST": iso_to_cst(task.get("UpdateTime")),
        "Runtime": human_runtime(task.get("RuntimeInSeconds")),
        "FailureReason": task.get("FailureReason") or "",
        "Message": task.get("Message") or "",
    }


def compact_data_configs(configs: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for config in configs or []:
        entry: dict[str, Any] = {
            "MappingPath": config.get("MappingPath"),
            "DataSourceType": config.get("DataSourceType"),
            "ReadOnly": config.get("ReadOnly"),
        }
        for key in [
            "PublicDataSource",
            "GooseFSSource",
            "CFSSource",
            "CFSTurboSource",
            "COSSource",
            "CBSSource",
            "LocalDiskSource",
            "DataSetSource",
            "HostPathSource",
            "PreloadFileSource",
        ]:
            value = config.get(key)
            if not value:
                continue
            if isinstance(value, dict):
                compact_value = {k: v for k, v in value.items() if v not in (None, "", [], {})}
                if compact_value:
                    entry[key] = compact_value
            else:
                entry[key] = value
        output.append(entry)
    return output


def compact_notebook(notebook: dict[str, Any], include_creation: bool = False) -> dict[str, Any]:
    image = notebook.get("ImageInfo") or {}
    ssh = notebook.get("SSHConfig") or {}
    expose = notebook.get("ExposePortConfig") or {}
    output: dict[str, Any] = {
        "Id": notebook.get("Id"),
        "Name": notebook.get("Name"),
        "Status": notebook.get("Status"),
        "SubUin": notebook.get("SubUin"),
        "SubUinName": notebook.get("SubUinName"),
        "ChargeType": notebook.get("ChargeType"),
        "ResourceGroupId": notebook.get("ResourceGroupId"),
        "ResourceGroupName": notebook.get("ResourceGroupName"),
        "ResourceConf": notebook.get("ResourceConf"),
        "InstanceTypeAlias": notebook.get("InstanceTypeAlias"),
        "ImageInfo": {
            key: image.get(key)
            for key in ["ImageType", "ImageUrl", "RegistryRegion", "RegistryId", "ImageName", "EntryPoint", "WorkDir"]
            if image.get(key) not in (None, "")
        },
        "VolumeSourceType": notebook.get("VolumeSourceType"),
        "VolumeSizeInGB": notebook.get("VolumeSizeInGB"),
        "VpcId": notebook.get("VpcId"),
        "SubnetId": notebook.get("SubnetId"),
        "RootAccess": notebook.get("RootAccess"),
        "DirectInternetAccess": notebook.get("DirectInternetAccess"),
        "LogEnable": notebook.get("LogEnable"),
        "AutoStopping": notebook.get("AutoStopping"),
        "AutomaticStopTime": notebook.get("AutomaticStopTime"),
        "CreateTimeCST": iso_to_cst(notebook.get("CreateTime")),
        "StartTimeCST": iso_to_cst(notebook.get("StartTime")),
        "UpdateTimeCST": iso_to_cst(notebook.get("UpdateTime")),
        "StopTimeCST": iso_to_cst(notebook.get("StopTime")),
        "Runtime": human_runtime(notebook.get("RuntimeInSeconds")),
        "FailureReason": notebook.get("FailureReason") or "",
        "Message": notebook.get("Message") or "",
        "LatestOperatorInfo": notebook.get("LatestOperatorInfo"),
    }
    if include_creation:
        output.update(
            {
                "SystemDiskConfig": notebook.get("SystemDiskConfig"),
                "DataConfigs": compact_data_configs(notebook.get("DataConfigs")),
                "SSHConfig": {
                    "Enable": ssh.get("Enable"),
                    "Port": ssh.get("Port"),
                    "LoginCommand": ssh.get("LoginCommand"),
                    "PodSSHInfo": ssh.get("PodSSHInfo"),
                    "SSHUserName": ssh.get("SSHUserName"),
                    "IP": ssh.get("IP"),
                }
                if ssh
                else None,
                "ExposePortConfig": {
                    "Enable": expose.get("Enable"),
                    "VpcId": expose.get("VpcId"),
                    "ClbId": expose.get("ClbId"),
                    "ClbHost": expose.get("ClbHost"),
                    "PortElements": expose.get("PortElements"),
                }
                if expose
                else None,
            }
        )
    return output


def iter_tasks(client: TioneClient, status: list[str] | None) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    filters = [{"Name": "Status", "Values": status}] if status else []
    offset = 0
    while True:
        payload: dict[str, Any] = {
            "Limit": 50,
            "Offset": offset,
            "Order": "DESC",
            "OrderField": "UpdateTime",
        }
        if filters:
            payload["Filters"] = filters
        response = client.call("DescribeTrainingTasks", payload)
        batch = response.get("TrainingTaskSet") or []
        tasks.extend(batch)
        offset += len(batch)
        if not batch or offset >= int(response.get("TotalCount") or 0):
            break
    return tasks


def iter_notebooks(client: TioneClient) -> list[dict[str, Any]]:
    notebooks: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = client.call(
            "DescribeNotebooks",
            {
                "Limit": 50,
                "Offset": offset,
                "Order": "DESC",
                "OrderField": "UpdateTime",
            },
        )
        batch = response.get("NotebookSet") or []
        notebooks.extend(batch)
        offset += len(batch)
        if not batch or offset >= int(response.get("TotalCount") or 0):
            break
    return notebooks


def command_list(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    tasks = iter_tasks(client, args.status)
    needle = (args.name_contains or "").lower()
    creator = (args.creator or "").lower()
    group = (args.resource_group_contains or "").lower()
    if needle:
        tasks = [
            t
            for t in tasks
            if needle in (t.get("Name") or "").lower()
            or needle in (t.get("ResourceGroupName") or "").lower()
            or needle in (t.get("SubUinName") or "").lower()
        ]
    if creator:
        # List responses may omit SubUinName. Describe candidates if needed.
        described = []
        for task in tasks:
            detail = task
            if "SubUinName" not in task:
                detail = client.call("DescribeTrainingTask", {"Id": task["Id"]}).get("TrainingTaskDetail") or task
            if creator in (detail.get("SubUinName") or "").lower():
                described.append(detail)
        tasks = described
    if group:
        tasks = [t for t in tasks if group in (t.get("ResourceGroupName") or "").lower()]
    return {"region": client.region, "count": len(tasks), "tasks": [compact_task(t) for t in tasks]}


def command_describe(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    return client.call("DescribeTrainingTask", {"Id": args.task_id}).get("TrainingTaskDetail")


def command_pods(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    return client.call("DescribeTrainingTaskPods", {"Id": args.task_id})


def command_pod_url(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    return client.call("DescribeTrainingTaskPodUrl", {"PodName": args.pod_name})


def command_logs(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    payload: dict[str, Any] = {
        "Service": args.service,
        "Limit": args.limit,
        "Order": args.order,
        "OrderField": "Timestamp",
    }
    if args.service_id:
        payload["ServiceId"] = args.service_id
    if args.pod_name:
        payload["PodName"] = args.pod_name
    if args.start_time:
        payload["StartTime"] = args.start_time
    if args.end_time:
        payload["EndTime"] = args.end_time
    if args.key:
        payload["Filters"] = [{"Name": "Key", "Values": args.key}]
    return client.call("DescribeLogs", payload)


def command_notebooks(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    notebooks = iter_notebooks(client)
    if args.status:
        statuses = {status.lower() for status in args.status}
        notebooks = [nb for nb in notebooks if (nb.get("Status") or "").lower() in statuses]
    if args.name_contains:
        needle = args.name_contains.lower()
        notebooks = [
            nb
            for nb in notebooks
            if needle in (nb.get("Name") or "").lower()
            or needle in (nb.get("ResourceGroupName") or "").lower()
            or needle in (nb.get("SubUinName") or "").lower()
        ]
    if args.creator:
        creator = args.creator.lower()
        notebooks = [
            nb
            for nb in notebooks
            if creator in (nb.get("SubUinName") or "").lower() or creator == str(nb.get("SubUin") or "")
        ]
    if args.details:
        detailed = []
        for notebook in notebooks:
            detail = client.call("DescribeNotebook", {"Id": notebook["Id"]}).get("NotebookDetail") or notebook
            detailed.append(detail)
        notebooks = detailed
    return {
        "region": client.region,
        "count": len(notebooks),
        "notebooks": [compact_notebook(notebook, include_creation=args.details) for notebook in notebooks],
    }


def command_notebook(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    detail = client.call("DescribeNotebook", {"Id": args.notebook_id}).get("NotebookDetail")
    return compact_notebook(detail or {}, include_creation=not args.full) if not args.full else detail


def command_notebook_url(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    return client.call("CreatePresignedNotebookUrl", {"Id": args.notebook_id})


def command_raw(args: argparse.Namespace) -> Any:
    client = TioneClient(args.region)
    raw_payload = args.payload or "{}"
    if raw_payload.startswith("@"):
        raw_payload = open(raw_payload[1:], "r", encoding="utf-8").read()
    payload = json.loads(raw_payload)
    return client.call(args.action, payload)


def command_encode_start_cmd(args: argparse.Namespace) -> Any:
    def read_value(value: str | None) -> str:
        if not value:
            return ""
        if value.startswith("@"):
            return open(value[1:], "r", encoding="utf-8").read()
        return value

    payload = {
        "StartCmd": read_value(args.start_cmd),
        "PsStartCmd": read_value(args.ps_start_cmd),
        "WorkerStartCmd": read_value(args.worker_start_cmd),
    }
    encoded = base64.b64encode(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return {"EncodedStartCmdInfo": {"StartCmdInfo": encoded}}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tencent Cloud TI-ONE API helper")
    parser.add_argument("--region", help="Override region; defaults to Keychain region")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List training tasks")
    list_parser.add_argument("--status", action="append", help="Task status; can repeat")
    list_parser.add_argument("--name-contains", help="Match task name/resource group/creator substring")
    list_parser.add_argument("--creator", help="Match exact-ish creator substring via SubUinName")
    list_parser.add_argument("--resource-group-contains", help="Match resource group substring")
    list_parser.set_defaults(func=command_list)

    describe = sub.add_parser("describe", help="Describe a training task")
    describe.add_argument("task_id")
    describe.set_defaults(func=command_describe)

    pods = sub.add_parser("pods", help="List task pods")
    pods.add_argument("task_id")
    pods.set_defaults(func=command_pods)

    pod_url = sub.add_parser("pod-url", help="Get a pod login URL")
    pod_url.add_argument("pod_name")
    pod_url.set_defaults(func=command_pod_url)

    logs = sub.add_parser("logs", help="Describe logs")
    logs.add_argument("--service", default="TRAIN", choices=["TRAIN", "NOTEBOOK", "INFER", "BATCH"])
    logs.add_argument("--service-id")
    logs.add_argument("--pod-name")
    logs.add_argument("--start-time")
    logs.add_argument("--end-time")
    logs.add_argument("--limit", type=int, default=100)
    logs.add_argument("--order", default="DESC", choices=["ASC", "DESC"])
    logs.add_argument("--key", action="append", help="Keyword filter; can repeat")
    logs.set_defaults(func=command_logs)

    notebooks = sub.add_parser("notebooks", help="List Notebook/development machines")
    notebooks.add_argument("--status", action="append", help="Notebook status; can repeat")
    notebooks.add_argument("--name-contains", help="Match notebook name/resource group/creator substring")
    notebooks.add_argument("--creator", help="Match creator SubUinName substring or exact SubUin")
    notebooks.add_argument("--details", action="store_true", help="Fetch each matching notebook detail and include creation parameters")
    notebooks.set_defaults(func=command_notebooks)

    notebook = sub.add_parser("notebook", help="Describe one Notebook/development machine")
    notebook.add_argument("notebook_id")
    notebook.add_argument("--full", action="store_true", help="Print full API detail instead of compact creation fields")
    notebook.set_defaults(func=command_notebook)

    notebook_url = sub.add_parser("notebook-url", help="Create a presigned Notebook URL; authToken is redacted")
    notebook_url.add_argument("notebook_id")
    notebook_url.set_defaults(func=command_notebook_url)

    raw = sub.add_parser("raw", help="Call a raw action with a JSON payload")
    raw.add_argument("action")
    raw.add_argument("--payload", default="{}", help="JSON payload string, or @path/to/payload.json")
    raw.set_defaults(func=command_raw)

    encode_start_cmd = sub.add_parser("encode-start-cmd", help="Base64-encode StartCmdInfo for CreateTrainingTask")
    encode_start_cmd.add_argument("--start-cmd", help="StartCmd value, or @file")
    encode_start_cmd.add_argument("--ps-start-cmd", help="PsStartCmd value, or @file")
    encode_start_cmd.add_argument("--worker-start-cmd", help="WorkerStartCmd value, or @file")
    encode_start_cmd.set_defaults(func=command_encode_start_cmd)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(redact(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
