"""Tests for graphite structure factors and finite-width diffraction rings."""

from __future__ import annotations

import unittest

import numpy as np

from task06_electron_diffraction.intensity_extension import (
    graphite_spacing_m,
    graphite_structure_factor,
    powder_profile,
    powder_ring,
    scherrer_fwhm_rad,
)


class ElectronDiffractionIntensityExtensionTests(unittest.TestCase):
    def test_graphite_100_and_110_spacings_match_official_rings(self) -> None:
        self.assertAlmostEqual(graphite_spacing_m(1, 0, 0) * 1.0e9, 0.213, places=3)
        self.assertAlmostEqual(graphite_spacing_m(1, 1, 0) * 1.0e9, 0.123, places=3)

    def test_ab_stacking_extinguishes_odd_00l(self) -> None:
        self.assertLess(abs(graphite_structure_factor(0, 0, 1)), 1.0e-12)
        self.assertAlmostEqual(abs(graphite_structure_factor(0, 0, 2)), 4.0, places=12)

    def test_structure_factor_changes_ring_strength(self) -> None:
        ring_100 = powder_ring(4000.0, 1, 0, 0)
        ring_110 = powder_ring(4000.0, 1, 1, 0)
        self.assertGreater(ring_110.structure_factor_squared, ring_100.structure_factor_squared)
        self.assertGreater(ring_100.radial_fwhm_mm, 0.0)
        self.assertGreater(ring_110.relative_integrated_intensity, 0.0)

    def test_scherrer_width_is_inverse_in_crystallite_size(self) -> None:
        small = scherrer_fwhm_rad(2.0e-11, 0.1, 10.0e-9)
        large = scherrer_fwhm_rad(2.0e-11, 0.1, 40.0e-9)
        self.assertAlmostEqual(small / large, 4.0, places=12)

    def test_profile_is_normalized_and_peaks_near_a_ring(self) -> None:
        rings = (
            powder_ring(4000.0, 1, 0, 0),
            powder_ring(4000.0, 1, 1, 0),
        )
        maximum = max(ring.radius_mm + 5.0 * ring.radial_fwhm_mm for ring in rings)
        radius = np.linspace(0.0, maximum, 6000)
        profile = powder_profile(radius, rings)
        self.assertAlmostEqual(float(np.trapezoid(profile, radius)), 1.0, places=6)
        peak = float(radius[int(np.argmax(profile))])
        self.assertLess(min(abs(peak - ring.radius_mm) for ring in rings), 0.03)

    def test_invalid_origin_reflection_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            graphite_spacing_m(0, 0, 0)


if __name__ == "__main__":
    unittest.main()
