"""Tests for validated, deterministic Task 3 figure generation."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest import mock

from PIL import Image
from matplotlib import pyplot as plt

from task03_thermal_radiation.analysis import (
    build_einstein_study,
    build_planck_study,
)
from task03_thermal_radiation.generate_task03 import (
    DATA_FILENAMES,
    FIGURE_FILENAMES,
    main,
)
from task03_thermal_radiation.plotting import (
    MATERIAL_COLOURS,
    PLANCK_COLOURS,
    create_einstein_heat_capacity_figure,
    create_einstein_normalized_figure,
    create_planck_spectra_figure,
    create_planck_validation_figure,
    create_task03_summary_figure,
    write_task03_figures,
)


EXPECTED_PNG_DIMENSIONS = {
    "planck_spectra.png": (1512, 936),
    "planck_validation.png": (1872, 936),
    "einstein_heat_capacity.png": (1512, 936),
    "einstein_normalized.png": (1872, 936),
    "task03_summary.png": (2400, 1350),
}


class Task03PlottingTests(unittest.TestCase):
    """Protect figure content, formats, validation, and transactions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.planck_result = build_planck_study()
        cls.einstein_result = build_einstein_study()

    def tearDown(self) -> None:
        plt.close("all")

    def test_public_figures_have_frozen_dimensions_and_structure(self) -> None:
        specifications = (
            (
                create_planck_spectra_figure,
                (8.4, 5.2),
                1,
                "Planck black-body spectra",
            ),
            (
                create_planck_validation_figure,
                (10.4, 5.2),
                2,
                "Wien displacement law",
            ),
            (
                create_einstein_heat_capacity_figure,
                (8.4, 5.2),
                1,
                "Einstein heat-capacity model",
            ),
            (
                create_einstein_normalized_figure,
                (10.4, 5.2),
                2,
                "Universal Einstein curve",
            ),
            (
                create_task03_summary_figure,
                (2400 / 180, 1350 / 180),
                4,
                "Planck black-body spectra",
            ),
        )

        for factory, expected_size, axis_count, expected_title in specifications:
            with self.subTest(factory=factory.__name__):
                figure = factory(self.planck_result, self.einstein_result)
                self.assertEqual(len(figure.axes), axis_count)
                self.assertAlmostEqual(figure.get_figwidth(), expected_size[0])
                self.assertAlmostEqual(figure.get_figheight(), expected_size[1])
                self.assertIn(
                    expected_title,
                    [axis.get_title() for axis in figure.axes],
                )
                plt.close(figure)

    def test_principal_figures_contain_required_scientific_elements(self) -> None:
        planck = create_planck_spectra_figure(
            self.planck_result,
            self.einstein_result,
        )
        self.assertEqual(len(planck.axes[0].lines), 3)
        self.assertEqual(len(planck.axes[0].collections), 3)
        self.assertEqual(
            planck.axes[0].get_ylabel(),
            "Spectral exitance (W m$^{-2}$ nm$^{-1}$)",
        )

        einstein = create_einstein_heat_capacity_figure(
            self.planck_result,
            self.einstein_result,
        )
        self.assertEqual(len(einstein.axes[0].lines), 8)
        legend_labels = [text.get_text() for text in einstein.axes[0].legend_.texts]
        self.assertTrue(any("Dulong" in label for label in legend_labels))
        self.assertEqual(
            einstein.axes[0].get_ylabel(),
            "Molar heat capacity (J mol$^{-1}$ K$^{-1}$)",
        )

        normalized = create_einstein_normalized_figure(
            self.planck_result,
            self.einstein_result,
        )
        self.assertEqual(len(normalized.axes[0].lines), 7)
        self.assertEqual(normalized.axes[1].get_yscale(), "log")

    def test_colour_contract_is_distinct_and_complete(self) -> None:
        self.assertEqual(len(PLANCK_COLOURS), 3)
        self.assertEqual(len(set(PLANCK_COLOURS)), 3)
        self.assertEqual(len(MATERIAL_COLOURS), 7)
        self.assertEqual(len(set(MATERIAL_COLOURS)), 7)

    def test_writer_creates_ordered_compact_png_and_svg_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "figures"
            result = write_task03_figures(
                self.planck_result,
                self.einstein_result,
                output_directory,
            )

            self.assertTrue(result.report.passed)
            self.assertEqual(
                tuple(path.name for path in result.output_paths),
                FIGURE_FILENAMES,
            )
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )
            self.assertLess(
                sum(path.stat().st_size for path in result.output_paths),
                15 * 1024 * 1024,
            )

            for filename, dimensions in EXPECTED_PNG_DIMENSIONS.items():
                path = output_directory / filename
                self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
                with Image.open(path) as image:
                    self.assertEqual(image.size, dimensions)
                    image.verify()

            for filename in FIGURE_FILENAMES[1::2]:
                text = (output_directory / filename).read_text(encoding="utf-8")
                self.assertIn("<svg", text)
                self.assertIn("viewBox=", text)
                self.assertNotIn("<dc:date>", text)
                self.assertTrue(text.endswith("\n"))
                self.assertTrue(
                    all(line == line.rstrip() for line in text.splitlines())
                )

    def test_outputs_are_byte_identical_across_repeated_local_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first_directory = root / "first"
            second_directory = root / "second"
            write_task03_figures(
                self.planck_result,
                self.einstein_result,
                first_directory,
            )
            write_task03_figures(
                self.planck_result,
                self.einstein_result,
                second_directory,
            )

            for filename in FIGURE_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (first_directory / filename).read_bytes(),
                        (second_directory / filename).read_bytes(),
                    )

    def test_failed_validation_does_not_create_output_directory(self) -> None:
        incorrect_planck = replace(
            self.planck_result,
            numerical_peak_wavelength_m=(
                self.planck_result.numerical_peak_wavelength_m * 1.1
            ),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "figures"
            with self.assertRaisesRegex(RuntimeError, "validation failed"):
                write_task03_figures(
                    incorrect_planck,
                    self.einstein_result,
                    output_directory,
                )
            self.assertFalse(output_directory.exists())

    def test_writer_failure_preserves_every_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            for filename in FIGURE_FILENAMES:
                (output_directory / filename).write_bytes(
                    f"old {filename}\n".encode("utf-8")
                )

            with mock.patch(
                "task03_thermal_radiation.plotting._save_figure",
                side_effect=RuntimeError("injected figure writer failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    write_task03_figures(
                        self.planck_result,
                        self.einstein_result,
                        output_directory,
                    )

            for filename in FIGURE_FILENAMES:
                self.assertEqual(
                    (output_directory / filename).read_bytes(),
                    f"old {filename}\n".encode("utf-8"),
                )
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )

    def test_file_output_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "not-a-directory"
            output_path.write_text("existing\n", encoding="utf-8")
            with self.assertRaises(NotADirectoryError):
                write_task03_figures(
                    self.planck_result,
                    self.einstein_result,
                    output_path,
                )
            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing\n")

    def test_complete_cli_writes_data_and_figures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_directory = root / "data"
            figure_directory = root / "figures"
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--data-dir",
                        str(data_directory),
                        "--figure-dir",
                        str(figure_directory),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Task 3 Stage 9", output.getvalue())
            self.assertIn("Validation checks: 27", output.getvalue())
            self.assertIn("Task 3 complete generation: PASS", output.getvalue())
            self.assertEqual(
                tuple(sorted(path.name for path in data_directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )
            self.assertEqual(
                tuple(sorted(path.name for path in figure_directory.iterdir())),
                tuple(sorted(FIGURE_FILENAMES)),
            )

    def test_committed_figures_match_fresh_regeneration(self) -> None:
        repository_root = Path(__file__).resolve().parent.parent
        committed_directory = repository_root / "figures" / "task03"
        self.assertTrue(committed_directory.is_dir())

        with tempfile.TemporaryDirectory() as temporary_directory:
            generated_directory = Path(temporary_directory)
            write_task03_figures(
                self.planck_result,
                self.einstein_result,
                generated_directory,
            )
            for filename in FIGURE_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (committed_directory / filename).read_bytes(),
                        (generated_directory / filename).read_bytes(),
                    )


if __name__ == "__main__":
    unittest.main()
