"""Validate the committed advanced-extension figure set."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures" / "advanced"


def main() -> int:
    manifest = json.loads((FIGURES / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "advanced-figures-v1":
        raise SystemExit("unexpected advanced figure manifest schema")
    if manifest.get("task_count") != 10 or len(manifest.get("files", [])) != 10:
        raise SystemExit("advanced figure manifest must contain ten tasks")
    for number in range(1, 11):
        stem = f"task{number:02d}_extension"
        png, svg = FIGURES / f"{stem}.png", FIGURES / f"{stem}.svg"
        if not png.is_file() or not svg.is_file():
            raise SystemExit(f"missing figure pair: {stem}")
        with Image.open(png) as image:
            if image.width < 1500 or image.height < 800:
                raise SystemExit(f"undersized figure: {png.name} {image.size}")
        text = svg.read_text(encoding="utf-8")
        if "Task " not in text or "advanced extension" not in text:
            raise SystemExit(f"missing figure title: {svg.name}")
    print("Advanced figures validation: PASS (10 publication PNG/SVG pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
