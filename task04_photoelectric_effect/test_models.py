"""Tests for the vectorized Task 4 photoelectric equations."""

from __future__ import annotations

import math
import unittest

import numpy as np

import task04_photoelectric_effect as task04
from task04_photoelectric_effect.constants import (
    HC_OVER_CHARGE_V_M,
    PLANCK_OVER_CHARGE_V_S,
    SPEED_OF_LIGHT_M_S,
)
from task04_photoelectric_effect.materials import OFFICIAL_MATERIALS
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


WORK_FUNCTIONS_EV = np.array(
    [material.work_function_ev for material in OFFICIAL_MATERIALS],
    dtype=np.float64,
)


class CutoffTests(unittest.TestCase):
    """Check analytical thresholds and return contracts."""

    def test_scalar_cutoffs_return_zero_dimensional_float_arrays(self) -> None:
        for function in (cutoff_frequency_hz, cutoff_wavelength_m):
            result = function(4.7)
            self.assertIsInstance(result, np.ndarray)
            self.assertEqual(result.shape, ())
            self.assertEqual(result.dtype, np.float64)

    def test_all_official_cutoff_frequencies(self) -> None:
        expected = np.array(
            [
                1.039735374097e15,
                1.039735374097e15,
                1.233174513463e15,
                1.136454943780e15,
                1.063915266517e15,
                1.039735374097e15,
                1.088095158938e15,
                1.112275051359e15,
                5.803174181004e14,
            ]
        )
        np.testing.assert_allclose(
            cutoff_frequency_hz(WORK_FUNCTIONS_EV),
            expected,
            rtol=5.0e-13,
            atol=0.0,
        )

    def test_all_official_cutoff_wavelengths(self) -> None:
        expected_nm = np.array(
            [
                288.335345193,
                288.335345193,
                243.106271438,
                263.796166879,
                281.782269166,
                288.335345193,
                275.520440963,
                269.530866159,
                516.600826805,
            ]
        )
        np.testing.assert_allclose(
            cutoff_wavelength_m(WORK_FUNCTIONS_EV) * 1.0e9,
            expected_nm,
            rtol=0.0,
            atol=5.1e-10,
        )

    def test_frequency_and_wavelength_cutoffs_are_reciprocal(self) -> None:
        np.testing.assert_allclose(
            cutoff_frequency_hz(WORK_FUNCTIONS_EV)
            * cutoff_wavelength_m(WORK_FUNCTIONS_EV),
            SPEED_OF_LIGHT_M_S,
            rtol=2.0e-16,
            atol=0.0,
        )

    def test_larger_work_function_has_higher_frequency_and_shorter_wavelength(self) -> None:
        work_functions = np.array([2.4, 4.3, 5.1])
        self.assertTrue(np.all(np.diff(cutoff_frequency_hz(work_functions)) > 0.0))
        self.assertTrue(np.all(np.diff(cutoff_wavelength_m(work_functions)) < 0.0))


class LinearVoltageTests(unittest.TestCase):
    """Check both signed coordinate forms and their units."""

    def test_frequency_intercept_and_common_gradient(self) -> None:
        work_function = np.array([2.4, 4.7, 5.1])[:, None]
        frequency = np.array([0.0, 1.0e15, 1.5e15])[None, :]
        voltage = linear_stopping_voltage_from_frequency(
            frequency,
            work_function,
        )
        self.assertEqual(voltage.shape, (3, 3))
        np.testing.assert_array_equal(voltage[:, 0], -work_function[:, 0])
        slopes = np.diff(voltage, axis=1) / np.diff(frequency, axis=1)
        np.testing.assert_allclose(
            slopes,
            PLANCK_OVER_CHARGE_V_S,
            rtol=5.0e-13,
            atol=0.0,
        )

    def test_frequency_anchor_values(self) -> None:
        expected = np.array(
            [
                1.903501545386,
                1.903501545386,
                1.103501545386,
                1.503501545386,
                1.803501545386,
                1.903501545386,
                1.703501545386,
                1.603501545386,
                3.803501545386,
            ]
        )
        np.testing.assert_allclose(
            linear_stopping_voltage_from_frequency(1.5e15, WORK_FUNCTIONS_EV),
            expected,
            rtol=0.0,
            atol=5.0e-12,
        )

    def test_wavelength_anchor_values(self) -> None:
        expected = np.array(
            [
                1.899209921660,
                1.899209921660,
                1.099209921660,
                1.499209921660,
                1.799209921660,
                1.899209921660,
                1.699209921660,
                1.599209921660,
                3.799209921660,
            ]
        )
        np.testing.assert_allclose(
            linear_stopping_voltage_from_wavelength(
                200.0e-9,
                WORK_FUNCTIONS_EV,
            ),
            expected,
            rtol=0.0,
            atol=5.0e-12,
        )

    def test_frequency_and_wavelength_forms_agree(self) -> None:
        frequencies = np.array([5.0e14, 1.0e15, 1.5e15, 2.0e15])
        wavelengths = SPEED_OF_LIGHT_M_S / frequencies
        frequency_voltage = linear_stopping_voltage_from_frequency(
            frequencies[None, :],
            WORK_FUNCTIONS_EV[:, None],
        )
        wavelength_voltage = linear_stopping_voltage_from_wavelength(
            wavelengths[None, :],
            WORK_FUNCTIONS_EV[:, None],
        )
        np.testing.assert_allclose(
            frequency_voltage,
            wavelength_voltage,
            rtol=0.0,
            atol=4.0e-15,
        )

    def test_scalar_voltage_returns_zero_dimensional_float_array(self) -> None:
        for result in (
            linear_stopping_voltage_from_frequency(1.5e15, 4.7),
            linear_stopping_voltage_from_wavelength(200.0e-9, 4.7),
        ):
            self.assertEqual(result.shape, ())
            self.assertEqual(result.dtype, np.float64)

    def test_wavelength_equation_uses_metres(self) -> None:
        observed = linear_stopping_voltage_from_wavelength(200.0e-9, 4.7)
        expected = HC_OVER_CHARGE_V_M / (200.0e-9) - 4.7
        self.assertEqual(float(observed), expected)


class PhysicalDomainTests(unittest.TestCase):
    """Check threshold masks and missing-value semantics."""

    def test_exact_frequency_threshold_is_physical_zero(self) -> None:
        cutoff = cutoff_frequency_hz(WORK_FUNCTIONS_EV)
        mask = emission_possible_from_frequency(cutoff, WORK_FUNCTIONS_EV)
        physical = physical_stopping_voltage_from_frequency(
            cutoff,
            WORK_FUNCTIONS_EV,
        )
        np.testing.assert_array_equal(mask, np.ones(9, dtype=bool))
        self.assertLessEqual(np.max(np.abs(physical)), 5.0e-12)
        self.assertTrue(np.all(physical >= 0.0))

    def test_frequency_neighbours_obey_exact_threshold(self) -> None:
        cutoff = cutoff_frequency_hz(4.7)
        frequencies = np.array(
            [
                np.nextafter(cutoff, -np.inf),
                cutoff,
                np.nextafter(cutoff, np.inf),
            ]
        )
        np.testing.assert_array_equal(
            emission_possible_from_frequency(frequencies, 4.7),
            np.array([False, True, True]),
        )
        physical = physical_stopping_voltage_from_frequency(frequencies, 4.7)
        self.assertTrue(math.isnan(physical[0]))
        self.assertGreaterEqual(physical[1], 0.0)
        self.assertGreater(physical[2], 0.0)

    def test_exact_wavelength_threshold_is_physical_zero(self) -> None:
        cutoff = cutoff_wavelength_m(WORK_FUNCTIONS_EV)
        mask = emission_possible_from_wavelength(cutoff, WORK_FUNCTIONS_EV)
        physical = physical_stopping_voltage_from_wavelength(
            cutoff,
            WORK_FUNCTIONS_EV,
        )
        np.testing.assert_array_equal(mask, np.ones(9, dtype=bool))
        self.assertLessEqual(np.max(np.abs(physical)), 5.0e-12)
        self.assertTrue(np.all(physical >= 0.0))

    def test_wavelength_neighbours_obey_exact_threshold(self) -> None:
        cutoff = cutoff_wavelength_m(4.7)
        wavelengths = np.array(
            [
                np.nextafter(cutoff, -np.inf),
                cutoff,
                np.nextafter(cutoff, np.inf),
            ]
        )
        np.testing.assert_array_equal(
            emission_possible_from_wavelength(wavelengths, 4.7),
            np.array([True, True, False]),
        )
        physical = physical_stopping_voltage_from_wavelength(wavelengths, 4.7)
        self.assertGreater(physical[0], 0.0)
        self.assertGreaterEqual(physical[1], 0.0)
        self.assertTrue(math.isnan(physical[2]))

    def test_below_threshold_is_missing_not_zero(self) -> None:
        frequency_physical = physical_stopping_voltage_from_frequency(
            5.0e14,
            4.7,
        )
        wavelength_physical = physical_stopping_voltage_from_wavelength(
            700.0e-9,
            4.7,
        )
        self.assertTrue(np.isnan(frequency_physical))
        self.assertTrue(np.isnan(wavelength_physical))

    def test_sodium_emits_in_visible_where_copper_does_not(self) -> None:
        green_frequency = SPEED_OF_LIGHT_M_S / (500.0e-9)
        sodium = emission_possible_from_frequency(green_frequency, 2.4)
        copper = emission_possible_from_frequency(green_frequency, 4.7)
        self.assertTrue(bool(sodium))
        self.assertFalse(bool(copper))

    def test_duplicate_work_functions_produce_exactly_equal_results(self) -> None:
        frequencies = np.linspace(4.0e14, 2.4e15, 101)
        work_functions = np.array([4.3, 4.3, 4.3])[:, None]
        linear = linear_stopping_voltage_from_frequency(
            frequencies[None, :],
            work_functions,
        )
        physical = physical_stopping_voltage_from_frequency(
            frequencies[None, :],
            work_functions,
        )
        np.testing.assert_array_equal(linear[0], linear[1])
        np.testing.assert_array_equal(linear[0], linear[2])
        np.testing.assert_array_equal(physical[0], physical[1])
        np.testing.assert_array_equal(physical[0], physical[2])

    def test_mask_outputs_are_boolean_arrays(self) -> None:
        for mask in (
            emission_possible_from_frequency(1.5e15, 4.7),
            emission_possible_from_wavelength(200.0e-9, 4.7),
        ):
            self.assertIsInstance(mask, np.ndarray)
            self.assertEqual(mask.shape, ())
            self.assertEqual(mask.dtype, np.bool_)


class InputContractTests(unittest.TestCase):
    """Reject ambiguous inputs and preserve array/broadcast behaviour."""

    def test_model_functions_do_not_mutate_inputs(self) -> None:
        frequencies = np.array([1.0e15, 1.5e15])
        wavelengths = np.array([200.0e-9, 300.0e-9])
        work_functions = np.array([4.3, 4.7])
        frequency_copy = frequencies.copy()
        wavelength_copy = wavelengths.copy()
        work_copy = work_functions.copy()
        linear_stopping_voltage_from_frequency(frequencies, work_functions)
        linear_stopping_voltage_from_wavelength(wavelengths, work_functions)
        np.testing.assert_array_equal(frequencies, frequency_copy)
        np.testing.assert_array_equal(wavelengths, wavelength_copy)
        np.testing.assert_array_equal(work_functions, work_copy)

    def test_explicit_outer_broadcast_contract(self) -> None:
        frequencies = np.array([1.0e15, 1.5e15, 2.0e15])[None, :]
        work_functions = np.array([2.4, 4.7])[:, None]
        result = linear_stopping_voltage_from_frequency(
            frequencies,
            work_functions,
        )
        self.assertEqual(result.shape, (2, 3))
        self.assertEqual(result.dtype, np.float64)

    def test_incompatible_shapes_raise_clear_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "broadcast-compatible"):
            linear_stopping_voltage_from_frequency(
                np.ones((2, 3)),
                np.ones((4,)),
            )
        with self.assertRaisesRegex(ValueError, "broadcast-compatible"):
            emission_possible_from_wavelength(
                np.ones((2, 3)),
                np.ones((4,)),
            )

    def test_booleans_are_rejected_including_mixed_sequences(self) -> None:
        functions_and_args = (
            (cutoff_frequency_hz, ([4.3, True],)),
            (cutoff_wavelength_m, (True,)),
            (linear_stopping_voltage_from_frequency, ([1.0e15, True], 4.3)),
            (linear_stopping_voltage_from_wavelength, ([200.0e-9, True], 4.3)),
            (emission_possible_from_frequency, (1.0e15, [4.3, False])),
            (emission_possible_from_wavelength, (200.0e-9, False)),
        )
        for function, args in functions_and_args:
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(*args)

    def test_text_and_complex_values_are_rejected(self) -> None:
        for value in ("4.7", 4.7 + 0.0j):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    cutoff_frequency_hz(value)
        with self.assertRaises(TypeError):
            linear_stopping_voltage_from_frequency("1e15", 4.7)
        with self.assertRaises(TypeError):
            linear_stopping_voltage_from_wavelength(200.0e-9 + 0.0j, 4.7)

    def test_non_finite_inputs_are_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    cutoff_frequency_hz(value)
                with self.assertRaises(ValueError):
                    linear_stopping_voltage_from_frequency(value, 4.7)
                with self.assertRaises(ValueError):
                    linear_stopping_voltage_from_wavelength(value, 4.7)

    def test_invalid_physical_domains_are_rejected(self) -> None:
        for work_function in (0.0, -1.0):
            with self.assertRaises(ValueError):
                cutoff_frequency_hz(work_function)
        with self.assertRaises(ValueError):
            linear_stopping_voltage_from_frequency(-1.0, 4.7)
        for wavelength in (0.0, -1.0):
            with self.assertRaises(ValueError):
                linear_stopping_voltage_from_wavelength(wavelength, 4.7)

    def test_unrepresentable_results_fail_explicitly(self) -> None:
        with self.assertRaises(FloatingPointError):
            cutoff_frequency_hz(np.finfo(np.float64).max)
        with self.assertRaises(FloatingPointError):
            linear_stopping_voltage_from_wavelength(
                np.nextafter(0.0, 1.0),
                4.7,
            )

    def test_public_package_exports_all_stage_four_symbols(self) -> None:
        for name in (
            "PLANCK_CONSTANT_J_S",
            "ELEMENTARY_CHARGE_C",
            "Task04Configuration",
            "PhotoelectricMaterial",
            "OFFICIAL_MATERIALS",
            "cutoff_frequency_hz",
            "cutoff_wavelength_m",
            "linear_stopping_voltage_from_frequency",
            "linear_stopping_voltage_from_wavelength",
            "emission_possible_from_frequency",
            "emission_possible_from_wavelength",
            "physical_stopping_voltage_from_frequency",
            "physical_stopping_voltage_from_wavelength",
        ):
            self.assertTrue(hasattr(task04, name), name)


if __name__ == "__main__":
    unittest.main()
