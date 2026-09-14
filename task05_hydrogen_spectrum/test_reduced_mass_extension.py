from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from task05_hydrogen_spectrum.generate_reduced_mass_extension import (
    CSV_FILENAME,
    JSON_FILENAME,
    build_reduced_mass_payload,
    generate_reduced_mass_evidence,
)
from task05_hydrogen_spectrum.models import (
    transition_energy_ev,
    transition_frequency_hz,
    transition_wavelength_m,
)
from task05_hydrogen_spectrum.reduced_mass_extension import (
    ELECTRON_PROTON_MASS_RATIO,
    reduced_mass_factor,
    reduced_mass_transition_energy_ev,
    reduced_mass_transition_frequency_hz,
    reduced_mass_transition_wavelength_m,
)


class ReducedMassModelTests(unittest.TestCase):
    def test_protium_factor_is_physical(self) -> None:
        factor = reduced_mass_factor()
        self.assertGreater(factor, 0.999)
        self.assertLess(factor, 1.0)
        self.assertAlmostEqual(
            1.0 / factor - 1.0,
            ELECTRON_PROTON_MASS_RATIO,
            places=15,
        )

    def test_infinite_mass_limit_recovers_baseline(self) -> None:
        self.assertEqual(reduced_mass_factor(0.0), 1.0)
        self.assertEqual(
            float(reduced_mass_transition_energy_ev(3, 2, electron_nucleus_mass_ratio=0.0)),
            float(transition_energy_ev(3, 2)),
        )
        self.assertEqual(
            float(reduced_mass_transition_wavelength_m(3, 2, electron_nucleus_mass_ratio=0.0)),
            float(transition_wavelength_m(3, 2)),
        )

    def test_energy_frequency_and_wavelength_scale_consistently(self) -> None:
        initial = np.array([2, 3, 4, 5, 10], dtype=np.int64)
        final = np.array([1, 2, 2, 2, 9], dtype=np.int64)
        factor = reduced_mass_factor()
        np.testing.assert_allclose(
            reduced_mass_transition_energy_ev(initial, final),
            transition_energy_ev(initial, final) * factor,
            rtol=5e-15,
        )
        np.testing.assert_allclose(
            reduced_mass_transition_frequency_hz(initial, final),
            transition_frequency_hz(initial, final) * factor,
            rtol=5e-15,
        )
        np.testing.assert_allclose(
            reduced_mass_transition_wavelength_m(initial, final),
            transition_wavelength_m(initial, final) / factor,
            rtol=5e-15,
        )

    def test_h_alpha_anchor(self) -> None:
        wavelength_nm = float(reduced_mass_transition_wavelength_m(3, 2) * 1e9)
        self.assertAlmostEqual(wavelength_nm, 656.469606333, places=9)
        self.assertGreater(wavelength_nm, 656.112)

    def test_invalid_mass_ratios_are_rejected(self) -> None:
        for value in (True, -1.0, float("inf"), float("nan"), "0.1"):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                reduced_mass_factor(value)  # type: ignore[arg-type]

    def test_invalid_transitions_still_use_baseline_validation(self) -> None:
        with self.assertRaises(ValueError):
            reduced_mass_transition_energy_ev(2, 2)


class ReducedMassEvidenceTests(unittest.TestCase):
    def test_payload_is_complete_and_accepted(self) -> None:
        payload = build_reduced_mass_payload()
        self.assertEqual(payload["schema_version"], "task05-reduced-mass-v1")
        self.assertEqual(payload["status"], "accepted_optional_extension")
        self.assertEqual(len(payload["transitions"]), 45)
        self.assertEqual(len(payload["featured_transitions"]), 5)
        self.assertTrue(payload["validation"]["passed"])
        self.assertEqual(payload["validation"]["check_count"], 12)
        self.assertTrue(
            all(check["passed"] for check in payload["validation"]["checks"])
        )

    def test_every_wavelength_shift_is_positive_and_constant_fractionally(self) -> None:
        transitions = build_reduced_mass_payload()["transitions"]
        self.assertTrue(all(row["wavelength_shift_nm"] > 0 for row in transitions))
        np.testing.assert_allclose(
            [row["relative_shift"] for row in transitions],
            ELECTRON_PROTON_MASS_RATIO,
            rtol=5e-13,
        )

    def test_generation_is_parseable_and_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = generate_reduced_mass_evidence(directory)
            first_bytes = {path.name: path.read_bytes() for path in first}
            second = generate_reduced_mass_evidence(directory)
            second_bytes = {path.name: path.read_bytes() for path in second}
            self.assertEqual(first_bytes, second_bytes)
            with (directory / JSON_FILENAME).open(encoding="utf-8") as handle:
                self.assertTrue(json.load(handle)["validation"]["passed"])
            with (directory / CSV_FILENAME).open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 45)


if __name__ == "__main__":
    unittest.main()
