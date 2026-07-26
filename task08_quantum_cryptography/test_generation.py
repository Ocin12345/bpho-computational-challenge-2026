from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from task08_quantum_cryptography.generate_task08 import (
    ANGLE_SWEEP_HEADER,
    DATA_FILENAMES,
    MISMATCH_GRID_HEADER,
    _commit_all,
    _format_float,
    generate_task08,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GenerationTests(unittest.TestCase):
    def test_complete_generation_schemas_and_reproducibility(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            first = generate_task08(data)
            self.assertTrue(first.report.passed)
            self.assertEqual(tuple(path.name for path in first.data_paths), DATA_FILENAMES)

            with (data / "angle_sweep.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                self.assertEqual(tuple(rows[0]), ANGLE_SWEEP_HEADER)
                self.assertEqual(len(rows), 361)
            with (data / "mismatch_grid.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
                self.assertEqual(tuple(rows[0]), MISMATCH_GRID_HEADER)
                self.assertEqual(len(rows), 181 * 181)
            with (data / "reference_cases.json").open(encoding="utf-8") as handle:
                references = json.load(handle)
            self.assertEqual(len(references["cases"]), 5)
            with (data / "validation_report.json").open(encoding="utf-8") as handle:
                validation = json.load(handle)
            self.assertTrue(validation["passed"])
            self.assertEqual(len(validation["checks"]), 42)
            with (data / "manifest.json").open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["validation_check_count"], 42)
            self.assertEqual(len(manifest["sha256"]), 4)
            self.assertEqual(manifest["official_pages"], [53, 54, 55, 56, 57, 58])
            self.assertEqual(
                manifest["official_source_sha256"]
                ["BPhO_ComPhys_Challenge_2026.zip"],
                "330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667",
            )

            first_hashes = {path.name: _digest(path) for path in first.data_paths}
            second = generate_task08(data)
            second_hashes = {path.name: _digest(path) for path in second.data_paths}
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
                "task08_quantum_cryptography.generate_task08.os.replace",
                side_effect=flaky_replace,
            ):
                with self.assertRaises(OSError):
                    _commit_all(tuple(prepared))
            for index in range(4):
                self.assertEqual(
                    (destinations / f"file-{index}.txt").read_text(encoding="utf-8"),
                    f"old-{index}",
                )

    def test_non_finite_values_and_wrong_configuration_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _format_float(math.nan)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(TypeError):
                generate_task08(Path(temporary), object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
