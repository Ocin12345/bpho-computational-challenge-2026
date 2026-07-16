"""Tests for independent Task 4 references and validation."""

from __future__ import annotations

import contextlib
import importlib
import io
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest import mock

import numpy as np

from task04_photoelectric_effect.analysis import build_task04_study
from task04_photoelectric_effect.configuration import DEFAULT_CONFIGURATION
from task04_photoelectric_effect.materials import PhotoelectricMaterial
from task04_photoelectric_effect.reference import (
    reference_common_gradient_v_s,
    reference_cutoff_frequency_hz,
    reference_cutoff_wavelength_nm,
    reference_voltage_at_frequency_v,
    reference_voltage_at_wavelength_v,
)
from task04_photoelectric_effect.validation import (
    Task04ValidationReport,
    ValidationCheck,
    validate_task04,
)


EXPECTED_CHECK_NAMES = (
    "exact_constants",
    "official_material_table",
    "work_function_joules",
    "frequency_grid",
    "wavelength_grid",
    "frequency_finiteness",
    "wavelength_finiteness",
    "frequency_energy_identity",
    "wavelength_energy_identity",
    "common_frequency_gradient",
    "cutoff_frequency_ag",
    "cutoff_frequency_al",
    "cutoff_frequency_au",
    "cutoff_frequency_cu",
    "cutoff_frequency_sn",
    "cutoff_frequency_pb",
    "cutoff_frequency_w",
    "cutoff_frequency_ni",
    "cutoff_frequency_na",
    "cutoff_wavelength_ag",
    "cutoff_wavelength_al",
    "cutoff_wavelength_au",
    "cutoff_wavelength_cu",
    "cutoff_wavelength_sn",
    "cutoff_wavelength_pb",
    "cutoff_wavelength_w",
    "cutoff_wavelength_ni",
    "cutoff_wavelength_na",
    "threshold_frequency_voltage",
    "threshold_wavelength_voltage",
    "frequency_emission_mask",
    "wavelength_emission_mask",
    "frequency_physical_voltage",
    "wavelength_physical_voltage",
    "frequency_physical_bounds",
    "wavelength_physical_bounds",
    "frequency_monotonicity",
    "wavelength_monotonicity",
    "duplicate_materials",
    "cutoff_ordering",
    "frequency_wavelength_consistency",
    "frequency_anchor",
    "wavelength_anchor",
)


class DecimalReferenceTests(unittest.TestCase):
    """Prove that the scalar reference path matches frozen analytical values."""

    def test_decimal_references_match_declared_values(self) -> None:
        self.assertAlmostEqual(
            reference_common_gradient_v_s(),
            4.135667696923859e-15,
            places=29,
        )
        self.assertAlmostEqual(
            reference_cutoff_frequency_hz(4.3),
            1.0397353740965148e15,
            delta=0.25,
        )
        self.assertAlmostEqual(
            reference_cutoff_wavelength_nm(4.3),
            288.335345193489,
            places=12,
        )
        self.assertAlmostEqual(
            reference_voltage_at_frequency_v(1.5e15, 4.3),
            1.9035015453857885,
            places=14,
        )
        self.assertAlmostEqual(
            reference_voltage_at_wavelength_v(200.0, 4.3),
            1.899209921660013,
            places=14,
        )

    def test_reference_thresholds_evaluate_to_numerical_zero(self) -> None:
        for work_function in (2.4, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1):
            with self.subTest(work_function=work_function):
                frequency = reference_cutoff_frequency_hz(work_function)
                wavelength = reference_cutoff_wavelength_nm(work_function)
                self.assertLess(
                    abs(
                        reference_voltage_at_frequency_v(
                            frequency,
                            work_function,
                        )
                    ),
                    2.0e-15,
                )
                self.assertLess(
                    abs(
                        reference_voltage_at_wavelength_v(
                            wavelength,
                            work_function,
                        )
                    ),
                    2.0e-15,
                )

    def test_reference_functions_reject_invalid_types_and_domains(self) -> None:
        with self.assertRaises(TypeError):
            reference_cutoff_frequency_hz(True)
        with self.assertRaises(TypeError):
            reference_cutoff_wavelength_nm("4.3")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            reference_cutoff_frequency_hz(0.0)
        with self.assertRaises(ValueError):
            reference_cutoff_wavelength_nm(float("nan"))
        with self.assertRaises(ValueError):
            reference_voltage_at_frequency_v(-1.0, 4.3)
        with self.assertRaises(ValueError):
            reference_voltage_at_frequency_v(float("inf"), 4.3)
        with self.assertRaises(ValueError):
            reference_voltage_at_wavelength_v(0.0, 4.3)
        with self.assertRaises(TypeError):
            reference_voltage_at_wavelength_v(200.0, False)

    def test_reference_source_executes_without_numpy(self) -> None:
        reference_path = Path(__file__).resolve().parent / "reference.py"
        script = (
            "import runpy, sys\n"
            f"runpy.run_path({str(reference_path)!r})\n"
            "assert 'numpy' not in sys.modules\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


class ValidationRecordTests(unittest.TestCase):
    """Check immutable validation-record boundaries."""

    def setUp(self) -> None:
        self.check = ValidationCheck(
            name="example_check",
            passed=True,
            observed=0.0,
            expected=0.0,
            unit="V",
            comparison="absolute_error_lte",
            tolerance=1.0e-12,
            explanation="Example complete scientific explanation.",
        )

    def test_check_is_frozen_and_normalizes_real_scalars(self) -> None:
        self.assertIsInstance(self.check.observed, float)
        with self.assertRaises(FrozenInstanceError):
            self.check.passed = False  # type: ignore[misc]

    def test_check_rejects_invalid_fields(self) -> None:
        with self.assertRaises(ValueError):
            replace(self.check, name="Not-Snake-Case")
        with self.assertRaises(TypeError):
            replace(self.check, passed=1)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            replace(self.check, observed=float("nan"))
        with self.assertRaises(ValueError):
            replace(self.check, tolerance=-1.0)
        with self.assertRaises(ValueError):
            replace(self.check, explanation="  ")

    def test_report_freezes_iterables_and_derives_overall_state(self) -> None:
        report = Task04ValidationReport(
            "task04-v1",
            [self.check],  # type: ignore[arg-type]
        )
        self.assertIsInstance(report.checks, tuple)
        self.assertTrue(report.passed)
        self.assertEqual(report.failed_checks, ())
        with self.assertRaises(FrozenInstanceError):
            report.checks = ()  # type: ignore[misc]

        failed = replace(self.check, name="failed_check", passed=False)
        failed_report = Task04ValidationReport("task04-v1", (self.check, failed))
        self.assertFalse(failed_report.passed)
        self.assertEqual(failed_report.failed_checks, (failed,))

    def test_report_rejects_schema_empty_wrong_and_duplicate_checks(self) -> None:
        with self.assertRaises(ValueError):
            Task04ValidationReport("wrong", (self.check,))
        with self.assertRaises(ValueError):
            Task04ValidationReport("task04-v1", ())
        with self.assertRaises(TypeError):
            Task04ValidationReport("task04-v1", ("check",))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Task04ValidationReport("task04-v1", (self.check, self.check))


class CompleteValidationTests(unittest.TestCase):
    """Check the complete baseline report and its scientific tolerances."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()
        cls.report = validate_task04(cls.study)

    def test_default_report_passes_all_43_checks(self) -> None:
        self.assertEqual(len(self.report.checks), 43)
        self.assertTrue(self.report.passed)
        self.assertEqual(self.report.failed_checks, ())
        self.assertTrue(all(check.passed for check in self.report.checks))

    def test_check_names_and_order_are_frozen(self) -> None:
        self.assertEqual(
            tuple(check.name for check in self.report.checks),
            EXPECTED_CHECK_NAMES,
        )

    def test_every_check_has_complete_finite_metadata(self) -> None:
        for check in self.report.checks:
            with self.subTest(check=check.name):
                self.assertTrue(np.isfinite(check.observed))
                self.assertTrue(np.isfinite(check.expected))
                self.assertTrue(np.isfinite(check.tolerance))
                self.assertGreaterEqual(check.tolerance, 0.0)
                self.assertTrue(check.unit)
                self.assertTrue(check.comparison)
                self.assertTrue(check.explanation)

    def test_repeated_validation_is_exactly_deterministic(self) -> None:
        self.assertEqual(validate_task04(self.study), self.report)

    def test_validation_does_not_mutate_any_study_array(self) -> None:
        array_fields = (
            "work_functions_ev",
            "work_functions_j",
            "cutoff_frequencies_hz",
            "cutoff_wavelengths_nm",
            "frequency_hz",
            "frequency_linear_voltage_v",
            "frequency_emission_mask",
            "frequency_physical_voltage_v",
            "wavelength_m",
            "wavelength_nm",
            "wavelength_linear_voltage_v",
            "wavelength_emission_mask",
            "wavelength_physical_voltage_v",
        )
        before = {
            field_name: getattr(self.study, field_name).tobytes()
            for field_name in array_fields
        }
        validate_task04(self.study)
        for field_name in array_fields:
            with self.subTest(field=field_name):
                array = getattr(self.study, field_name)
                self.assertEqual(array.tobytes(), before[field_name])
                self.assertFalse(array.flags.writeable)

    def test_build_and_validation_remain_below_runtime_budget(self) -> None:
        start = time.perf_counter()
        validate_task04(build_task04_study())
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, DEFAULT_CONFIGURATION.study_runtime_budget_s)

    def test_validator_rejects_wrong_public_argument_types(self) -> None:
        with self.assertRaises(TypeError):
            validate_task04("study")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            validate_task04(
                self.study,
                configuration="default",  # type: ignore[arg-type]
            )

    def test_non_official_study_returns_a_failed_report_without_crashing(self) -> None:
        custom = build_task04_study(
            materials=(PhotoelectricMaterial("Example", "X", 3.0),)
        )
        report = validate_task04(custom)
        self.assertFalse(report.passed)
        self.assertEqual(len(report.checks), 43)
        self.assertIn("official_material_table", {c.name for c in report.failed_checks})


class DeliberateFailureDetectionTests(unittest.TestCase):
    """Prove that structurally valid scientific corruption cannot pass."""

    def setUp(self) -> None:
        self.study = build_task04_study()

    @staticmethod
    def _failed_names(report: Task04ValidationReport) -> set[str]:
        return {check.name for check in report.failed_checks}

    def test_perturbed_work_function_is_detected(self) -> None:
        work_functions = self.study.work_functions_ev.copy()
        work_functions[0] += 0.1
        corrupted = replace(self.study, work_functions_ev=work_functions)
        report = validate_task04(corrupted)
        failed = self._failed_names(report)
        self.assertFalse(report.passed)
        self.assertIn("official_material_table", failed)
        self.assertIn("work_function_joules", failed)
        self.assertIn("frequency_energy_identity", failed)
        self.assertIn("wavelength_energy_identity", failed)

    def test_perturbed_frequency_curve_is_detected(self) -> None:
        curve = self.study.frequency_linear_voltage_v.copy()
        curve[0, 1000] += 0.1
        corrupted = replace(self.study, frequency_linear_voltage_v=curve)
        report = validate_task04(corrupted)
        failed = self._failed_names(report)
        self.assertFalse(report.passed)
        self.assertIn("frequency_energy_identity", failed)
        self.assertIn("common_frequency_gradient", failed)

    def test_corrupted_emission_mask_is_detected(self) -> None:
        mask = self.study.frequency_emission_mask.copy()
        physical = self.study.frequency_physical_voltage_v.copy()
        row, column = np.argwhere(~mask)[0]
        mask[row, column] = True
        physical[row, column] = 0.0
        corrupted = replace(
            self.study,
            frequency_emission_mask=mask,
            frequency_physical_voltage_v=physical,
        )
        report = validate_task04(corrupted)
        failed = self._failed_names(report)
        self.assertFalse(report.passed)
        self.assertIn("frequency_emission_mask", failed)
        self.assertIn("frequency_physical_voltage", failed)

    def test_corrupted_cutoff_is_detected_at_value_and_threshold(self) -> None:
        cutoffs = self.study.cutoff_frequencies_hz.copy()
        cutoffs[0] *= 1.01
        corrupted = replace(self.study, cutoff_frequencies_hz=cutoffs)
        report = validate_task04(corrupted)
        failed = self._failed_names(report)
        self.assertFalse(report.passed)
        self.assertIn("cutoff_frequency_ag", failed)
        self.assertIn("threshold_frequency_voltage", failed)


class ValidationCommandTests(unittest.TestCase):
    """Check validation-only command output, status, and side effects."""

    def test_module_command_reports_success_and_all_checks(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        completed = subprocess.run(
            [sys.executable, "-m", "task04_photoelectric_effect.validate_task04"],
            cwd=repository_root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(len(completed.stdout.splitlines()), 44)
        self.assertIn("Task 4 validation: PASS (43/43 checks passed)", completed.stdout)
        self.assertNotIn("FAIL", completed.stdout)

    def test_main_returns_failure_for_a_failed_report(self) -> None:
        command = importlib.import_module(
            "task04_photoelectric_effect.validate_task04"
        )
        failed_check = ValidationCheck(
            name="injected_failure",
            passed=False,
            observed=1.0,
            expected=0.0,
            unit="count",
            comparison="exact_equal",
            tolerance=0.0,
            explanation="Deliberate test-only failed report.",
        )
        failed_report = Task04ValidationReport(
            "task04-v1",
            (failed_check,),
        )
        output = io.StringIO()
        with mock.patch.object(command, "validate_task04", return_value=failed_report):
            with contextlib.redirect_stdout(output):
                status = command.main([])
        self.assertEqual(status, 1)
        self.assertIn("FAIL", output.getvalue())

    def test_main_rejects_unexpected_arguments(self) -> None:
        command = importlib.import_module(
            "task04_photoelectric_effect.validate_task04"
        )
        with self.assertRaises(ValueError):
            command.main(["unexpected"])

    def test_validation_command_writes_no_files_and_imports_no_matplotlib(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = (
                "import pathlib, sys\n"
                f"sys.path.insert(0, {str(repository_root)!r})\n"
                "before = set(pathlib.Path('.').iterdir())\n"
                "from task04_photoelectric_effect.validate_task04 import main\n"
                "status = main([])\n"
                "after = set(pathlib.Path('.').iterdir())\n"
                "assert status == 0\n"
                "assert before == after\n"
                "assert 'matplotlib' not in sys.modules\n"
            )
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=temporary_directory,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
