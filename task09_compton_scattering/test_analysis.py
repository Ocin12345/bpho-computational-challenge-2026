"""Tests for the immutable Task 9 multi-energy study."""

from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from task09_compton_scattering.analysis import build_task09_study


class StudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task09_study()

    def test_shapes_axes_and_official_endpoints(self) -> None:
        self.assertEqual(self.study.incident_energies_kev.shape, (5,))
        self.assertEqual(self.study.theta_axis_deg.shape, (721,))
        self.assertEqual(self.study.incident_energy_kev.shape, (5, 721))
        self.assertEqual(self.study.row_count, 3_605)
        np.testing.assert_array_equal(
            self.study.incident_energy_kev[:, 0],
            self.study.incident_energies_kev,
        )
        self.assertEqual(float(self.study.theta_axis_deg[0]), 0.0)
        self.assertEqual(float(self.study.theta_axis_deg[360]), 90.0)
        self.assertEqual(float(self.study.theta_axis_deg[-1]), 180.0)

    def test_all_study_arrays_are_read_only(self) -> None:
        for name, value in vars(self.study).items():
            if name == "schema_version":
                continue
            self.assertFalse(value.flags.writeable, name)
        with self.assertRaises(ValueError):
            self.study.electron_beta[0, 0] = 1.0

    def test_invalid_study_shapes_and_values_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            replace(self.study, schema_version="wrong")
        with self.assertRaises(ValueError):
            replace(self.study, electron_beta=np.zeros((5, 3)))
        values = self.study.electron_beta.copy()
        values[0, 0] = np.nan
        with self.assertRaises(ValueError):
            replace(self.study, electron_beta=values)
        with self.assertRaises(TypeError):
            build_task09_study(object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
