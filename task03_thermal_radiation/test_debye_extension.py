"""Tests for the optional Einstein--Debye comparison."""

from __future__ import annotations

import math
import unittest

import numpy as np

from task03_thermal_radiation.constants import (
    EINSTEIN_DEBYE_FACTOR,
    MOLAR_GAS_CONSTANT_J_MOL_K,
)
from task03_thermal_radiation.debye_extension import (
    DEBYE_INTEGRAL_INFINITY,
    debye_integral,
    debye_low_temperature_heat_capacity,
    debye_molar_heat_capacity,
)
from task03_thermal_radiation.models import einstein_molar_heat_capacity


class DebyeIntegralTests(unittest.TestCase):
    def test_infinite_limit_matches_analytic_value(self) -> None:
        self.assertAlmostEqual(
            float(debye_integral(80.0)),
            4.0 * math.pi**4 / 15.0,
            places=13,
        )
        self.assertAlmostEqual(
            DEBYE_INTEGRAL_INFINITY,
            4.0 * math.pi**4 / 15.0,
            places=15,
        )

    def test_quadrature_converges(self) -> None:
        upper = np.array([0.02, 0.2, 1.0, 5.0, 20.0, 50.0])
        lower_order = debye_integral(upper, quadrature_order=160)
        higher_order = debye_integral(upper, quadrature_order=320)
        np.testing.assert_allclose(lower_order, higher_order, rtol=2e-12, atol=2e-14)

    def test_integral_rejects_invalid_inputs(self) -> None:
        for value in (-1.0, np.nan, np.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    debye_integral(value)
        with self.assertRaises(TypeError):
            debye_integral(True)
        with self.assertRaises(ValueError):
            debye_integral(1.0, quadrature_order=8)


class DebyeHeatCapacityTests(unittest.TestCase):
    def test_zero_temperature_and_physical_bounds(self) -> None:
        temperatures = np.linspace(0.0, 5000.0, 1001)
        capacity = debye_molar_heat_capacity(temperatures, 470.0)
        upper = 3.0 * MOLAR_GAS_CONSTANT_J_MOL_K
        self.assertEqual(float(capacity[0]), 0.0)
        self.assertTrue(np.all(capacity >= 0.0))
        self.assertTrue(np.all(capacity <= upper))
        self.assertTrue(np.all(np.diff(capacity) >= -1e-12))

    def test_low_temperature_cubic_law(self) -> None:
        ratios = np.array([0.005, 0.01, 0.02])
        exact = debye_molar_heat_capacity(ratios, 1.0)
        asymptote = debye_low_temperature_heat_capacity(ratios, 1.0)
        np.testing.assert_allclose(exact, asymptote, rtol=2e-10, atol=0.0)
        observed_ratio = exact[2] / exact[1]
        self.assertAlmostEqual(float(observed_ratio), 8.0, places=9)

    def test_high_temperature_series(self) -> None:
        ratio = 100.0
        normalized = float(
            debye_molar_heat_capacity(ratio, 1.0)
            / (3.0 * MOLAR_GAS_CONSTANT_J_MOL_K)
        )
        expected = 1.0 - 1.0 / (20.0 * ratio**2) + 1.0 / (560.0 * ratio**4)
        self.assertAlmostEqual(normalized, expected, places=13)

    def test_normalized_curve_is_material_independent(self) -> None:
        ratios = np.linspace(0.02, 2.0, 80)
        reference = debye_molar_heat_capacity(ratios * 170.0, 170.0)
        comparison = debye_molar_heat_capacity(ratios * 2230.0, 2230.0)
        np.testing.assert_allclose(reference, comparison, rtol=2e-14, atol=1e-14)

    def test_debye_recovers_more_low_temperature_capacity_than_einstein(self) -> None:
        ratios = np.linspace(0.02, 2.0, 120)
        debye = debye_molar_heat_capacity(ratios, 1.0)
        einstein = einstein_molar_heat_capacity(
            ratios,
            EINSTEIN_DEBYE_FACTOR,
        )
        self.assertTrue(np.all(debye > einstein))
        self.assertGreater(float(debye[0] / einstein[0]), 1_000_000.0)

    def test_broadcasting_and_invalid_inputs(self) -> None:
        result = debye_molar_heat_capacity(
            np.array([[0.0], [100.0]]),
            np.array([170.0, 470.0]),
        )
        self.assertEqual(result.shape, (2, 2))
        for temperature, debye_temperature in [
            (-1.0, 170.0),
            (100.0, 0.0),
            (100.0, np.nan),
        ]:
            with self.subTest(
                temperature=temperature,
                debye_temperature=debye_temperature,
            ):
                with self.assertRaises(ValueError):
                    debye_molar_heat_capacity(temperature, debye_temperature)
        with self.assertRaises(TypeError):
            debye_molar_heat_capacity(True, 170.0)


if __name__ == "__main__":
    unittest.main()
