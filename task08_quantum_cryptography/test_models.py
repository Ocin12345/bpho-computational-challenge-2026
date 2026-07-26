"""Focused tests for the Task 8 Python reference model."""

from __future__ import annotations

import unittest

import numpy as np

from task08_quantum_cryptography.configuration import DEFAULT_CONFIGURATION
from task08_quantum_cryptography.constants import (
    OFFICIAL_CLASSICAL_MISMATCH,
    OFFICIAL_PHI_DEG,
    OFFICIAL_QUANTUM_MISMATCH,
    OFFICIAL_SIGNED_DIFFERENCE,
    OFFICIAL_THETA_DEG,
)
from task08_quantum_cryptography.models import (
    angle_samples,
    angle_sweep,
    degrees_to_radians,
    detector_probabilities,
    mismatch_comparison,
    mismatch_grid,
    normalize_polarisation_angle_deg,
    probability_percent,
    radians_to_degrees,
    relative_detector_angle_deg,
)


class ReferenceModelTests(unittest.TestCase):
    def test_degree_conversion_and_polarisation_normalisation(self) -> None:
        angles = np.asarray([-270.0, -180.0, -90.0, 0.0, 90.0, 180.0, 270.0])
        radians = degrees_to_radians(angles)
        np.testing.assert_allclose(radians_to_degrees(radians), angles, atol=1e-13)
        np.testing.assert_allclose(
            normalize_polarisation_angle_deg(angles),
            np.asarray([-90.0, 0.0, -90.0, 0.0, -90.0, 0.0, -90.0]),
            atol=0.0,
        )

    def test_official_reference_case(self) -> None:
        result = mismatch_comparison(OFFICIAL_THETA_DEG, OFFICIAL_PHI_DEG)
        self.assertAlmostEqual(
            float(result.classical_mismatch),
            OFFICIAL_CLASSICAL_MISMATCH,
            places=15,
        )
        self.assertAlmostEqual(
            float(result.quantum_mismatch),
            OFFICIAL_QUANTUM_MISMATCH,
            places=15,
        )
        self.assertAlmostEqual(
            float(result.signed_difference),
            OFFICIAL_SIGNED_DIFFERENCE,
            places=15,
        )

    def test_frozen_reference_cases(self) -> None:
        theta = np.asarray([0.0, 45.0, -45.0, 0.0])
        phi = np.asarray([0.0, 45.0, 45.0, 90.0])
        result = mismatch_comparison(theta, phi)
        np.testing.assert_allclose(
            result.classical_mismatch,
            np.asarray([0.0, 0.5, 0.5, 1.0]),
            atol=5e-16,
        )
        np.testing.assert_allclose(
            result.quantum_mismatch,
            np.asarray([0.0, 0.0, 1.0, 1.0]),
            atol=5e-16,
        )
        np.testing.assert_allclose(
            result.signed_difference,
            np.asarray([0.0, -0.5, 0.5, 0.0]),
            atol=5e-16,
        )

    def test_detector_probabilities_and_complements(self) -> None:
        angles = np.linspace(-90.0, 90.0, 721)
        detector = detector_probabilities(angles)
        np.testing.assert_allclose(detector.x + detector.y, 1.0, atol=7e-16)
        result = mismatch_comparison(angles[:, None], angles[None, :])
        np.testing.assert_allclose(
            result.classical_match + result.classical_mismatch,
            1.0,
            atol=0.0,
        )
        np.testing.assert_allclose(
            result.quantum_match + result.quantum_mismatch,
            1.0,
            atol=7e-16,
        )
        self.assertTrue(np.all(result.classical_mismatch >= 0.0))
        self.assertTrue(np.all(result.classical_mismatch <= 1.0))
        self.assertTrue(np.all(result.quantum_mismatch >= 0.0))
        self.assertTrue(np.all(result.quantum_mismatch <= 1.0))

    def test_symmetry_and_periodicity(self) -> None:
        theta = np.asarray([-73.5, -30.0, 0.0, 19.25, 87.0])
        phi = np.asarray([62.0, 30.0, -45.0, 81.75, -88.0])
        forward = mismatch_comparison(theta, phi)
        reversed_result = mismatch_comparison(phi, theta)
        shifted = mismatch_comparison(theta + 180.0, phi - 360.0)
        np.testing.assert_allclose(
            forward.classical_mismatch,
            reversed_result.classical_mismatch,
            atol=1e-15,
        )
        np.testing.assert_allclose(
            forward.quantum_mismatch,
            reversed_result.quantum_mismatch,
            atol=1e-15,
        )
        np.testing.assert_allclose(
            forward.classical_mismatch,
            shifted.classical_mismatch,
            atol=1e-15,
        )
        np.testing.assert_allclose(
            forward.quantum_mismatch,
            shifted.quantum_mismatch,
            atol=1e-15,
        )

    def test_relative_angle_and_percent_conversion(self) -> None:
        np.testing.assert_allclose(
            relative_detector_angle_deg(
                np.asarray([-30.0, 80.0, -80.0]),
                np.asarray([30.0, -80.0, 80.0]),
            ),
            np.asarray([60.0, 20.0, -20.0]),
            atol=0.0,
        )
        np.testing.assert_allclose(
            probability_percent(np.asarray([0.0, 0.375, 0.75, 1.0])),
            np.asarray([0.0, 37.5, 75.0, 100.0]),
            atol=0.0,
        )

    def test_angle_samples_and_both_sweep_directions(self) -> None:
        samples = angle_samples()
        self.assertEqual(samples.shape, (DEFAULT_CONFIGURATION.sweep_point_count,))
        self.assertEqual(float(samples[0]), -90.0)
        self.assertEqual(float(samples[len(samples) // 2]), 0.0)
        self.assertEqual(float(samples[-1]), 90.0)

        phi_sweep = angle_sweep(-30.0, variable="phi", point_count=181)
        self.assertTrue(np.all(phi_sweep.theta_deg == -30.0))
        self.assertEqual(float(phi_sweep.phi_deg[90]), 0.0)
        theta_sweep = angle_sweep(30.0, variable="theta", point_count=181)
        self.assertTrue(np.all(theta_sweep.phi_deg == 30.0))
        self.assertEqual(float(theta_sweep.theta_deg[90]), 0.0)

    def test_default_and_custom_grids_have_theta_by_phi_shape(self) -> None:
        default_grid = mismatch_grid()
        expected = DEFAULT_CONFIGURATION.heatmap_point_count
        self.assertEqual(default_grid.theta_deg.shape, (expected, expected))
        self.assertEqual(default_grid.phi_deg.shape, (expected, expected))
        self.assertEqual(
            default_grid.comparison.quantum_mismatch.shape,
            (expected, expected),
        )

        custom = mismatch_grid(
            theta_deg=np.asarray([-30.0, 0.0, 30.0]),
            phi_deg=np.asarray([-45.0, 45.0]),
        )
        self.assertEqual(custom.theta_deg.shape, (3, 2))
        self.assertEqual(custom.phi_deg.shape, (3, 2))
        np.testing.assert_allclose(custom.theta_deg[:, 0], [-30.0, 0.0, 30.0])
        np.testing.assert_allclose(custom.phi_deg[0, :], [-45.0, 45.0])

    def test_scalar_and_broadcast_outputs(self) -> None:
        scalar = mismatch_comparison(0.0, 0.0)
        self.assertEqual(scalar.quantum_mismatch.shape, ())
        vector = mismatch_comparison(
            np.asarray([-30.0, 0.0, 30.0])[:, None],
            np.asarray([-45.0, 45.0])[None, :],
        )
        self.assertEqual(vector.classical_mismatch.shape, (3, 2))
        self.assertEqual(vector.quantum_mismatch.shape, (3, 2))

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            mismatch_comparison(True, 0.0)
        with self.assertRaises(TypeError):
            mismatch_comparison(1.0 + 2.0j, 0.0)
        with self.assertRaises(ValueError):
            mismatch_comparison(np.nan, 0.0)
        with self.assertRaises(ValueError):
            mismatch_comparison(np.ones((2, 3)), np.ones((4,)))
        with self.assertRaises(ValueError):
            probability_percent(1.01)
        with self.assertRaises(ValueError):
            angle_sweep(0.0, variable="gamma")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            angle_sweep(91.0)
        with self.assertRaises(TypeError):
            angle_sweep(np.asarray([0.0]))
        with self.assertRaises(ValueError):
            mismatch_grid(theta_deg=np.asarray([[0.0]]))
        with self.assertRaises(ValueError):
            mismatch_grid(phi_deg=np.asarray([]))


if __name__ == "__main__":
    unittest.main()
