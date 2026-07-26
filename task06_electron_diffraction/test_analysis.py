from __future__ import annotations

import unittest

import numpy as np

from task06_electron_diffraction.analysis import build_task06_study


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task06_study()

    def test_complete_study_shapes_and_counts(self) -> None:
        study = self.study
        self.assertEqual(study.voltages_v.shape, (401,))
        self.assertEqual(study.spacings_m.shape, (2,))
        self.assertEqual(study.maximum_bragg_orders.shape, (401, 2))
        self.assertEqual(study.catalogue_size, 11386)
        self.assertEqual(study.forward_screen_count, 7927)
        self.assertEqual(len(study.first_order_fits), 2)
        self.assertEqual(len(study.normalized_fits), 2)

    def test_catalogue_is_ordered_and_complete_at_first_voltage(self) -> None:
        study = self.study
        first_voltage = study.voltage_indices == 0
        rows = list(
            zip(
                study.spacing_indices[first_voltage].tolist(),
                study.orders_n[first_voltage].tolist(),
            )
        )
        self.assertEqual(rows[:6], [(0, order) for order in range(1, 7)])
        self.assertEqual(rows[6:], [(1, order) for order in range(1, 11)])

    def test_endpoint_maximum_orders(self) -> None:
        np.testing.assert_array_equal(self.study.maximum_bragg_orders[0], [6, 10])
        np.testing.assert_array_equal(self.study.maximum_bragg_orders[-1], [14, 24])
        np.testing.assert_array_equal(self.study.maximum_screen_orders[0], [4, 7])
        np.testing.assert_array_equal(self.study.maximum_screen_orders[-1], [10, 17])

    def test_first_order_fit_results_recover_both_spacings(self) -> None:
        expected = (0.123e-9, 0.213e-9)
        expected_gradients = (0.20058283741173638, 0.347350767225202)
        for fit, spacing, gradient in zip(self.study.first_order_fits, expected, expected_gradients):
            self.assertAlmostEqual(fit.recovered_spacing_m, spacing, places=22)
            self.assertAlmostEqual(fit.constrained_gradient_v_inv_sqrt, gradient, places=14)
            self.assertGreaterEqual(fit.r_squared, 1.0 - 1e-14)
            self.assertLess(abs(fit.unconstrained_intercept_v_inv_sqrt), 1e-15)

    def test_normalized_fits_use_all_family_records(self) -> None:
        self.assertEqual(self.study.normalized_fits[0].point_count, 4113)
        self.assertEqual(self.study.normalized_fits[1].point_count, 7273)
        for primary, normalized in zip(self.study.first_order_fits, self.study.normalized_fits):
            self.assertAlmostEqual(
                primary.constrained_gradient_v_inv_sqrt,
                normalized.constrained_gradient_v_inv_sqrt,
                places=14,
            )

    def test_first_order_radius_anchors(self) -> None:
        anchors = {
            (0, 0): 38.465414872,
            (0, 1): 23.181331826,
            (400, 0): 18.103939862,
            (400, 1): 10.541869105,
        }
        for (voltage_index, spacing_index), radius_mm in anchors.items():
            mask = (
                (self.study.voltage_indices == voltage_index)
                & (self.study.spacing_indices == spacing_index)
                & (self.study.orders_n == 1)
            )
            self.assertEqual(np.count_nonzero(mask), 1)
            self.assertAlmostEqual(float(self.study.photo_radii_m[mask][0]) * 1e3, radius_mm, places=8)

    def test_arrays_are_defensively_read_only(self) -> None:
        arrays = (
            self.study.voltages_v,
            self.study.wavelengths_m,
            self.study.maximum_bragg_orders,
            self.study.orders_n,
            self.study.photo_radii_m,
            self.study.screen_visible_flags,
        )
        for array in arrays:
            self.assertFalse(array.flags.writeable)
            with self.assertRaises(ValueError):
                array.flat[0] = array.flat[0]


if __name__ == "__main__":
    unittest.main()
