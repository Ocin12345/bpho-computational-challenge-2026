"""Unit tests for the Task 3 Planck-spectrum model."""

from __future__ import annotations

import math
import unittest
import warnings

import numpy as np

from task03_thermal_radiation.constants import (
    BOLTZMANN_CONSTANT_J_K,
    SPEED_OF_LIGHT_M_S,
)
from task03_thermal_radiation.models import (
    planck_spectral_exitance,
    planck_spectral_radiance,
    spectral_density_per_nanometre,
)


class PlanckReferenceValueTests(unittest.TestCase):
    """Check numerical values that were frozen before implementation."""

    def test_reference_radiance_at_500_nm_and_6000_k(self) -> None:
        radiance = planck_spectral_radiance(500.0e-9, 6000.0)

        self.assertEqual(radiance.shape, ())
        self.assertEqual(radiance.dtype, np.dtype(np.float64))
        self.assertAlmostEqual(
            float(radiance),
            3.1756906656226242e13,
            delta=0.7,
        )

    def test_reference_exitance_per_nm_at_500_nm_and_6000_k(self) -> None:
        exitance_per_m = planck_spectral_exitance(500.0e-9, 6000.0)
        exitance_per_nm = spectral_density_per_nanometre(exitance_per_m)

        self.assertAlmostEqual(
            float(exitance_per_nm),
            99_767.26465193718,
            delta=2.0e-9,
        )

    def test_exitance_is_exactly_pi_times_radiance(self) -> None:
        wavelength = np.linspace(100.0e-9, 3000.0e-9, 701)
        temperature = np.array([[4000.0], [5000.0], [6000.0]])

        radiance = planck_spectral_radiance(wavelength, temperature)
        exitance = planck_spectral_exitance(wavelength, temperature)

        np.testing.assert_allclose(
            exitance,
            math.pi * radiance,
            rtol=2.0e-16,
            atol=0.0,
        )


class PlanckArrayContractTests(unittest.TestCase):
    """Verify broadcasting, shape, dtype, and input-preservation contracts."""

    def test_explicit_outer_broadcast_has_expected_shape(self) -> None:
        wavelength = np.array([400.0e-9, 500.0e-9, 700.0e-9])
        temperature = np.array([[4000.0], [5000.0]])

        result = planck_spectral_radiance(wavelength, temperature)

        self.assertEqual(result.shape, (2, 3))
        self.assertEqual(result.dtype, np.dtype(np.float64))
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(np.all(result >= 0.0))

    def test_hotter_body_has_greater_radiance_at_fixed_wavelength(self) -> None:
        result = planck_spectral_radiance(
            500.0e-9,
            np.array([4000.0, 5000.0, 6000.0]),
        )

        self.assertTrue(np.all(np.diff(result) > 0.0))

    def test_inputs_are_not_modified(self) -> None:
        wavelength = np.array([300.0e-9, 600.0e-9, 1200.0e-9])
        temperature = np.array([4000.0, 5000.0, 6000.0])
        original_wavelength = wavelength.copy()
        original_temperature = temperature.copy()

        planck_spectral_radiance(wavelength, temperature)

        np.testing.assert_array_equal(wavelength, original_wavelength)
        np.testing.assert_array_equal(temperature, original_temperature)

    def test_integer_inputs_still_return_float64(self) -> None:
        result = planck_spectral_radiance(1, 4000)

        self.assertEqual(result.dtype, np.dtype(np.float64))
        self.assertEqual(result.shape, ())

    def test_incompatible_shapes_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "broadcast-compatible"):
            planck_spectral_radiance(np.ones(3), np.ones(2))


class PlanckDomainTests(unittest.TestCase):
    """Verify that invalid physical and numerical inputs fail explicitly."""

    def test_non_positive_wavelengths_are_rejected(self) -> None:
        for value in (0.0, -1.0, [500.0e-9, 0.0]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "strictly positive"):
                    planck_spectral_radiance(value, 5000.0)

    def test_non_positive_temperatures_are_rejected(self) -> None:
        for value in (0.0, -1.0, [4000.0, 0.0]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "strictly positive"):
                    planck_spectral_radiance(500.0e-9, value)

    def test_non_finite_inputs_are_rejected(self) -> None:
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(wavelength=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    planck_spectral_radiance(value, 5000.0)
            with self.subTest(temperature=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    planck_spectral_radiance(500.0e-9, value)

    def test_boolean_complex_and_text_inputs_are_rejected(self) -> None:
        for value in (True, 1.0 + 2.0j, "5e-7"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    planck_spectral_radiance(value, 5000.0)

    def test_density_conversion_rejects_negative_or_non_finite_values(self) -> None:
        for value in (-1.0, np.nan, np.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    spectral_density_per_nanometre(value)


class PlanckNumericalStabilityTests(unittest.TestCase):
    """Exercise both exponential branches and relevant asymptotic regions."""

    def test_declared_integration_domain_is_finite_without_warnings(self) -> None:
        wavelength = np.logspace(-9.0, -2.0, 10_001)
        temperature = np.array([[4000.0], [5000.0], [6000.0]])

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            result = planck_spectral_radiance(wavelength, temperature)

        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(np.all(result >= 0.0))

    def test_extreme_short_wavelength_underflows_cleanly_to_zero(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            result = planck_spectral_radiance(1.0e-20, 100.0)

        self.assertEqual(float(result), 0.0)
        self.assertTrue(np.isfinite(result))

    def test_large_exponent_branch_remains_positive_when_representable(self) -> None:
        result = planck_spectral_radiance(100.0e-9, 1000.0)

        self.assertGreater(float(result), 0.0)
        self.assertTrue(np.isfinite(result))

    def test_long_wavelength_limit_approaches_rayleigh_jeans_law(self) -> None:
        wavelength = 0.1
        temperature = 300.0
        planck = float(planck_spectral_radiance(wavelength, temperature))
        rayleigh_jeans = (
            2.0
            * SPEED_OF_LIGHT_M_S
            * BOLTZMANN_CONSTANT_J_K
            * temperature
            / wavelength**4
        )

        self.assertLess(abs(planck / rayleigh_jeans - 1.0), 3.0e-4)

    def test_per_nanometre_conversion_is_linear_and_shape_preserving(self) -> None:
        source = np.array([[0.0, 1.0], [2.5e9, 8.0e12]])
        converted = spectral_density_per_nanometre(source)

        self.assertEqual(converted.shape, source.shape)
        self.assertEqual(converted.dtype, np.dtype(np.float64))
        np.testing.assert_array_equal(converted, source * 1.0e-9)


if __name__ == "__main__":
    unittest.main()
