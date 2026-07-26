"""Generate the deterministic Task 7 report integrity manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_DIRECTORY = REPOSITORY_ROOT / "reports/task07"
REPORT_FILENAMES = (
    "particle_in_box_uncertainty.tex",
    "particle_in_box_uncertainty.pdf",
    "particle_in_box_uncertainty_accessible.md",
)
MANIFEST_FILENAME = "manifest.json"
REPRODUCIBLE_BUILD_TIMESTAMP_UTC = "2026-01-01T00:00:00Z"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pdf_metadata(path: Path) -> dict[str, object]:
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo is None:
        raise RuntimeError("pdfinfo is required to validate the Task 7 PDF")
    completed = subprocess.run(
        [pdfinfo, str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    fields: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    required = ("Pages", "Page size", "Tagged", "PDF version")
    if any(key not in fields for key in required):
        raise ValueError("pdfinfo did not return the required Task 7 PDF fields")
    return {
        "pages": int(fields["Pages"]),
        "page_size": fields["Page size"],
        "tagged": fields["Tagged"].lower() == "yes",
        "pdf_version": fields["PDF version"],
    }


def generate_report_manifest(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> Path:
    """Hash all report representations and record the accepted PDF properties."""

    directory = Path(report_directory)
    paths = tuple(directory / filename for filename in REPORT_FILENAMES)
    missing = tuple(path.name for path in paths if not path.is_file())
    if missing:
        raise FileNotFoundError(f"missing Task 7 report files: {', '.join(missing)}")
    if any(path.stat().st_size == 0 for path in paths):
        raise ValueError("Task 7 report files must be non-empty")

    pdf = paths[1]
    metadata = _pdf_metadata(pdf)
    if metadata["pages"] != 4 or "A4" not in str(metadata["page_size"]):
        raise ValueError("accepted Task 7 PDF must be four A4 pages")

    payload = {
        "schema_version": "task07-report-manifest-v1",
        "reproducible_build_timestamp_utc": REPRODUCIBLE_BUILD_TIMESTAMP_UTC,
        "report_title": "Particle in a One-Dimensional Box",
        "files": [
            {
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in paths
        ],
        "pdf": metadata,
        "accessibility": {
            "pdf_structurally_tagged": metadata["tagged"],
            "semantic_alternative": REPORT_FILENAMES[2],
            "alternative_required_for_handoff": True,
            "figure_descriptions_present": True,
        },
    }

    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / MANIFEST_FILENAME
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=directory,
        prefix=f".{MANIFEST_FILENAME}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-directory",
        type=Path,
        default=DEFAULT_REPORT_DIRECTORY,
    )
    arguments = parser.parse_args()
    path = generate_report_manifest(arguments.report_directory)
    print(f"Task 7 report manifest generated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_REPORT_DIRECTORY",
    "MANIFEST_FILENAME",
    "REPORT_FILENAMES",
    "generate_report_manifest",
]
