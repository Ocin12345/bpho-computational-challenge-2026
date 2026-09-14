from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from task07_particle_in_box.configuration import DEFAULT_CONFIGURATION
from task07_particle_in_box.models import (
    expected_momentum_squared_kg2_m2_s2,
    momentum_uncertainty_kg_m_s,
    uncertainty_product_over_hbar,
)
from task07_particle_in_box.momentum import (
    build_numerical_momentum_study,
    numerical_momentum_observables,
)
from task07_particle_in_box.analysis import solve_numerical_box


class NumericalMomentumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.configuration = DEFAULT_CONFIGURATION
        cls.study = build_numerical_momentum_study(cls.configuration)

    def test_operator_route_is_based_on_the_eigenvector(self) -> None:
        solution = solve_numerical_box(
            100,
            2,
            self.configuration.particle_mass_kg,
            self.configuration.box_width_m,
        )
        first = numerical_momentum_observables(solution, self.configuration.particle_mass_kg)
        perturbed = np.array(solution.wavefunctions_m_neg_half, copy=True)
        perturbed[0, 0] *= 0.91
        perturbed_solution = solution.__class__(
            interior_point_count=solution.interior_point_count,
            positions_m=solution.positions_m,
            energies_j=solution.energies_j,
            wavefunctions_m_neg_half=perturbed,
            overlaps=solution.overlaps,
        )
        changed = numerical_momentum_observables(
            perturbed_solution,
            self.configuration.particle_mass_kg,
        )
        self.assertNotAlmostEqual(first.delta_p_kg_m_s[0], changed.delta_p_kg_m_s[0], places=30)

    def test_discrete_position_and_momentum_moments_are_complete(self) -> None:
        solution = solve_numerical_box(
            1600,
            10,
            self.configuration.particle_mass_kg,
            self.configuration.box_width_m,
        )
        observables = numerical_momentum_observables(
            solution,
            self.configuration.particle_mass_kg,
        )
        self.assertEqual(observables.normalizations.shape, (10,))
        self.assertEqual(observables.expected_x_m.shape, (10,))
        self.assertEqual(observables.expected_x_squared_m2.shape, (10,))
        self.assertEqual(observables.p_mean_kg_m_s.shape, (10,))
        self.assertTrue(np.issubdtype(observables.p_mean_kg_m_s.dtype, np.complexfloating))
        np.testing.assert_allclose(observables.normalizations, 1.0, rtol=0.0, atol=2e-13)
        np.testing.assert_allclose(
            observables.expected_x_m,
            self.configuration.box_width_m / 2.0,
            rtol=0.0,
            atol=2e-22,
        )
        self.assertLess(float(np.max(np.abs(observables.p_mean_kg_m_s.imag))), 1e-38)

        index = 4
        self.assertAlmostEqual(
            float(observables.expected_x_squared_m2[index])
            / self.configuration.box_width_m**2,
            0.331306909659,
            delta=5e-13,
        )
        self.assertAlmostEqual(
            float(observables.p_squared_kg2_m2_s2[index]),
            2.744028339689e-48,
            delta=5e-60,
        )

    def test_numerical_operator_does_not_call_analytical_delta_p(self) -> None:
        solution = solve_numerical_box(
            100,
            2,
            self.configuration.particle_mass_kg,
            self.configuration.box_width_m,
        )
        with patch(
            "task07_particle_in_box.momentum.momentum_uncertainty_kg_m_s",
            side_effect=AssertionError("analytical delta-p path must not be used"),
        ):
            observables = numerical_momentum_observables(
                solution,
                self.configuration.particle_mass_kg,
            )
        self.assertTrue(np.all(observables.delta_p_kg_m_s > 0.0))

    def test_numerical_momentum_matches_analytical_reference(self) -> None:
        for n in (1, 2, 3, 5, 10):
            index = n - 1
            self.assertLess(float(self.study.relative_delta_p_errors[-1, index]), 2e-5)
            self.assertLess(float(self.study.relative_p_squared_errors[-1, index]), 4e-5)
            self.assertLess(float(self.study.relative_uncertainty_errors[-1, index]), 2e-5)
            p_mean = complex(self.study.p_mean_kg_m_s[-1, index])
            self.assertLess(abs(p_mean.real), 1e-38)
            self.assertLess(abs(p_mean.imag), 1e-38)
            self.assertGreaterEqual(
                float(self.study.uncertainty_products_over_hbar[-1, index]), 0.5
            )
            expected_p2 = expected_momentum_squared_kg2_m2_s2(
                np.asarray([n]), self.configuration.box_width_m
            )[0]
            self.assertLess(
                abs(float(self.study.p_squared_kg2_m2_s2[-1, index]) - expected_p2)
                / expected_p2,
                4e-5,
            )
            expected_dp = momentum_uncertainty_kg_m_s(
                np.asarray([n]), self.configuration.box_width_m
            )[0]
            self.assertLess(
                abs(float(self.study.delta_p_kg_m_s[-1, index]) - expected_dp) / expected_dp,
                2e-5,
            )
            self.assertAlmostEqual(
                float(self.study.uncertainty_products_over_hbar[-1, index]),
                float(uncertainty_product_over_hbar(np.asarray([n]))[0]),
                delta=2e-4,
            )

    def test_momentum_errors_refine_and_have_measured_order(self) -> None:
        self.assertTrue(np.all(np.diff(self.study.relative_delta_p_errors, axis=0) < 0.0))
        self.assertTrue(np.all(np.diff(self.study.relative_p_squared_errors, axis=0) < 0.0))
        self.assertGreater(float(np.min(self.study.delta_p_convergence_orders)), 1.9)
        self.assertLess(float(np.max(self.study.delta_p_convergence_orders)), 2.1)
        self.assertTrue(
            np.all(np.diff(self.study.relative_uncertainty_errors, axis=0) < 0.0)
        )
        self.assertGreater(
            float(np.min(self.study.uncertainty_product_convergence_orders)), 1.9
        )
        self.assertLess(
            float(np.max(self.study.uncertainty_product_convergence_orders)), 2.1
        )

    def test_all_finest_grid_states_obey_heisenberg(self) -> None:
        self.assertTrue(np.all(self.study.uncertainty_products_over_hbar[-1] >= 0.5))
        self.assertTrue(np.all(self.study.heisenberg_ratios[-1] >= 1.0))


if __name__ == "__main__":
    unittest.main()
