"""Tests for deterministic validated Task 3 data generation."""

from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import fields, replace
from pathlib import Path
from unittest import mock

import numpy as np

from task03_thermal_radiation.analysis import (
    build_einstein_study,
    build_planck_study,
)
from task03_thermal_radiation.configuration import DEFAULT_CONFIGURATION
from task03_thermal_radiation.generate_task03 import (
    DATA_FILENAMES,
    MATHEMATICAL_SPECIFICATION_PATH,
    generate_task03_data,
    main,
    write_task03_data,
)


def _csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or ()), list(reader)


class Task03DataGenerationTests(unittest.TestCase):
    """Protect schemas, transactions, reproducibility, and CLI behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.planck_result = build_planck_study()
        cls.einstein_result = build_einstein_study()

    def test_generation_writes_ordered_complete_compact_file_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "data"
            result = write_task03_data(
                self.planck_result,
                self.einstein_result,
                output_directory,
            )

            self.assertTrue(result.report.passed)
            self.assertEqual(
                tuple(path.name for path in result.output_paths),
                DATA_FILENAMES,
            )
            self.assertTrue(all(path.is_file() for path in result.output_paths))
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )
            total_bytes = sum(path.stat().st_size for path in result.output_paths)
            self.assertLess(total_bytes, 10 * 1024 * 1024)

    def test_planck_csv_schemas_values_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task03_data(
                self.planck_result,
                self.einstein_result,
                output_directory,
            )

            header, spectra = _csv_rows(output_directory / DATA_FILENAMES[0])
            self.assertEqual(
                header,
                [
                    "temperature_k",
                    "wavelength_nm",
                    "spectral_exitance_w_m2_nm",
                ],
            )
            self.assertEqual(len(spectra), 3 * 2901)
            self.assertEqual(
                (spectra[0]["temperature_k"], spectra[0]["wavelength_nm"]),
                ("4000", "100"),
            )
            self.assertEqual(
                (
                    spectra[2900]["temperature_k"],
                    spectra[2900]["wavelength_nm"],
                ),
                ("4000", "3000"),
            )
            self.assertEqual(
                (
                    spectra[2901]["temperature_k"],
                    spectra[2901]["wavelength_nm"],
                ),
                ("5000", "100"),
            )
            self.assertEqual(
                float(spectra[-1]["spectral_exitance_w_m2_nm"]),
                float(self.planck_result.spectral_exitance_w_m2_nm[-1, -1]),
            )

            header, validation = _csv_rows(
                output_directory / DATA_FILENAMES[1]
            )
            self.assertEqual(
                header,
                [
                    "temperature_k",
                    "numerical_peak_nm",
                    "wien_peak_nm",
                    "peak_relative_error",
                    "numerical_exitance_w_m2",
                    "stefan_boltzmann_w_m2",
                    "integral_relative_error",
                ],
            )
            self.assertEqual(len(validation), 3)
            self.assertEqual(
                [row["temperature_k"] for row in validation],
                ["4000", "5000", "6000"],
            )
            self.assertEqual(
                float(validation[0]["numerical_peak_nm"]),
                float(self.planck_result.numerical_peak_wavelength_m[0] * 1.0e9),
            )

    def test_einstein_csv_schemas_values_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task03_data(
                self.planck_result,
                self.einstein_result,
                output_directory,
            )

            header, materials = _csv_rows(
                output_directory / DATA_FILENAMES[2]
            )
            self.assertEqual(
                header,
                [
                    "material",
                    "symbol",
                    "debye_temperature_k",
                    "einstein_temperature_k",
                    "einstein_frequency_hz",
                    "official_frequency_1e13_hz",
                ],
            )
            self.assertEqual(len(materials), 7)
            self.assertEqual(
                [row["symbol"] for row in materials],
                ["Au", "Cu", "Ti", "Al", "Fe", "Si", "C"],
            )
            self.assertEqual(materials[0]["official_frequency_1e13_hz"], "0.2855")
            self.assertEqual(materials[-1]["official_frequency_1e13_hz"], "3.7451")

            header, capacities = _csv_rows(
                output_directory / DATA_FILENAMES[3]
            )
            self.assertEqual(
                header,
                [
                    "material",
                    "symbol",
                    "temperature_k",
                    "molar_heat_capacity_j_mol_k",
                ],
            )
            self.assertEqual(len(capacities), 7 * 801)
            self.assertEqual(
                (capacities[0]["symbol"], capacities[0]["temperature_k"]),
                ("Au", "0"),
            )
            self.assertEqual(
                (capacities[800]["symbol"], capacities[800]["temperature_k"]),
                ("Au", "800"),
            )
            self.assertEqual(
                (capacities[801]["symbol"], capacities[801]["temperature_k"]),
                ("Cu", "0"),
            )
            self.assertEqual(float(capacities[0]["molar_heat_capacity_j_mol_k"]), 0.0)

            header, normalized = _csv_rows(
                output_directory / DATA_FILENAMES[4]
            )
            self.assertEqual(
                header,
                [
                    "material",
                    "symbol",
                    "reduced_temperature",
                    "normalized_heat_capacity",
                ],
            )
            self.assertEqual(len(normalized), 7 * 1001)
            self.assertEqual(
                (
                    normalized[1000]["symbol"],
                    normalized[1000]["reduced_temperature"],
                ),
                ("Au", "5"),
            )
            self.assertEqual(
                (
                    normalized[1001]["symbol"],
                    normalized[1001]["reduced_temperature"],
                ),
                ("Cu", "0"),
            )

    def test_validation_json_is_complete_finite_and_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task03_data(
                self.planck_result,
                self.einstein_result,
                output_directory,
            )
            path = output_directory / DATA_FILENAMES[5]
            text = path.read_text(encoding="utf-8")
            payload = json.loads(text)

            self.assertEqual(set(payload), {"schema_version", "passed", "checks"})
            self.assertEqual(payload["schema_version"], 1)
            self.assertIs(payload["passed"], True)
            self.assertEqual(len(payload["checks"]), 27)
            self.assertEqual(
                len({check["name"] for check in payload["checks"]}),
                27,
            )
            self.assertNotIn("NaN", text)
            self.assertNotIn("Infinity", text)
            self.assertTrue(text.endswith("\n"))

    def test_manifest_contains_complete_portable_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_task03_data(
                self.planck_result,
                self.einstein_result,
                output_directory,
            )
            path = output_directory / DATA_FILENAMES[6]
            text = path.read_text(encoding="utf-8")
            payload = json.loads(text)
            expected_configuration = {
                field.name: (
                    list(value) if isinstance(value, tuple) else value
                )
                for field in fields(DEFAULT_CONFIGURATION)
                for value in (getattr(DEFAULT_CONFIGURATION, field.name),)
            }

            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["configuration"], expected_configuration)
            self.assertEqual(payload["expected_output_filenames"], list(DATA_FILENAMES))
            self.assertEqual(
                payload["expected_figure_filenames"],
                [
                    "planck_spectra.png",
                    "planck_spectra.svg",
                    "planck_validation.png",
                    "planck_validation.svg",
                    "einstein_heat_capacity.png",
                    "einstein_heat_capacity.svg",
                    "einstein_normalized.png",
                    "einstein_normalized.svg",
                    "task03_summary.png",
                    "task03_summary.svg",
                ],
            )
            self.assertEqual(
                payload["mathematical_specification"],
                MATHEMATICAL_SPECIFICATION_PATH,
            )
            self.assertEqual(len(payload["official_materials"]), 7)
            self.assertEqual(payload["official_materials"][0]["symbol"], "Au")
            self.assertEqual(payload["official_materials"][-1]["symbol"], "C")
            self.assertIn("planck_constant_j_s", payload["constants"])
            self.assertIn("einstein_debye_factor", payload["constants"])
            for forbidden in ("/Users/", "timestamp", "hostname", "generated_at"):
                self.assertNotIn(forbidden, text)

    def test_outputs_are_byte_identical_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory:
            with tempfile.TemporaryDirectory() as second_directory:
                first = Path(first_directory)
                second = Path(second_directory)
                generate_task03_data(first)
                baseline = {
                    filename: (first / filename).read_bytes()
                    for filename in DATA_FILENAMES
                }
                generate_task03_data(second)
                for filename in DATA_FILENAMES:
                    self.assertEqual(
                        baseline[filename],
                        (second / filename).read_bytes(),
                    )

                generate_task03_data(first)
                for filename in DATA_FILENAMES:
                    self.assertEqual(
                        baseline[filename],
                        (first / filename).read_bytes(),
                    )

    def test_failed_validation_does_not_change_existing_outputs(self) -> None:
        incorrect_planck = replace(
            self.planck_result,
            numerical_peak_wavelength_m=(
                self.planck_result.numerical_peak_wavelength_m * 1.1
            ),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "data"
            output_directory.mkdir()
            existing = output_directory / DATA_FILENAMES[0]
            existing.write_text("preserve me\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "validation failed"):
                write_task03_data(
                    incorrect_planck,
                    self.einstein_result,
                    output_directory,
                )

            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve me\n")
            self.assertEqual(tuple(path.name for path in output_directory.iterdir()), (
                DATA_FILENAMES[0],
            ))

    def test_writer_failure_preserves_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            for filename in DATA_FILENAMES:
                (output_directory / filename).write_text(
                    f"old {filename}\n",
                    encoding="utf-8",
                )

            with mock.patch(
                "task03_thermal_radiation.generate_task03._write_einstein_normalized",
                side_effect=RuntimeError("injected writer failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    write_task03_data(
                        self.planck_result,
                        self.einstein_result,
                        output_directory,
                    )

            for filename in DATA_FILENAMES:
                self.assertEqual(
                    (output_directory / filename).read_text(encoding="utf-8"),
                    f"old {filename}\n",
                )
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )

    def test_data_only_cli_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--data-only",
                        "--data-dir",
                        temporary_directory,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Task 3 Stage 8", output.getvalue())
            self.assertIn("Validation checks: 27", output.getvalue())
            self.assertIn("Task 3 data generation: PASS", output.getvalue())
            self.assertEqual(
                tuple(path.name for path in sorted(
                    Path(temporary_directory).iterdir()
                )),
                tuple(sorted(DATA_FILENAMES)),
            )

    def test_data_only_subprocess_does_not_import_matplotlib(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = (
                "import sys\n"
                "from task03_thermal_radiation.generate_task03 import main\n"
                f"status = main(['--data-only', '--data-dir', "
                f"{temporary_directory!r}])\n"
                "loaded = any(name == 'matplotlib' or "
                "name.startswith('matplotlib.') for name in sys.modules)\n"
                "print(f'matplotlib_loaded={loaded}')\n"
                "raise SystemExit(status)\n"
            )
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=repository_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("matplotlib_loaded=False", completed.stdout)

    def test_file_output_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "not-a-directory"
            output_path.write_text("existing\n", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                write_task03_data(
                    self.planck_result,
                    self.einstein_result,
                    output_path,
                )

            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing\n")

    def test_committed_outputs_match_fresh_regeneration(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        committed_directory = repository_root / "data" / "task03"
        self.assertTrue(committed_directory.is_dir())

        with tempfile.TemporaryDirectory() as temporary_directory:
            generated_directory = Path(temporary_directory)
            generate_task03_data(generated_directory)
            for filename in DATA_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (committed_directory / filename).read_bytes(),
                        (generated_directory / filename).read_bytes(),
                    )

    def test_csv_files_use_only_lf_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            generate_task03_data(output_directory)

            for filename in DATA_FILENAMES[:5]:
                with self.subTest(filename=filename):
                    content = (output_directory / filename).read_bytes()
                    self.assertNotIn(b"\r\n", content)
                    self.assertTrue(content.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main()
