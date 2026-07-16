"""Deterministic schematic animation extension for Task 4."""

from __future__ import annotations

import math
import os
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from numbers import Integral, Real
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from PIL import Image

from task04_photoelectric_effect.analysis import (
    Task04StudyResult,
    build_task04_study,
)
from task04_photoelectric_effect.configuration import DEFAULT_CONFIGURATION
from task04_photoelectric_effect.generate_task04 import (
    ANIMATION_FILENAMES,
    DEFAULT_FIGURE_DIRECTORY,
)
from task04_photoelectric_effect.validation import (
    Task04ValidationReport,
    validate_task04,
)


ANIMATION_BACKGROUND = "#F8FAFC"
TEXT_COLOUR = "#172033"
SUBTLE_TEXT = "#475569"
PHOTON_COLOUR = "#F5C542"
ELECTRON_COLOUR = "#06B6D4"
SODIUM_COLOUR = "#64748B"
COLLECTOR_COLOUR = "#334155"
FIELD_COLOUR = "#8B5CF6"
PASS_COLOUR = "#14804A"
STOP_COLOUR = "#B45309"
FAIL_COLOUR = "#B91C1C"

STORYBOARD_DIMENSIONS = (1600, 900)
STORYBOARD_DPI = 100


def _integer(
    value: Integral,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < minimum or normalized > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return normalized


def _finite_real(value: Real, *, name: str, non_negative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if non_negative and normalized < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _non_empty_text(value: str, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


@dataclass(frozen=True)
class AnimationConfiguration:
    """Frozen portable rendering configuration for the optional extension."""

    fps: int = 8
    frames_per_scene: int = 12
    width_px: int = 1200
    height_px: int = 675
    dpi: int = 100

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fps",
            _integer(self.fps, name="fps", minimum=1, maximum=30),
        )
        object.__setattr__(
            self,
            "frames_per_scene",
            _integer(
                self.frames_per_scene,
                name="frames_per_scene",
                minimum=4,
                maximum=60,
            ),
        )
        object.__setattr__(
            self,
            "width_px",
            _integer(
                self.width_px,
                name="width_px",
                minimum=640,
                maximum=2400,
            ),
        )
        object.__setattr__(
            self,
            "height_px",
            _integer(
                self.height_px,
                name="height_px",
                minimum=360,
                maximum=1350,
            ),
        )
        object.__setattr__(
            self,
            "dpi",
            _integer(self.dpi, name="dpi", minimum=72, maximum=240),
        )
        if self.width_px * 9 != self.height_px * 16:
            raise ValueError("animation dimensions must have an exact 16:9 ratio")

    @property
    def total_frames(self) -> int:
        return 4 * self.frames_per_scene

    @property
    def duration_s(self) -> float:
        return self.total_frames / self.fps

    @property
    def figure_size_in(self) -> tuple[float, float]:
        return self.width_px / self.dpi, self.height_px / self.dpi


DEFAULT_ANIMATION_CONFIGURATION = AnimationConfiguration()


@dataclass(frozen=True)
class AnimationScene:
    """One scientifically explicit scene in the four-part extension."""

    number: int
    title: str
    explanation: str
    wavelength_nm: float
    intensity_level: int
    reverse_voltage_v: float
    photon_energy_ev: float
    work_function_ev: float
    maximum_kinetic_energy_ev: float
    stopping_voltage_v: float
    photoemission: bool
    electrons_reach_collector: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "number",
            _integer(self.number, name="number", minimum=1, maximum=4),
        )
        object.__setattr__(
            self,
            "intensity_level",
            _integer(
                self.intensity_level,
                name="intensity_level",
                minimum=1,
                maximum=3,
            ),
        )
        for field_name in ("title", "explanation"):
            object.__setattr__(
                self,
                field_name,
                _non_empty_text(getattr(self, field_name), name=field_name),
            )
        for field_name in (
            "wavelength_nm",
            "reverse_voltage_v",
            "photon_energy_ev",
            "work_function_ev",
            "maximum_kinetic_energy_ev",
            "stopping_voltage_v",
        ):
            object.__setattr__(
                self,
                field_name,
                _finite_real(
                    getattr(self, field_name),
                    name=field_name,
                    non_negative=True,
                ),
            )
        if not isinstance(self.photoemission, bool):
            raise TypeError("photoemission must be a bool")
        if not isinstance(self.electrons_reach_collector, bool):
            raise TypeError("electrons_reach_collector must be a bool")
        if self.electrons_reach_collector and not self.photoemission:
            raise ValueError("collector current requires photoemission")


@dataclass(frozen=True)
class Task04AnimationGenerationResult:
    """Passing report and ordered extension artifacts."""

    report: Task04ValidationReport
    output_paths: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.report, Task04ValidationReport):
            raise TypeError("report must be a Task04ValidationReport")
        if not self.report.passed:
            raise ValueError("animation generation requires a passing report")
        try:
            paths = tuple(Path(path) for path in self.output_paths)
        except TypeError as exc:
            raise TypeError("output_paths must be an iterable of paths") from exc
        if tuple(path.name for path in paths) != ANIMATION_FILENAMES:
            raise ValueError("output_paths must follow the frozen animation order")
        object.__setattr__(self, "output_paths", paths)


def _require_validated(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> None:
    if not isinstance(study, Task04StudyResult):
        raise TypeError("study must be a Task04StudyResult")
    if not isinstance(report, Task04ValidationReport):
        raise TypeError("report must be a Task04ValidationReport")
    if not report.passed:
        failed_names = ", ".join(check.name for check in report.failed_checks)
        raise RuntimeError(
            "Task 4 animation refused because validation failed: "
            f"{failed_names}"
        )
    if report != validate_task04(study):
        raise ValueError("report does not exactly describe the supplied study")


def _wavelength_index(study: Task04StudyResult, wavelength_nm: float) -> int:
    matches = np.flatnonzero(study.wavelength_nm == wavelength_nm)
    if matches.size != 1:
        raise ValueError(
            "wavelength is not an exact study-grid point: "
            f"{wavelength_nm}"
        )
    return int(matches[0])


def build_animation_scenes(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> tuple[AnimationScene, ...]:
    """Return the frozen threshold/intensity/stopping-potential storyboard."""

    _require_validated(study, report)
    sodium_row = 8
    work_function = float(study.work_functions_ev[sodium_row])

    def values(wavelength_nm: float) -> tuple[float, float, float, bool]:
        index = _wavelength_index(study, wavelength_nm)
        signed_voltage = float(
            study.wavelength_linear_voltage_v[sodium_row, index]
        )
        photon_energy = signed_voltage + work_function
        photoemission = bool(
            study.wavelength_emission_mask[sodium_row, index]
        )
        kinetic_energy = max(signed_voltage, 0.0) if photoemission else 0.0
        stopping_voltage = kinetic_energy
        return photon_energy, kinetic_energy, stopping_voltage, photoemission

    low_energy = values(550.0)
    high_energy = values(450.0)
    return (
        AnimationScene(
            number=1,
            title="Below threshold",
            explanation="Photon energy is smaller than W: no electron is emitted.",
            wavelength_nm=550.0,
            intensity_level=2,
            reverse_voltage_v=0.0,
            photon_energy_ev=low_energy[0],
            work_function_ev=work_function,
            maximum_kinetic_energy_ev=low_energy[1],
            stopping_voltage_v=low_energy[2],
            photoemission=low_energy[3],
            electrons_reach_collector=False,
        ),
        AnimationScene(
            number=2,
            title="Above threshold",
            explanation="Emitted maximum-energy electrons reach the collector.",
            wavelength_nm=450.0,
            intensity_level=1,
            reverse_voltage_v=0.0,
            photon_energy_ev=high_energy[0],
            work_function_ev=work_function,
            maximum_kinetic_energy_ev=high_energy[1],
            stopping_voltage_v=high_energy[2],
            photoemission=high_energy[3],
            electrons_reach_collector=True,
        ),
        AnimationScene(
            number=3,
            title="Increase intensity",
            explanation=(
                "More photons emit more electrons, but their maximum energy "
                "and V_s are unchanged."
            ),
            wavelength_nm=450.0,
            intensity_level=3,
            reverse_voltage_v=0.0,
            photon_energy_ev=high_energy[0],
            work_function_ev=work_function,
            maximum_kinetic_energy_ev=high_energy[1],
            stopping_voltage_v=high_energy[2],
            photoemission=high_energy[3],
            electrons_reach_collector=True,
        ),
        AnimationScene(
            number=4,
            title="Apply the stopping potential",
            explanation=(
                "At reverse voltage V_s, even maximum-energy electrons are "
                "turned back and the photocurrent is zero."
            ),
            wavelength_nm=450.0,
            intensity_level=3,
            reverse_voltage_v=high_energy[2],
            photon_energy_ev=high_energy[0],
            work_function_ev=work_function,
            maximum_kinetic_energy_ev=high_energy[1],
            stopping_voltage_v=high_energy[2],
            photoemission=high_energy[3],
            electrons_reach_collector=False,
        ),
    )


def _draw_apparatus(axis: Axes, scene: AnimationScene, phase: float) -> None:
    """Draw one deterministic apparatus state in normalized coordinates."""

    axis.add_patch(
        FancyBboxPatch(
            (0.055, 0.355),
            0.09,
            0.30,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor="#1E293B",
            edgecolor="#0F172A",
            linewidth=1.6,
        )
    )
    axis.add_patch(Circle((0.10, 0.505), 0.032, color=PHOTON_COLOUR))
    axis.text(
        0.10,
        0.32,
        "monochromatic\nlight",
        ha="center",
        va="top",
        fontsize=8.5,
        color=SUBTLE_TEXT,
    )

    axis.add_patch(
        Rectangle(
            (0.425, 0.27),
            0.028,
            0.46,
            facecolor=SODIUM_COLOUR,
            edgecolor="#334155",
            linewidth=1.5,
        )
    )
    axis.text(
        0.439,
        0.245,
        "Na cathode\n$W=2.4$ eV",
        ha="center",
        va="top",
        fontsize=8.3,
        color=SUBTLE_TEXT,
    )
    axis.add_patch(
        Rectangle(
            (0.785, 0.27),
            0.028,
            0.46,
            facecolor=COLLECTOR_COLOUR,
            edgecolor="#0F172A",
            linewidth=1.5,
        )
    )
    axis.text(
        0.799,
        0.245,
        "collector",
        ha="center",
        va="top",
        fontsize=8.3,
        color=SUBTLE_TEXT,
    )

    stream_count = 2 * scene.intensity_level
    stream_offsets = np.linspace(-0.105, 0.105, stream_count)
    for index, offset in enumerate(stream_offsets):
        progress = (phase + index / stream_count) % 1.0
        photon_x = 0.15 + 0.265 * progress
        photon_y = 0.505 + offset
        axis.scatter(
            [photon_x],
            [photon_y],
            s=30,
            color=PHOTON_COLOUR,
            edgecolor="#B7791F",
            linewidth=0.6,
            zorder=4,
        )
        axis.annotate(
            "",
            xy=(min(photon_x + 0.03, 0.422), photon_y),
            xytext=(photon_x, photon_y),
            arrowprops={
                "arrowstyle": "->",
                "color": PHOTON_COLOUR,
                "linewidth": 1.0,
            },
        )

    if scene.photoemission:
        electron_count = 2 * scene.intensity_level
        electron_offsets = np.linspace(-0.10, 0.10, electron_count)
        for index, offset in enumerate(electron_offsets):
            progress = (phase + index / electron_count) % 1.0
            if scene.electrons_reach_collector:
                electron_x = 0.46 + 0.315 * progress
            else:
                electron_x = 0.46 + 0.105 * math.sin(math.pi * progress)
            electron_y = 0.505 + offset
            axis.scatter(
                [electron_x],
                [electron_y],
                s=35,
                color=ELECTRON_COLOUR,
                edgecolor="#0E7490",
                linewidth=0.7,
                zorder=5,
            )
            axis.text(
                electron_x,
                electron_y,
                "−",
                ha="center",
                va="center",
                fontsize=7.0,
                fontweight="bold",
                color="white",
                zorder=6,
            )

    if scene.reverse_voltage_v > 0.0:
        axis.annotate(
            "",
            xy=(0.47, 0.78),
            xytext=(0.77, 0.78),
            arrowprops={
                "arrowstyle": "-|>",
                "color": FIELD_COLOUR,
                "linewidth": 2.1,
            },
        )
        axis.text(
            0.62,
            0.805,
            "reverse electric force",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=FIELD_COLOUR,
            fontweight="bold",
        )


def _draw_energy_bars(axis: Axes, scene: AnimationScene, *, compact: bool) -> None:
    """Draw a compact energy accounting panel."""

    maximum_scale = 3.0
    left = 0.075
    width = 0.31
    base_y = 0.095 if not compact else 0.075
    bar_height = 0.026 if not compact else 0.022
    entries = (
        ("photon $E_\\gamma$", scene.photon_energy_ev, PHOTON_COLOUR),
        ("work function $W$", scene.work_function_ev, SODIUM_COLOUR),
        (
            "maximum $K$",
            scene.maximum_kinetic_energy_ev,
            ELECTRON_COLOUR,
        ),
    )
    for index, (label, value, colour) in enumerate(entries):
        y = base_y + (2 - index) * (0.055 if not compact else 0.047)
        axis.add_patch(
            Rectangle(
                (left, y),
                width,
                bar_height,
                facecolor="#E2E8F0",
                edgecolor="none",
            )
        )
        axis.add_patch(
            Rectangle(
                (left, y),
                width * value / maximum_scale,
                bar_height,
                facecolor=colour,
                edgecolor="none",
            )
        )
        value_text = f"{value:.3f} eV"
        if label == "maximum $K$" and not scene.photoemission:
            value_text = "not defined"
        axis.text(
            left,
            y + bar_height + 0.006,
            f"{label}: {value_text}",
            ha="left",
            va="bottom",
            fontsize=7.2 if compact else 8.2,
            color=SUBTLE_TEXT,
        )


def _status(scene: AnimationScene) -> tuple[str, str, str]:
    if not scene.photoemission:
        return "NO PHOTOEMISSION", FAIL_COLOUR, "photon energy < work function"
    if scene.electrons_reach_collector:
        return "PHOTOCURRENT", PASS_COLOUR, "electrons reach collector"
    return "CURRENT = 0", STOP_COLOUR, "stopping potential reached"


def _draw_scene(
    axis: Axes,
    scene: AnimationScene,
    phase: float,
    *,
    compact: bool = False,
) -> None:
    """Render one complete frame or storyboard panel."""

    axis.clear()
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.set_facecolor(ANIMATION_BACKGROUND)
    axis.axis("off")
    axis.text(
        0.04,
        0.96,
        f"{scene.number}/4  {scene.title}",
        ha="left",
        va="top",
        fontsize=11.0 if compact else 17.0,
        fontweight="bold",
        color=TEXT_COLOUR,
    )
    axis.text(
        0.96,
        0.955,
        f"Sodium  •  $\\lambda={scene.wavelength_nm:.0f}$ nm  •  "
        f"intensity {scene.intensity_level}/3",
        ha="right",
        va="top",
        fontsize=7.2 if compact else 10.0,
        color=SUBTLE_TEXT,
    )

    _draw_apparatus(axis, scene, phase)
    _draw_energy_bars(axis, scene, compact=compact)

    status, status_colour, status_detail = _status(scene)
    axis.text(
        0.90,
        0.61,
        status,
        ha="center",
        va="center",
        fontsize=8.5 if compact else 12.0,
        fontweight="bold",
        color=status_colour,
        bbox={
            "boxstyle": "round,pad=0.42",
            "facecolor": "white",
            "edgecolor": status_colour,
            "linewidth": 1.2,
        },
    )
    axis.text(
        0.90,
        0.545,
        status_detail,
        ha="center",
        va="top",
        fontsize=6.8 if compact else 8.3,
        color=SUBTLE_TEXT,
    )
    stopping_text = (
        f"$V_s={scene.stopping_voltage_v:.3f}$ V"
        if scene.photoemission
        else "$V_s$: undefined"
    )
    axis.text(
        0.90,
        0.42,
        f"{stopping_text}\nreverse $V={scene.reverse_voltage_v:.3f}$ V",
        ha="center",
        va="center",
        fontsize=7.5 if compact else 10.0,
        color=TEXT_COLOUR,
    )
    axis.text(
        0.50,
        0.025,
        scene.explanation,
        ha="center",
        va="bottom",
        fontsize=7.0 if compact else 10.0,
        color=TEXT_COLOUR,
        fontweight="bold",
    )
    if not compact:
        axis.text(
            0.99,
            0.01,
            "Schematic maximum-energy electrons; motion and scale are illustrative.",
            ha="right",
            va="bottom",
            fontsize=6.8,
            color="#64748B",
            fontstyle="italic",
        )


def create_photoelectric_storyboard(
    study: Task04StudyResult,
    report: Task04ValidationReport,
) -> Figure:
    """Return a static four-panel preview of the animated extension."""

    scenes = build_animation_scenes(study, report)
    figure, axes = plt.subplots(
        2,
        2,
        figsize=(
            STORYBOARD_DIMENSIONS[0] / STORYBOARD_DPI,
            STORYBOARD_DIMENSIONS[1] / STORYBOARD_DPI,
        ),
        facecolor="white",
    )
    for axis, scene in zip(axes.flat, scenes):
        _draw_scene(axis, scene, 0.55, compact=True)
    figure.suptitle(
        "Optional extension — threshold, intensity and stopping potential",
        fontsize=18.0,
        fontweight="bold",
        color=TEXT_COLOUR,
        y=0.985,
    )
    figure.subplots_adjust(
        left=0.015,
        right=0.985,
        bottom=0.025,
        top=0.92,
        wspace=0.035,
        hspace=0.10,
    )
    return figure


def _save_storyboard(
    study: Task04StudyResult,
    report: Task04ValidationReport,
    path: Path,
) -> None:
    figure = create_photoelectric_storyboard(study, report)
    try:
        figure.savefig(
            path,
            format="png",
            dpi=STORYBOARD_DPI,
            metadata={"Software": "BPhO Computational Challenge 2026"},
            facecolor="white",
            edgecolor="white",
        )
    finally:
        plt.close(figure)


def _save_animation(
    study: Task04StudyResult,
    report: Task04ValidationReport,
    path: Path,
    configuration: AnimationConfiguration,
) -> None:
    scenes = build_animation_scenes(study, report)
    figure, axis = plt.subplots(
        figsize=configuration.figure_size_in,
        dpi=configuration.dpi,
        facecolor="white",
    )
    figure.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)

    def update(frame: int) -> tuple[object, ...]:
        scene_index, local_frame = divmod(frame, configuration.frames_per_scene)
        phase = local_frame / configuration.frames_per_scene
        _draw_scene(axis, scenes[scene_index], phase)
        return ()

    animation = FuncAnimation(
        figure,
        update,
        frames=configuration.total_frames,
        interval=1000.0 / configuration.fps,
        blit=False,
        repeat=True,
    )
    try:
        animation.save(
            path,
            writer=PillowWriter(fps=configuration.fps),
            dpi=configuration.dpi,
            savefig_kwargs={"facecolor": "white", "edgecolor": "white"},
        )
    finally:
        plt.close(figure)


def _verify_animation_outputs(
    prepared: tuple[tuple[str, Path], ...],
    configuration: AnimationConfiguration,
) -> None:
    if tuple(filename for filename, _ in prepared) != ANIMATION_FILENAMES:
        raise ValueError("prepared animation names do not match frozen order")
    gif_path = prepared[0][1]
    storyboard_path = prepared[1][1]
    with Image.open(gif_path) as image:
        if image.size != (configuration.width_px, configuration.height_px):
            raise ValueError("animation dimensions are invalid")
        if image.n_frames != configuration.total_frames:
            raise ValueError("animation frame count is invalid")
        if image.info.get("loop") != 0:
            raise ValueError("animation loop setting is invalid")
    with Image.open(storyboard_path) as image:
        if image.size != STORYBOARD_DIMENSIONS:
            raise ValueError("storyboard dimensions are invalid")
        image.verify()
    total_bytes = sum(path.stat().st_size for _, path in prepared)
    if total_bytes > DEFAULT_CONFIGURATION.figure_size_budget_bytes:
        raise ValueError("optional animation exceeds the figure size budget")


def _replace_animation_path(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _unused_sibling(path: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".bak",
        dir=path.parent,
    )
    os.close(descriptor)
    sibling = Path(name)
    sibling.unlink()
    return sibling


def _restore_animation_transaction(
    installed: list[Path],
    backups: list[tuple[Path, Path]],
) -> None:
    rollback_errors: list[OSError] = []
    for destination in reversed(installed):
        try:
            if destination.exists():
                destination.unlink()
        except OSError as exc:
            rollback_errors.append(exc)
    for destination, backup in reversed(backups):
        try:
            if backup.exists():
                _replace_animation_path(backup, destination)
        except OSError as exc:
            rollback_errors.append(exc)
    if rollback_errors:
        raise RuntimeError("Task 4 animation rollback failed") from rollback_errors[0]


def _atomic_write_animation(
    output_directory: Path,
    writers: tuple[tuple[str, Callable[[Path], None]], ...],
    configuration: AnimationConfiguration,
) -> tuple[Path, ...]:
    if output_directory.exists() and not output_directory.is_dir():
        raise NotADirectoryError(
            f"output path is not a directory: {output_directory}"
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    destinations = tuple(output_directory / name for name, _ in writers)
    for destination in destinations:
        if destination.exists() and destination.is_dir():
            raise IsADirectoryError(
                f"animation destination is a directory: {destination}"
            )

    temporary_paths: list[Path] = []
    backups: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for filename, writer in writers:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{Path(filename).stem}.",
                suffix=Path(filename).suffix,
                dir=output_directory,
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_paths.append(temporary_path)
            writer(temporary_path)
            temporary_path.chmod(0o644)
        prepared = tuple(
            (filename, path)
            for (filename, _), path in zip(writers, temporary_paths)
        )
        _verify_animation_outputs(prepared, configuration)

        for destination in destinations:
            if destination.exists():
                backup = _unused_sibling(destination)
                _replace_animation_path(destination, backup)
                backups.append((destination, backup))
        for temporary_path, destination in zip(temporary_paths, destinations):
            _replace_animation_path(temporary_path, destination)
            installed.append(destination)
        return destinations
    except Exception:
        _restore_animation_transaction(installed, backups)
        raise
    finally:
        for path in temporary_paths:
            if path.exists():
                path.unlink()
        for _, backup in backups:
            if backup.exists():
                backup.unlink()


def write_task04_animation(
    study: Task04StudyResult,
    report: Task04ValidationReport,
    output_directory: str | os.PathLike[str] = DEFAULT_FIGURE_DIRECTORY,
    configuration: AnimationConfiguration = DEFAULT_ANIMATION_CONFIGURATION,
) -> Task04AnimationGenerationResult:
    """Write the validated GIF and storyboard in one rollback-safe transaction."""

    _require_validated(study, report)
    if not isinstance(configuration, AnimationConfiguration):
        raise TypeError("configuration must be an AnimationConfiguration")
    writers: tuple[tuple[str, Callable[[Path], None]], ...] = (
        (
            ANIMATION_FILENAMES[0],
            lambda path: _save_animation(
                study,
                report,
                path,
                configuration,
            ),
        ),
        (
            ANIMATION_FILENAMES[1],
            lambda path: _save_storyboard(study, report, path),
        ),
    )
    output_paths = _atomic_write_animation(
        Path(output_directory),
        writers,
        configuration,
    )
    return Task04AnimationGenerationResult(report, output_paths)


def main(argv: Sequence[str] | None = None) -> int:
    """Generate only the optional extension artifacts."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Generate the optional Task 4 photoelectric animation.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_FIGURE_DIRECTORY,
        help="destination directory for the GIF and storyboard PNG",
    )
    arguments = parser.parse_args(argv)
    study = build_task04_study()
    report = validate_task04(study)
    result = write_task04_animation(study, report, arguments.output_dir)
    print("Task 4 Stage 10: optional animation extension")
    for path in result.output_paths:
        print(path)
    print("Task 4 animation generation: PASS")
    return 0


__all__ = [
    "ANIMATION_FILENAMES",
    "AnimationConfiguration",
    "AnimationScene",
    "DEFAULT_ANIMATION_CONFIGURATION",
    "STORYBOARD_DIMENSIONS",
    "Task04AnimationGenerationResult",
    "build_animation_scenes",
    "create_photoelectric_storyboard",
    "main",
    "write_task04_animation",
]


if __name__ == "__main__":
    raise SystemExit(main())
