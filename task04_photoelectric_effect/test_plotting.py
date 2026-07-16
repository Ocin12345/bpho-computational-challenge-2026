"""Tests for validated deterministic Task 4 figure generation."""

from __future__ import annotations

import io
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image
from matplotlib import pyplot as plt

from task04_photoelectric_effect.analysis import build_task04_study
from task04_photoelectric_effect.configuration import DEFAULT_CONFIGURATION
from task04_photoelectric_effect.generate_task04 import (
    DATA_FILENAMES,
    FIGURE_FILENAMES,
    REPOSITORY_ROOT,
    main,
)
from task04_photoelectric_effect.plotting import (
    CURVE_GROUPS,
    EXPECTED_PNG_DIMENSIONS,
    GROUP_COLOURS,
    Task04FigureGenerationResult,
    create_copper_threshold_explanation_figure,
    create_photoelectric_validation_figure,
    create_stopping_voltage_frequency_figure,
    create_stopping_voltage_wavelength_figure,
    create_task04_summary_figure,
    write_task04_figures,
)
from task04_photoelectric_effect.validation import validate_task04


class Task04FigureContentTests(unittest.TestCase):
    """Protect scientific content, dimensions, grouping, and annotations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()
        cls.report = validate_task04(cls.study)

    def tearDown(self) -> None:
        plt.close("all")

    def test_public_figures_have_frozen_dimensions_and_structure(self) -> None:
        specifications = (
            (
                create_stopping_voltage_frequency_figure,
                (10.4, 5.8),
                2,
                "Stopping potential versus frequency",
            ),
            (
                create_stopping_voltage_wavelength_figure,
                (10.4, 5.8),
                2,
                "Stopping potential versus vacuum wavelength",
            ),
            (
                create_copper_threshold_explanation_figure,
                (8.4, 5.2),
                1,
                "Copper threshold",
            ),
            (
                create_photoelectric_validation_figure,
                (10.4, 5.2),
                2,
                "Whole-study numerical checks",
            ),
            (
                create_task04_summary_figure,
                (2400 / 180, 1350 / 180),
                4,
                "Stopping potential versus frequency",
            ),
        )
        for factory, expected_size, axes, expected_title in specifications:
            with self.subTest(factory=factory.__name__):
                figure = factory(self.study, self.report)
                self.assertEqual(len(figure.axes), axes)
                self.assertAlmostEqual(figure.get_figwidth(), expected_size[0])
                self.assertAlmostEqual(figure.get_figheight(), expected_size[1])
                self.assertTrue(
                    any(
                        expected_title in axis.get_title()
                        for axis in figure.axes
                    )
                )
                plt.close(figure)

    def test_frequency_figure_uses_seven_honest_physical_groups(self) -> None:
        figure = create_stopping_voltage_frequency_figure(
            self.study,
            self.report,
        )
        axis, guide = figure.axes
        self.assertEqual(len(axis.lines), 7)
        self.assertEqual(len(axis.collections), 7)
        legend_labels = [text.get_text() for text in axis.legend_.texts]
        self.assertEqual(len(legend_labels), 7)
        self.assertTrue(any("Ag / Al / Pb" in label for label in legend_labels))
        guide_text = " ".join(text.get_text() for text in guide.texts)
        self.assertIn("Analytical threshold", guide_text)
        self.assertIn("Ag, Al and Pb coincide", guide_text)
        self.assertEqual(
            axis.get_ylabel(),
            "Stopping-potential magnitude, $V_s$ (V)",
        )
        for line, group in zip(axis.lines, CURVE_GROUPS):
            y_values = np.asarray(line.get_ydata(), dtype=np.float64)
            x_values = np.asarray(line.get_xdata(), dtype=np.float64)
            finite = np.isfinite(y_values)
            self.assertTrue(np.all(y_values[finite] >= 0.0))
            self.assertGreaterEqual(
                x_values[finite][0],
                self.study.cutoff_frequencies_hz[group.source_row] / 1.0e15,
            )

    def test_wavelength_figure_marks_visible_band_and_physical_cutoffs(self) -> None:
        figure = create_stopping_voltage_wavelength_figure(
            self.study,
            self.report,
        )
        axis, guide = figure.axes
        physical_lines = axis.lines[1:]
        self.assertEqual(len(physical_lines), 7)
        self.assertEqual(len(axis.collections), 7)
        self.assertGreaterEqual(len(axis.patches), 1)
        axis_text = " ".join(text.get_text() for text in axis.texts)
        self.assertIn("Visible band", axis_text)
        self.assertIn("Only Na reaches visible light", axis_text)
        self.assertIn("not a zero stopping potential", axis_text)
        self.assertIn(
            "Analytical cut-off",
            " ".join(text.get_text() for text in guide.texts),
        )
        maximum_active_wavelengths = []
        for line in physical_lines:
            y_values = np.asarray(line.get_ydata(), dtype=np.float64)
            x_values = np.asarray(line.get_xdata(), dtype=np.float64)
            maximum_active_wavelengths.append(
                float(np.max(x_values[np.isfinite(y_values)]))
            )
        self.assertEqual(
            sum(value >= 380.0 for value in maximum_active_wavelengths),
            1,
        )

    def test_copper_figure_distinguishes_extrapolation_from_physics(self) -> None:
        figure = create_copper_threshold_explanation_figure(
            self.study,
            self.report,
        )
        axis = figure.axes[0]
        self.assertEqual(axis.lines[0].get_linestyle(), "--")
        self.assertEqual(axis.lines[1].get_linestyle(), "-")
        self.assertTrue(np.all(np.asarray(axis.lines[0].get_ydata()) <= 0.0))
        self.assertTrue(np.all(np.asarray(axis.lines[1].get_ydata()) >= 0.0))
        text = " ".join(item.get_text() for item in axis.texts)
        self.assertIn(
            "mathematical extrapolation: no photoemission",
            text,
        )
        self.assertIn("eV", text)
        self.assertIn("1.136", text)

    def test_validation_figure_normalizes_every_error_to_tolerance(self) -> None:
        figure = create_photoelectric_validation_figure(
            self.study,
            self.report,
        )
        general_axis, cutoff_axis = figure.axes
        self.assertEqual(general_axis.get_yscale(), "log")
        self.assertEqual(cutoff_axis.get_yscale(), "log")
        self.assertEqual(len(general_axis.patches), 8)
        self.assertTrue(
            all(patch.get_height() <= 1.0 for patch in general_axis.patches)
        )
        self.assertIn(
            "Declared tolerance",
            [text.get_text() for text in general_axis.legend_.texts],
        )
        figure_text = " ".join(text.get_text() for text in figure.texts)
        self.assertIn("43/43 checks", figure_text)

    def test_summary_is_slide_ready_and_contains_the_key_conclusions(self) -> None:
        figure = create_task04_summary_figure(self.study, self.report)
        self.assertEqual(len(figure.axes), 4)
        key_text = " ".join(text.get_text() for text in figure.axes[3].texts)
        self.assertIn("What the simulation shows", key_text)
        self.assertIn("Only Na reaches visible light", key_text)
        self.assertIn("43/43 independent checks", key_text)
        self.assertIn("no photoelectrons", key_text)

    def test_colour_contract_is_distinct_and_complete(self) -> None:
        self.assertEqual(len(CURVE_GROUPS), 7)
        self.assertEqual(len(GROUP_COLOURS), 7)
        self.assertEqual(len(set(GROUP_COLOURS)), 7)
        self.assertEqual(
            tuple(group.colour for group in CURVE_GROUPS),
            GROUP_COLOURS,
        )

    def test_factories_refuse_failed_mismatched_or_wrong_inputs(self) -> None:
        failed_check = replace(self.report.checks[0], passed=False)
        failed_report = replace(
            self.report,
            checks=(failed_check,) + self.report.checks[1:],
        )
        with self.assertRaisesRegex(RuntimeError, "validation failed"):
            create_stopping_voltage_frequency_figure(
                self.study,
                failed_report,
            )

        changed_check = replace(
            self.report.checks[-1],
            observed=self.report.checks[-1].observed + 1.0e-16,
        )
        mismatched_report = replace(
            self.report,
            checks=self.report.checks[:-1] + (changed_check,),
        )
        self.assertTrue(mismatched_report.passed)
        with self.assertRaisesRegex(ValueError, "does not exactly describe"):
            create_stopping_voltage_frequency_figure(
                self.study,
                mismatched_report,
            )
        with self.assertRaises(TypeError):
            create_stopping_voltage_frequency_figure(
                "study",  # type: ignore[arg-type]
                self.report,
            )


class Task04FigureWriterTests(unittest.TestCase):
    """Protect formats, deterministic bytes, transactions, and the CLI."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()
        cls.report = validate_task04(cls.study)

    def tearDown(self) -> None:
        plt.close("all")

    def test_writer_creates_ordered_compact_png_and_svg_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "figures"
            result = write_task04_figures(
                self.study,
                self.report,
                output_directory,
            )
            self.assertIsInstance(result, Task04FigureGenerationResult)
            self.assertTrue(result.report.passed)
            self.assertEqual(
                tuple(path.name for path in result.output_paths),
                FIGURE_FILENAMES,
            )
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(FIGURE_FILENAMES)),
            )
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )
            self.assertLess(
                sum(path.stat().st_size for path in result.output_paths),
                DEFAULT_CONFIGURATION.figure_size_budget_bytes,
            )
            self.assertTrue(
                all(
                    (path.stat().st_mode & 0o777) == 0o644
                    for path in result.output_paths
                )
            )

            for filename, dimensions in EXPECTED_PNG_DIMENSIONS.items():
                path = output_directory / filename
                self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
                with Image.open(path) as image:
                    self.assertEqual(image.size, dimensions)
                    self.assertEqual(image.mode, "RGBA")
                    image.verify()

            for filename in FIGURE_FILENAMES[1::2]:
                text = (output_directory / filename).read_text(encoding="utf-8")
                root = ET.fromstring(text)
                self.assertTrue(root.tag.endswith("svg"))
                self.assertIn("viewBox", root.attrib)
                self.assertNotIn("<dc:date>", text)
                self.assertTrue(text.endswith("\n"))
                self.assertTrue(
                    all(line == line.rstrip() for line in text.splitlines())
                )

    def test_outputs_are_byte_identical_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first"
            second = root / "second"
            write_task04_figures(self.study, self.report, first)
            baseline = {
                filename: (first / filename).read_bytes()
                for filename in FIGURE_FILENAMES
            }
            write_task04_figures(self.study, self.report, second)
            for filename in FIGURE_FILENAMES:
                self.assertEqual(
                    baseline[filename],
                    (second / filename).read_bytes(),
                )
            write_task04_figures(self.study, self.report, first)
            for filename in FIGURE_FILENAMES:
                self.assertEqual(
                    baseline[filename],
                    (first / filename).read_bytes(),
                )

    def test_failed_validation_creates_no_figure_directory(self) -> None:
        failed_check = replace(self.report.checks[0], passed=False)
        failed_report = replace(
            self.report,
            checks=(failed_check,) + self.report.checks[1:],
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "figures"
            with self.assertRaisesRegex(RuntimeError, "validation failed"):
                write_task04_figures(
                    self.study,
                    failed_report,
                    output_directory,
                )
            self.assertFalse(output_directory.exists())

    def test_writer_failure_preserves_destinations_and_cleans_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            originals = {}
            for filename in FIGURE_FILENAMES:
                content = f"old {filename}\n".encode()
                originals[filename] = content
                (output_directory / filename).write_bytes(content)
            with mock.patch(
                "task04_photoelectric_effect.plotting._save_figure",
                side_effect=RuntimeError("injected figure writer failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected figure"):
                    write_task04_figures(
                        self.study,
                        self.report,
                        output_directory,
                    )
            for filename, content in originals.items():
                self.assertEqual((output_directory / filename).read_bytes(), content)
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(FIGURE_FILENAMES)),
            )

    def test_install_failure_rolls_back_every_existing_figure(self) -> None:
        module = sys.modules["task04_photoelectric_effect.plotting"]
        real_replace = module._replace_figure_path
        state = {"raised": False}

        def fail_second_install(source: Path, destination: Path) -> None:
            if (
                not state["raised"]
                and source.suffix in (".png", ".svg")
                and ".bak" not in source.name
                and destination.name == FIGURE_FILENAMES[1]
            ):
                state["raised"] = True
                raise OSError("injected figure install failure")
            real_replace(source, destination)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            originals = {}
            for filename in FIGURE_FILENAMES:
                content = f"original {filename}\n".encode()
                originals[filename] = content
                (output_directory / filename).write_bytes(content)
            with mock.patch.object(
                module,
                "_replace_figure_path",
                side_effect=fail_second_install,
            ):
                with self.assertRaisesRegex(OSError, "injected figure install"):
                    write_task04_figures(
                        self.study,
                        self.report,
                        output_directory,
                    )
            self.assertTrue(state["raised"])
            for filename, content in originals.items():
                self.assertEqual((output_directory / filename).read_bytes(), content)
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(FIGURE_FILENAMES)),
            )

    def test_verification_failure_occurs_before_destination_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            existing = output_directory / FIGURE_FILENAMES[0]
            existing.write_text("original\n", encoding="utf-8")
            with mock.patch(
                "task04_photoelectric_effect.plotting._verify_prepared_figures",
                side_effect=ValueError("injected figure verification failure"),
            ):
                with self.assertRaisesRegex(ValueError, "injected figure"):
                    write_task04_figures(
                        self.study,
                        self.report,
                        output_directory,
                    )
            self.assertEqual(existing.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(tuple(output_directory.iterdir()), (existing,))

    def test_invalid_figure_paths_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            file_path = root / "not-a-directory"
            file_path.write_text("existing\n", encoding="utf-8")
            with self.assertRaises(NotADirectoryError):
                write_task04_figures(self.study, self.report, file_path)
            self.assertEqual(file_path.read_text(encoding="utf-8"), "existing\n")

            output_directory = root / "figures"
            output_directory.mkdir()
            destination = output_directory / FIGURE_FILENAMES[0]
            destination.mkdir()
            with self.assertRaises(IsADirectoryError):
                write_task04_figures(
                    self.study,
                    self.report,
                    output_directory,
                )
            self.assertEqual(tuple(output_directory.iterdir()), (destination,))

    def test_figure_generation_remains_below_runtime_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            start = time.perf_counter()
            result = write_task04_figures(
                self.study,
                self.report,
                temporary_directory,
            )
            elapsed = time.perf_counter() - start
        self.assertTrue(result.report.passed)
        self.assertLess(elapsed, DEFAULT_CONFIGURATION.generation_runtime_budget_s)

    def test_complete_cli_writes_data_and_figures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_directory = root / "data"
            figure_directory = root / "figures"
            output = io.StringIO()
            with redirect_stdout(output):
                status = main(
                    [
                        "--data-dir",
                        str(data_directory),
                        "--figure-dir",
                        str(figure_directory),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertIn("Task 4 Stage 8", output.getvalue())
            self.assertIn("Validation checks: 43", output.getvalue())
            self.assertIn("Task 4 complete generation: PASS", output.getvalue())
            self.assertEqual(
                tuple(sorted(path.name for path in data_directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )
            self.assertEqual(
                tuple(sorted(path.name for path in figure_directory.iterdir())),
                tuple(sorted(FIGURE_FILENAMES)),
            )

    def test_committed_figures_match_fresh_regeneration(self) -> None:
        committed_directory = REPOSITORY_ROOT / "figures" / "task04"
        self.assertTrue(committed_directory.is_dir())
        with tempfile.TemporaryDirectory() as temporary_directory:
            generated_directory = Path(temporary_directory)
            write_task04_figures(
                self.study,
                self.report,
                generated_directory,
            )
            for filename in FIGURE_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (committed_directory / filename).read_bytes(),
                        (generated_directory / filename).read_bytes(),
                    )

    def test_figure_result_rejects_failed_or_misordered_records(self) -> None:
        failed_check = replace(self.report.checks[0], passed=False)
        failed_report = replace(
            self.report,
            checks=(failed_check,) + self.report.checks[1:],
        )
        with self.assertRaises(ValueError):
            Task04FigureGenerationResult(
                failed_report,
                tuple(Path(name) for name in FIGURE_FILENAMES),
            )
        with self.assertRaises(ValueError):
            Task04FigureGenerationResult(
                self.report,
                tuple(Path(name) for name in reversed(FIGURE_FILENAMES)),
            )


if __name__ == "__main__":
    unittest.main()
