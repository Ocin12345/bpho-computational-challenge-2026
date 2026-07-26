"""Tests for deterministic Task 9 cross-section extension generation."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from task09_compton_scattering.generate_task09_cross_section import (
    CROSS_SECTION_FILENAMES,
    CROSS_SECTION_STUDY_HEADER,
    CROSS_SECTION_SUMMARY_HEADER,
    generate_task09_cross_section,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CrossSectionGenerationTests(unittest.TestCase):
    def test_complete_extension_package_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "data"
            first = generate_task09_cross_section(output)
            self.assertTrue(first.report.passed)
            self.assertEqual(
                tuple(path.name for path in first.data_paths),
                CROSS_SECTION_FILENAMES,
            )
            with (output / CROSS_SECTION_FILENAMES[0]).open(
                encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(tuple(rows[0]), CROSS_SECTION_STUDY_HEADER)
            self.assertEqual(len(rows), 3_605)
            with (output / CROSS_SECTION_FILENAMES[1]).open(
                encoding="utf-8", newline=""
            ) as handle:
                summary = list(csv.DictReader(handle))
            self.assertEqual(tuple(summary[0]), CROSS_SECTION_SUMMARY_HEADER)
            self.assertEqual(len(summary), 5)
            with (output / CROSS_SECTION_FILENAMES[2]).open(encoding="utf-8") as handle:
                validation = json.load(handle)
            self.assertTrue(validation["passed"])
            self.assertEqual(len(validation["checks"]), 30)
            with (output / CROSS_SECTION_FILENAMES[3]).open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(len(manifest["sha256"]), 3)

            first_hashes = {path.name: _digest(path) for path in first.data_paths}
            second = generate_task09_cross_section(output)
            second_hashes = {path.name: _digest(path) for path in second.data_paths}
            self.assertEqual(first_hashes, second_hashes)

    def test_wrong_configuration_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(TypeError):
                generate_task09_cross_section(
                    Path(temporary),
                    object(),  # type: ignore[arg-type]
                )


if __name__ == "__main__":
    unittest.main()
