"""Build and verify a clean, checksummed Tasks 1–10 evidence archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "BPhO_Computational_Challenge_2026"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
ROOT_FILES = (Path(".gitignore"), Path("README.md"), Path("requirements.txt"))
ROOT_DIRECTORIES = (
    Path("data"),
    Path("figures"),
    Path("reports"),
    Path("presentation"),
    Path("submission"),
    Path("task01_random_walk"),
    Path("task02_brownian_motion"),
    Path("task03_thermal_radiation"),
    Path("task04_photoelectric_effect"),
    Path("task05_hydrogen_spectrum"),
    Path("task06_electron_diffraction"),
    Path("task07_particle_in_box"),
    Path("task08_quantum_cryptography"),
    Path("task09_compton_scattering"),
    Path("task10_hydrogenic_orbitals"),
)
EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".analysis_cache",
    ".pytest_cache",
    ".venv",
    ".vscode",
    ".idea",
    "__pycache__",
    "node_modules",
    "venv",
    "env",
}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp", ".zip"}
STORED_SUFFIXES = {
    ".gif",
    ".jpg",
    ".jpeg",
    ".mp4",
    ".mov",
    ".pdf",
    ".png",
    ".pptx",
    ".svgz",
    ".webp",
}


def _include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return not (
        any(part in EXCLUDED_PARTS for part in relative.parts)
        or path.name in EXCLUDED_NAMES
        or path.suffix.lower() in EXCLUDED_SUFFIXES
        or path.is_symlink()
    )


def _release_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for relative in ROOT_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        files.append(path)
    for relative in ROOT_DIRECTORIES:
        directory = ROOT / relative
        if not directory.is_dir():
            raise FileNotFoundError(directory)
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file() and _include(path)
        )
    unique = {path.relative_to(ROOT).as_posix(): path for path in files}
    return tuple(unique[key] for key in sorted(unique))


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zip_info(name: str, *, stored: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    return info


def _manifest(files: Iterable[Path]) -> tuple[str, int]:
    lines: list[str] = []
    total = 0
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        size = path.stat().st_size
        total += size
        lines.append(f"{_sha256_file(path)}  {size:12d}  {relative}")
    return "\n".join(lines) + "\n", total


def build_archive(output_path: Path) -> tuple[int, int, str]:
    files = _release_files()
    manifest, total_bytes = _manifest(files)
    metadata = json.dumps(
        {
            "project": "BPhO Computational Challenge 2026 Tasks 1–10",
            "archive_date": date.today().isoformat(),
            "file_count": len(files),
            "uncompressed_file_bytes": total_bytes,
            "manifest": "SUBMISSION_MANIFEST.sha256",
            "zip_timestamps": "2026-01-01T00:00:00",
        },
        indent=2,
    ) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(
        temporary,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            archive_name = f"{ARCHIVE_ROOT}/{relative}"
            content = path.read_bytes()
            archive.writestr(
                _zip_info(
                    archive_name,
                    stored=path.suffix.lower() in STORED_SUFFIXES,
                ),
                content,
                compresslevel=9,
            )
        archive.writestr(
            _zip_info(f"{ARCHIVE_ROOT}/SUBMISSION_MANIFEST.sha256", stored=False),
            manifest.encode("utf-8"),
            compresslevel=9,
        )
        archive.writestr(
            _zip_info(f"{ARCHIVE_ROOT}/BUILD_METADATA.json", stored=False),
            metadata.encode("utf-8"),
            compresslevel=9,
        )
    temporary.replace(output_path)

    verify_archive(output_path)
    archive_digest = _sha256_file(output_path)
    sidecar = output_path.with_suffix(output_path.suffix + ".sha256")
    sidecar.write_text(
        f"{archive_digest}  {output_path.name}\n",
        encoding="utf-8",
    )
    return len(files), total_bytes, archive_digest


def verify_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise RuntimeError(f"corrupt ZIP member: {corrupt}")
        manifest_name = f"{ARCHIVE_ROOT}/SUBMISSION_MANIFEST.sha256"
        lines = archive.read(manifest_name).decode("utf-8").splitlines()
        for line in lines:
            expected_hash, size_text, relative = line.split(maxsplit=2)
            content = archive.read(f"{ARCHIVE_ROOT}/{relative}")
            if len(content) != int(size_text):
                raise RuntimeError(f"size mismatch: {relative}")
            if _sha256_bytes(content) != expected_hash:
                raise RuntimeError(f"SHA-256 mismatch: {relative}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a clean checksummed BPhO Tasks 1–10 evidence ZIP."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "release"
            / f"BPhO_Computational_Challenge_2026_{date.today().isoformat()}.zip"
        ),
        help="archive destination",
    )
    parser.add_argument(
        "--verify-only",
        type=Path,
        help="verify an existing archive instead of building one",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    if options.verify_only is not None:
        verify_archive(options.verify_only)
        print(f"Release archive verification: PASS\n{options.verify_only}")
        return 0

    output = options.output
    if not output.is_absolute():
        output = ROOT / output
    file_count, total_bytes, digest = build_archive(output)
    print("Release archive build: PASS")
    print(f"files: {file_count}")
    print(f"uncompressed evidence: {total_bytes:,} bytes")
    print(f"archive: {output}")
    print(f"SHA-256: {digest}")
    print(f"sidecar: {output.with_suffix(output.suffix + '.sha256')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
