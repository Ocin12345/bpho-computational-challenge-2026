from __future__ import annotations

import csv
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from task05_hydrogen_spectrum.generate_task05 import (
    DATA_FILENAMES,
    generate_task05_data,
    main,
)


class Task05GenerationTests(unittest.TestCase):
    def test_generation_writes_complete_parseable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "data"
            result = generate_task05_data(directory)
            self.assertTrue(result.report.passed)
            self.assertEqual(tuple(path.name for path in result.output_paths), DATA_FILENAMES)

            with (directory / "energy_levels.csv").open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 10)
            with (directory / "emission_transitions.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
                self.assertEqual(len(rows), 45)
                self.assertEqual((rows[0]["initial_n"], rows[0]["final_n"]), ("2", "1"))
                self.assertEqual((rows[-1]["initial_n"], rows[-1]["final_n"]), ("10", "9"))
            with (directory / "validation_report.json").open(encoding="utf-8") as handle:
                payload = json.load(handle)
                self.assertTrue(payload["passed"])
                self.assertEqual(len(payload["checks"]), 30)

    def test_repeated_generation_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "data"
            first = generate_task05_data(directory)
            first_bytes = {path.name: path.read_bytes() for path in first.output_paths}
            second = generate_task05_data(directory)
            second_bytes = {path.name: path.read_bytes() for path in second.output_paths}
            self.assertEqual(first_bytes, second_bytes)

    def test_late_failure_restores_every_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "data"
            directory.mkdir()
            originals = {}
            for index, filename in enumerate(DATA_FILENAMES):
                content = f"sentinel-{index}".encode()
                (directory / filename).write_bytes(content)
                originals[filename] = content

            from task05_hydrogen_spectrum import generate_task05 as module

            real_replace = module._replace_path
            calls = 0

            def failing_replace(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise OSError("injected late failure")
                real_replace(source, destination)

            with patch.object(module, "_replace_path", side_effect=failing_replace):
                with self.assertRaisesRegex(OSError, "injected late failure"):
                    generate_task05_data(directory)
            self.assertEqual(
                {filename: (directory / filename).read_bytes() for filename in DATA_FILENAMES},
                originals,
            )

    def test_data_only_cli_does_not_require_plotting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "data"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["--data-dir", str(directory), "--data-only"]), 0)
            self.assertEqual(
                tuple(path.name for path in sorted(directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )


if __name__ == "__main__":
    unittest.main()
