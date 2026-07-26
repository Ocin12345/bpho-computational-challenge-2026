from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from task06_electron_diffraction.generate_task06 import (
    DATA_FILENAMES,
    _commit_all,
    generate_task06,
)
from task06_electron_diffraction.plotting import FIGURE_FILENAMES


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GenerationTests(unittest.TestCase):
    def test_complete_generation_schemas_and_reproducibility(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            figures = root / "figures"
            first = generate_task06(data, figures)
            self.assertTrue(first.report.passed)
            self.assertEqual(tuple(path.name for path in first.data_paths), DATA_FILENAMES)
            self.assertEqual(tuple(path.name for path in first.figure_paths), FIGURE_FILENAMES)

            with (data / "voltage_sweep.csv").open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 401)
            with (data / "diffraction_orders.csv").open(encoding="utf-8", newline="") as handle:
                order_rows = list(csv.DictReader(handle))
            self.assertEqual(len(order_rows), 11386)
            self.assertEqual(order_rows[0]["spacing_id"], "d1")
            self.assertEqual(order_rows[0]["order_n"], "1")
            with (data / "validation_fits.csv").open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 4)

            with (data / "validation_report.json").open(encoding="utf-8") as handle:
                validation = json.load(handle)
            self.assertTrue(validation["passed"])
            self.assertEqual(len(validation["checks"]), 39)
            with (data / "manifest.json").open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["catalogue_size"], 11386)
            self.assertEqual(manifest["forward_screen_count"], 7927)

            first_hashes = {
                path.name: _digest(path)
                for path in first.data_paths + first.figure_paths
            }
            second = generate_task06(data, figures)
            second_hashes = {
                path.name: _digest(path)
                for path in second.data_paths + second.figure_paths
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
                "task06_electron_diffraction.generate_task06.os.replace",
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
