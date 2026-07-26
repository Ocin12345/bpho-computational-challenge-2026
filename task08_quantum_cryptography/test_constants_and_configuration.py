"""Focused tests for the frozen Task 8 constants and configuration."""

from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError

from task08_quantum_cryptography.configuration import (
    DEFAULT_CONFIGURATION,
    Task08Configuration,
)
from task08_quantum_cryptography.constants import (
    CLASSICAL_STREAM_SALT,
    DEGREES_PER_RADIAN,
    OFFICIAL_CLASSICAL_MISMATCH,
    OFFICIAL_PHI_DEG,
    OFFICIAL_QUANTUM_MISMATCH,
    OFFICIAL_SIGNED_DIFFERENCE,
    OFFICIAL_THETA_DEG,
    POLARISATION_PERIOD_DEG,
    RADIANS_PER_DEGREE,
    QUANTUM_STREAM_SALT,
    UINT32_MAXIMUM,
    WILSON_95_Z,
)


class ConstantsAndConfigurationTests(unittest.TestCase):
    def test_angle_conversions_are_reciprocal(self) -> None:
        self.assertAlmostEqual(RADIANS_PER_DEGREE * DEGREES_PER_RADIAN, 1.0)
        self.assertEqual(POLARISATION_PERIOD_DEG, 180.0)

    def test_official_reference_values_are_frozen(self) -> None:
        self.assertEqual(OFFICIAL_THETA_DEG, -30.0)
        self.assertEqual(OFFICIAL_PHI_DEG, 30.0)
        self.assertEqual(OFFICIAL_CLASSICAL_MISMATCH, 3.0 / 8.0)
        self.assertEqual(OFFICIAL_QUANTUM_MISMATCH, 3.0 / 4.0)
        self.assertEqual(OFFICIAL_SIGNED_DIFFERENCE, 3.0 / 8.0)

    def test_default_configuration_samples_zero_and_official_case(self) -> None:
        config = DEFAULT_CONFIGURATION
        self.assertEqual(config.schema_version, "task08-v1")
        self.assertEqual(config.default_theta_deg, OFFICIAL_THETA_DEG)
        self.assertEqual(config.default_phi_deg, OFFICIAL_PHI_DEG)
        self.assertEqual(config.angle_span_deg, 180.0)
        self.assertEqual(config.sweep_spacing_deg, 0.5)
        self.assertEqual(config.heatmap_spacing_deg, 1.0)
        self.assertEqual(config.summary_width_px, 3840)
        self.assertEqual(config.summary_height_px, 2160)
        self.assertEqual(config.evidence_size_budget_bytes, 25 * 1024 * 1024)
        self.assertEqual(config.figure_size_budget_bytes, 60 * 1024 * 1024)
        self.assertEqual(config.study_runtime_budget_s, 2.0)
        self.assertEqual(config.generation_runtime_budget_s, 20.0)
        self.assertEqual(config.simulation_minimum_photon_pairs, 10)
        self.assertEqual(config.simulation_maximum_photon_pairs, 100_000)
        self.assertEqual(config.simulation_default_photon_pairs, 1_000)
        self.assertEqual(config.simulation_default_seed, 2_026)
        self.assertEqual(config.simulation_runtime_budget_ms, 100.0)
        self.assertNotEqual(CLASSICAL_STREAM_SALT, QUANTUM_STREAM_SALT)
        self.assertEqual(UINT32_MAXIMUM, 2**32 - 1)
        self.assertAlmostEqual(WILSON_95_Z, 1.959963984540054)

    def test_configuration_is_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIGURATION.angle_step_deg = 2.0  # type: ignore[misc]

    def test_invalid_range_and_step_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task08Configuration(angle_minimum_deg=90.0, angle_maximum_deg=-90.0)
        with self.assertRaises(ValueError):
            Task08Configuration(angle_minimum_deg=-80.0, angle_maximum_deg=100.0)
        with self.assertRaises(ValueError):
            Task08Configuration(angle_step_deg=7.0)

    def test_non_finite_and_out_of_range_angles_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task08Configuration(default_theta_deg=math.inf)
        with self.assertRaises(ValueError):
            Task08Configuration(default_phi_deg=91.0)

    def test_grids_must_be_odd_and_include_zero(self) -> None:
        with self.assertRaises(ValueError):
            Task08Configuration(sweep_point_count=360)
        with self.assertRaises(ValueError):
            Task08Configuration(heatmap_point_count=180)

    def test_boolean_numeric_values_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Task08Configuration(angle_step_deg=True)
        with self.assertRaises(TypeError):
            Task08Configuration(figure_dpi=False)

    def test_invalid_simulation_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task08Configuration(simulation_minimum_photon_pairs=1)
        with self.assertRaises(ValueError):
            Task08Configuration(
                simulation_minimum_photon_pairs=100,
                simulation_maximum_photon_pairs=99,
            )
        with self.assertRaises(ValueError):
            Task08Configuration(simulation_default_photon_pairs=100_001)
        with self.assertRaises(ValueError):
            Task08Configuration(simulation_default_seed=2**32)
        with self.assertRaises(TypeError):
            Task08Configuration(simulation_default_seed=True)


if __name__ == "__main__":
    unittest.main()
