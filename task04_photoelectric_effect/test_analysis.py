"""Tests for the immutable Task 4 in-memory study."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import numpy as np

from task04_photoelectric_effect.analysis import (
    Task04StudyResult,
    build_task04_study,
)
from task04_photoelectric_effect.configuration import DEFAULT_CONFIGURATION
from task04_photoelectric_effect.constants import (
    ELECTRONVOLT_J,
    METRES_PER_NANOMETRE,
    NANOMETRES_PER_METRE,
)
from task04_photoelectric_effect.materials import (
    OFFICIAL_MATERIALS,
    PhotoelectricMaterial,
)
from task04_photoelectric_effect.models import (
    cutoff_frequency_hz,
    cutoff_wavelength_m,
    emission_possible_from_frequency,
    emission_possible_from_wavelength,
    linear_stopping_voltage_from_frequency,
    linear_stopping_voltage_from_wavelength,
    physical_stopping_voltage_from_frequency,
    physical_stopping_voltage_from_wavelength,
)


ARRAY_FIELDS = (
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


class StudyConstructionTests(unittest.TestCase):
    """Check the complete default calculation and public study contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()

    def test_default_materials_and_work_functions_are_retained(self) -> None:
        self.assertEqual(self.study.materials, OFFICIAL_MATERIALS)
        self.assertIs(self.study.materials[0], OFFICIAL_MATERIALS[0])
        np.testing.assert_array_equal(
            self.study.work_functions_ev,
            [4.3, 4.3, 5.1, 4.7, 4.4, 4.3, 4.5, 4.6, 2.4],
        )
        np.testing.assert_array_equal(
            self.study.work_functions_j,
            self.study.work_functions_ev * ELECTRONVOLT_J,
        )

    def test_frequency_grid_is_exact(self) -> None:
        grid = self.study.frequency_hz
        self.assertEqual(grid.shape, (2001,))
        self.assertEqual(grid.dtype, np.float64)
        self.assertEqual(grid[0], 4.0e14)
        self.assertEqual(grid[-1], 2.4e15)
        np.testing.assert_array_equal(np.diff(grid), 1.0e12)

    def test_wavelength_grids_are_exact_and_consistent(self) -> None:
        wavelength_nm = self.study.wavelength_nm
        wavelength_m = self.study.wavelength_m
        self.assertEqual(wavelength_nm.shape, (2201,))
        self.assertEqual(wavelength_m.shape, (2201,))
        self.assertEqual(wavelength_nm[0], 150.0)
        self.assertEqual(wavelength_nm[-1], 700.0)
        np.testing.assert_array_equal(np.diff(wavelength_nm), 0.25)
        np.testing.assert_array_equal(
            wavelength_m,
            wavelength_nm * METRES_PER_NANOMETRE,
        )

    def test_cutoffs_equal_the_public_models(self) -> None:
        np.testing.assert_array_equal(
            self.study.cutoff_frequencies_hz,
            cutoff_frequency_hz(self.study.work_functions_ev),
        )
        np.testing.assert_array_equal(
            self.study.cutoff_wavelengths_nm,
            cutoff_wavelength_m(self.study.work_functions_ev)
            * NANOMETRES_PER_METRE,
        )

    def test_frequency_arrays_have_frozen_shapes_and_dtypes(self) -> None:
        expected_shape = (9, 2001)
        self.assertEqual(self.study.frequency_linear_voltage_v.shape, expected_shape)
        self.assertEqual(self.study.frequency_emission_mask.shape, expected_shape)
        self.assertEqual(self.study.frequency_physical_voltage_v.shape, expected_shape)
        self.assertEqual(self.study.frequency_linear_voltage_v.dtype, np.float64)
        self.assertEqual(self.study.frequency_emission_mask.dtype, np.bool_)
        self.assertEqual(self.study.frequency_physical_voltage_v.dtype, np.float64)

    def test_wavelength_arrays_have_frozen_shapes_and_dtypes(self) -> None:
        expected_shape = (9, 2201)
        self.assertEqual(self.study.wavelength_linear_voltage_v.shape, expected_shape)
        self.assertEqual(self.study.wavelength_emission_mask.shape, expected_shape)
        self.assertEqual(self.study.wavelength_physical_voltage_v.shape, expected_shape)
        self.assertEqual(self.study.wavelength_linear_voltage_v.dtype, np.float64)
        self.assertEqual(self.study.wavelength_emission_mask.dtype, np.bool_)
        self.assertEqual(self.study.wavelength_physical_voltage_v.dtype, np.float64)

    def test_stored_frequency_arrays_equal_public_model_results(self) -> None:
        work = self.study.work_functions_ev[:, None]
        frequency = self.study.frequency_hz[None, :]
        np.testing.assert_array_equal(
            self.study.frequency_linear_voltage_v,
            linear_stopping_voltage_from_frequency(frequency, work),
        )
        np.testing.assert_array_equal(
            self.study.frequency_emission_mask,
            emission_possible_from_frequency(frequency, work),
        )
        np.testing.assert_array_equal(
            self.study.frequency_physical_voltage_v,
            physical_stopping_voltage_from_frequency(frequency, work),
        )

    def test_stored_wavelength_arrays_equal_public_model_results(self) -> None:
        work = self.study.work_functions_ev[:, None]
        wavelength = self.study.wavelength_m[None, :]
        np.testing.assert_array_equal(
            self.study.wavelength_linear_voltage_v,
            linear_stopping_voltage_from_wavelength(wavelength, work),
        )
        np.testing.assert_array_equal(
            self.study.wavelength_emission_mask,
            emission_possible_from_wavelength(wavelength, work),
        )
        np.testing.assert_array_equal(
            self.study.wavelength_physical_voltage_v,
            physical_stopping_voltage_from_wavelength(wavelength, work),
        )

    def test_physical_arrays_follow_mask_and_nan_contract(self) -> None:
        for mask, physical in (
            (
                self.study.frequency_emission_mask,
                self.study.frequency_physical_voltage_v,
            ),
            (
                self.study.wavelength_emission_mask,
                self.study.wavelength_physical_voltage_v,
            ),
        ):
            self.assertTrue(np.all(np.isfinite(physical[mask])))
            self.assertTrue(np.all(physical[mask] >= 0.0))
            self.assertTrue(np.all(np.isnan(physical[~mask])))
            self.assertGreater(np.count_nonzero(mask), 0)
            self.assertGreater(np.count_nonzero(~mask), 0)

    def test_all_arrays_are_read_only(self) -> None:
        for field_name in ARRAY_FIELDS:
            with self.subTest(field=field_name):
                array = getattr(self.study, field_name)
                self.assertFalse(array.flags.writeable)
                with self.assertRaises(ValueError):
                    array.flat[0] = array.flat[0]

    def test_study_dataclass_is_frozen(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            self.study.materials = ()  # type: ignore[misc]

    def test_repeated_studies_are_exactly_reproducible(self) -> None:
        repeated = build_task04_study()
        self.assertEqual(repeated.materials, self.study.materials)
        for field_name in ARRAY_FIELDS:
            with self.subTest(field=field_name):
                np.testing.assert_array_equal(
                    getattr(repeated, field_name),
                    getattr(self.study, field_name),
                )

    def test_custom_material_collection_controls_outer_shape(self) -> None:
        materials = (
            PhotoelectricMaterial("Example A", "Xa", 2.0),
            PhotoelectricMaterial("Example B", "Xb", 6.0),
        )
        study = build_task04_study(materials=materials)
        self.assertEqual(study.materials, materials)
        self.assertEqual(study.frequency_linear_voltage_v.shape, (2, 2001))
        self.assertEqual(study.wavelength_linear_voltage_v.shape, (2, 2201))

    def test_builder_rejects_wrong_configuration_or_materials(self) -> None:
        with self.assertRaises(TypeError):
            build_task04_study(configuration="default")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            build_task04_study(materials=())

    def test_study_runtime_is_below_budget(self) -> None:
        start = time.perf_counter()
        build_task04_study()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, DEFAULT_CONFIGURATION.study_runtime_budget_s)

    def test_study_build_has_no_filesystem_or_matplotlib_side_effect(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = (
                "import pathlib, sys\n"
                f"sys.path.insert(0, {str(repository_root)!r})\n"
                "before = set(pathlib.Path('.').iterdir())\n"
                "from task04_photoelectric_effect import build_task04_study\n"
                "build_task04_study()\n"
                "after = set(pathlib.Path('.').iterdir())\n"
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


class StudyInvariantTests(unittest.TestCase):
    """Prove that result records reject structural corruption."""

    def setUp(self) -> None:
        self.study = build_task04_study()

    def test_constructor_makes_defensive_array_copies(self) -> None:
        external = self.study.frequency_hz.copy()
        copied = replace(self.study, frequency_hz=external)
        original_value = copied.frequency_hz[0]
        external[0] = external[0] + 1.0
        self.assertEqual(copied.frequency_hz[0], original_value)

    def test_result_rejects_invalid_material_array_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "work_functions_ev must have shape"):
            replace(self.study, work_functions_ev=np.ones(8))

    def test_result_rejects_non_finite_or_non_positive_metadata(self) -> None:
        invalid_cutoffs = self.study.cutoff_frequencies_hz.copy()
        invalid_cutoffs[0] = -1.0
        with self.assertRaises(ValueError):
            replace(self.study, cutoff_frequencies_hz=invalid_cutoffs)
        invalid_work = self.study.work_functions_j.copy()
        invalid_work[0] = np.nan
        with self.assertRaises(ValueError):
            replace(self.study, work_functions_j=invalid_work)

    def test_result_rejects_non_increasing_or_wrong_grid(self) -> None:
        decreasing = self.study.frequency_hz.copy()
        decreasing[1] = decreasing[0]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            replace(self.study, frequency_hz=decreasing)
        with self.assertRaisesRegex(ValueError, "one-dimensional"):
            replace(self.study, frequency_hz=np.ones((2, 2)))
        with self.assertRaisesRegex(ValueError, "must match"):
            replace(self.study, wavelength_nm=np.ones(2))

    def test_result_rejects_wrong_voltage_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "must have shape"):
            replace(
                self.study,
                frequency_linear_voltage_v=np.ones((9, 2000)),
            )

    def test_result_rejects_non_boolean_mask(self) -> None:
        with self.assertRaises(TypeError):
            replace(
                self.study,
                frequency_emission_mask=self.study.frequency_emission_mask.astype(int),
            )

    def test_result_rejects_nan_or_negative_active_physical_voltage(self) -> None:
        active_index = tuple(np.argwhere(self.study.frequency_emission_mask)[0])
        corrupted_nan = self.study.frequency_physical_voltage_v.copy()
        corrupted_nan[active_index] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            replace(self.study, frequency_physical_voltage_v=corrupted_nan)
        corrupted_negative = self.study.frequency_physical_voltage_v.copy()
        corrupted_negative[active_index] = -1.0
        with self.assertRaisesRegex(ValueError, "non-negative"):
            replace(self.study, frequency_physical_voltage_v=corrupted_negative)

    def test_result_rejects_finite_inactive_physical_voltage(self) -> None:
        inactive_index = tuple(np.argwhere(~self.study.wavelength_emission_mask)[0])
        corrupted = self.study.wavelength_physical_voltage_v.copy()
        corrupted[inactive_index] = 0.0
        with self.assertRaisesRegex(ValueError, "must be NaN"):
            replace(self.study, wavelength_physical_voltage_v=corrupted)

    def test_structurally_valid_scientific_perturbation_is_preserved(self) -> None:
        perturbed = self.study.cutoff_frequencies_hz.copy()
        perturbed[0] *= 1.01
        modified = replace(self.study, cutoff_frequencies_hz=perturbed)
        self.assertEqual(modified.cutoff_frequencies_hz[0], perturbed[0])
        self.assertFalse(modified.cutoff_frequencies_hz.flags.writeable)


if __name__ == "__main__":
    unittest.main()
