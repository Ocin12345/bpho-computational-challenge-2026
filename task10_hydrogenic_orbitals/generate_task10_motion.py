"""Generate the deterministic Task 10 4K motion package and integrity manifest."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageOps

from task10_hydrogenic_orbitals.animation import (
    ANIMATION_FILENAME,
    POSTER_FILENAME,
    verify_task10_animation,
    write_task10_animation,
)
from task10_hydrogenic_orbitals.configuration import DEFAULT_CONFIGURATION
from task10_hydrogenic_orbitals.generate_task10 import REPOSITORY_ROOT
from task10_hydrogenic_orbitals.models import orbital_summary
from task10_hydrogenic_orbitals.configuration import HydrogenicState
from task10_hydrogenic_orbitals.plotting import (
    FIGURE_FONT_FAMILY,
    _require_figure_font,
)
from task10_hydrogenic_orbitals.validation import task10_state_digest, validate_task10


DEFAULT_MEDIA_DIRECTORY = REPOSITORY_ROOT / "figures" / "task10"
DEFAULT_REPORT_DIRECTORY = REPOSITORY_ROOT / "reports" / "task10"
VIEWER_FILENAME = "orbital_view_rotation_viewer.html"
MOTION_MANIFEST_FILENAME = "motion_manifest.json"
CONTACT_SHEET_FILENAME = "orbital_view_rotation_contact_sheet.png"
MOTION_SCHEMA_VERSION = "task10-motion-v2"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.stem}-",
            suffix=path.suffix,
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        path.chmod(0o644)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _viewer_html() -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light">
    <title>Task 10 · Stationary orbital view rotation</title>
    <link rel="icon" href="../../task10_hydrogenic_orbitals/app/favicon.svg" type="image/svg+xml">
    <style>
      :root {{ font-family: "Times New Roman", Times, serif; color: #202124; background: #f2f4f5; }}
      * {{ box-sizing: border-box; }}
      body {{ min-width: 320px; margin: 0; padding: clamp(14px, 3vw, 42px); }}
      main {{ width: min(1500px, 100%); margin: auto; }}
      h1 {{ margin: 0 0 8px; font-size: clamp(1.8rem, 5vw, 4rem); line-height: 1; letter-spacing: -.015em; }}
      p {{ color: #5f6368; line-height: 1.55; }}
      figure {{ margin: 24px 0 0; overflow: hidden; border: 1px solid #74879e; border-radius: 18px; background: white; box-shadow: 0 18px 52px rgba(28,52,82,.12); }}
      img {{ display: block; width: 100%; height: auto; background: white; }}
      figcaption {{ padding: 15px 18px; color: #45494d; font-size: .92rem; }}
      .inspection {{ margin-top: 28px; }}
      .inspection h2 {{ margin-bottom: 8px; }}
      .inspection img {{ border: 1px solid #74879e; border-radius: 14px; }}
      strong {{ color: #007a5e; }}
      @media (prefers-reduced-motion: reduce) {{ .motion-note::after {{ content: " A static 4K poster is shown because reduced motion is enabled."; }} }}
    </style>
  </head>
  <body>
    <main>
      <h1>Stationary orbital · view rotation</h1>
      <p class="motion-note">This is a camera orbit around one normalized hydrogen 3d state. It is not electron motion or time evolution.</p>
      <figure>
        <picture>
          <source media="(prefers-reduced-motion: reduce)" srcset="./{POSTER_FILENAME}">
          <img id="motion-artifact" src="./{ANIMATION_FILENAME}" width="3840" height="2160" alt="A continuously rotating camera view of the stationary normalized hydrogen 3d, m equals zero probability density, accompanied by fixed orthogonal slices and radial probability.">
        </picture>
        <figcaption><strong>4K animated WebP · seamless loop.</strong> Threshold 0.15 changes visibility only; the unthresholded state remains normalized.</figcaption>
      </figure>
      <section class="inspection" aria-labelledby="inspection-heading">
        <h2 id="inspection-heading">Decoded frame inspection</h2>
        <p>Beginning, quarter-turn, half-turn, three-quarter-turn and final loop frames.</p>
        <img id="inspection-sheet" src="../../reports/task10/{CONTACT_SHEET_FILENAME}" width="2400" height="2300" alt="Five decoded frames from the Task 10 orbital view rotation at camera azimuths zero, ninety, one hundred eighty, two hundred seventy and three hundred fifty-five point five degrees.">
      </section>
    </main>
  </body>
</html>
"""


def write_motion_viewer(media_directory: Path = DEFAULT_MEDIA_DIRECTORY) -> Path:
    destination = Path(media_directory) / VIEWER_FILENAME
    _atomic_text(destination, _viewer_html())
    return destination


def write_contact_sheet(
    animation_path: Path,
    output_path: Path,
) -> Path:
    """Extract five exact frames into a high-resolution visual-audit sheet."""

    animation_path = Path(animation_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (2400, 2300), "#f2f4f5")
    draw = ImageDraw.Draw(canvas)
    _require_figure_font()
    regular_path = font_manager.findfont(
        font_manager.FontProperties(family=FIGURE_FONT_FAMILY, weight="normal"),
        fallback_to_default=False,
    )
    bold_path = font_manager.findfont(
        font_manager.FontProperties(family=FIGURE_FONT_FAMILY, weight="bold"),
        fallback_to_default=False,
    )
    title_font = ImageFont.truetype(bold_path, 54)
    subtitle_font = ImageFont.truetype(regular_path, 27)
    label_font = ImageFont.truetype(bold_path, 27)
    draw.text((90, 58), "Task 10 · 4K orbital view-rotation inspection", font=title_font, fill="#202124")
    draw.text(
        (90, 130),
        "Five decoded full frames · stationary hydrogen 3d (m=0) density · threshold 0.15",
        font=subtitle_font,
        fill="#5f6368",
    )
    sample_indices = (0, 20, 40, 60, 79)
    positions = ((90, 200), (1220, 200), (90, 880), (1220, 880), (655, 1560))
    with Image.open(animation_path) as animation:
        if animation.n_frames != DEFAULT_CONFIGURATION.animation_frame_count:
            raise ValueError("contact sheet requires the frozen production animation")
        for frame_index, (left, top) in zip(sample_indices, positions):
            animation.seek(frame_index)
            animation.load()
            frame = ImageOps.fit(
                animation.convert("RGB"),
                (1080, 608),
                method=Image.Resampling.LANCZOS,
            )
            canvas.paste(frame, (left, top))
            rotation = 360.0 * frame_index / animation.n_frames
            label = f"frame {frame_index + 1:02d}/{animation.n_frames:02d} · camera azimuth {rotation:05.1f}°"
            draw.text((left, top + 618), label, font=label_font, fill="#007a5e")
    draw.text(
        (90, 2250),
        "The last frame advances one equal camera step into the first, so the loop has no duplicated pause frame.",
        font=subtitle_font,
        fill="#45494d",
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output_path.stem}-",
            suffix=".png",
            dir=output_path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        canvas.save(temporary_path, format="PNG", dpi=(200, 200), compress_level=9)
        os.replace(temporary_path, output_path)
        output_path.chmod(0o644)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return output_path


def build_motion_manifest(
    media_directory: Path = DEFAULT_MEDIA_DIRECTORY,
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> dict:
    """Validate and describe the complete current motion package."""

    media_directory = Path(media_directory)
    report_directory = Path(report_directory)
    animation_path = media_directory / ANIMATION_FILENAME
    poster_path = media_directory / POSTER_FILENAME
    viewer_path = media_directory / VIEWER_FILENAME
    contact_path = report_directory / CONTACT_SHEET_FILENAME
    missing = [path.name for path in (animation_path, poster_path, viewer_path, contact_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing Task 10 motion files: {', '.join(missing)}")
    configuration = DEFAULT_CONFIGURATION
    evidence = verify_task10_animation(
        animation_path,
        width_px=configuration.animation_width_px,
        height_px=configuration.animation_height_px,
        frame_count=configuration.animation_frame_count,
        frame_duration_ms=1000 // configuration.animation_frames_per_second,
        size_budget_bytes=configuration.animation_size_budget_bytes,
    )
    with Image.open(poster_path) as poster:
        if poster.format != "PNG" or poster.size != (
            configuration.animation_width_px,
            configuration.animation_height_px,
        ):
            raise ValueError("motion poster is not the frozen 4K PNG")
        poster_dpi = [round(float(value), 3) for value in poster.info.get("dpi", (0, 0))]
    with Image.open(contact_path) as contact:
        if contact.format != "PNG" or contact.size != (2400, 2300):
            raise ValueError("motion contact sheet has invalid dimensions")
    viewer = viewer_path.read_text(encoding="utf-8")
    for required in (
        ANIMATION_FILENAME,
        POSTER_FILENAME,
        CONTACT_SHEET_FILENAME,
        "prefers-reduced-motion",
        "not electron motion",
        FIGURE_FONT_FAMILY,
    ):
        if required not in viewer:
            raise ValueError(f"motion viewer is missing {required}")
    science = validate_task10()
    if not science.passed or science.state_digest != task10_state_digest():
        raise RuntimeError("motion manifest requires the passing current science state")
    state = HydrogenicState(3, 2, 0)
    summary = orbital_summary(state)
    return {
        "schema_version": MOTION_SCHEMA_VERSION,
        "science_gate": {
            "state_digest": science.state_digest,
            "checks_passed": sum(check.passed for check in science.checks),
            "checks_total": len(science.checks),
        },
        "rendering_contract": {
            "state": {"n": 3, "l": 2, "m": 0, "Z": 1, "A": 1},
            "energy_ev": format(summary.energy_ev, ".17g"),
            "display_threshold": configuration.display_threshold,
            "slice_count": configuration.slice_count,
            "width_px": configuration.animation_width_px,
            "height_px": configuration.animation_height_px,
            "frame_count": configuration.animation_frame_count,
            "frames_per_second": configuration.animation_frames_per_second,
            "quality": configuration.animation_quality,
            "font_family": FIGURE_FONT_FAMILY,
            "camera_path": "360 degree azimuth; periodic 24 plus or minus 5 degree elevation; endpoint excluded",
            "motion_interpretation": "view rotation only; normalized state is stationary",
        },
        "animation": {
            **evidence,
            "filename": animation_path.name,
            "sha256": _sha256(animation_path),
        },
        "poster": {
            "filename": poster_path.name,
            "width_px": configuration.animation_width_px,
            "height_px": configuration.animation_height_px,
            "dpi": poster_dpi,
            "bytes": poster_path.stat().st_size,
            "sha256": _sha256(poster_path),
        },
        "viewer": {
            "filename": viewer_path.name,
            "bytes": viewer_path.stat().st_size,
            "sha256": _sha256(viewer_path),
            "reduced_motion_fallback": POSTER_FILENAME,
        },
        "inspection_contact_sheet": {
            "filename": str(contact_path.relative_to(REPOSITORY_ROOT)),
            "width_px": 2400,
            "height_px": 2300,
            "bytes": contact_path.stat().st_size,
            "sha256": _sha256(contact_path),
            "sampled_frames": [0, 20, 40, 60, 79],
        },
    }


def write_motion_manifest(
    media_directory: Path = DEFAULT_MEDIA_DIRECTORY,
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> Path:
    destination = Path(media_directory) / MOTION_MANIFEST_FILENAME
    payload = build_motion_manifest(media_directory, report_directory)
    _atomic_text(destination, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return destination


def generate_motion_package(
    media_directory: Path = DEFAULT_MEDIA_DIRECTORY,
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> tuple[Path, Path, Path, Path, Path]:
    """Generate and verify the animation, poster, viewer, contact sheet and manifest."""

    media_directory = Path(media_directory)
    report_directory = Path(report_directory)
    report = validate_task10()
    if not report.passed:
        raise RuntimeError("motion generation requires passing Task 10 science")
    animation, poster, _ = write_task10_animation(
        report,
        media_directory / ANIMATION_FILENAME,
        poster_path=media_directory / POSTER_FILENAME,
    )
    assert poster is not None
    viewer = write_motion_viewer(media_directory)
    contact = write_contact_sheet(
        animation,
        report_directory / CONTACT_SHEET_FILENAME,
    )
    manifest = write_motion_manifest(media_directory, report_directory)
    return animation, poster, viewer, contact, manifest


def main() -> int:
    animation, poster, viewer, contact, manifest = generate_motion_package()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    print(
        f"Task 10 motion generated: {animation} "
        f"({payload['animation']['width_px']}x{payload['animation']['height_px']}, "
        f"{payload['animation']['frame_count']} frames, "
        f"{payload['animation']['bytes']} bytes)"
    )
    print(f"Poster: {poster}")
    print(f"Offline viewer: {viewer}")
    print(f"Inspection sheet: {contact}")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CONTACT_SHEET_FILENAME",
    "MOTION_MANIFEST_FILENAME",
    "VIEWER_FILENAME",
    "build_motion_manifest",
    "generate_motion_package",
    "write_contact_sheet",
    "write_motion_manifest",
    "write_motion_viewer",
]
