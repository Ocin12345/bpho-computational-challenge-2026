"""Tests for Task 4 constants, configuration, and source materials."""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from task04_photoelectric_effect.configuration import (
    DEFAULT_CONFIGURATION,
    Task04Configuration,
)
from task04_photoelectric_effect.constants import (
    ELECTRONVOLT_J,
    ELEMENTARY_CHARGE_C,
    HC_OVER_CHARGE_V_M,
    METRES_PER_NANOMETRE,
    NANOMETRES_PER_METRE,
    PLANCK_CONSTANT_J_S,
    PLANCK_OVER_CHARGE_V_S,
    SPEED_OF_LIGHT_M_S,
)
from task04_photoelectric_effect.materials import (
    OFFICIAL_MATERIALS,
    PhotoelectricMaterial,
    validate_material_collection,
)


class PhysicalConstantTests(unittest.TestCase):
    """Protect the exact SI definitions and their derived identities."""

    def test_exact_defining_constants(self) -> None:
        self.assertEqual(PLANCK_CONSTANT_J_S, 6.62607015e-34)
        self.assertEqual(ELEMENTARY_CHARGE_C, 1.602176634e-19)
        self.assertEqual(SPEED_OF_LIGHT_M_S, 299_792_458.0)
        self.assertEqual(ELECTRONVOLT_J, ELEMENTARY_CHARGE_C)

    def test_derived_constants_are_calculated_from_definitions(self) -> None:
        self.assertEqual(
            PLANCK_OVER_CHARGE_V_S,
            PLANCK_CONSTANT_J_S / ELEMENTARY_CHARGE_C,
        )
        self.assertEqual(
            HC_OVER_CHARGE_V_M,
            PLANCK_CONSTANT_J_S
            * SPEED_OF_LIGHT_M_S
            / ELEMENTARY_CHARGE_C,
        )
        self.assertEqual(METRES_PER_NANOMETRE, 1.0e-9)
        self.assertEqual(NANOMETRES_PER_METRE, 1.0e9)
        self.assertEqual(
            METRES_PER_NANOMETRE * NANOMETRES_PER_METRE,
            1.0,
        )

    def test_derived_values_match_the_frozen_specification(self) -> None:
        self.assertAlmostEqual(
            PLANCK_OVER_CHARGE_V_S,
            4.1356676969238586e-15,
            places=29,
        )
        self.assertAlmostEqual(
            HC_OVER_CHARGE_V_M,
            1.2398419843320026e-6,
            places=20,
        )


class ConfigurationTests(unittest.TestCase):
    """Protect the frozen Stage 2 grids, tolerances, and budgets."""

    def test_default_configuration_matches_the_specification(self) -> None:
        configuration = DEFAULT_CONFIGURATION
        self.assertEqual(configuration.schema_version, "task04-v1")
        self.assertEqual(configuration.frequency_start_hz, 4.0e14)
        self.assertEqual(configuration.frequency_step_hz, 1.0e12)
        self.assertEqual(configuration.frequency_points, 2001)
        self.assertEqual(configuration.frequency_stop_hz, 2.4e15)
        self.assertEqual(configuration.wavelength_start_nm, 150.0)
        self.assertEqual(configuration.wavelength_step_nm, 0.25)
        self.assertEqual(configuration.wavelength_points, 2201)
        self.assertEqual(configuration.wavelength_stop_nm, 700.0)
        self.assertEqual(
            (configuration.visible_min_nm, configuration.visible_max_nm),
            (380.0, 750.0),
        )
        self.assertEqual(configuration.boundary_clamp_tolerance_v, 5.0e-12)
        self.assertEqual(configuration.energy_identity_tolerance_ev, 5.0e-12)
        self.assertEqual(configuration.gradient_relative_tolerance, 5.0e-13)
        self.assertEqual(configuration.cutoff_relative_tolerance, 5.0e-13)
        self.assertEqual(
            configuration.coordinate_consistency_tolerance_v,
            1.0e-11,
        )
        self.assertEqual(configuration.evidence_size_budget_bytes, 10_485_760)
        self.assertEqual(configuration.figure_size_budget_bytes, 10_485_760)

    def test_configuration_is_frozen(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIGURATION.frequency_points = 3  # type: ignore[misc]

    def test_configuration_rejects_invalid_schema(self) -> None:
        with self.assertRaises(TypeError):
            Task04Configuration(schema_version=1)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Task04Configuration(schema_version="task04-v2")

    def test_configuration_rejects_invalid_numeric_values(self) -> None:
        for field_name, value, expected_error in (
            ("frequency_start_hz", True, TypeError),
            ("frequency_step_hz", 0.0, ValueError),
            ("wavelength_start_nm", math.nan, ValueError),
            ("visible_min_nm", math.inf, ValueError),
            ("gradient_relative_tolerance", -1.0, ValueError),
            ("study_runtime_budget_s", 0.0, ValueError),
        ):
            with self.subTest(field=field_name):
                with self.assertRaises(expected_error):
                    Task04Configuration(**{field_name: value})

    def test_configuration_rejects_invalid_counts_and_budgets(self) -> None:
        for field_name, value, expected_error in (
            ("frequency_points", True, TypeError),
            ("frequency_points", 1, ValueError),
            ("wavelength_points", 2.5, TypeError),
            ("evidence_size_budget_bytes", 0, ValueError),
            ("figure_size_budget_bytes", 1.5, TypeError),
        ):
            with self.subTest(field=field_name):
                with self.assertRaises(expected_error):
                    Task04Configuration(**{field_name: value})

    def test_configuration_rejects_reversed_visible_band(self) -> None:
        with self.assertRaises(ValueError):
            Task04Configuration(visible_min_nm=750.0, visible_max_nm=380.0)

    def test_configuration_rejects_grid_endpoint_drift(self) -> None:
        with self.assertRaises(ValueError):
            Task04Configuration(frequency_points=2000)
        with self.assertRaises(ValueError):
            Task04Configuration(wavelength_step_nm=0.5)


class MaterialTests(unittest.TestCase):
    """Protect the exact official source table and record contracts."""

    def test_official_material_table_is_exact_and_ordered(self) -> None:
        observed = tuple(
            (item.name, item.symbol, item.work_function_ev)
            for item in OFFICIAL_MATERIALS
        )
        expected = (
            ("Silver", "Ag", 4.3),
            ("Aluminium", "Al", 4.3),
            ("Gold", "Au", 5.1),
            ("Copper", "Cu", 4.7),
            ("Tin", "Sn", 4.4),
            ("Lead", "Pb", 4.3),
            ("Tungsten", "W", 4.5),
            ("Nickel", "Ni", 4.6),
            ("Sodium", "Na", 2.4),
        )
        self.assertEqual(observed, expected)

    def test_material_record_is_frozen(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            OFFICIAL_MATERIALS[0].work_function_ev = 1.0  # type: ignore[misc]

    def test_material_rejects_invalid_identity(self) -> None:
        with self.assertRaises(TypeError):
            PhotoelectricMaterial(1, "X", 4.0)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            PhotoelectricMaterial(" ", "X", 4.0)
        with self.assertRaises(TypeError):
            PhotoelectricMaterial("Test", 1, 4.0)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            PhotoelectricMaterial("Test", " ", 4.0)

    def test_material_rejects_invalid_work_function(self) -> None:
        for value, expected_error in (
            (True, TypeError),
            ("4.3", TypeError),
            (0.0, ValueError),
            (-1.0, ValueError),
            (math.nan, ValueError),
            (math.inf, ValueError),
        ):
            with self.subTest(value=value):
                with self.assertRaises(expected_error):
                    PhotoelectricMaterial("Test", "X", value)  # type: ignore[arg-type]

    def test_collection_validation_preserves_identity_and_order(self) -> None:
        result = validate_material_collection(iter(OFFICIAL_MATERIALS))
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, OFFICIAL_MATERIALS)
        self.assertIs(result[0], OFFICIAL_MATERIALS[0])

    def test_collection_validation_rejects_empty_or_wrong_records(self) -> None:
        with self.assertRaises(ValueError):
            validate_material_collection(())
        with self.assertRaises(TypeError):
            validate_material_collection(5)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            validate_material_collection((OFFICIAL_MATERIALS[0], "not a record"))  # type: ignore[arg-type]

    def test_collection_validation_rejects_duplicate_symbols(self) -> None:
        duplicate = PhotoelectricMaterial("Other silver", "Ag", 3.0)
        with self.assertRaises(ValueError):
            validate_material_collection((OFFICIAL_MATERIALS[0], duplicate))

    def test_package_import_has_no_filesystem_or_matplotlib_side_effect(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = (
                "import pathlib, sys\n"
                f"sys.path.insert(0, {str(repository_root)!r})\n"
                "before = set(pathlib.Path('.').iterdir())\n"
                "import task04_photoelectric_effect\n"
                "after = set(pathlib.Path('.').iterdir())\n"
                "assert before == after\n"
                "assert 'matplotlib' not in sys.modules\n"
            )
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=temporary_directory,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
