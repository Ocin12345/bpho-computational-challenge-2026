"""Verify the standardized Times New Roman figure and slide typography."""

from __future__ import annotations

import zipfile
from pathlib import Path


PRESENTATION_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PRESENTATION_ROOT.parent

SVG_DIRECTORIES = (
    REPOSITORY_ROOT / "figures/task01",
    REPOSITORY_ROOT / "task02_brownian_motion/figures",
    REPOSITORY_ROOT / "figures/task03",
    REPOSITORY_ROOT / "figures/task04",
    REPOSITORY_ROOT / "figures/task05",
    REPOSITORY_ROOT / "figures/task06",
)

POWERPOINTS = tuple(
    path
    for directory in (PRESENTATION_ROOT / f"task{number:02d}" for number in range(1, 11))
    for path in directory.glob("*.pptx")
) + (
    PRESENTATION_ROOT
    / "master/BPhO_Computational_Challenge_Tasks_1_to_10.pptx",
)


def validate() -> None:
    svg_paths = tuple(
        path for directory in SVG_DIRECTORIES for path in sorted(directory.glob("*.svg"))
    )
    if len(svg_paths) < 25:
        raise AssertionError(f"too few Task 1–6 SVG figures to audit: {len(svg_paths)}")
    for path in svg_paths:
        text = path.read_text(encoding="utf-8")
        if "TimesNewRoman" not in text:
            raise AssertionError(f"Times New Roman glyph outlines are missing: {path}")
        if "DejaVuSans" in text or "Arial" in text:
            raise AssertionError(f"legacy sans-serif glyphs remain: {path}")

    if len(POWERPOINTS) != 11:
        raise AssertionError(f"expected ten task decks and one master deck, found {len(POWERPOINTS)}")
    for path in POWERPOINTS:
        with zipfile.ZipFile(path) as archive:
            theme = archive.read("ppt/theme/theme1.xml").decode("utf-8")
            if theme.count('typeface="Times New Roman"') < 2:
                raise AssertionError(f"Times New Roman theme is missing: {path}")
            if 'typeface="Arial"' in theme:
                raise AssertionError(f"Arial remains in PowerPoint theme: {path}")

    print(
        "Typography validation: PASS "
        f"({len(svg_paths)} Task 1–6 SVG figures use Times New Roman glyphs; "
        "10 task decks and the master deck use Times New Roman themes)"
    )


if __name__ == "__main__":
    validate()
