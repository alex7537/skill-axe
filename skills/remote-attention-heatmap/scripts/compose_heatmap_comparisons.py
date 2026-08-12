#!/usr/bin/env python3
"""Create deterministic original-vs-attention comparison PNGs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
PANEL_SIDE = 448
HEADER_HEIGHT = 58
GAP = 12
BACKGROUND = (18, 22, 30)
COLORS = [
    (73, 190, 255),
    (255, 174, 66),
    (128, 222, 128),
    (220, 130, 255),
    (255, 105, 130),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--labels-json", required=True)
    return parser.parse_args()


def load_fonts() -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, 27), ImageFont.truetype(candidate, 22)
    return ImageFont.load_default(), ImageFont.load_default()


FONT, SMALL_FONT = load_fonts()


def make_panel(image: Image.Image, label: str, color: tuple[int, int, int]) -> Image.Image:
    canvas = Image.new("RGB", (PANEL_SIDE, HEADER_HEIGHT + PANEL_SIDE), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    active_font = FONT
    if draw.textbbox((0, 0), label, font=active_font)[2] > PANEL_SIDE - 24:
        active_font = SMALL_FONT
    box = draw.textbbox((0, 0), label, font=active_font)
    x = (PANEL_SIDE - (box[2] - box[0])) // 2
    y = (HEADER_HEIGHT - (box[3] - box[1])) // 2 - box[1]
    draw.text((x, y), label, font=active_font, fill=color)
    resized = image.resize((PANEL_SIDE, PANEL_SIDE), Image.Resampling.LANCZOS)
    canvas.paste(resized, (0, HEADER_HEIGHT))
    return canvas


def join_panels(panels: list[Image.Image]) -> Image.Image:
    width = sum(panel.width for panel in panels) + GAP * (len(panels) - 1)
    canvas = Image.new("RGB", (width, panels[0].height), BACKGROUND)
    x = 0
    for panel in panels:
        canvas.paste(panel, (x, 0))
        x += panel.width + GAP
    return canvas


def stack_rows(rows: list[Image.Image]) -> Image.Image:
    width = max(row.width for row in rows)
    height = sum(row.height for row in rows) + GAP * (len(rows) - 1)
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    y = 0
    for row in rows:
        canvas.paste(row, ((width - row.width) // 2, y))
        y += row.height + GAP
    return canvas


def find_overlay(results: Path, label: str, stem: str) -> Path:
    matches = list((results / label).rglob(f"{stem}__attention_overlay.png"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one overlay for {label}/{stem}, found {len(matches)}")
    return matches[0]


def main() -> int:
    args = parse_args()
    inputs = Path(args.inputs)
    results = Path(args.results)
    output = Path(args.output)
    labels: list[str] = json.loads(args.labels_json)
    images = sorted(
        path for path in inputs.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images or not labels:
        raise ValueError("at least one input image and one model label are required")

    output.mkdir(parents=True)
    per_model_rows: dict[str, list[Image.Image]] = {label: [] for label in labels}
    all_rows: list[Image.Image] = []
    all_dir = output / "all_models"
    all_dir.mkdir()
    for label in labels:
        (output / label).mkdir()

    for input_path in images:
        with Image.open(input_path) as image:
            original = image.convert("RGB").resize((224, 224), Image.Resampling.BICUBIC)
        original_panel = make_panel(original, f"ORIGINAL · {input_path.stem}", (235, 235, 235))
        model_panels: list[Image.Image] = []
        for index, label in enumerate(labels):
            with Image.open(find_overlay(results, label, input_path.stem)) as image:
                overlay = image.convert("RGB")
            model_panel = make_panel(overlay, f"{label.upper()} ATTENTION", COLORS[index % len(COLORS)])
            model_panels.append(model_panel)
            pair = join_panels([original_panel, model_panel])
            pair.save(output / label / f"{input_path.stem}__original_vs_{label}.png", optimize=True)
            per_model_rows[label].append(pair)
        all_models = join_panels([original_panel, *model_panels])
        all_models.save(all_dir / f"{input_path.stem}__original_and_all_models.png", optimize=True)
        all_rows.append(all_models)

    for label, rows in per_model_rows.items():
        stack_rows(rows).save(output / label / f"overview_original_vs_{label}.png", optimize=True)
    stack_rows(all_rows).save(output / "overview_original_and_all_models.png", optimize=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
