from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION
from task07_particle_in_box.generate_superposition_extension import (
    CSV_FILENAME,
    JSON_FILENAME,
    build_superposition_payload,
    generate_superposition_evidence,
)
from task07_particle_in_box.superposition_extension import (
    beat_period_s,
    dimensionless_probability_density,
    dimensionless_wavefunction,
    energy_uncertainty_ev,
    expected_position_over_width,
    left_half_probability,
    mean_energy_ev,
)


class SuperpositionModelTests(unittest.TestCase):
    def test_density_normalizes_for_several_phases(self) -> None:
        positions = np.linspace(0.0, 1.0, 10001)[:, None]
        phases = np.linspace(0.0, 2.0 * np.pi, 9)[None, :]
        densities = dimensionless_probability_density(positions, phases)
        np.testing.assert_allclose(
            np.trapezoid(densities, positions[:, 0], axis=0),
            1.0,
            atol=2e-14,
        )

    def test_wavefunction_obeys_infinite_walls_and_is_zero_outside(self) -> None:
        values = dimensionless_wavefunction(
            np.asarray([-1.0, 0.0, 1.0, 2.0]),
            np.zeros(4),
        )
        np.testing.assert_allclose(values, 0.0, atol=4e-16)

    def test_full_period_revival_and_half_period_mirror(self) -> None:
        positions = np.linspace(0.0, 1.0, 501)
        start = dimensionless_probability_density(positions, 0.0)
        full = dimensionless_probability_density(positions, 2.0 * np.pi)
        half = dimensionless_probability_density(positions, np.pi)
        np.testing.assert_allclose(full, start, atol=2e-15)
        np.testing.assert_allclose(half[::-1], start, atol=3e-15)

    def test_analytical_position_and_left_probability_anchors(self) -> None:
        self.assertAlmostEqual(float(expected_position_over_width(0.0)), 0.319873, places=6)
        self.assertAlmostEqual(float(expected_position_over_width(np.pi)), 0.680127, places=6)
        self.assertAlmostEqual(float(expected_position_over_width(np.pi / 2)), 0.5, places=15)
        self.assertAlmostEqual(float(left_half_probability(0.0)), 0.924413, places=6)
        self.assertAlmostEqual(float(left_half_probability(np.pi)), 0.075587, places=6)

    def test_energy_and_beat_period_anchors(self) -> None:
        configuration = DEFAULT_CONFIGURATION
        mean = mean_energy_ev(
            configuration.particle_mass_kg, configuration.box_width_m
        )
        uncertainty = energy_uncertainty_ev(
            configuration.particle_mass_kg, configuration.box_width_m
        )
        period_fs = beat_period_s(
            configuration.particle_mass_kg, configuration.box_width_m
        ) * 1e15
        self.assertAlmostEqual(mean, 0.9400754052621815, places=14)
        self.assertAlmostEqual(uncertainty, 0.5640452431573089, places=14)
        self.assertAlmostEqual(period_fs, 3.666077985, places=9)

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            dimensionless_probability_density([0.5, np.nan], 0.0)
        with self.assertRaises(TypeError):
            dimensionless_probability_density([True], 0.0)
        with self.assertRaises(ValueError):
            beat_period_s(-1.0, 1.0)


class SuperpositionEvidenceTests(unittest.TestCase):
    def test_payload_is_accepted_and_complete(self) -> None:
        payload = build_superposition_payload()
        self.assertEqual(payload["schema_version"], "task07-superposition-v1")
        self.assertEqual(payload["status"], "accepted_optional_extension")
        self.assertEqual(len(payload["phase_anchors"]), 17)
        self.assertTrue(payload["validation"]["passed"])
        self.assertEqual(payload["validation"]["check_count"], 14)
        self.assertTrue(
            all(check["passed"] for check in payload["validation"]["checks"])
        )

    def test_generation_is_parseable_and_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = generate_superposition_evidence(directory)
            first_bytes = {path.name: path.read_bytes() for path in first}
            second = generate_superposition_evidence(directory)
            second_bytes = {path.name: path.read_bytes() for path in second}
            self.assertEqual(first_bytes, second_bytes)
            with (directory / JSON_FILENAME).open(encoding="utf-8") as handle:
                self.assertTrue(json.load(handle)["validation"]["passed"])
            with (directory / CSV_FILENAME).open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 17)


if __name__ == "__main__":
    unittest.main()
