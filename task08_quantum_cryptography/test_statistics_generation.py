"""Tests for deterministic finite-photon evidence generation."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from task08_quantum_cryptography.generate_task08_statistics import (
    REFERENCE_EXPERIMENTS,
    STATISTICS_DATA_FILENAMES,
    generate_task08_statistics,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StatisticsGenerationTests(unittest.TestCase):
    def test_generation_is_complete_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "task08"
            first = generate_task08_statistics(output)
            self.assertTrue(first.report.passed)
            self.assertEqual(
                tuple(path.name for path in first.data_paths),
                STATISTICS_DATA_FILENAMES,
            )
            hashes = {path.name: _digest(path) for path in first.data_paths}
            second = generate_task08_statistics(output)
            self.assertEqual(
                hashes,
                {path.name: _digest(path) for path in second.data_paths},
            )

            reference = json.loads((output / STATISTICS_DATA_FILENAMES[0]).read_text())
            validation = json.loads((output / STATISTICS_DATA_FILENAMES[1]).read_text())
            manifest = json.loads((output / STATISTICS_DATA_FILENAMES[2]).read_text())
            self.assertEqual(len(reference["cases"]), len(REFERENCE_EXPERIMENTS))
            self.assertFalse(reference["cryptographic_security"])
            self.assertEqual(reference["cases"][0]["classical"]["mismatches"], 363)
            self.assertEqual(reference["cases"][0]["quantum"]["mismatches"], 770)
            self.assertTrue(validation["passed"])
            self.assertEqual(len(validation["checks"]), 24)
            self.assertEqual(len(manifest["sha256"]), 2)

    def test_wrong_configuration_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(TypeError):
                generate_task08_statistics(
                    Path(temporary),
                    object(),  # type: ignore[arg-type]
                )


if __name__ == "__main__":
    unittest.main()
