"""Independent-reference comparisons for Task 10."""

from __future__ import annotations

import unittest

import numpy as np

from task10_hydrogenic_orbitals.configuration import (
    HydrogenicState,
    official_gallery_states,
)
from task10_hydrogenic_orbitals.models import (
    associated_ferrers,
    associated_laguerre,
    real_spherical_harmonic,
    scaled_radial_wavefunction,
    scaled_wavefunction_cartesian,
)
from task10_hydrogenic_orbitals.reference import (
    reference_associated_ferrers,
    reference_associated_laguerre,
    reference_real_spherical_harmonic,
    reference_scaled_radial_wavefunction,
    reference_scaled_wavefunction_cartesian,
)


class IndependentReferenceTests(unittest.TestCase):
    def test_laguerre_recurrence_matches_official_factorial_sum(self) -> None:
        sample_points = (0.0, 0.17, 1.3, 5.9, 17.0)
        for order in range(8):
            for alpha in range(1, 16, 2):
                for x in sample_points:
                    with self.subTest(order=order, alpha=alpha, x=x):
                        self.assertAlmostEqual(
                            associated_laguerre(order, alpha, x),
                            reference_associated_laguerre(order, alpha, x),
                            delta=5e-12 * max(1.0, abs(reference_associated_laguerre(order, alpha, x))),
                        )

    def test_ferrers_recurrence_matches_explicit_derivative(self) -> None:
        sample_points = (-1.0, -0.73, -0.11, 0.0, 0.38, 0.91, 1.0)
        for l in range(8):
            for m in range(l + 1):
                for x in sample_points:
                    expected = reference_associated_ferrers(l, m, x)
                    with self.subTest(l=l, m=m, x=x):
                        self.assertAlmostEqual(
                            associated_ferrers(l, m, x),
                            expected,
                            delta=5e-13 * max(1.0, abs(expected)),
                        )

    def test_all_real_harmonics_match_independent_reference(self) -> None:
        angles = (
            (0.17, -2.4),
            (0.83, -0.37),
            (1.41, 0.26),
            (2.37, 1.73),
            (2.91, 5.21),
        )
        for l in range(8):
            for m in range(-l, l + 1):
                for polar, azimuth in angles:
                    expected = reference_real_spherical_harmonic(
                        l, m, polar, azimuth
                    )
                    with self.subTest(l=l, m=m, polar=polar, azimuth=azimuth):
                        self.assertAlmostEqual(
                            real_spherical_harmonic(l, m, polar, azimuth),
                            expected,
                            delta=5e-13 * max(1.0, abs(expected)),
                        )

    def test_all_official_gallery_states_match_scalar_reference(self) -> None:
        points = (
            (0.0, 0.0, 0.0),
            (0.17, -0.31, 0.47),
            (0.73, 1.19, -0.28),
            (-1.31, 0.83, 2.17),
            (3.7, -2.9, 1.6),
        )
        for state in official_gallery_states():
            for point in points:
                expected = reference_scaled_wavefunction_cartesian(state, *point)
                with self.subTest(state=state, point=point):
                    self.assertAlmostEqual(
                        scaled_wavefunction_cartesian(state, *point),
                        expected,
                        delta=5e-13 * max(1.0, abs(expected)),
                    )

    def test_full_supported_radial_domain_matches_reference(self) -> None:
        radii = (0.0, 0.03, 0.7, 3.1, 11.0, 37.0, 95.0)
        for n in range(1, 9):
            for l in range(n):
                state = HydrogenicState(n, l, 0)
                for radius in radii:
                    expected = reference_scaled_radial_wavefunction(state, radius)
                    with self.subTest(n=n, l=l, radius=radius):
                        self.assertAlmostEqual(
                            scaled_radial_wavefunction(state, radius),
                            expected,
                            delta=5e-12 * max(1.0, abs(expected)),
                        )

    def test_reference_rejects_invalid_scalars(self) -> None:
        state = HydrogenicState(1, 0, 0)
        calls = (
            lambda: reference_associated_laguerre(-1, 0, 0.0),
            lambda: reference_associated_laguerre(1, 0, float("inf")),
            lambda: reference_associated_ferrers(1, 2, 0.0),
            lambda: reference_associated_ferrers(1, 0, 1.1),
            lambda: reference_real_spherical_harmonic(1, 2, 0.1, 0.2),
            lambda: reference_real_spherical_harmonic(1, 0, -0.1, 0.2),
            lambda: reference_scaled_radial_wavefunction(state, -1.0),
            lambda: reference_scaled_wavefunction_cartesian(
                state, float("nan"), 0.0, 0.0
            ),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


if __name__ == "__main__":
    unittest.main()
