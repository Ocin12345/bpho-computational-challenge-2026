from __future__ import annotations

import time
import unittest
from dataclasses import FrozenInstanceError, replace

import numpy as np

from task05_hydrogen_spectrum.analysis import Task05StudyResult, build_task05_study
from task05_hydrogen_spectrum.configuration import DEFAULT_CONFIGURATION
from task05_hydrogen_spectrum.models import transition_energy_ev


class Task05StudyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.study = build_task05_study()

    def test_complete_shapes_counts_and_dtypes(self) -> None:
        self.assertEqual(self.study.levels_n.shape, (10,))
        self.assertEqual(self.study.initial_n.shape, (45,))
        self.assertEqual(self.study.series_limit_final_n.shape, (5,))
        self.assertEqual(self.study.levels_n.dtype, np.int64)
        self.assertEqual(self.study.photon_energy_ev.dtype, np.float64)
        self.assertEqual(len(self.study.series_names), 45)
        self.assertEqual(len(self.study.line_names), 45)

    def test_complete_transition_order(self) -> None:
        self.assertEqual(
            tuple(zip(self.study.initial_n[:3], self.study.final_n[:3])),
            ((2, 1), (3, 1), (4, 1)),
        )
        self.assertEqual(
            tuple(zip(self.study.initial_n[-3:], self.study.final_n[-3:])),
            ((9, 8), (10, 8), (10, 9)),
        )

    def test_stored_outputs_equal_public_models(self) -> None:
        np.testing.assert_array_equal(
            self.study.photon_energy_ev,
            transition_energy_ev(self.study.initial_n, self.study.final_n),
        )

    def test_labels_and_region_counts(self) -> None:
        self.assertEqual(self.study.series_names.count("Lyman"), 9)
        self.assertEqual(self.study.series_names.count("Balmer"), 8)
        self.assertEqual(self.study.display_groups.count("Higher series (n_f>=6)"), 10)
        self.assertEqual(self.study.spectral_regions.count("visible"), 7)
        self.assertEqual(self.study.spectral_regions.count("ultraviolet"), 10)
        self.assertEqual(self.study.spectral_regions.count("infrared"), 28)

    def test_arrays_are_read_only_and_dataclass_is_frozen(self) -> None:
        arrays = (
            self.study.levels_n,
            self.study.level_energy_ev,
            self.study.initial_n,
            self.study.photon_energy_ev,
            self.study.wavelength_nm,
            self.study.series_limit_wavelength_nm,
        )
        self.assertTrue(all(not array.flags.writeable for array in arrays))
        with self.assertRaises(ValueError):
            self.study.photon_energy_ev[0] = 0.0
        with self.assertRaises(FrozenInstanceError):
            self.study.series_names = ()  # type: ignore[misc]

    def test_constructor_makes_defensive_copies(self) -> None:
        source = np.array(self.study.photon_energy_ev, copy=True)
        rebuilt = replace(self.study, photon_energy_ev=source)
        source[0] = 1.0
        self.assertNotEqual(float(rebuilt.photon_energy_ev[0]), 1.0)

    def test_structurally_valid_scientific_corruption_is_preserved(self) -> None:
        corrupted = np.array(self.study.photon_energy_ev, copy=True)
        corrupted[0] += 0.1
        rebuilt = replace(self.study, photon_energy_ev=corrupted)
        self.assertAlmostEqual(
            float(rebuilt.photon_energy_ev[0]),
            float(self.study.photon_energy_ev[0] + 0.1),
        )

    def test_constructor_rejects_pair_or_shape_corruption(self) -> None:
        duplicate = np.array(self.study.initial_n, copy=True)
        duplicate[0] = duplicate[1]
        with self.assertRaises(ValueError):
            replace(self.study, initial_n=duplicate)
        with self.assertRaises(ValueError):
            replace(self.study, wavelength_nm=self.study.wavelength_nm[:-1])

    def test_repeated_studies_are_exactly_reproducible(self) -> None:
        other = build_task05_study()
        for field_name in (
            "levels_n",
            "level_energy_ev",
            "initial_n",
            "final_n",
            "photon_energy_ev",
            "frequency_hz",
            "wavelength_nm",
        ):
            np.testing.assert_array_equal(
                getattr(self.study, field_name),
                getattr(other, field_name),
            )
        self.assertEqual(self.study.series_names, other.series_names)

    def test_builder_runtime_is_below_budget(self) -> None:
        started = time.perf_counter()
        build_task05_study()
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, DEFAULT_CONFIGURATION.study_runtime_budget_s)

    def test_builder_rejects_wrong_configuration_type(self) -> None:
        with self.assertRaises(TypeError):
            build_task05_study(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
