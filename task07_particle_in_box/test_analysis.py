from __future__ import annotations

import unittest

import numpy as np

from task07_particle_in_box.analysis import build_task07_study, solve_numerical_box
from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task07_study()

    def test_study_shapes_and_read_only_arrays(self) -> None:
        self.assertEqual(self.study.energies_j.shape, (10,))
        self.assertEqual(self.study.wavefunctions_m_neg_half.shape, (2001, 4))
        self.assertEqual(self.study.numerical_energies_j.shape, (5, 10))
        self.assertEqual(self.study.numerical_wavefunctions_m_neg_half.shape, (1600, 10))
        with self.assertRaises(ValueError):
            self.study.energies_j[0] = 0.0

    def test_numerical_accuracy_convergence_and_overlap(self) -> None:
        self.assertLess(float(np.max(self.study.numerical_relative_errors[-1])), 4e-5)
        self.assertTrue(
            np.all(np.diff(self.study.numerical_relative_errors, axis=0) < 0.0)
        )
        self.assertGreater(float(np.min(self.study.numerical_convergence_orders)), 1.9)
        self.assertLess(float(np.max(self.study.numerical_convergence_orders)), 2.05)
        self.assertGreater(float(np.min(self.study.numerical_overlaps)), 0.999999)

    def test_numerical_solution_is_physically_normalized(self) -> None:
        solution = solve_numerical_box(
            400,
            6,
            DEFAULT_CONFIGURATION.particle_mass_kg,
            DEFAULT_CONFIGURATION.box_width_m,
        )
        dx = DEFAULT_CONFIGURATION.box_width_m / 401.0
        gram = solution.wavefunctions_m_neg_half.T @ solution.wavefunctions_m_neg_half * dx
        np.testing.assert_allclose(gram, np.eye(6), rtol=0.0, atol=2e-13)

    def test_rejects_invalid_numerical_requests(self) -> None:
        with self.assertRaises(TypeError):
            solve_numerical_box(True, 1, 1.0, 1.0)
        with self.assertRaises(ValueError):
            solve_numerical_box(3, 3, 1.0, 1.0)
        with self.assertRaises(ValueError):
            solve_numerical_box(20, 2, 0.0, 1.0)
        with self.assertRaises(ValueError):
            solve_numerical_box(20, 2, 1.0, -1.0)


if __name__ == "__main__":
    unittest.main()
