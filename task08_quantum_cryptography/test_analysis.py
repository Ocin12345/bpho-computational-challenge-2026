from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, replace

import numpy as np

from task08_quantum_cryptography.analysis import build_task08_study
from task08_quantum_cryptography.configuration import DEFAULT_CONFIGURATION


class StudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task08_study()

    def test_shapes_and_official_anchor(self) -> None:
        self.assertEqual(
            self.study.sweep_point_count,
            DEFAULT_CONFIGURATION.sweep_point_count,
        )
        self.assertEqual(
            self.study.grid_shape,
            (
                DEFAULT_CONFIGURATION.heatmap_point_count,
                DEFAULT_CONFIGURATION.heatmap_point_count,
            ),
        )
        index = int(np.flatnonzero(self.study.sweep_phi_deg == 30.0)[0])
        self.assertAlmostEqual(float(self.study.sweep_classical_mismatch[index]), 3 / 8)
        self.assertAlmostEqual(float(self.study.sweep_quantum_mismatch[index]), 3 / 4)

    def test_arrays_are_read_only(self) -> None:
        self.assertFalse(self.study.sweep_phi_deg.flags.writeable)
        self.assertFalse(self.study.grid_quantum_mismatch.flags.writeable)
        with self.assertRaises(ValueError):
            self.study.sweep_phi_deg[0] = 1.0
        with self.assertRaises(FrozenInstanceError):
            self.study.schema_version = "changed"  # type: ignore[misc]

    def test_invalid_configuration_and_shapes_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            build_task08_study(object())  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            replace(self.study, sweep_phi_deg=np.asarray([0.0, 1.0]))
        with self.assertRaises(ValueError):
            replace(self.study, grid_phi_deg=np.zeros((2, 2)))


if __name__ == "__main__":
    unittest.main()
