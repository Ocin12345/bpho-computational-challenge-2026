"""Structural and evidence checks for the generated Task 4 PowerPoint pack."""

from __future__ import annotations

import re
import struct
import zipfile
from pathlib import Path

from PIL import Image


PRESENTATION_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = PRESENTATION_DIRECTORY.parent.parent
PRESENTATION_PATH = (
    PRESENTATION_DIRECTORY / "Task04_Photoelectric_Effect.pptx"
)
PREVIEW_PATH = (
    PRESENTATION_DIRECTORY
    / "preview"
    / "Task04_Photoelectric_Effect_preview.png"
)
REPRODUCIBLE_CORE_TIMESTAMP = "2026-01-01T00:00:00Z"

ASSET_PAIRS = (
    (
        REPOSITORY_ROOT / "figures/task04/stopping_voltage_frequency.png",
        PRESENTATION_DIRECTORY / "images/01_stopping_voltage_frequency.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task04/photoelectric_demo.gif",
        PRESENTATION_DIRECTORY / "images/02_photoelectric_demo.gif",
    ),
    (
        REPOSITORY_ROOT / "figures/task04/stopping_voltage_wavelength.png",
        PRESENTATION_DIRECTORY / "images/03_stopping_voltage_wavelength.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task04/copper_threshold_explanation.png",
        PRESENTATION_DIRECTORY / "images/04_copper_threshold_explanation.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task04/photoelectric_validation.png",
        PRESENTATION_DIRECTORY / "images/05_photoelectric_validation.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task04/task04_summary.png",
        PRESENTATION_DIRECTORY / "images/06_task04_summary.png",
    ),
    (
        REPOSITORY_ROOT / "figures/task04/photoelectric_demo_storyboard.png",
        PRESENTATION_DIRECTORY / "images/07_photoelectric_demo_storyboard.png",
    ),
)

REQUIRED_XML_TEXT = (
    "Task 4",
    "Work function sets the emission threshold",
    "All physical curves share gradient h/e",
    "Intensity changes count, not maximum energy",
    "516.6 nm",
    "43/43 CHECKS PASS",
    "FINAL SCRIPT",
    "forty-three",
    "Stopping-potential magnitude against photon frequency",
    "Four-scene schematic sodium photoelectric demonstration",
)


def _png_dimensions(path: Path) -> tuple[int, int]:
    content = path.read_bytes()
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
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
    """Raise on any invalid package contract, otherwise print a pass summary."""

    if not PRESENTATION_PATH.is_file():
        raise AssertionError(f"missing PowerPoint: {PRESENTATION_PATH}")
    if not PREVIEW_PATH.is_file():
        raise AssertionError(f"missing preview: {PREVIEW_PATH}")

    for source, copied in ASSET_PAIRS:
        if source.read_bytes() != copied.read_bytes():
            raise AssertionError(f"presentation asset differs from source: {copied}")

    with Image.open(ASSET_PAIRS[1][1]) as animation:
        if animation.size != (1920, 1080):
            raise AssertionError(f"invalid GIF dimensions: {animation.size}")
        if animation.n_frames != 60:
            raise AssertionError(f"invalid GIF frame count: {animation.n_frames}")
        if animation.info.get("loop") != 0:
            raise AssertionError("the embedded GIF does not loop continuously")

    with zipfile.ZipFile(PRESENTATION_PATH) as archive:
        archive.testzip()
        names = archive.namelist()
        slides = [
            name
            for name in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        notes = [
            name
            for name in names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        media = [
            name
            for name in names
            if re.fullmatch(r"ppt/media/[^/]+", name)
        ]
        if len(slides) != 1:
            raise AssertionError(f"expected one slide, found {len(slides)}")
        if len(notes) != 1:
            raise AssertionError(f"expected one notes page, found {len(notes)}")
        if len(media) != 2:
            raise AssertionError(f"expected two embedded images, found {len(media)}")
        embedded_media = [archive.read(name) for name in media]
        expected_media = {
            ASSET_PAIRS[0][1].read_bytes(),
            ASSET_PAIRS[1][1].read_bytes(),
        }
        if set(embedded_media) != expected_media:
            raise AssertionError(
                "embedded graph or animated GIF differs from its validated asset"
            )
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
        core_properties = archive.read("docProps/core.xml").decode("utf-8")
        if core_properties.count(REPRODUCIBLE_CORE_TIMESTAMP) != 2:
            raise AssertionError(
                "PowerPoint creation and modification timestamps are not "
                "reproducible"
            )

    width, height = _png_dimensions(PREVIEW_PATH)
    if width < 1900 or height < 1000:
        raise AssertionError(f"preview resolution is too small: {width}x{height}")
    if abs(width / height - 16.0 / 9.0) > 0.002:
        raise AssertionError(f"preview is not 16:9: {width}x{height}")

    speaker_script = (
        PRESENTATION_DIRECTORY / "SPEAKER_SCRIPT.md"
    ).read_text(encoding="utf-8")
    final_section = speaker_script.split(
        "## Final competition version",
        1,
    )[1].split("### Visual cues", 1)[0]
    spoken_text = " ".join(
        line[2:] for line in final_section.splitlines() if line.startswith("> ")
    )
    word_count = len(re.findall(r"\b[\w’'-]+\b", spoken_text))
    if not 42 <= word_count <= 50:
        raise AssertionError(
            f"final script must remain near 18 seconds, found {word_count} words"
        )

    for markdown_path in (
        PRESENTATION_DIRECTORY / "README.md",
        PRESENTATION_DIRECTORY / "SLIDE_CONTENT.md",
        PRESENTATION_DIRECTORY / "SPEAKER_SCRIPT.md",
    ):
        _check_local_markdown_links(markdown_path)

    print(
        "Task 4 presentation validation: PASS "
        f"(1 slide, 2 embedded visuals, {word_count}-word final script, "
        f"{width}x{height} preview, 60-frame GIF)"
    )


if __name__ == "__main__":
    validate()
