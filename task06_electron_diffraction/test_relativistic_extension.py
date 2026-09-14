"""Focused tests for the Task 6 relativistic precision extension."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from task06_electron_diffraction.relativistic_extension import (
    build_relativistic_evidence,
    corrupted_copy,
    first_order_radius_from_wavelength_m,
    relativistic_momentum_kg_m_s,
    relativistic_wavelength_m,
    validate_relativistic_evidence,
    write_relativistic_evidence,
)


class RelativisticExtensionTests(unittest.TestCase):
    def test_endpoint_wavelength_corrections_match_frozen_values(self) -> None:
        evidence = build_relativistic_evidence()
        self.assertAlmostEqual(
            evidence["records"][0]["wavelength_correction_percent"],
            -0.04888790572988855,
            places=12,
        )
        self.assertAlmostEqual(
            evidence["records"][-1]["wavelength_correction_percent"],
            -0.2437249653422624,
            places=12,
        )

    def test_relativistic_wavelength_is_shorter_and_monotonic(self) -> None:
        voltage = np.asarray([1000.0, 3000.0, 5000.0])
        wavelength = relativistic_wavelength_m(voltage)
        self.assertTrue(np.all(np.diff(wavelength) < 0.0))
        self.assertTrue(np.all(relativistic_momentum_kg_m_s(voltage) > 0.0))

    def test_exact_radius_accepts_valid_inputs_and_rejects_invalid_ones(self) -> None:
        radius = first_order_radius_from_wavelength_m(
            relativistic_wavelength_m([1000.0, 5000.0]), 0.123e-9
        )
        self.assertTrue(np.all(radius > 0.0))
        with self.assertRaises(ValueError):
            first_order_radius_from_wavelength_m([1.0], 0.1e-9)
        with self.assertRaises(ValueError):
            first_order_radius_from_wavelength_m([1.0e-11], -0.1e-9)

    def test_voltage_validation_rejects_invalid_inputs(self) -> None:
        for invalid in ([999.0], [5001.0], [float("nan")]):
            with self.assertRaises(ValueError):
                relativistic_wavelength_m(invalid)
        with self.assertRaises(TypeError):
            relativistic_wavelength_m([True])
        with self.assertRaises(TypeError):
            relativistic_wavelength_m([1.0 + 2.0j])

    def test_evidence_passes_all_extension_checks(self) -> None:
        evidence = build_relativistic_evidence()
        validation = evidence["validation"]
        self.assertTrue(validation["passed"])
        self.assertEqual(validation["check_count"], 10)
        self.assertTrue(all(check["passed"] for check in validation["checks"]))
        self.assertEqual(len(evidence["records"]), 401)

    def test_corruption_is_detected(self) -> None:
        evidence = corrupted_copy(build_relativistic_evidence())
        checks = validate_relativistic_evidence(evidence)
        failed = {check["name"] for check in checks if not check["passed"]}
        self.assertIn("relativistic_wavelength", failed)
        self.assertIn("energy_momentum_identity", failed)

    def test_json_generation_is_reproducible_and_finite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            write_relativistic_evidence(first)
            write_relativistic_evidence(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            payload = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "task06-relativistic-extension-v1")


if __name__ == "__main__":
    unittest.main()
