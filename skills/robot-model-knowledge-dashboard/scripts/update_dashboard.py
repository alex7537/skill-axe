#!/usr/bin/env python3
"""Generate the curated robot-model skill inventory as one Obsidian dashboard."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys


MARKER = "<!-- generated-by: robot-model-knowledge-dashboard -->"
SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}
    try:
        block = text.split("---", 2)[1]
    except IndexError:
        return {}
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        if key in {"name", "description"}:
            result[key] = value.strip().strip('"').strip("'")
    return result


def skill_info(skills_root: Path, name: str) -> dict[str, object]:
    path = skills_root / name / "SKILL.md"
    metadata = parse_frontmatter(path) if path.is_file() else {}
    return {
        "name": name,
        "installed": path.is_file(),
        "description": metadata.get("description", ""),
    }


def registry_sha256(registry_path: Path) -> str:
    return hashlib.sha256(registry_path.read_bytes()).hexdigest()


def find_untracked(registry: dict, skills_root: Path, tracked: set[str]) -> list[dict[str, str]]:
    keywords = [word.lower() for word in registry.get("untracked_discovery_keywords", [])]
    ignored = set(registry.get("ignored_untracked_skills", []))
    found: list[dict[str, str]] = []
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        metadata = parse_frontmatter(skill_file)
        name = metadata.get("name", skill_file.parent.name)
        if name in tracked or name in ignored:
            continue
        description = metadata.get("description", "")
        haystack = f"{name} {description}".lower()
        if any(keyword in haystack for keyword in keywords):
            found.append({"name": name, "description": description})
    return found


def render_dashboard(registry: dict, skills_root: Path, registry_path: Path) -> str:
    route_rows: list[tuple[dict, list[dict]]] = []
    adjacent_rows: list[tuple[dict, list[dict]]] = []
    tracked: set[str] = set()
    core_unique: set[str] = set()
    adjacent_unique: set[str] = set()
    covered_routes = 0

    for route in registry["routes"]:
        skills = []
        for entry in route.get("skills", []):
            info = skill_info(skills_root, entry["name"])
            merged = {**entry, **info}
            skills.append(merged)
            tracked.add(entry["name"])
            if info["installed"]:
                core_unique.add(entry["name"])
        if any(item["installed"] for item in skills):
            covered_routes += 1
        route_rows.append((route, skills))

    for route in registry.get("adjacent_routes", []):
        skills = []
        for entry in route.get("skills", []):
            info = skill_info(skills_root, entry["name"])
            merged = {**entry, **info}
            skills.append(merged)
            tracked.add(entry["name"])
            if info["installed"]:
                adjacent_unique.add(entry["name"])
        adjacent_rows.append((route, skills))

    support_rows = []
    for entry in registry.get("supporting_skills", []):
        info = skill_info(skills_root, entry["name"])
        support_rows.append({**entry, **info})
        tracked.add(entry["name"])

    untracked = find_untracked(registry, skills_root, tracked)
    today = dt.datetime.now().astimezone().date().isoformat()
    reg_hash = registry_sha256(registry_path)

    lines = [
        "---",
        "type: dashboard",
        "status: active",
        "topic:",
        "  - robot-learning",
        "  - model-architecture",
        f"reviewed: {today}",
        "generator_skill: robot-model-knowledge-dashboard",
        "---",
        MARKER,
        f"# {registry['dashboard_title']}",
        "",
        "> 这是模型学习导航层：模型机制在专题 Skill/笔记中，代码在仓库，运行证据在实验平台。候选模型不计入已总结数量。",
        "",
        "## 当前统计",
        "",
        f"- 模型主路线：**{len(registry['routes'])}**",
        f"- 已有专题模型 Skill：**{len(core_unique)}**",
        f"- 已覆盖主路线：**{covered_routes}/{len(registry['routes'])}**",
        f"- 相邻基础路线：**{len(registry.get('adjacent_routes', []))}**（专题 Skill：{len(adjacent_unique)}）",
        f"- 支撑型 Skill：**{sum(bool(row['installed']) for row in support_rows)}**",
        f"- 待学习最新候选：**{len(registry.get('candidates', []))}**",
        f"- 候选来源快照：**{registry['snapshot_date']}**",
        "",
        "## 路线关系",
        "",
        "```mermaid",
        "flowchart LR",
        '  A[生成式 Action Policy] --> B[VLA / 语言条件策略]',
        '  A --> C[World Model / WAM]',
        '  A --> D[Value / Reward / Critic]',
        '  A --> E[感知与辅助表征]',
        '  B --> F[分层规划 / Test-Time Compute]',
        '  C --> F',
        '  D -. 评估与选择 .-> B',
        '  D -. 评估与选择 .-> C',
        '  G[通用多模态基础模型] -. 视觉生成 / 长上下文 .-> B',
        '  G -. 视频 latent / 稀疏注意力 .-> C',
        '  G -. 规划与记忆机制 .-> F',
        "```",
        "",
        "## 已学习模型路线",
        "",
    ]

    for route, skills in route_rows:
        lines.extend([
            f"### {route['title']}",
            "",
            f"> {route['role']}",
            "",
            "| 专题 Skill | 安装 | 已总结内容 | 证据 | 最近核对 | Obsidian |",
            "|---|---:|---|---|---|---|",
        ])
        if skills:
            for item in skills:
                notes = "<br>".join(item.get("notes", [])) or "—"
                installed = "✅" if item["installed"] else "❌"
                lines.append(
                    f"| `${item['name']}` | {installed} | {item['summary']} | "
                    f"{item['evidence']} | {item['last_verified']} | {notes} |"
                )
        else:
            lines.append("| — | — | 尚无专用总结 Skill | gap | — | — |")
        lines.extend([
            "",
            f"**下一问题：** {route['next_question']}",
            "",
        ])

    lines.extend([
        "## 相邻基础模型路线（不计入机器人主路线覆盖率）",
        "",
        "> 这些模型不直接证明机器人控制能力；这里只记录可迁移到 VLA、WAM、规划与记忆的机制。",
        "",
    ])

    for route, skills in adjacent_rows:
        lines.extend([
            f"### {route['title']}",
            "",
            f"> {route['role']}",
            "",
            "| 专题 Skill | 安装 | 已总结内容 | 证据 | 最近核对 | Obsidian |",
            "|---|---:|---|---|---|---|",
        ])
        if skills:
            for item in skills:
                notes = "<br>".join(item.get("notes", [])) or "—"
                installed = "✅" if item["installed"] else "❌"
                lines.append(
                    f"| `${item['name']}` | {installed} | {item['summary']} | "
                    f"{item['evidence']} | {item['last_verified']} | {notes} |"
                )
        else:
            lines.append("| — | — | 尚无专用总结 Skill | gap | — | — |")
        lines.extend([
            "",
            f"**下一问题：** {route['next_question']}",
            "",
        ])

    lines.extend([
        "## 最新拓展候选（未计入已总结）",
        "",
        "| 优先级 | 模型 | 路线 | 发布 | 为什么值得扩展 | 第一个学习问题 | 来源 |",
        "|---|---|---|---|---|---|---|",
    ])
    route_titles = {route["id"]: route["title"] for route in registry["routes"]}
    for item in registry.get("candidates", []):
        lines.append(
            f"| {item['priority']} | {item['model']} | {route_titles[item['route']]} | "
            f"{item['released']} | {item['why']} | {item['first_question']} | [官方来源]({item['source']}) |"
        )

    lines.extend([
        "",
        "## 支撑环（不计入模型架构数量）",
        "",
        "| Skill | 安装 | 作用 |",
        "|---|---:|---|",
    ])
    for item in support_rows:
        lines.append(f"| `${item['name']}` | {'✅' if item['installed'] else '❌'} | {item['role']} |")

    lines.extend(["", "## 待分类的新 Skill", ""])
    if untracked:
        for item in untracked:
            lines.append(f"- `{item['name']}` — {item['description']}")
    else:
        lines.append("- 暂无。")

    lines.extend([
        "",
        "## 更新规则",
        "",
        "1. 新模型先进入“候选”，只有完成专用 Skill 或经审阅的稳定笔记后才算已总结。",
        "2. 模型路线记录机制、输入输出、训练目标、推理和证据；运行日志与 checkpoint 不复制到 Vault。",
        "3. ‘最新候选’仅使用官方仓库、项目页或原论文，并保留快照日期。",
        "4. 看板为全自动生成文件；人工判断应写进链接的专题笔记。",
        "",
        "---",
        f"生成日期：`{today}`  ",
        f"Registry SHA256：`{reg_hash}`  ",
        "生成器：`$robot-model-knowledge-dashboard`",
        "",
    ])
    return "\n".join(lines)


def resolve_dashboard(config: dict) -> tuple[Path, Path]:
    vault = Path(config["vault_root"]).expanduser().resolve()
    if not (vault / ".obsidian").is_dir():
        raise RuntimeError(f"Not an Obsidian vault: {vault}")
    relative = Path(config["dashboard_relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("dashboard_relative_path must be a safe relative path")
    if relative.parts and relative.parts[0] in set(config.get("protected_roots", [])):
        raise RuntimeError("Dashboard target is inside a protected root")
    dashboard = (vault / relative).resolve()
    try:
        dashboard.relative_to(vault)
    except ValueError as exc:
        raise RuntimeError("Dashboard escapes the vault") from exc
    return vault, dashboard


def validate_wikilinks(text: str, vault: Path) -> list[str]:
    missing = []
    for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
        target = raw.split("|", 1)[0].split("#", 1)[0]
        path = vault / (target if target.endswith(".md") else f"{target}.md")
        if not path.exists():
            missing.append(target)
    return sorted(set(missing))


def write_dashboard(path: Path, text: str) -> None:
    if path.exists() and MARKER not in path.read_text(encoding="utf-8", errors="replace"):
        raise RuntimeError(f"Refusing to overwrite non-generated note: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print dashboard without writing")
    mode.add_argument("--write", action="store_true", help="write the configured dashboard")
    mode.add_argument("--check", action="store_true", help="require current dashboard to match generation")
    parser.add_argument("--config", type=Path, default=SKILL_ROOT / "config.json")
    parser.add_argument("--registry", type=Path, default=SKILL_ROOT / "references/model-routes.json")
    args = parser.parse_args()

    config = load_json(args.config)
    registry = load_json(args.registry)
    skills_root = Path(config["skills_root"]).expanduser().resolve()
    if not skills_root.is_dir():
        raise RuntimeError(f"Missing skills root: {skills_root}")
    vault, dashboard = resolve_dashboard(config)
    text = render_dashboard(registry, skills_root, args.registry)
    missing_links = validate_wikilinks(text, vault)
    if missing_links:
        raise RuntimeError(f"Missing Obsidian Wiki targets: {missing_links}")

    if args.write:
        write_dashboard(dashboard, text)
        print(f"WROTE {dashboard}")
    elif args.check:
        if not dashboard.exists() or dashboard.read_text(encoding="utf-8") != text:
            print(f"OUT_OF_DATE {dashboard}")
            return 1
        print(f"CURRENT {dashboard}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
