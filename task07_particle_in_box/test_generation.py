from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from task07_particle_in_box.generate_task07 import (
    DATA_FILENAMES,
    _commit_all,
    generate_task07,
)
from task07_particle_in_box.plotting import FIGURE_FILENAMES


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GenerationTests(unittest.TestCase):
    def test_complete_generation_schemas_and_reproducibility(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            figures = root / "figures"
            first = generate_task07(data, figures)
            self.assertTrue(first.report.passed)
            self.assertEqual(tuple(path.name for path in first.data_paths), DATA_FILENAMES)
            self.assertEqual(tuple(path.name for path in first.figure_paths), FIGURE_FILENAMES)

            expected_rows = {
                "energy_levels.csv": 10,
                "stationary_states.csv": 8004,
                "expectation_values.csv": 10,
                "numerical_eigenvalues.csv": 50,
            }
            for filename, expected in expected_rows.items():
                with (data / filename).open(encoding="utf-8", newline="") as handle:
                    self.assertEqual(len(list(csv.DictReader(handle))), expected)
            with (data / "validation_report.json").open(encoding="utf-8") as handle:
                validation = json.load(handle)
            self.assertTrue(validation["passed"])
            self.assertEqual(len(validation["checks"]), 37)
            with (data / "manifest.json").open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["validation_check_count"], 37)
            self.assertEqual(len(manifest["sha256"]), 18)
            self.assertEqual(manifest["figure_font_family"], "Times New Roman")
            self.assertEqual(manifest["official_pages"], [48, 49])
            self.assertEqual(
                manifest["official_requirements"],
                "task07_particle_in_box/OFFICIAL_REQUIREMENTS.md",
            )
            self.assertEqual(
                manifest["official_source_sha256"]
                ["BPhO_ComPhys_Challenge_2026.zip"],
                "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667",
            )

            first_hashes = {
                path.name: _digest(path) for path in first.data_paths + first.figure_paths
            }
            second = generate_task07(data, figures)
            second_hashes = {
                path.name: _digest(path) for path in second.data_paths + second.figure_paths
            }
            self.assertEqual(first_hashes, second_hashes)

    def test_commit_rolls_back_after_late_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources = root / "sources"
            destinations = root / "destinations"
            sources.mkdir()
            destinations.mkdir()
            prepared = []
            for index in range(4):
                source = sources / f"file-{index}.txt"
                destination = destinations / f"file-{index}.txt"
                source.write_text(f"new-{index}", encoding="utf-8")
                destination.write_text(f"old-{index}", encoding="utf-8")
                prepared.append((source, destination))

            real_replace = os.replace
            calls = 0

            def flaky_replace(source: object, destination: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("forced late replacement failure")
                real_replace(source, destination)

            with patch(
                "task07_particle_in_box.generate_task07.os.replace",
                side_effect=flaky_replace,
            ):
                with self.assertRaises(OSError):
                    _commit_all(tuple(prepared))
            for index in range(4):
                self.assertEqual(
                    (destinations / f"file-{index}.txt").read_text(encoding="utf-8"),
                    f"old-{index}",
                )


if __name__ == "__main__":
    unittest.main()
