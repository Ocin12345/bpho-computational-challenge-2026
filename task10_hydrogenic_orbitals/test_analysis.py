"""Tests for Task 10 state inventories, nodes and radial extents."""

from __future__ import annotations

import unittest

import numpy as np

from task10_hydrogenic_orbitals.analysis import (
    associated_laguerre_coefficients,
    build_radial_profile,
    distinct_radial_states,
    official_family_representatives,
    radial_containment_radius_over_a,
    radial_node_positions_over_a,
    radial_probability_cdf,
    supported_states,
)
from task10_hydrogenic_orbitals.configuration import HydrogenicState


class AnalysisTests(unittest.TestCase):
    def test_state_inventories_are_complete(self) -> None:
        self.assertEqual(len(supported_states()), 204)
        self.assertEqual(len(set(supported_states())), 204)
        self.assertEqual(len(distinct_radial_states()), 36)
        self.assertEqual(
            official_family_representatives(),
            tuple(HydrogenicState(l + 1, l, 0) for l in range(5)),
        )

    def test_node_counts_and_exact_two_s_node(self) -> None:
        total_nodes = 0
        for state in distinct_radial_states():
            nodes = radial_node_positions_over_a(state)
            self.assertEqual(len(nodes), state.radial_node_count)
            self.assertTrue(np.all(nodes > 0.0))
            self.assertTrue(np.all(np.diff(nodes) > 0.0))
            self.assertFalse(nodes.flags.writeable)
            total_nodes += len(nodes)
        self.assertEqual(total_nodes, 84)
        np.testing.assert_allclose(
            radial_node_positions_over_a(HydrogenicState(2, 0, 0)),
            [2.0],
            rtol=0.0,
            atol=2e-15,
        )

    def test_containment_radius_reaches_declared_probability(self) -> None:
        for state in official_family_representatives():
            radius = radial_containment_radius_over_a(state)
            self.assertGreater(radius, 0.0)
            self.assertAlmostEqual(
                radial_probability_cdf(state, radius),
                0.9995,
                delta=2e-13,
            )

    def test_radial_profiles_are_complete_and_immutable(self) -> None:
        for state in official_family_representatives():
            profile = build_radial_profile(state)
            self.assertEqual(len(profile.radius_over_a), 1201)
            self.assertEqual(profile.radius_over_a[0], 0.0)
            self.assertAlmostEqual(
                profile.radius_over_a[-1], profile.extent_over_a, 14
            )
            self.assertAlmostEqual(
                profile.cumulative_probability[-1],
                0.9995,
                delta=8e-9,
            )
            for array in (
                profile.radius_over_a,
                profile.radius_over_n_squared_a,
                profile.scaled_radial_wavefunction,
                profile.scaled_radial_probability,
                profile.cumulative_probability,
            ):
                self.assertFalse(array.flags.writeable)

    def test_invalid_analysis_inputs_are_rejected(self) -> None:
        state = HydrogenicState(1, 0, 0)
        calls = (
            lambda: associated_laguerre_coefficients(-1, 1),
            lambda: associated_laguerre_coefficients(1, -1),
            lambda: radial_probability_cdf(state, -1.0),
            lambda: radial_containment_radius_over_a(state, 0.9),
            lambda: build_radial_profile(state, points=500),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


if __name__ == "__main__":
    unittest.main()
