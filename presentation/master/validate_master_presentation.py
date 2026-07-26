"""Validate the ten-slide master PowerPoint, narration and rendered previews."""

from __future__ import annotations

import re
import struct
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


MASTER_DIRECTORY = Path(__file__).resolve().parent
PRESENTATION_ROOT = MASTER_DIRECTORY.parent
REPOSITORY_ROOT = PRESENTATION_ROOT.parent
POWERPOINT_PATH = (
    MASTER_DIRECTORY / "BPhO_Computational_Challenge_Tasks_1_to_10.pptx"
)
PDF_PATH = MASTER_DIRECTORY / "BPhO_Computational_Challenge_Tasks_1_to_10.pdf"
NARRATION_PATH = MASTER_DIRECTORY / "MASTER_NARRATION.md"
PREVIEW_DIRECTORY = MASTER_DIRECTORY / "preview"
REPRODUCIBLE_CORE_TIMESTAMP = "2026-01-01T00:00:00Z"

SOURCE_SUMMARIES = (
    REPOSITORY_ROOT / "figures/task01/task01_summary.png",
    REPOSITORY_ROOT / "task02_brownian_motion/figures/task02_summary.png",
    REPOSITORY_ROOT / "figures/task03/task03_summary.png",
    REPOSITORY_ROOT / "figures/task04/task04_summary.png",
    REPOSITORY_ROOT / "figures/task05/task05_summary.png",
    REPOSITORY_ROOT / "figures/task06/task06_summary.png",
    REPOSITORY_ROOT / "figures/task07/task07_summary.png",
    REPOSITORY_ROOT / "figures/task08/task08_summary.png",
    REPOSITORY_ROOT / "figures/task09/task09_summary.png",
    REPOSITORY_ROOT / "figures/task10/task10_summary.png",
)


def _png_dimensions(path: Path) -> tuple[int, int]:
    content = path.read_bytes()
    if len(content) < 24 or not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"not a PNG file: {path}")
    return struct.unpack(">II", content[16:24])


def _xml_text(content: bytes) -> str:
    root = ET.fromstring(content)
    return " ".join(text.strip() for text in root.itertext() if text.strip())


def _parse_narration() -> dict[int, str]:
    lines = NARRATION_PATH.read_text(encoding="utf-8").splitlines()
    scripts: dict[int, list[str]] = {}
    current: int | None = None
    for line in lines:
        heading = re.match(r"^## Task (\d+)\s+—", line)
        if heading:
            current = int(heading.group(1))
            scripts[current] = []
            continue
        if current is not None and line.startswith("> "):
            scripts[current].append(line[2:].strip())
    if set(scripts) != set(range(1, 11)):
        raise AssertionError(f"master narration does not contain Tasks 1–10: {sorted(scripts)}")
    joined = {number: " ".join(lines) for number, lines in scripts.items()}
    for number, script in joined.items():
        if not script:
            raise AssertionError(f"Task {number} master narration is empty")
    return joined


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


def validate() -> None:
    for path in (POWERPOINT_PATH, PDF_PATH, NARRATION_PATH):
        if not path.is_file():
            raise AssertionError(f"missing master presentation artifact: {path}")

    scripts = _parse_narration()
    counts = {number: _word_count(script) for number, script in scripts.items()}
    if any(count < 35 or count > 46 for count in counts.values()):
        raise AssertionError(f"per-task narration is outside the concise range: {counts}")
    total_words = sum(counts.values())
    if not 405 <= total_words <= 420:
        raise AssertionError(f"master narration must remain near 410 words: {total_words}")

    copied_images = tuple(
        MASTER_DIRECTORY
        / "images"
        / f"{number:02d}_task{number:02d}_summary.png"
        for number in range(1, 11)
    )
    for number, (source, copied) in enumerate(
        zip(SOURCE_SUMMARIES, copied_images), start=1
    ):
        if not source.is_file() or not copied.is_file():
            raise AssertionError(f"Task {number} master summary is missing")
        if source.read_bytes() != copied.read_bytes():
            raise AssertionError(f"Task {number} master summary differs from source")
        if _png_dimensions(copied) != (3840, 2160):
            raise AssertionError(f"Task {number} master summary is not 4K")

    with zipfile.ZipFile(POWERPOINT_PATH) as archive:
        if archive.testzip() is not None:
            raise AssertionError("master PowerPoint ZIP contains a corrupt member")
        names = archive.namelist()
        slides = sorted(
            (
                name
                for name in names
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=lambda name: int(re.search(r"\d+", Path(name).name).group()),
        )
        notes = sorted(
            (
                name
                for name in names
                if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
            ),
            key=lambda name: int(re.search(r"\d+", Path(name).name).group()),
        )
        media = [name for name in names if re.fullmatch(r"ppt/media/[^/]+", name)]
        if (len(slides), len(notes), len(media)) != (10, 10, 10):
            raise AssertionError(
                "master deck requires 10 slides, 10 notes pages and 10 images; "
                f"found {len(slides)}, {len(notes)}, {len(media)}"
            )

        for number, (slide_path, notes_path, expected_image) in enumerate(
            zip(slides, notes, copied_images), start=1
        ):
            slide_xml = archive.read(slide_path).decode("utf-8", errors="strict")
            if f"Task {number} summary" not in slide_xml:
                raise AssertionError(f"master slide {number} is out of order or lacks alt text")
            notes_text = _xml_text(archive.read(notes_path))
            if f"TASK {number} FINAL MASTER SCRIPT" not in notes_text:
                raise AssertionError(f"master slide {number} notes header is missing")
            if scripts[number] not in notes_text:
                raise AssertionError(f"master slide {number} notes differ from narration source")

            relationships = (
                f"ppt/slides/_rels/slide{number}.xml.rels"
            )
            relationship_xml = archive.read(relationships).decode("utf-8")
            target_match = re.search(r'Target="\.\./media/([^\"]+)"', relationship_xml)
            if not target_match:
                raise AssertionError(f"master slide {number} has no embedded image relationship")
            media_path = f"ppt/media/{target_match.group(1)}"
            if archive.read(media_path) != expected_image.read_bytes():
                raise AssertionError(f"master slide {number} embeds the wrong summary image")

        portable_xml = "\n".join(
            archive.read(name).decode("utf-8", errors="strict")
            for name in names
            if name.endswith((".xml", ".rels"))
        )
        if "/Users/" in portable_xml:
            raise AssertionError("master PowerPoint contains a machine-specific path")
        theme_xml = archive.read("ppt/theme/theme1.xml").decode("utf-8")
        if theme_xml.count('typeface="Times New Roman"') < 2:
            raise AssertionError("master theme does not use Times New Roman")
        if 'typeface="Arial"' in theme_xml:
            raise AssertionError("master theme still contains Arial")
        core_xml = archive.read("docProps/core.xml").decode("utf-8")
        if core_xml.count(REPRODUCIBLE_CORE_TIMESTAMP) != 2:
            raise AssertionError("master PowerPoint timestamps are not reproducible")

    previews = sorted(PREVIEW_DIRECTORY.glob("*preview-[0-9][0-9].png"))
    if len(previews) != 10:
        raise AssertionError(f"expected ten master slide previews, found {len(previews)}")
    for number, preview in enumerate(previews, start=1):
        dimensions = _png_dimensions(preview)
        if dimensions[0] < 3900 or dimensions[1] < 2100:
            raise AssertionError(f"master preview {number} is below 300 DPI: {dimensions}")
        if abs(dimensions[0] / dimensions[1] - 16 / 9) > 0.002:
            raise AssertionError(f"master preview {number} is not 16:9: {dimensions}")

    contact_sheet = PREVIEW_DIRECTORY / "BPhO_Master_Contact_Sheet.png"
    if not contact_sheet.is_file():
        raise AssertionError("master contact sheet is missing")

    estimated_seconds = total_words / 150 * 60
    if estimated_seconds >= 170:
        raise AssertionError(
            f"master narration leaves insufficient transition time: {estimated_seconds:.1f}s"
        )

    print(
        "Master presentation validation: PASS "
        f"(10 slides, 10 embedded 4K summaries, 10 notes pages, "
        f"{total_words} words, {estimated_seconds:.1f}s at 150 wpm, "
        "all previews 4001x2250)"
    )


if __name__ == "__main__":
    validate()
