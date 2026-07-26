"""Validate the standardized high-resolution Task 1–6 slide packs."""

from __future__ import annotations

import re
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path


PRESENTATION_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PRESENTATION_ROOT.parent
REPRODUCIBLE_CORE_TIMESTAMP = "2026-01-01T00:00:00Z"


@dataclass(frozen=True)
class TaskPresentationContract:
    number: int
    filename: str
    preview_filename: str
    image_filename: str
    summary_source: Path
    required_text: tuple[str, ...]


CONTRACTS = {
    1: TaskPresentationContract(
        1,
        "Task01_Random_Walk.pptx",
        "Task01_Random_Walk_preview.png",
        "05_task01_summary.png",
        REPOSITORY_ROOT / "figures/task01/task01_summary.png",
        ("FINAL SCRIPT", "fixed-length steps", "Task 1 summary"),
    ),
    2: TaskPresentationContract(
        2,
        "Task02_Brownian_Motion.pptx",
        "Task02_Brownian_Motion_preview.png",
        "06_task02_summary.png",
        REPOSITORY_ROOT / "task02_brownian_motion/figures/task02_summary.png",
        ("FINAL SCRIPT", "one thousand small particles", "Task 2 summary"),
    ),
    3: TaskPresentationContract(
        3,
        "Task03_Planck_Einstein.pptx",
        "Task03_Planck_Einstein_preview.png",
        "05_task03_summary.png",
        REPOSITORY_ROOT / "figures/task03/task03_summary.png",
        ("FINAL SCRIPT", "Planck radiation", "Task 3 summary"),
    ),
    4: TaskPresentationContract(
        4,
        "Task04_Photoelectric_Effect.pptx",
        "Task04_Photoelectric_Effect_preview.png",
        "06_task04_summary.png",
        REPOSITORY_ROOT / "figures/task04/task04_summary.png",
        ("FINAL SCRIPT", "photoelectric equation", "Task 4 summary"),
    ),
    5: TaskPresentationContract(
        5,
        "Task05_Hydrogen_Spectrum.pptx",
        "Task05_Hydrogen_Spectrum_preview.png",
        "06_task05_summary.png",
        REPOSITORY_ROOT / "figures/task05/task05_summary.png",
        ("FINAL SCRIPT", "ideal Bohr energy levels", "Task 5 summary"),
    ),
    6: TaskPresentationContract(
        6,
        "Task06_Electron_Diffraction.pptx",
        "Task06_Electron_Diffraction_preview.png",
        "06_task06_summary.png",
        REPOSITORY_ROOT / "figures/task06/task06_summary.png",
        ("FINAL SCRIPT", "electrons accelerated", "Task 6 summary"),
    ),
}


def _png_dimensions(path: Path) -> tuple[int, int]:
    content = path.read_bytes()
    if len(content) < 24 or not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"not a PNG file: {path}")
    return struct.unpack(">II", content[16:24])


def validate_task(number: int) -> None:
    try:
        contract = CONTRACTS[number]
    except KeyError as exc:
        raise ValueError(f"unsupported standardized task: {number}") from exc

    directory = PRESENTATION_ROOT / f"task{number:02d}"
    powerpoint = directory / contract.filename
    preview = directory / "preview" / contract.preview_filename
    copied_image = directory / "images" / contract.image_filename
    for path in (powerpoint, preview, copied_image, contract.summary_source):
        if not path.is_file():
            raise AssertionError(f"missing Task {number} presentation artifact: {path}")

    if contract.summary_source.read_bytes() != copied_image.read_bytes():
        raise AssertionError(f"Task {number} summary copy differs from validated source")
    if _png_dimensions(copied_image) != (3840, 2160):
        raise AssertionError(f"Task {number} summary is not 4K")

    with zipfile.ZipFile(powerpoint) as archive:
        if archive.testzip() is not None:
            raise AssertionError(f"Task {number} PowerPoint contains a corrupt member")
        names = archive.namelist()
        slides = [name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        notes = [
            name
            for name in names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        media = [name for name in names if re.fullmatch(r"ppt/media/[^/]+", name)]
        if len(slides) != 1 or len(notes) != 1 or len(media) != 1:
            raise AssertionError(
                f"Task {number} requires one slide, one notes page and one image; "
                f"found {len(slides)}, {len(notes)}, {len(media)}"
            )
        if archive.read(media[0]) != copied_image.read_bytes():
            raise AssertionError(f"Task {number} embedded media differs from 4K summary")

        visible_xml = "\n".join(
            archive.read(name).decode("utf-8", errors="strict")
            for name in slides + notes
        )
        for required in contract.required_text:
            if required not in visible_xml:
                raise AssertionError(f"Task {number} missing PowerPoint content: {required}")

        portable_xml = "\n".join(
            archive.read(name).decode("utf-8", errors="strict")
            for name in names
            if name.endswith((".xml", ".rels"))
        )
        if "/Users/" in portable_xml:
            raise AssertionError(f"Task {number} PowerPoint contains a machine-specific path")
        theme_xml = archive.read("ppt/theme/theme1.xml").decode("utf-8")
        if theme_xml.count('typeface="Times New Roman"') < 2:
            raise AssertionError(f"Task {number} theme does not use Times New Roman")
        if 'typeface="Arial"' in theme_xml:
            raise AssertionError(f"Task {number} theme still contains Arial")
        core_xml = archive.read("docProps/core.xml").decode("utf-8")
        if core_xml.count(REPRODUCIBLE_CORE_TIMESTAMP) != 2:
            raise AssertionError(f"Task {number} timestamps are not reproducible")

    preview_dimensions = _png_dimensions(preview)
    if preview_dimensions[0] < 3900 or preview_dimensions[1] < 2100:
        raise AssertionError(
            f"Task {number} preview is below 300-DPI standard: {preview_dimensions}"
        )
    if abs(preview_dimensions[0] / preview_dimensions[1] - 16 / 9) > 0.002:
        raise AssertionError(f"Task {number} preview is not 16:9: {preview_dimensions}")

    print(
        f"Task {number} presentation validation: PASS "
        f"(1 slide, 1 embedded 4K visual, {preview_dimensions[0]}x{preview_dimensions[1]} preview)"
    )


def validate_all() -> None:
    for number in CONTRACTS:
        validate_task(number)


if __name__ == "__main__":
    validate_all()
