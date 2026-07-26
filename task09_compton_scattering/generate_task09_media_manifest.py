"""Create a deterministic integrity manifest for the Task 9 media package."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from task09_compton_scattering.analysis import build_task09_study
from task09_compton_scattering.animation import ANIMATION_FILENAME
from task09_compton_scattering.configuration import DEFAULT_CONFIGURATION
from task09_compton_scattering.cross_section import build_klein_nishina_study
from task09_compton_scattering.cross_section_validation import (
    cross_section_study_digest,
    validate_cross_section_study,
)
from task09_compton_scattering.plotting import FIGURE_FILENAMES, FIGURE_FONT_FAMILY
from task09_compton_scattering.validation import task09_study_digest, validate_task09


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MEDIA_DIRECTORY = REPOSITORY_ROOT / "figures" / "task09"
MANIFEST_FILENAME = "manifest.json"
MEDIA_FILENAMES = (*FIGURE_FILENAMES, ANIMATION_FILENAME)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_media_manifest(media_directory: Path = DEFAULT_MEDIA_DIRECTORY) -> dict:
    """Return the complete manifest after verifying every expected media file."""

    directory = Path(media_directory)
    missing = [name for name in MEDIA_FILENAMES if not (directory / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing Task 9 media: {', '.join(missing)}")

    study = build_task09_study()
    report = validate_task09(study)
    cross_section_study = build_klein_nishina_study(
        study.incident_energy_kev,
        study.theta_deg,
    )
    cross_section_report = validate_cross_section_study(cross_section_study)
    if not report.passed or not cross_section_report.passed:
        raise RuntimeError("media manifest requires passing scientific reports")

    files = []
    for name in MEDIA_FILENAMES:
        path = directory / name
        record = {
            "filename": name,
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        if path.suffix == ".png":
            with Image.open(path) as image:
                record.update(
                    {
                        "media_type": "image/png",
                        "width_px": image.width,
                        "height_px": image.height,
                        "dpi": [round(float(value), 3) for value in image.info["dpi"]],
                    }
                )
        elif path.suffix == ".svg":
            root = ET.parse(path).getroot()
            if not root.tag.endswith("svg"):
                raise ValueError(f"invalid SVG root: {name}")
            font_families = sorted(
                set(re.findall(r"font:[^;]+?'([^']+)'", path.read_text(encoding="utf-8")))
            )
            if font_families != [FIGURE_FONT_FAMILY]:
                raise ValueError(
                    f"unexpected SVG font families in {name}: {font_families}"
                )
            record.update(
                {
                    "media_type": "image/svg+xml",
                    "scalable": True,
                    "view_box": root.attrib.get("viewBox"),
                    "font_families": font_families,
                    "editable_text": True,
                }
            )
        elif path.suffix == ".pdf":
            pdf_bytes = path.read_bytes()
            if (
                not pdf_bytes.startswith(b"%PDF-")
                or b"TimesNewRoman" not in pdf_bytes
                or b"/FontFile2" not in pdf_bytes
            ):
                raise ValueError(
                    f"invalid PDF or missing embedded Times New Roman: {name}"
                )
            record.update(
                {
                    "media_type": "application/pdf",
                    "font_family": FIGURE_FONT_FAMILY,
                    "font_embedded": True,
                    "font_type": 42,
                    "editable_text": True,
                }
            )
        else:
            with Image.open(path) as image:
                record.update(
                    {
                        "media_type": "image/gif",
                        "width_px": image.width,
                        "height_px": image.height,
                        "frame_count": image.n_frames,
                        "configured_frames_per_second": (
                            DEFAULT_CONFIGURATION.animation_frames_per_second
                        ),
                        "stored_frame_duration_ms": image.info.get("duration"),
                        "continuous_loop": image.info.get("loop") == 0,
                    }
                )
        files.append(record)

    return {
        "schema_version": "task09-media-manifest-v2",
        "scientific_evidence": {
            "kinematic_study_sha256": task09_study_digest(study),
            "kinematic_checks": {
                "passed": sum(check.passed for check in report.checks),
                "total": len(report.checks),
            },
            "cross_section_study_sha256": cross_section_study_digest(
                cross_section_study
            ),
            "cross_section_checks": {
                "passed": sum(check.passed for check in cross_section_report.checks),
                "total": len(cross_section_report.checks),
            },
        },
        "rendering_contract": {
            "font_family": FIGURE_FONT_FAMILY,
            "figure_dpi": DEFAULT_CONFIGURATION.figure_dpi,
            "standard_raster_px": [
                DEFAULT_CONFIGURATION.figure_width_px,
                DEFAULT_CONFIGURATION.figure_height_px,
            ],
            "summary_raster_px": [
                DEFAULT_CONFIGURATION.summary_width_px,
                DEFAULT_CONFIGURATION.summary_height_px,
            ],
            "animation_px": [
                DEFAULT_CONFIGURATION.animation_width_px,
                DEFAULT_CONFIGURATION.animation_height_px,
            ],
            "animation_frame_count": DEFAULT_CONFIGURATION.animation_frame_count,
        },
        "files": files,
        "total_bytes": sum(record["bytes"] for record in files),
    }


def write_media_manifest(media_directory: Path = DEFAULT_MEDIA_DIRECTORY) -> Path:
    directory = Path(media_directory)
    manifest = build_media_manifest(directory)
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / MANIFEST_FILENAME
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".task09-manifest-",
            suffix=".json",
            dir=directory,
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, destination)
        destination.chmod(0o644)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return destination


def main() -> int:
    path = write_media_manifest()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    print(
        f"Task 9 media manifest: {len(manifest['files'])} files, "
        f"{manifest['total_bytes']} bytes, all scientific gates passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "MANIFEST_FILENAME",
    "MEDIA_FILENAMES",
    "build_media_manifest",
    "write_media_manifest",
]
