"""Tests for deterministic transactional Task 10 generation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from task10_hydrogenic_orbitals.generate_task10 import (
    DATA_FILENAMES,
    _commit_all,
    generate_task10,
)


class GenerationTests(unittest.TestCase):
    def test_complete_package_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first_name, tempfile.TemporaryDirectory() as second_name:
            first = generate_task10(Path(first_name))
            second = generate_task10(Path(second_name))
            self.assertTrue(first.validation_report.passed)
            self.assertEqual(len(first.files), 7)
            for name in DATA_FILENAMES:
                self.assertEqual(
                    (Path(first_name) / name).read_bytes(),
                    (Path(second_name) / name).read_bytes(),
                    msg=name,
                )
            manifest = json.loads(
                (Path(first_name) / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["validation"]["check_count"], 22)
            self.assertTrue(manifest["validation"]["passed"])
            self.assertEqual(len(manifest["sha256"]), 6)

    def test_commit_rolls_back_after_late_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            sources = []
            destinations = []
            for index in range(3):
                source = directory / f"source-{index}"
                destination = directory / f"destination-{index}"
                source.write_bytes(f"new-{index}".encode())
                destination.write_bytes(f"old-{index}".encode())
                sources.append(source)
                destinations.append(destination)

            calls = 0

            def failing_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected late replacement failure")
                Path(destination).write_bytes(Path(source).read_bytes())
                Path(source).unlink()

            with self.assertRaisesRegex(OSError, "injected"):
                _commit_all(
                    tuple(zip(sources, destinations)),
                    replace=failing_replace,
                )
            for index, destination in enumerate(destinations):
                self.assertEqual(destination.read_bytes(), f"old-{index}".encode())

    def test_failed_scientific_report_prevents_generation(self) -> None:
        fake_report = SimpleNamespace(
            passed=False,
            failed_checks=(SimpleNamespace(name="corrupt"),),
        )
        with tempfile.TemporaryDirectory() as name:
            with mock.patch(
                "task10_hydrogenic_orbitals.generate_task10.validate_task10",
                return_value=fake_report,
            ):
                with self.assertRaises(RuntimeError):
                    generate_task10(Path(name))
            self.assertEqual(list(Path(name).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
