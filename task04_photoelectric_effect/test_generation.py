"""Tests for deterministic validated Task 4 evidence generation."""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import fields, replace
from pathlib import Path
from unittest import mock

import numpy as np

from task04_photoelectric_effect.analysis import build_task04_study
from task04_photoelectric_effect.configuration import DEFAULT_CONFIGURATION
from task04_photoelectric_effect.generate_task04 import (
    DATA_FILENAMES,
    DEFAULT_DATA_DIRECTORY,
    FIGURE_FILENAMES,
    MATHEMATICAL_SPECIFICATION_PATH,
    OUTPUT_SCHEMA_VERSION,
    REPOSITORY_ROOT,
    Task04DataGenerationResult,
    generate_task04_data,
    main,
    write_task04_data,
)
from task04_photoelectric_effect.validation import validate_task04


def _csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or ()), list(reader)


def _assert_json_finite(test_case: unittest.TestCase, value: object) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _assert_json_finite(test_case, nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_json_finite(test_case, nested)
    elif isinstance(value, float):
        test_case.assertTrue(np.isfinite(value))


class Task04DataGenerationTests(unittest.TestCase):
    """Protect schemas, evidence values, transactions, and reproducibility."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()

    def test_generation_writes_ordered_complete_compact_file_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "data"
            result = write_task04_data(self.study, output_directory)

            self.assertIsInstance(result, Task04DataGenerationResult)
            self.assertTrue(result.report.passed)
            self.assertEqual(
                tuple(path.name for path in result.output_paths),
                DATA_FILENAMES,
            )
            self.assertTrue(all(path.is_file() for path in result.output_paths))
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )
            total_bytes = sum(path.stat().st_size for path in result.output_paths)
            self.assertLess(
                total_bytes,
                DEFAULT_CONFIGURATION.evidence_size_budget_bytes,
            )
            self.assertTrue(
                all(
                    (path.stat().st_mode & 0o777) == 0o644
                    for path in result.output_paths
                )
            )

    def test_material_cutoff_csv_schema_values_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task04_data(self.study, output_directory)
            header, rows = _csv_rows(output_directory / DATA_FILENAMES[0])

        self.assertEqual(
            header,
            [
                "material",
                "symbol",
                "work_function_ev",
                "work_function_j",
                "cutoff_frequency_hz",
                "cutoff_wavelength_nm",
            ],
        )
        self.assertEqual(len(rows), 9)
        self.assertEqual(
            [row["symbol"] for row in rows],
            ["Ag", "Al", "Au", "Cu", "Sn", "Pb", "W", "Ni", "Na"],
        )
        self.assertEqual(rows[0]["work_function_ev"], "4.3")
        self.assertEqual(rows[-1]["work_function_ev"], "2.4")
        for index, row in enumerate(rows):
            with self.subTest(symbol=row["symbol"]):
                self.assertEqual(
                    float(row["work_function_j"]),
                    float(self.study.work_functions_j[index]),
                )
                self.assertEqual(
                    float(row["cutoff_frequency_hz"]),
                    float(self.study.cutoff_frequencies_hz[index]),
                )
                self.assertEqual(
                    float(row["cutoff_wavelength_nm"]),
                    float(self.study.cutoff_wavelengths_nm[index]),
                )

    def test_frequency_csv_schema_rows_values_and_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task04_data(self.study, output_directory)
            header, rows = _csv_rows(output_directory / DATA_FILENAMES[1])

        self.assertEqual(
            header,
            [
                "material",
                "symbol",
                "frequency_hz",
                "linear_stopping_voltage_v",
                "emission_possible",
                "physical_stopping_voltage_v",
            ],
        )
        self.assertEqual(len(rows), 9 * 2001)
        self.assertEqual(
            (rows[0]["symbol"], rows[0]["frequency_hz"]),
            ("Ag", "400000000000000"),
        )
        self.assertEqual(
            (rows[2000]["symbol"], rows[2000]["frequency_hz"]),
            ("Ag", "2400000000000000"),
        )
        self.assertEqual(
            (rows[2001]["symbol"], rows[2001]["frequency_hz"]),
            ("Al", "400000000000000"),
        )
        self.assertEqual(rows[-1]["symbol"], "Na")
        for row_index in (0, 1000, 2000, 8004, len(rows) - 1):
            material_index, frequency_index = divmod(row_index, 2001)
            row = rows[row_index]
            with self.subTest(row=row_index):
                self.assertEqual(
                    float(row["frequency_hz"]),
                    float(self.study.frequency_hz[frequency_index]),
                )
                self.assertEqual(
                    float(row["linear_stopping_voltage_v"]),
                    float(
                        self.study.frequency_linear_voltage_v[
                            material_index,
                            frequency_index,
                        ]
                    ),
                )
        for row_index, row in enumerate(rows):
            material_index, frequency_index = divmod(row_index, 2001)
            expected_mask = bool(
                self.study.frequency_emission_mask[
                    material_index,
                    frequency_index,
                ]
            )
            self.assertEqual(row["emission_possible"], str(expected_mask).lower())
            if expected_mask:
                self.assertEqual(
                    float(row["physical_stopping_voltage_v"]),
                    float(
                        self.study.frequency_physical_voltage_v[
                            material_index,
                            frequency_index,
                        ]
                    ),
                )
            else:
                self.assertEqual(row["physical_stopping_voltage_v"], "")

    def test_wavelength_csv_schema_rows_values_and_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task04_data(self.study, output_directory)
            header, rows = _csv_rows(output_directory / DATA_FILENAMES[2])

        self.assertEqual(
            header,
            [
                "material",
                "symbol",
                "wavelength_nm",
                "linear_stopping_voltage_v",
                "emission_possible",
                "physical_stopping_voltage_v",
            ],
        )
        self.assertEqual(len(rows), 9 * 2201)
        self.assertEqual(
            (rows[0]["symbol"], rows[0]["wavelength_nm"]),
            ("Ag", "150"),
        )
        self.assertEqual(
            (rows[2200]["symbol"], rows[2200]["wavelength_nm"]),
            ("Ag", "700"),
        )
        self.assertEqual(
            (rows[2201]["symbol"], rows[2201]["wavelength_nm"]),
            ("Al", "150"),
        )
        self.assertEqual(rows[-1]["symbol"], "Na")
        for row_index in (0, 200, 2200, 8804, len(rows) - 1):
            material_index, wavelength_index = divmod(row_index, 2201)
            row = rows[row_index]
            with self.subTest(row=row_index):
                self.assertEqual(
                    float(row["wavelength_nm"]),
                    float(self.study.wavelength_nm[wavelength_index]),
                )
                self.assertEqual(
                    float(row["linear_stopping_voltage_v"]),
                    float(
                        self.study.wavelength_linear_voltage_v[
                            material_index,
                            wavelength_index,
                        ]
                    ),
                )
        for row_index, row in enumerate(rows):
            material_index, wavelength_index = divmod(row_index, 2201)
            expected_mask = bool(
                self.study.wavelength_emission_mask[
                    material_index,
                    wavelength_index,
                ]
            )
            self.assertEqual(row["emission_possible"], str(expected_mask).lower())
            if expected_mask:
                self.assertEqual(
                    float(row["physical_stopping_voltage_v"]),
                    float(
                        self.study.wavelength_physical_voltage_v[
                            material_index,
                            wavelength_index,
                        ]
                    ),
                )
            else:
                self.assertEqual(row["physical_stopping_voltage_v"], "")

    def test_validation_json_is_complete_ordered_finite_and_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task04_data(self.study, output_directory)
            text = (output_directory / DATA_FILENAMES[3]).read_text(
                encoding="utf-8"
            )
            payload = json.loads(text)

        expected_report = validate_task04(self.study)
        self.assertEqual(set(payload), {"schema_version", "passed", "checks"})
        self.assertEqual(payload["schema_version"], "task04-v1")
        self.assertIs(payload["passed"], True)
        self.assertEqual(len(payload["checks"]), 43)
        self.assertEqual(
            [check["name"] for check in payload["checks"]],
            [check.name for check in expected_report.checks],
        )
        self.assertEqual(
            set(payload["checks"][0]),
            {
                "name",
                "passed",
                "observed",
                "expected",
                "unit",
                "comparison",
                "tolerance",
                "explanation",
            },
        )
        self.assertTrue(text.endswith("\n"))
        _assert_json_finite(self, payload)

    def test_manifest_contains_complete_portable_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task04_data(self.study, output_directory)
            text = (output_directory / DATA_FILENAMES[4]).read_text(
                encoding="utf-8"
            )
            payload = json.loads(text)

        expected_configuration = {
            field.name: getattr(DEFAULT_CONFIGURATION, field.name)
            for field in fields(DEFAULT_CONFIGURATION)
        }
        self.assertEqual(payload["schema_version"], "task04-v1")
        self.assertEqual(payload["output_schema_version"], OUTPUT_SCHEMA_VERSION)
        self.assertEqual(payload["configuration"], expected_configuration)
        self.assertEqual(payload["expected_data_filenames"], list(DATA_FILENAMES))
        self.assertEqual(
            payload["expected_figure_filenames"],
            list(FIGURE_FILENAMES),
        )
        self.assertEqual(
            payload["mathematical_specification"],
            MATHEMATICAL_SPECIFICATION_PATH,
        )
        self.assertEqual(
            payload["material_source"],
            "BPhO CompPhys2026 Quantum, slide 28",
        )
        self.assertEqual(
            [material["symbol"] for material in payload["official_materials"]],
            ["Ag", "Al", "Au", "Cu", "Sn", "Pb", "W", "Ni", "Na"],
        )
        self.assertEqual(len(payload["constants"]), 8)
        self.assertIn("planck_constant_j_s", payload["constants"])
        self.assertIn("threshold_voltage_tolerance_v", payload["tolerances"])
        self.assertEqual(payload["units"]["frequency_hz"], "Hz")
        self.assertEqual(payload["units"]["emission_possible"], "boolean")
        for forbidden in (
            "/Users/",
            "timestamp",
            "hostname",
            "generated_at",
            "username",
        ):
            self.assertNotIn(forbidden, text)
        _assert_json_finite(self, payload)

    def test_outputs_are_byte_identical_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory:
            with tempfile.TemporaryDirectory() as second_directory:
                first = Path(first_directory)
                second = Path(second_directory)
                generate_task04_data(first)
                baseline = {
                    filename: (first / filename).read_bytes()
                    for filename in DATA_FILENAMES
                }
                generate_task04_data(second)
                for filename in DATA_FILENAMES:
                    self.assertEqual(
                        baseline[filename],
                        (second / filename).read_bytes(),
                    )
                generate_task04_data(first)
                for filename in DATA_FILENAMES:
                    self.assertEqual(
                        baseline[filename],
                        (first / filename).read_bytes(),
                    )

    def test_failed_validation_creates_nothing_and_preserves_existing_files(
        self,
    ) -> None:
        curve = self.study.frequency_linear_voltage_v.copy()
        curve[0, 500] += 0.25
        corrupted = replace(self.study, frequency_linear_voltage_v=curve)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            missing_directory = root / "missing"
            with self.assertRaisesRegex(RuntimeError, "validation failed"):
                write_task04_data(corrupted, missing_directory)
            self.assertFalse(missing_directory.exists())

            existing_directory = root / "existing"
            existing_directory.mkdir()
            existing = existing_directory / DATA_FILENAMES[0]
            existing.write_text("preserve me\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "validation failed"):
                write_task04_data(corrupted, existing_directory)
            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve me\n")
            self.assertEqual(tuple(existing_directory.iterdir()), (existing,))

    def test_writer_failure_preserves_all_destinations_and_cleans_siblings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            originals = {}
            for filename in DATA_FILENAMES:
                content = f"old {filename}\n".encode()
                originals[filename] = content
                (output_directory / filename).write_bytes(content)

            with mock.patch(
                "task04_photoelectric_effect.generate_task04."
                "_write_stopping_voltage_wavelength",
                side_effect=RuntimeError("injected writer failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected writer"):
                    write_task04_data(self.study, output_directory)

            for filename, content in originals.items():
                self.assertEqual((output_directory / filename).read_bytes(), content)
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )

    def test_install_failure_rolls_back_every_existing_destination(self) -> None:
        module = sys.modules["task04_photoelectric_effect.generate_task04"]
        real_replace = module._replace_path
        state = {"raised": False}

        def fail_second_install(source: Path, destination: Path) -> None:
            if (
                not state["raised"]
                and source.suffix == ".tmp"
                and destination.name == DATA_FILENAMES[1]
            ):
                state["raised"] = True
                raise OSError("injected install failure")
            real_replace(source, destination)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            originals = {}
            for filename in DATA_FILENAMES:
                content = f"original {filename}\n".encode()
                originals[filename] = content
                (output_directory / filename).write_bytes(content)

            with mock.patch.object(
                module,
                "_replace_path",
                side_effect=fail_second_install,
            ):
                with self.assertRaisesRegex(OSError, "injected install"):
                    write_task04_data(self.study, output_directory)

            self.assertTrue(state["raised"])
            for filename, content in originals.items():
                self.assertEqual((output_directory / filename).read_bytes(), content)
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )

    def test_verification_failure_occurs_before_destination_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            existing = output_directory / DATA_FILENAMES[0]
            existing.write_text("original\n", encoding="utf-8")
            with mock.patch(
                "task04_photoelectric_effect.generate_task04."
                "_verify_prepared_outputs",
                side_effect=ValueError("injected verification failure"),
            ):
                with self.assertRaisesRegex(ValueError, "injected verification"):
                    write_task04_data(self.study, output_directory)
            self.assertEqual(existing.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(tuple(output_directory.iterdir()), (existing,))

    def test_invalid_output_paths_fail_without_modifying_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            file_path = root / "not-a-directory"
            file_path.write_text("existing\n", encoding="utf-8")
            with self.assertRaises(NotADirectoryError):
                write_task04_data(self.study, file_path)
            self.assertEqual(file_path.read_text(encoding="utf-8"), "existing\n")

            output_directory = root / "data"
            output_directory.mkdir()
            destination_directory = output_directory / DATA_FILENAMES[0]
            destination_directory.mkdir()
            with self.assertRaises(IsADirectoryError):
                write_task04_data(self.study, output_directory)
            self.assertTrue(destination_directory.is_dir())
            self.assertEqual(
                tuple(output_directory.iterdir()),
                (destination_directory,),
            )

    def test_generation_rejects_invalid_public_arguments(self) -> None:
        with self.assertRaises(TypeError):
            generate_task04_data(configuration="default")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            write_task04_data("study")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            write_task04_data(self.study, None)  # type: ignore[arg-type]

    def test_generation_result_rejects_failed_or_misordered_records(self) -> None:
        passing_report = validate_task04(self.study)
        failed_check = replace(passing_report.checks[0], passed=False)
        failed_report = replace(
            passing_report,
            checks=(failed_check,) + passing_report.checks[1:],
        )
        with self.assertRaises(ValueError):
            Task04DataGenerationResult(
                failed_report,
                tuple(Path(x) for x in DATA_FILENAMES),
            )
        with self.assertRaises(ValueError):
            Task04DataGenerationResult(
                passing_report,
                tuple(Path(x) for x in reversed(DATA_FILENAMES)),
            )

    def test_data_only_cli_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = io.StringIO()
            with redirect_stdout(output):
                status = main(
                    ["--data-only", "--data-dir", temporary_directory]
                )
            self.assertEqual(status, 0)
            self.assertIn("Task 4 Stage 7", output.getvalue())
            self.assertIn("Validation checks: 43", output.getvalue())
            self.assertIn("Task 4 data generation: PASS", output.getvalue())
            self.assertEqual(
                tuple(
                    sorted(
                        path.name
                        for path in Path(temporary_directory).iterdir()
                    )
                ),
                tuple(sorted(DATA_FILENAMES)),
            )

    def test_data_only_subprocess_does_not_import_matplotlib(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = (
                "import sys\n"
                "from task04_photoelectric_effect.generate_task04 import main\n"
                f"status = main(['--data-only', '--data-dir', "
                f"{temporary_directory!r}])\n"
                "loaded = any(name == 'matplotlib' or "
                "name.startswith('matplotlib.') for name in sys.modules)\n"
                "print(f'matplotlib_loaded={loaded}')\n"
                "raise SystemExit(status)\n"
            )
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("matplotlib_loaded=False", completed.stdout)

    def test_custom_cli_output_is_independent_of_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as working_directory:
            with tempfile.TemporaryDirectory() as output_directory:
                script = (
                    "import sys\n"
                    f"sys.path.insert(0, {str(REPOSITORY_ROOT)!r})\n"
                    "from task04_photoelectric_effect.generate_task04 import main\n"
                    f"raise SystemExit(main(['--data-only', '--data-dir', "
                    f"{output_directory!r}]))\n"
                )
                completed = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=working_directory,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    tuple(
                        sorted(
                            path.name for path in Path(output_directory).iterdir()
                        )
                    ),
                    tuple(sorted(DATA_FILENAMES)),
                )
                self.assertEqual(tuple(Path(working_directory).iterdir()), ())

    def test_incomplete_stage_default_command_refuses_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "data"
            error = io.StringIO()
            with redirect_stderr(error):
                with self.assertRaises(SystemExit) as context:
                    main(["--data-dir", str(output_directory)])
            self.assertEqual(context.exception.code, 2)
            self.assertIn("use --data-only", error.getvalue())
            self.assertFalse(output_directory.exists())

    def test_unknown_cli_option_refuses_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "data"
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as context:
                    main(
                        [
                            "--data-only",
                            "--data-dir",
                            str(output_directory),
                            "--unknown",
                        ]
                    )
            self.assertEqual(context.exception.code, 2)
            self.assertFalse(output_directory.exists())

    def test_default_directory_is_repository_relative_and_absolute(self) -> None:
        self.assertTrue(DEFAULT_DATA_DIRECTORY.is_absolute())
        self.assertEqual(
            DEFAULT_DATA_DIRECTORY,
            REPOSITORY_ROOT / "data" / "task04",
        )

    def test_all_generated_text_files_use_only_lf_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            generate_task04_data(output_directory)
            for filename in DATA_FILENAMES:
                with self.subTest(filename=filename):
                    content = (output_directory / filename).read_bytes()
                    self.assertNotIn(b"\r\n", content)
                    self.assertTrue(content.endswith(b"\n"))

    def test_complete_generation_remains_below_runtime_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            start = time.perf_counter()
            result = generate_task04_data(temporary_directory)
            elapsed = time.perf_counter() - start
        self.assertTrue(result.report.passed)
        self.assertLess(elapsed, DEFAULT_CONFIGURATION.generation_runtime_budget_s)

    def test_committed_outputs_match_fresh_regeneration(self) -> None:
        committed_directory = REPOSITORY_ROOT / "data" / "task04"
        self.assertTrue(committed_directory.is_dir())
        with tempfile.TemporaryDirectory() as temporary_directory:
            generated_directory = Path(temporary_directory)
            generate_task04_data(generated_directory)
            for filename in DATA_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (committed_directory / filename).read_bytes(),
                        (generated_directory / filename).read_bytes(),
                    )


if __name__ == "__main__":
    unittest.main()
