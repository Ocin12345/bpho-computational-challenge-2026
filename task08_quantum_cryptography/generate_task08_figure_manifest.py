"""Create the deterministic integrity manifest for Task 8 publication figures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from PIL import Image

from task08_quantum_cryptography.plotting import (
    FIGURE_FILENAMES,
    FIGURE_FONT_FAMILY,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIGURE_DIRECTORY = REPOSITORY_ROOT / "figures" / "task08"
REPRODUCIBLE_BUILD_TIMESTAMP_UTC = "2026-01-01T00:00:00Z"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_task08_figure_manifest(
    figure_directory: Path = DEFAULT_FIGURE_DIRECTORY,
) -> Path:
    """Validate and hash all accepted publication figure representations."""

    directory = Path(figure_directory)
    records: list[dict[str, object]] = []
    for filename in FIGURE_FILENAMES:
        path = directory / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"missing Task 8 figure: {path}")
        record: dict[str, object] = {
            "filename": filename,
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        if path.suffix == ".png":
            with Image.open(path) as image:
                dpi = image.info.get("dpi", (0.0, 0.0))
                record.update(
                    {
                        "format": image.format,
                        "width_px": image.width,
                        "height_px": image.height,
                        "dpi": [round(float(value), 3) for value in dpi],
                    }
                )
        elif path.suffix == ".svg":
            svg_text = path.read_text(encoding="utf-8")
            font_families = sorted(
                set(re.findall(r"font:[^;]+?'([^']+)'", svg_text))
            )
            if font_families != [FIGURE_FONT_FAMILY]:
                raise ValueError(
                    f"unexpected SVG font families in {filename}: {font_families}"
                )
            record.update(
                {
                    "format": "SVG",
                    "font_families": font_families,
                    "editable_text": True,
                }
            )
        else:
            pdf_bytes = path.read_bytes()
            if (
                not pdf_bytes.startswith(b"%PDF-")
                or b"TimesNewRoman" not in pdf_bytes
                or b"/FontFile2" not in pdf_bytes
            ):
                raise ValueError(
                    f"invalid PDF or missing embedded Times New Roman: {filename}"
                )
            record.update(
                {
                    "format": "PDF",
                    "font_family": FIGURE_FONT_FAMILY,
                    "editable_text": True,
                    "font_embedded": True,
                    "font_type": 42,
                }
            )
        records.append(record)

    payload = {
        "schema_version": "task08-figure-manifest-v2",
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "figure_font_family": FIGURE_FONT_FAMILY,
        "files": records,
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    path = generate_task08_figure_manifest()
    print(f"Task 8 figure manifest generated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
