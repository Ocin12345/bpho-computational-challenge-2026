"""Tests for Task 3 configuration, references, analysis, and validation."""

from __future__ import annotations

import io
import time
import unittest
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError, replace

import numpy as np

from task03_thermal_radiation.analysis import (
    PlanckStudyResult,
    build_planck_study,
)
from task03_thermal_radiation.configuration import (
    DEFAULT_CONFIGURATION,
    Task03Configuration,
)
from task03_thermal_radiation.reference import (
    stefan_boltzmann_exitance,
    wien_peak_wavelength,
)
from task03_thermal_radiation.validate_task03 import main
from task03_thermal_radiation.validation import validate_planck_study


class ConfigurationTests(unittest.TestCase):
    """Protect the frozen grids and pre-declared tolerances."""

    def test_default_planck_configuration_matches_specification(self) -> None:
        configuration = DEFAULT_CONFIGURATION

        self.assertEqual(
            configuration.planck_temperatures_k,
            (4000.0, 5000.0, 6000.0),
        )
        self.assertEqual(configuration.planck_display_min_nm, 100.0)
        self.assertEqual(configuration.planck_display_max_nm, 3000.0)
        self.assertEqual(configuration.planck_display_interval_nm, 1.0)
        self.assertEqual(configuration.planck_peak_interval_nm, 0.01)
        self.assertEqual(configuration.planck_integration_points, 200_001)
        self.assertEqual(configuration.wien_peak_relative_tolerance, 1.0e-3)
        self.assertEqual(
            configuration.stefan_boltzmann_relative_tolerance,
            2.0e-3,
        )

    def test_configuration_is_frozen(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIGURATION.planck_display_min_nm = 1.0  # type: ignore[misc]

    def test_temperatures_must_be_several_positive_increasing_values(self) -> None:
        invalid_values = (
            (4000.0,),
            (0.0, 4000.0),
            (5000.0, 4000.0),
            (4000.0, 4000.0),
        )
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    Task03Configuration(planck_temperatures_k=values)

    def test_grid_range_and_interval_must_be_consistent(self) -> None:
        with self.assertRaises(ValueError):
            Task03Configuration(planck_display_min_nm=3000.0)
        with self.assertRaises(ValueError):
            Task03Configuration(planck_display_interval_nm=7.0)
        with self.assertRaises(ValueError):
            Task03Configuration(planck_integration_points=2)

    def test_tolerances_cannot_be_negative(self) -> None:
        with self.assertRaises(ValueError):
            Task03Configuration(wien_peak_relative_tolerance=-1.0)


class IndependentReferenceTests(unittest.TestCase):
    """Check analytical targets without calling the numerical model."""

    def test_wien_targets_match_frozen_reference_values(self) -> None:
        targets_nm = (
            wien_peak_wavelength(np.array([4000.0, 5000.0, 6000.0]))
            * 1.0e9
        )

        np.testing.assert_allclose(
            targets_nm,
            np.array([724.442988796, 579.554391037, 482.961992531]),
            rtol=0.0,
            atol=5.0e-10,
        )

    def test_stefan_targets_match_frozen_reference_values(self) -> None:
        targets = stefan_boltzmann_exitance(
            np.array([4000.0, 5000.0, 6000.0])
        )

        np.testing.assert_allclose(
            targets,
            np.array(
                [
                    14_516_158.513112145,
                    35_439_840.11990269,
                    73_488_052.47263023,
                ]
            ),
            rtol=2.0e-15,
            atol=0.0,
        )

    def test_reference_functions_reject_invalid_temperatures(self) -> None:
        for value in (0.0, -1.0, np.nan, np.inf, True, "4000"):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    wien_peak_wavelength(value)  # type: ignore[arg-type]


class PlanckStudyTests(unittest.TestCase):
    """Verify the complete immutable in-memory Planck study."""

    @classmethod
    def setUpClass(cls) -> None:
        start = time.perf_counter()
        cls.result = build_planck_study()
        cls.runtime_seconds = time.perf_counter() - start

    def test_study_shapes_match_frozen_grids(self) -> None:
        result = self.result

        self.assertEqual(result.temperatures_k.shape, (3,))
        self.assertEqual(result.wavelengths_nm.shape, (2901,))
        self.assertEqual(result.spectral_radiance_w_m3_sr.shape, (3, 2901))
        self.assertEqual(result.spectral_exitance_w_m2_nm.shape, (3, 2901))
        self.assertEqual(result.numerical_peak_wavelength_m.shape, (3,))

    def test_study_arrays_are_read_only(self) -> None:
        for field_name in (
            "temperatures_k",
            "wavelengths_m",
            "spectral_radiance_w_m3_sr",
            "spectral_exitance_w_m2_nm",
            "numerical_peak_wavelength_m",
            "numerical_integrated_exitance_w_m2",
        ):
            with self.subTest(field_name=field_name):
                array = getattr(self.result, field_name)
                self.assertFalse(array.flags.writeable)
                with self.assertRaises(ValueError):
                    array.flat[0] = 0.0

    def test_mismatched_wavelength_units_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must describe one grid"):
            replace(
                self.result,
                wavelengths_m=self.result.wavelengths_m * 2.0,
            )

    def test_numerical_peaks_meet_predeclared_tolerance(self) -> None:
        errors = np.abs(
            self.result.numerical_peak_wavelength_m
            - self.result.wien_peak_wavelength_m
        ) / self.result.wien_peak_wavelength_m

        self.assertLess(float(np.max(errors)), 1.0e-3)
        self.assertLess(float(np.max(errors)), 8.0e-6)

    def test_integrated_exitance_meets_predeclared_tolerance(self) -> None:
        errors = np.abs(
            self.result.numerical_integrated_exitance_w_m2
            - self.result.stefan_boltzmann_exitance_w_m2
        ) / self.result.stefan_boltzmann_exitance_w_m2

        self.assertLess(float(np.max(errors)), 2.0e-3)
        self.assertLess(float(np.max(errors)), 2.0e-9)

    def test_study_is_exactly_reproducible(self) -> None:
        repeated = build_planck_study()

        for field_name in (
            "spectral_radiance_w_m3_sr",
            "spectral_exitance_w_m2_nm",
            "numerical_peak_wavelength_m",
            "numerical_integrated_radiance_w_m2_sr",
            "numerical_integrated_exitance_w_m2",
        ):
            with self.subTest(field_name=field_name):
                np.testing.assert_array_equal(
                    getattr(self.result, field_name),
                    getattr(repeated, field_name),
                )

    def test_study_runtime_is_within_portability_budget(self) -> None:
        self.assertLess(self.runtime_seconds, 5.0)


class PlanckValidationTests(unittest.TestCase):
    """Verify structured pass/fail behaviour and command-line reporting."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = build_planck_study()
        cls.report = validate_planck_study(cls.result)

    def test_reference_study_passes_every_check(self) -> None:
        self.assertTrue(self.report.passed, self.report.failures)
        self.assertEqual(self.report.failures, ())
        self.assertEqual(len(self.report.checks), 13)
        self.assertEqual(
            len({check.name for check in self.report.checks}),
            len(self.report.checks),
        )

    def test_report_detects_a_deliberately_incorrect_peak(self) -> None:
        incorrect = replace(
            self.result,
            numerical_peak_wavelength_m=(
                self.result.numerical_peak_wavelength_m * 1.1
            ),
        )
        report = validate_planck_study(incorrect)

        self.assertFalse(report.passed)
        self.assertEqual(len(report.failures), 3)
        self.assertTrue(
            all(check.name.startswith("wien_peak_") for check in report.failures)
        )

    def test_mismatched_configuration_is_rejected(self) -> None:
        different = Task03Configuration(
            wien_peak_relative_tolerance=5.0e-4
        )
        with self.assertRaisesRegex(ValueError, "must match"):
            validate_planck_study(self.result, different)

    def test_stage_5_command_reports_success(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("Task 3 Stage 5", output.getvalue())
        self.assertIn("Planck validation: PASS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
