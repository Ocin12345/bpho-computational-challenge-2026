"""Structural, evidence and readability checks for the Task 8 slide pack."""

from __future__ import annotations

import re
import struct
import zipfile
from pathlib import Path


PRESENTATION_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = PRESENTATION_DIRECTORY.parent.parent
PRESENTATION_PATH = (
    PRESENTATION_DIRECTORY / "Task08_Quantum_Mismatch_Calculator.pptx"
)
PREVIEW_PATH = (
    PRESENTATION_DIRECTORY
    / "preview"
    / "Task08_Quantum_Mismatch_Calculator_preview.png"
)
REPRODUCIBLE_CORE_TIMESTAMP = "2026-01-01T00:00:00Z"

ASSET_PAIRS = (
    (
        REPOSITORY_ROOT / "figures/task08/probability_sweep.png",
        PRESENTATION_DIRECTORY / "images/01_probability_sweep.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task08/mismatch_landscape.png",
        PRESENTATION_DIRECTORY / "images/02_mismatch_landscape.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task08/finite_photon_sampling.png",
        PRESENTATION_DIRECTORY / "images/03_finite_photon_sampling.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task08/task08_summary.png",
        PRESENTATION_DIRECTORY / "images/04_task08_summary.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task08/screenshots/detector_workspace_4k.png",
        PRESENTATION_DIRECTORY / "images/05_detector_workspace_4k.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task08/screenshots/probability_chart_4k.png",
        PRESENTATION_DIRECTORY / "images/06_probability_chart_4k.png",
    ),
    (
        REPOSITORY_ROOT
        / "figures/task08/screenshots/finite_photon_extension_4k.png",
        PRESENTATION_DIRECTORY / "images/07_finite_photon_extension_4k.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task08/screenshots/finite_photon_mobile_2x.png",
        PRESENTATION_DIRECTORY / "images/08_finite_photon_mobile_2x.png",
    ),
)
EXPECTED_ASSET_DIMENSIONS = (
    (2400, 1500),
    (2400, 1500),
    (2400, 1500),
    (3840, 2160),
    (3840, 2160),
    (3840, 2160),
    (3840, 2160),
    (860, 1864),
)
REQUIRED_XML_TEXT = (
    "FINAL SCRIPT",
    "classical Malus probabilities",
    "seventy-five percent",
    "All sixty-six validation checks pass",
    "Task 8 quantum mismatch summary",
    "separated by sixty degrees",
    "363 classical and 770 quantum",
    "forty-two scientific and twenty-four statistical",
)


def _png_dimensions(path: Path) -> tuple[int, int]:
    content = path.read_bytes()
    if len(content) < 24 or not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"not a PNG file: {path}")
    return struct.unpack(">II", content[16:24])


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
        if source.read_bytes() != copied.read_bytes():
            raise AssertionError(f"presentation asset differs from source: {copied}")
        if _png_dimensions(copied) != EXPECTED_ASSET_DIMENSIONS[index]:
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
            raise AssertionError("embedded image differs from validated Task 8 summary")

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

    width, height = _png_dimensions(PREVIEW_PATH)
    if width < 3900 or height < 2100:
        raise AssertionError(
            f"300-DPI preview resolution is too small: {width}x{height}"
        )
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
    if not 46 <= word_count <= 50:
        raise AssertionError(
            f"final script must remain near 18 seconds, found {word_count} words"
        )

    for markdown_path in (
        PRESENTATION_DIRECTORY / "README.md",
        PRESENTATION_DIRECTORY / "SLIDE_CONTENT.md",
        PRESENTATION_DIRECTORY / "SPEAKER_SCRIPT.md",
    ):
        _check_local_markdown_links(markdown_path)

    if PRESENTATION_PATH.stat().st_size > 10 * 1024 * 1024:
        raise AssertionError("PowerPoint exceeds the 10 MiB portability budget")

    print(
        "Task 8 presentation validation: PASS "
        f"(1 slide, 1 embedded 4K visual, {word_count}-word final script, "
        f"{width}x{height} 300-DPI preview, 8 byte-identical source assets)"
    )


if __name__ == "__main__":
    validate()
