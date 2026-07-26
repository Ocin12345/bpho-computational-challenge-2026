"""Read-only validation of the generated Task 10 motion package."""

from __future__ import annotations

import json

from task10_hydrogenic_orbitals.generate_task10_motion import (
    DEFAULT_MEDIA_DIRECTORY,
    DEFAULT_REPORT_DIRECTORY,
    MOTION_MANIFEST_FILENAME,
    build_motion_manifest,
)


def main() -> int:
    stored_path = DEFAULT_MEDIA_DIRECTORY / MOTION_MANIFEST_FILENAME
    if not stored_path.is_file():
        print(f"FAIL missing motion manifest: {stored_path}")
        return 1
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    observed = build_motion_manifest(DEFAULT_MEDIA_DIRECTORY, DEFAULT_REPORT_DIRECTORY)
    if stored != observed:
        print("FAIL motion manifest does not match current media")
        return 1
    print(
        "Task 10 motion validation: PASS "
        f"({observed['animation']['width_px']}x{observed['animation']['height_px']}; "
        f"{observed['animation']['frame_count']} frames; continuous loop; "
        "reduced-motion poster present)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
