"""Structural, evidence and readability checks for the Task 9 slide pack."""

from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path


PRESENTATION_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = PRESENTATION_DIRECTORY.parent.parent
PRESENTATION_PATH = PRESENTATION_DIRECTORY / "Task09_Compton_Scattering.pptx"
PREVIEW_PATH = (
    PRESENTATION_DIRECTORY
    / "preview"
    / "Task09_Compton_Scattering_preview.png"
)
REPRODUCIBLE_CORE_TIMESTAMP = "2026-01-01T00:00:00Z"

ASSET_PAIRS = (
    (
        REPOSITORY_ROOT / "figures/task09/required_kinematics.png",
        PRESENTATION_DIRECTORY / "images/01_required_kinematics.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task09/energy_transfer_geometry.png",
        PRESENTATION_DIRECTORY / "images/02_energy_transfer_geometry.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task09/klein_nishina_extension.png",
        PRESENTATION_DIRECTORY / "images/03_klein_nishina_extension.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task09/task09_summary.png",
        PRESENTATION_DIRECTORY / "images/04_task09_summary.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task09/compton_angle_sweep.gif",
        PRESENTATION_DIRECTORY / "images/05_compton_angle_sweep.gif",
    ),
)
EXPECTED_ASSET_DIMENSIONS = (
    (2400, 1500),
    (2400, 1500),
    (2400, 1500),
    (3840, 2160),
    (1600, 900),
)
REQUIRED_XML_TEXT = (
    "FINAL SCRIPT",
    "exact Compton scattering",
    "0.391",
    "0.434 c",
    "35.7 degrees",
    "passed all 44 checks",
    "Task 9 Compton-scattering summary",
    "50, 100, 200, 500 and 1000 keV",
    "44 of 44 core and 30 of 30 extension",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raster_dimensions(path: Path) -> tuple[int, int]:
    content = path.read_bytes()
    if content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) >= 24:
        return struct.unpack(">II", content[16:24])
    if content.startswith((b"GIF87a", b"GIF89a")) and len(content) >= 10:
        return struct.unpack("<HH", content[6:10])
    raise AssertionError(f"unsupported raster file: {path}")


def _check_local_markdown_links(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "/Users/" in text:
        raise AssertionError(f"machine-specific path in {path}")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        destination = (path.parent / target.split("#", 1)[0]).resolve()
        if not destination.exists():
            raise AssertionError(f"broken local link in {path}: {target}")


def validate() -> None:
    if not PRESENTATION_PATH.is_file():
        raise AssertionError(f"missing PowerPoint: {PRESENTATION_PATH}")
    if not PREVIEW_PATH.is_file():
        raise AssertionError(f"missing preview: {PREVIEW_PATH}")

    for index, (source, copied) in enumerate(ASSET_PAIRS):
        if not source.is_file() or not copied.is_file():
            raise AssertionError(f"missing presentation asset pair: {source}, {copied}")
        if _sha256(source) != _sha256(copied):
            raise AssertionError(f"presentation asset differs from source: {copied}")
        if _raster_dimensions(copied) != EXPECTED_ASSET_DIMENSIONS[index]:
            raise AssertionError(f"unexpected asset dimensions: {copied}")

    with zipfile.ZipFile(PRESENTATION_PATH) as archive:
        if archive.testzip() is not None:
            raise AssertionError("PowerPoint ZIP contains a corrupt member")
        names = archive.namelist()
        slides = [
            name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        notes = [
            name
            for name in names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        media = [name for name in names if re.fullmatch(r"ppt/media/[^/]+", name)]
        if len(slides) != 1:
            raise AssertionError(f"expected one slide, found {len(slides)}")
        if len(notes) != 1:
            raise AssertionError(f"expected one notes page, found {len(notes)}")
        if len(media) != 1:
            raise AssertionError(f"expected one embedded image, found {len(media)}")
        if archive.read(media[0]) != ASSET_PAIRS[3][1].read_bytes():
            raise AssertionError("embedded image differs from validated Task 9 summary")

        xml = "\n".join(
            archive.read(name).decode("utf-8", errors="strict")
            for name in slides + notes
        )
        for required in REQUIRED_XML_TEXT:
            if required not in xml:
                raise AssertionError(f"missing PowerPoint content: {required}")
        portable_text = "\n".join(
            archive.read(name).decode("utf-8", errors="strict")
            for name in names
            if name.endswith((".xml", ".rels"))
        )
        if "/Users/" in portable_text:
            raise AssertionError("PowerPoint contains a machine-specific path")
        theme_xml = archive.read("ppt/theme/theme1.xml").decode("utf-8")
        if theme_xml.count('typeface="Times New Roman"') < 10:
            raise AssertionError("PowerPoint theme does not use Times New Roman")
        if 'typeface="Arial"' in theme_xml:
            raise AssertionError("PowerPoint theme still contains Arial")
        core_properties = archive.read("docProps/core.xml").decode("utf-8")
        if core_properties.count(REPRODUCIBLE_CORE_TIMESTAMP) != 2:
            raise AssertionError("PowerPoint timestamps are not reproducible")
        presentation_xml = archive.read("ppt/presentation.xml").decode("utf-8")
        if 'cx="12192000" cy="6858000"' not in presentation_xml:
            raise AssertionError("PowerPoint canvas is not 13.333 by 7.5 inch widescreen")

    width, height = _raster_dimensions(PREVIEW_PATH)
    if width < 3900 or height < 2100:
        raise AssertionError(f"300-DPI preview resolution is too small: {width}x{height}")
    if abs(width / height - 16.0 / 9.0) > 0.002:
        raise AssertionError(f"preview is not 16:9: {width}x{height}")

    speaker_script = (PRESENTATION_DIRECTORY / "SPEAKER_SCRIPT.md").read_text(
        encoding="utf-8"
    )
    final_section = speaker_script.split("## Final competition version", 1)[1].split(
        "### Visual cues", 1
    )[0]
    spoken_text = " ".join(
        line[2:] for line in final_section.splitlines() if line.startswith("> ")
    )
    word_count = len(re.findall(r"\b[\w’'-]+\b", spoken_text))
    if word_count != 48:
        raise AssertionError(f"final script must remain 48 words, found {word_count}")

    for markdown_path in (
        PRESENTATION_DIRECTORY / "README.md",
        PRESENTATION_DIRECTORY / "SLIDE_CONTENT.md",
        PRESENTATION_DIRECTORY / "SPEAKER_SCRIPT.md",
    ):
        _check_local_markdown_links(markdown_path)

    if PRESENTATION_PATH.stat().st_size > 10 * 1024 * 1024:
        raise AssertionError("PowerPoint exceeds the 10 MiB portability budget")

    print(
        "Task 9 presentation validation: PASS "
        f"(1 slide, 1 embedded 4K visual, {word_count}-word final script, "
        f"{width}x{height} preview, 5 byte-identical source assets)"
    )


if __name__ == "__main__":
    validate()
