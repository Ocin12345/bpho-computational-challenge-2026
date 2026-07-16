"""Unit tests for the Task 3 Einstein-solid model."""

from __future__ import annotations

import math
import unittest
import warnings

import numpy as np

from task03_thermal_radiation.constants import MOLAR_GAS_CONSTANT_J_MOL_K
from task03_thermal_radiation.materials import OFFICIAL_MATERIALS
from task03_thermal_radiation.models import (
    einstein_frequency_from_temperature,
    einstein_molar_heat_capacity,
    einstein_temperature_from_debye,
)


DEBYE_TEMPERATURES_K = np.array(
    [material.debye_temperature_k for material in OFFICIAL_MATERIALS]
)
EINSTEIN_TEMPERATURES_K = np.array(
    [
        137.019316,
        276.859618,
        338.518310,
        344.966278,
        378.818109,
        519.867405,
        1797.371029,
    ]
)
EINSTEIN_FREQUENCIES_1E13_HZ = np.array(
    [
        0.285501930,
        0.576881841,
        0.705357710,
        0.718793095,
        0.789328866,
        1.083227912,
        3.745113555,
    ]
)


class EinsteinConversionTests(unittest.TestCase):
    """Check all seven conversions frozen before model implementation."""

    def test_official_einstein_temperatures_match_reference_table(self) -> None:
        observed = einstein_temperature_from_debye(DEBYE_TEMPERATURES_K)

        np.testing.assert_allclose(
            observed,
            EINSTEIN_TEMPERATURES_K,
            rtol=0.0,
            atol=5.0e-7,
        )

    def test_official_frequencies_match_unrounded_reference_table(self) -> None:
        temperatures = einstein_temperature_from_debye(DEBYE_TEMPERATURES_K)
        observed = einstein_frequency_from_temperature(temperatures) / 1.0e13

        np.testing.assert_allclose(
            observed,
            EINSTEIN_FREQUENCIES_1E13_HZ,
            rtol=0.0,
            atol=5.0e-10,
        )

    def test_frequencies_reproduce_every_official_displayed_value(self) -> None:
        temperatures = einstein_temperature_from_debye(DEBYE_TEMPERATURES_K)
        observed = np.round(
            einstein_frequency_from_temperature(temperatures) / 1.0e13,
            decimals=4,
        )
        expected = np.array(
            [material.official_frequency_1e13_hz for material in OFFICIAL_MATERIALS]
        )

        np.testing.assert_array_equal(observed, expected)

    def test_scalar_conversions_preserve_array_contract(self) -> None:
        temperature = einstein_temperature_from_debye(170)
        frequency = einstein_frequency_from_temperature(temperature)

        self.assertEqual(temperature.shape, ())
        self.assertEqual(frequency.shape, ())
        self.assertEqual(temperature.dtype, np.dtype(np.float64))
        self.assertEqual(frequency.dtype, np.dtype(np.float64))


class EinsteinHeatCapacityReferenceTests(unittest.TestCase):
    """Test pre-declared anchors, limits, and physical behaviour."""

    def test_zero_temperature_returns_exactly_zero(self) -> None:
        observed = einstein_molar_heat_capacity(
            0.0,
            EINSTEIN_TEMPERATURES_K,
        )

        np.testing.assert_array_equal(observed, np.zeros(7))

    def test_einstein_temperature_anchor_matches_reference_ratio(self) -> None:
        capacity = einstein_molar_heat_capacity(
            EINSTEIN_TEMPERATURES_K,
            EINSTEIN_TEMPERATURES_K,
        )
        observed = capacity / (3.0 * MOLAR_GAS_CONSTANT_J_MOL_K)

        np.testing.assert_allclose(
            observed,
            0.920673594207792,
            rtol=0.0,
            atol=1.0e-15,
        )

    def test_ordinary_branch_matches_direct_equation_at_x_two(self) -> None:
        einstein_temperature = 400.0
        temperature = einstein_temperature / 2.0
        observed = float(
            einstein_molar_heat_capacity(temperature, einstein_temperature)
        )
        expected_ratio = 4.0 * math.exp(2.0) / math.expm1(2.0) ** 2
        expected = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K * expected_ratio

        self.assertAlmostEqual(observed, expected, delta=5.0e-15)

    def test_high_temperature_series_is_used_without_cancellation(self) -> None:
        ratio = 1.0e-4
        einstein_temperature = 300.0
        temperature = einstein_temperature / ratio
        observed = float(
            einstein_molar_heat_capacity(temperature, einstein_temperature)
        )
        expected_ratio = 1.0 - ratio**2 / 12.0 + ratio**4 / 240.0
        expected = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K * expected_ratio

        self.assertEqual(observed, expected)

    def test_extreme_low_temperature_underflows_cleanly_to_zero(self) -> None:
        temperature = np.nextafter(0.0, 1.0)

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            observed = einstein_molar_heat_capacity(temperature, 1800.0)

        self.assertEqual(float(observed), 0.0)
        self.assertTrue(np.isfinite(observed))

    def test_official_grid_stays_bounded_and_non_decreasing(self) -> None:
        temperatures = np.arange(0.0, 801.0, 1.0)
        einstein_temperatures = einstein_temperature_from_debye(
            DEBYE_TEMPERATURES_K
        )
        capacity = einstein_molar_heat_capacity(
            temperatures,
            einstein_temperatures[:, None],
        )
        limit = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K

        self.assertTrue(np.all(np.isfinite(capacity)))
        self.assertTrue(np.all(capacity >= 0.0))
        self.assertTrue(np.all(capacity <= limit))
        self.assertTrue(np.all(np.diff(capacity, axis=1) >= -1.0e-12))


class EinsteinArrayContractTests(unittest.TestCase):
    """Verify explicit broadcasting, dtype, and input preservation."""

    def test_explicit_outer_broadcast_has_expected_shape(self) -> None:
        temperature = np.array([0.0, 100.0, 300.0, 800.0])
        einstein_temperature = np.array([[137.0], [520.0], [1797.0]])

        observed = einstein_molar_heat_capacity(
            temperature,
            einstein_temperature,
        )

        self.assertEqual(observed.shape, (3, 4))
        self.assertEqual(observed.dtype, np.dtype(np.float64))

    def test_scalar_inputs_return_zero_dimensional_float64(self) -> None:
        observed = einstein_molar_heat_capacity(300, 400)

        self.assertEqual(observed.shape, ())
        self.assertEqual(observed.dtype, np.dtype(np.float64))

    def test_inputs_are_not_modified(self) -> None:
        temperature = np.array([0.0, 100.0, 300.0])
        einstein_temperature = np.array([137.0, 277.0, 339.0])
        original_temperature = temperature.copy()
        original_einstein_temperature = einstein_temperature.copy()

        einstein_molar_heat_capacity(temperature, einstein_temperature)

        np.testing.assert_array_equal(temperature, original_temperature)
        np.testing.assert_array_equal(
            einstein_temperature,
            original_einstein_temperature,
        )

    def test_incompatible_shapes_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "broadcast-compatible"):
            einstein_molar_heat_capacity(np.ones(3), np.ones(2))


class EinsteinDomainTests(unittest.TestCase):
    """Require explicit failure for invalid physical and numerical inputs."""

    def test_negative_heat_capacity_temperatures_are_rejected(self) -> None:
        for value in (-1.0, [0.0, -1.0]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "non-negative"):
                    einstein_molar_heat_capacity(value, 300.0)

    def test_non_positive_einstein_temperatures_are_rejected(self) -> None:
        for value in (0.0, -1.0, [300.0, 0.0]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "strictly positive"):
                    einstein_molar_heat_capacity(300.0, value)

    def test_non_finite_inputs_are_rejected(self) -> None:
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(temperature=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    einstein_molar_heat_capacity(value, 300.0)
            with self.subTest(einstein_temperature=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    einstein_molar_heat_capacity(300.0, value)

    def test_boolean_complex_and_text_inputs_are_rejected(self) -> None:
        for value in (True, 1.0 + 2.0j, "300"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    einstein_molar_heat_capacity(value, 300.0)
                with self.assertRaises(TypeError):
                    einstein_molar_heat_capacity(300.0, value)

    def test_conversion_functions_reject_non_positive_inputs(self) -> None:
        functions = (
            einstein_temperature_from_debye,
            einstein_frequency_from_temperature,
        )
        for function in functions:
            for value in (0.0, -1.0, np.nan, np.inf):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(ValueError):
                        function(value)

    def test_unrepresentable_frequency_raises_explicitly(self) -> None:
        with self.assertRaisesRegex(FloatingPointError, "not representable"):
            einstein_frequency_from_temperature(np.finfo(np.float64).max)


if __name__ == "__main__":
    unittest.main()
