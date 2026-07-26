from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

import numpy as np

from task06_electron_diffraction.configuration import (
    DEFAULT_CONFIGURATION,
    SpacingDefinition,
    Task06Configuration,
)
from task06_electron_diffraction.constants import (
    ELECTRON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
)
from task06_electron_diffraction.orders import (
    enumerate_order_indices,
    order_status_labels,
)


class ConstantAndConfigurationTests(unittest.TestCase):
    def test_frozen_source_constants(self) -> None:
        self.assertEqual(PLANCK_CONSTANT_J_S, float("6.62607015e-34"))
        self.assertEqual(ELEMENTARY_CHARGE_C, float("1.602176634e-19"))
        self.assertEqual(ELECTRON_MASS_KG, float("9.1093837139e-31"))

    def test_default_configuration_is_complete_and_frozen(self) -> None:
        self.assertEqual(DEFAULT_CONFIGURATION.voltage_count, 401)
        self.assertEqual(DEFAULT_CONFIGURATION.spacing_count, 2)
        self.assertEqual(DEFAULT_CONFIGURATION.tube_radius_m, 0.065)
        np.testing.assert_allclose(
            [spacing.spacing_nm for spacing in DEFAULT_CONFIGURATION.spacings],
            [0.123, 0.213],
            rtol=0.0,
            atol=1e-15,
        )
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIGURATION.voltage_step_v = 20.0  # type: ignore[misc]

    def test_spacing_definition_rejects_invalid_values(self) -> None:
        invalid = (
            {"identifier": "", "label": "d", "spacing_m": 1e-10},
            {"identifier": "d-1", "label": "d", "spacing_m": 1e-10},
            {"identifier": "d1", "label": "", "spacing_m": 1e-10},
            {"identifier": "d1", "label": "d", "spacing_m": 0.0},
            {"identifier": "d1", "label": "d", "spacing_m": True},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                SpacingDefinition(**kwargs)

    def test_configuration_rejects_invalid_values(self) -> None:
        duplicate = (
            SpacingDefinition("d1", "one", 1e-10),
            SpacingDefinition("d1", "two", 2e-10),
        )
        unsorted = (
            SpacingDefinition("d1", "one", 2e-10),
            SpacingDefinition("d2", "two", 1e-10),
        )
        invalid = (
            {"voltage_min_v": True},
            {"voltage_min_v": 5000.0, "voltage_max_v": 1000.0},
            {"voltage_step_v": 33.0},
            {"tube_radius_m": 0.0},
            {"spacings": duplicate},
            {"spacings": unsorted},
            {"fit_relative_tolerance": -1.0},
            {"figure_dpi": 0},
            {"evidence_size_budget_bytes": 0},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                Task06Configuration(**kwargs)

    def test_order_enumeration_is_complete_and_ordered(self) -> None:
        voltage_index, spacing_index, order = enumerate_order_indices(
            np.asarray([[2, 3], [1, 2]], dtype=np.int64)
        )
        rows = list(zip(voltage_index.tolist(), spacing_index.tolist(), order.tolist()))
        self.assertEqual(
            rows,
            [
                (0, 0, 1),
                (0, 0, 2),
                (0, 1, 1),
                (0, 1, 2),
                (0, 1, 3),
                (1, 0, 1),
                (1, 1, 1),
                (1, 1, 2),
            ],
        )

    def test_order_helpers_reject_invalid_inputs(self) -> None:
        with self.assertRaises(TypeError):
            enumerate_order_indices([[2.0]])
        with self.assertRaises(ValueError):
            enumerate_order_indices([2, 3])
        with self.assertRaises(ValueError):
            enumerate_order_indices([[0]])
        with self.assertRaises(TypeError):
            order_status_labels([1, 0])
        self.assertEqual(
            order_status_labels(np.asarray([True, False], dtype=np.bool_)),
            ("forward_screen", "back_scattering"),
        )


if __name__ == "__main__":
    unittest.main()
