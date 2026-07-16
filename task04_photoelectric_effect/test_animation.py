"""Tests for the optional deterministic Task 4 animation extension."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest import mock

from matplotlib import pyplot as plt
from PIL import Image

from task04_photoelectric_effect import animation as animation_module
from task04_photoelectric_effect.analysis import build_task04_study
from task04_photoelectric_effect.animation import (
    AnimationConfiguration,
    AnimationScene,
    DEFAULT_ANIMATION_CONFIGURATION,
    STORYBOARD_DIMENSIONS,
    Task04AnimationGenerationResult,
    build_animation_scenes,
    create_photoelectric_storyboard,
    main as animation_main,
    write_task04_animation,
)
from task04_photoelectric_effect.generate_task04 import (
    ANIMATION_FILENAMES,
    DATA_FILENAMES,
    FIGURE_FILENAMES,
    REPOSITORY_ROOT,
    main as generation_main,
)
from task04_photoelectric_effect.validation import validate_task04


class Task04AnimationContentTests(unittest.TestCase):
    """Protect the extension's scientific story and visual declarations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()
        cls.report = validate_task04(cls.study)
        cls.scenes = build_animation_scenes(cls.study, cls.report)

    def tearDown(self) -> None:
        plt.close("all")

    def test_configuration_is_frozen_bounded_and_exactly_sixteen_by_nine(
        self,
    ) -> None:
        configuration = DEFAULT_ANIMATION_CONFIGURATION
        self.assertEqual(configuration.total_frames, 60)
        self.assertEqual(configuration.duration_s, 6.0)
        self.assertEqual(configuration.figure_size_in, (12.0, 6.75))
        with self.assertRaises(FrozenInstanceError):
            configuration.fps = 12  # type: ignore[misc]
        with self.assertRaisesRegex(ValueError, "16:9"):
            AnimationConfiguration(width_px=1200, height_px=700)
        with self.assertRaises(TypeError):
            AnimationConfiguration(fps=True)  # type: ignore[arg-type]

    def test_four_scenes_cover_threshold_intensity_and_stopping_potential(
        self,
    ) -> None:
        self.assertEqual(tuple(scene.number for scene in self.scenes), (1, 2, 3, 4))
        below, low_intensity, high_intensity, stopped = self.scenes

        self.assertEqual((below.wavelength_nm, below.photoemission), (550.0, False))
        self.assertFalse(below.electrons_reach_collector)
        self.assertLess(below.photon_energy_ev, below.work_function_ev)
        self.assertEqual(below.maximum_kinetic_energy_ev, 0.0)

        self.assertEqual(low_intensity.wavelength_nm, 450.0)
        self.assertTrue(low_intensity.photoemission)
        self.assertTrue(low_intensity.electrons_reach_collector)
        self.assertGreater(low_intensity.maximum_kinetic_energy_ev, 0.0)
        self.assertAlmostEqual(
            low_intensity.maximum_kinetic_energy_ev,
            low_intensity.stopping_voltage_v,
        )

        self.assertGreater(
            high_intensity.intensity_level,
            low_intensity.intensity_level,
        )
        self.assertEqual(
            high_intensity.maximum_kinetic_energy_ev,
            low_intensity.maximum_kinetic_energy_ev,
        )
        self.assertEqual(
            high_intensity.stopping_voltage_v,
            low_intensity.stopping_voltage_v,
        )

        self.assertFalse(stopped.electrons_reach_collector)
        self.assertEqual(stopped.reverse_voltage_v, stopped.stopping_voltage_v)
        self.assertIn("photocurrent is zero", stopped.explanation)

    def test_scene_record_rejects_current_without_photoemission(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires photoemission"):
            replace(
                self.scenes[0],
                electrons_reach_collector=True,
            )

    def test_storyboard_has_four_panels_and_explicit_schematic_boundary(self) -> None:
        figure = create_photoelectric_storyboard(self.study, self.report)
        self.assertEqual(len(figure.axes), 4)
        self.assertEqual(
            (figure.get_figwidth(), figure.get_figheight()),
            (16.0, 9.0),
        )
        all_text = " ".join(
            text.get_text()
            for axis in figure.axes
            for text in axis.texts
        )
        self.assertIn("NO PHOTOEMISSION", all_text)
        self.assertIn("$V_s$: undefined", all_text)
        self.assertIn("maximum $K$: not defined", all_text)
        self.assertIn("More photons emit more electrons", all_text)
        self.assertIn("CURRENT = 0", all_text)

    def test_factories_refuse_failed_mismatched_or_wrong_inputs(self) -> None:
        failed_check = replace(self.report.checks[0], passed=False)
        failed_report = replace(
            self.report,
            checks=(failed_check,) + self.report.checks[1:],
        )
        with self.assertRaisesRegex(RuntimeError, "validation failed"):
            build_animation_scenes(self.study, failed_report)

        changed_check = replace(
            self.report.checks[-1],
            observed=self.report.checks[-1].observed + 1.0e-16,
        )
        mismatched = replace(
            self.report,
            checks=self.report.checks[:-1] + (changed_check,),
        )
        with self.assertRaisesRegex(ValueError, "does not exactly describe"):
            create_photoelectric_storyboard(self.study, mismatched)
        with self.assertRaises(TypeError):
            build_animation_scenes("study", self.report)  # type: ignore[arg-type]


class Task04AnimationWriterTests(unittest.TestCase):
    """Protect output formats, reproducibility, transactions, and CLIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.study = build_task04_study()
        cls.report = validate_task04(cls.study)

    def tearDown(self) -> None:
        plt.close("all")

    def test_writer_creates_the_exact_validated_extension_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "animation"
            result = write_task04_animation(
                self.study,
                self.report,
                output_directory,
            )
            self.assertIsInstance(result, Task04AnimationGenerationResult)
            self.assertEqual(
                tuple(path.name for path in result.output_paths),
                ANIMATION_FILENAMES,
            )
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(ANIMATION_FILENAMES)),
            )
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )
            self.assertTrue(
                all(
                    (path.stat().st_mode & 0o777) == 0o644
                    for path in result.output_paths
                )
            )

            with Image.open(result.output_paths[0]) as image:
                self.assertEqual(image.format, "GIF")
                self.assertEqual(image.size, (1920, 1080))
                self.assertEqual(image.n_frames, 60)
                self.assertEqual(image.info["loop"], 0)
                self.assertEqual(image.info["duration"], 100)
            with Image.open(result.output_paths[1]) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, STORYBOARD_DIMENSIONS)
                image.verify()

    def test_outputs_are_byte_identical_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first"
            second = root / "second"
            write_task04_animation(self.study, self.report, first)
            write_task04_animation(self.study, self.report, second)
            for filename in ANIMATION_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (first / filename).read_bytes(),
                        (second / filename).read_bytes(),
                    )

    def test_late_writer_failure_preserves_existing_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            baseline = {
                filename: f"existing-{filename}".encode("ascii")
                for filename in ANIMATION_FILENAMES
            }
            for filename, payload in baseline.items():
                (output_directory / filename).write_bytes(payload)

            with mock.patch.object(
                animation_module,
                "_save_storyboard",
                side_effect=RuntimeError("injected storyboard failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    write_task04_animation(
                        self.study,
                        self.report,
                        output_directory,
                    )

            for filename, payload in baseline.items():
                self.assertEqual((output_directory / filename).read_bytes(), payload)
            self.assertFalse(
                any(path.name.startswith(".") for path in output_directory.iterdir())
            )

    def test_animation_cli_generates_only_the_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "extension"
            output = io.StringIO()
            with redirect_stdout(output):
                status = animation_main(["--output-dir", str(output_directory)])
            self.assertEqual(status, 0)
            self.assertIn("Stage 10", output.getvalue())
            self.assertIn("PASS", output.getvalue())
            self.assertEqual(
                tuple(sorted(path.name for path in output_directory.iterdir())),
                tuple(sorted(ANIMATION_FILENAMES)),
            )

    def test_integrated_cli_writes_data_figures_and_animation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_directory = root / "data"
            figure_directory = root / "figures"
            output = io.StringIO()
            with redirect_stdout(output):
                status = generation_main(
                    [
                        "--with-animation",
                        "--data-dir",
                        str(data_directory),
                        "--figure-dir",
                        str(figure_directory),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertIn("Stage 10", output.getvalue())
            self.assertIn("with animation: PASS", output.getvalue())
            self.assertEqual(
                tuple(sorted(path.name for path in data_directory.iterdir())),
                tuple(sorted(DATA_FILENAMES)),
            )
            self.assertEqual(
                tuple(sorted(path.name for path in figure_directory.iterdir())),
                tuple(sorted(FIGURE_FILENAMES + ANIMATION_FILENAMES)),
            )

    def test_integrated_cli_rejects_data_only_animation_conflict(self) -> None:
        error = io.StringIO()
        with redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                generation_main(["--data-only", "--with-animation"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("cannot be combined", error.getvalue())

    def test_committed_extension_is_current_and_has_no_hidden_files(self) -> None:
        committed_directory = REPOSITORY_ROOT / "figures" / "task04"
        with tempfile.TemporaryDirectory() as temporary_directory:
            regenerated_directory = Path(temporary_directory)
            write_task04_animation(
                self.study,
                self.report,
                regenerated_directory,
            )
            for filename in ANIMATION_FILENAMES:
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (committed_directory / filename).read_bytes(),
                        (regenerated_directory / filename).read_bytes(),
                    )
        self.assertFalse(
            any(path.name.startswith(".") for path in committed_directory.iterdir())
        )


if __name__ == "__main__":
    unittest.main()
