"""Tests for deterministic Task 9 data generation and atomic commit."""

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

from task09_compton_scattering.generate_task09 import (
    ANGLE_STUDY_HEADER,
    DATA_FILENAMES,
    ENERGY_SUMMARY_HEADER,
    _commit_all,
    _format_float,
    generate_task09,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GenerationTests(unittest.TestCase):
    def test_complete_generation_schemas_and_reproducibility(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            first = generate_task09(data)
            self.assertTrue(first.report.passed)
            self.assertEqual(tuple(path.name for path in first.data_paths), DATA_FILENAMES)

            with (data / "compton_angle_study.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(tuple(rows[0]), ANGLE_STUDY_HEADER)
            self.assertEqual(len(rows), 3_605)
            with (data / "energy_summary.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                summary = list(csv.DictReader(handle))
            self.assertEqual(tuple(summary[0]), ENERGY_SUMMARY_HEADER)
            self.assertEqual(len(summary), 5)
            with (data / "reference_anchors.json").open(encoding="utf-8") as handle:
                references = json.load(handle)
            self.assertEqual(len(references["anchors"]), 15)
            with (data / "validation_report.json").open(encoding="utf-8") as handle:
                validation = json.load(handle)
            self.assertTrue(validation["passed"])
            self.assertEqual(len(validation["checks"]), 44)
            with (data / "manifest.json").open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["validation_check_count"], 44)
            self.assertEqual(len(manifest["sha256"]), 4)

            first_hashes = {path.name: _digest(path) for path in first.data_paths}
            second = generate_task09(data)
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
                "task09_compton_scattering.generate_task09.os.replace",
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
                generate_task09(Path(temporary), object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
