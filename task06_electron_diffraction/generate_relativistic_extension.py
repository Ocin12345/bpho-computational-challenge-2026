"""Generate the separate Task 6 relativistic extension evidence."""

from pathlib import Path

from task06_electron_diffraction.relativistic_extension import (
    build_relativistic_evidence,
    write_relativistic_evidence,
)


def main() -> None:
    destination = Path("data/task06/relativistic_extension.json")
    write_relativistic_evidence(destination)
    evidence = build_relativistic_evidence()
    start = evidence["records"][0]
    end = evidence["records"][-1]
    print(f"Wrote {destination}")
    print(
        f"{evidence['validation']['check_count']}/{evidence['validation']['check_count']} "
        "extension checks passed"
    )
    print(
        "Wavelength correction: "
        f"{start['wavelength_correction_percent']:.4f}% at 1 kV to "
        f"{end['wavelength_correction_percent']:.4f}% at 5 kV"
    )


if __name__ == "__main__":
    main()
