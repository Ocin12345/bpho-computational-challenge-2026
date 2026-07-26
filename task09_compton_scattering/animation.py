"""Deterministic high-resolution Compton angle-sweep animation for Task 9."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyArrowPatch
from PIL import Image

from task09_compton_scattering.analysis import Task09StudyResult
from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.plotting import (
    ELECTRON,
    GRID,
    MUTED,
    PHOTON,
    PLOT_STYLE,
    TEXT,
    _require_figure_font,
)
from task09_compton_scattering.validation import (
    Task09ValidationReport,
    task09_study_digest,
)


ANIMATION_FILENAME = "compton_angle_sweep.gif"


class _FullFramePillowWriter(PillowWriter):
    """Write opaque full frames to avoid browser-dependent GIF disposal artifacts."""

    def finish(self) -> None:
        frames = [frame.convert("RGB") for frame in self._frames]
        frames[0].save(
            self.outfile,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / self.fps),
            loop=0,
            optimize=False,
            disposal=1,
        )


@dataclass
class Task09AnimationScene:
    """Built animation plus explicit frame schedule and renderer."""

    figure: Figure
    animation: FuncAnimation
    frame_indices: np.ndarray
    update: Callable[[int], tuple[object, ...]]


def _require_validated(
    study: Task09StudyResult,
    report: Task09ValidationReport,
) -> None:
    if not isinstance(study, Task09StudyResult):
        raise TypeError("study must be a Task09StudyResult")
    if not isinstance(report, Task09ValidationReport):
        raise TypeError("report must be a Task09ValidationReport")
    if not report.passed:
        raise RuntimeError("animation requires a passing Task 9 kinematic report")
    if report.study_digest != task09_study_digest(study):
        raise ValueError("validation report belongs to a different Task 9 study")


def _integer(value: int, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return normalized


def build_task09_animation_scene(
    study: Task09StudyResult,
    report: Task09ValidationReport,
    *,
    energy_kev: float = 200.0,
    frame_count: int = DEFAULT_CONFIGURATION.animation_frame_count,
    frames_per_second: int = DEFAULT_CONFIGURATION.animation_frames_per_second,
    width_px: int = DEFAULT_CONFIGURATION.animation_width_px,
    height_px: int = DEFAULT_CONFIGURATION.animation_height_px,
    dpi: int = DEFAULT_CONFIGURATION.animation_dpi,
) -> Task09AnimationScene:
    """Build the complete fixed-scale animation without saving it."""

    _require_validated(study, report)
    frame_count = _integer(frame_count, name="frame_count", minimum=3)
    frames_per_second = _integer(
        frames_per_second, name="frames_per_second", minimum=1
    )
    width_px = _integer(width_px, name="width_px", minimum=320)
    height_px = _integer(height_px, name="height_px", minimum=180)
    dpi = _integer(dpi, name="dpi", minimum=50)
    if width_px * 9 != height_px * 16:
        raise ValueError("animation dimensions must have an exact 16:9 ratio")
    if frame_count > study.angle_count:
        raise ValueError("frame_count cannot exceed the validated angle grid")
    if not np.isfinite(energy_kev):
        raise ValueError("energy_kev must be finite")
    energy_matches = np.flatnonzero(
        np.isclose(study.incident_energies_kev, float(energy_kev), atol=1.0e-12)
    )
    if energy_matches.size != 1:
        raise ValueError("energy_kev must be one official incident energy")
    _require_figure_font()
    energy_index = int(energy_matches[0])
    frame_indices = np.rint(
        np.linspace(0, study.angle_count - 1, frame_count)
    ).astype(np.int64)
    if np.unique(frame_indices).size != frame_count:
        raise ValueError("animation schedule contains duplicate grid frames")
    frame_indices.setflags(write=False)

    with plt.rc_context(PLOT_STYLE):
        figure = plt.figure(
            figsize=(width_px / dpi, height_px / dpi),
            dpi=dpi,
            facecolor="white",
        )
        grid = figure.add_gridspec(
            3,
            2,
            left=0.055,
            right=0.97,
            bottom=0.10,
            top=0.82,
            hspace=0.52,
            wspace=0.28,
            width_ratios=(1.15, 1.0),
        )
        collision_axis = figure.add_subplot(grid[:, 0])
        shift_axis = figure.add_subplot(grid[0, 1])
        beta_axis = figure.add_subplot(grid[1, 1])
        phi_axis = figure.add_subplot(grid[2, 1])

        collision_axis.axhline(
            0.0,
            color="#9AAEC3",
            linewidth=1.0,
            linestyle=(0, (4, 4)),
        )
        incident_arrow = FancyArrowPatch(
            (-1.0, 0.0),
            (0.0, 0.0),
            arrowstyle="-|>",
            mutation_scale=20,
            linewidth=4.0,
            color=PHOTON,
        )
        scattered_arrow = FancyArrowPatch(
            (0.0, 0.0),
            (1.0, 0.0),
            arrowstyle="-|>",
            mutation_scale=20,
            linewidth=4.0,
            color=PHOTON,
        )
        electron_arrow = FancyArrowPatch(
            (0.0, 0.0),
            (0.0, 0.0),
            arrowstyle="-|>",
            mutation_scale=20,
            linewidth=4.0,
            color=ELECTRON,
        )
        collision_axis.add_patch(incident_arrow)
        collision_axis.add_patch(scattered_arrow)
        collision_axis.add_patch(electron_arrow)
        collision_axis.add_patch(
            Circle(
                (0.0, 0.0),
                0.055,
                facecolor="white",
                edgecolor=TEXT,
                linewidth=2.0,
                zorder=5,
            )
        )
        collision_axis.text(
            -0.98,
            0.09,
            "incident photon · E",
            color=PHOTON,
            fontsize=10,
            weight="bold",
        )
        scattered_label = collision_axis.text(
            0.9,
            0.12,
            "scattered photon · E′",
            color=PHOTON,
            fontsize=9.2,
            weight="bold",
            ha="center",
        )
        electron_label = collision_axis.text(
            0.55,
            -0.5,
            "recoil electron · pₑ",
            color=ELECTRON,
            fontsize=9.2,
            weight="bold",
            ha="center",
        )
        geometry_title = collision_axis.set_title(
            "Momentum-vector geometry",
            loc="left",
            fontsize=13,
            fontweight="bold",
            color=TEXT,
            pad=10,
        )
        collision_axis.set(
            xlim=(-1.18, 1.62),
            ylim=(-1.12, 1.12),
            aspect="equal",
        )
        collision_axis.set_xticks([])
        collision_axis.set_yticks([])
        for spine in collision_axis.spines.values():
            spine.set_visible(False)

        theta = study.theta_axis_deg
        plot_specs = (
            (
                shift_axis,
                study.fractional_wavelength_shift[energy_index],
                "(a) Fractional wavelength shift",
                "Δλ / λ",
                (0.0, 0.84),
            ),
            (
                beta_axis,
                study.electron_beta[energy_index],
                "(b) Electron recoil speed",
                "v / c",
                (0.0, 0.56),
            ),
            (
                phi_axis,
                study.electron_recoil_angle_deg[energy_index],
                "(c) Electron recoil angle",
                "φ (°)",
                (0.0, 92.0),
            ),
        )
        markers = []
        guides = []
        for axis, values, title, ylabel, limits in plot_specs:
            axis.plot(theta, values, color=PHOTON, linewidth=2.8)
            guide = axis.axvline(
                0.0,
                color="#667B94",
                linewidth=1.3,
                linestyle=(0, (3, 4)),
            )
            (marker,) = axis.plot(
                [0.0],
                [values[0]],
                marker="o",
                markersize=7,
                markerfacecolor="white",
                markeredgecolor=TEXT,
                markeredgewidth=1.8,
                linestyle="none",
                zorder=5,
            )
            axis.set(
                title=title,
                ylabel=ylabel,
                xlim=(0.0, 180.0),
                ylim=limits,
                xticks=(0, 45, 90, 135, 180),
            )
            axis.grid(True, color=GRID)
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            markers.append(marker)
            guides.append(guide)
        shift_axis.tick_params(labelbottom=False)
        beta_axis.tick_params(labelbottom=False)
        phi_axis.set_xlabel("Photon scattering angle, θ (°)")

        figure.suptitle(
            "Compton angle sweep",
            x=0.055,
            y=0.955,
            ha="left",
            fontsize=19,
            fontweight="bold",
            color=TEXT,
        )
        figure.text(
            0.055,
            0.89,
            f"Exact {energy_kev:g} keV relativistic collision · all axes fixed · arrows share the incident-photon momentum scale",
            color=MUTED,
            fontsize=9.6,
        )
        status = figure.text(
            0.97,
            0.94,
            "",
            ha="right",
            va="center",
            color="#0F7866",
            fontsize=9.0,
            fontstyle="italic",
        )
        figure.text(
            0.055,
            0.035,
            "At θ = 0° the electron momentum is zero and φ is undefined; the plotted 90° point is the continuous limit.",
            color=MUTED,
            fontsize=8.2,
        )

        def update(frame_number: int) -> tuple[object, ...]:
            frame = int(frame_number)
            if frame < 0 or frame >= frame_count:
                raise IndexError("animation frame is outside the frozen schedule")
            index = int(frame_indices[frame])
            angle = float(study.theta_axis_deg[index])
            angle_rad = np.radians(angle)
            scattered_energy = float(study.scattered_energy_kev[energy_index, index])
            ratio = scattered_energy / float(energy_kev)
            photon_end = (ratio * np.cos(angle_rad), ratio * np.sin(angle_rad))
            electron_end = (1.0 - photon_end[0], -photon_end[1])
            scattered_arrow.set_positions((0.0, 0.0), photon_end)
            electron_arrow.set_positions((0.0, 0.0), electron_end)
            electron_arrow.set_alpha(0.28 if index == 0 else 1.0)
            label_y = 0.28 if angle >= 150.0 else photon_end[1] + 0.14
            scattered_label.set_position((photon_end[0], label_y))
            electron_label.set_position((electron_end[0], electron_end[1] - 0.12))
            electron_label.set_text(
                "recoil electron · pₑ = 0"
                if index == 0
                else "recoil electron · pₑ"
            )
            geometry_title.set_text(
                f"Momentum-vector geometry · θ = {angle:.1f}°"
            )
            values = (
                float(study.fractional_wavelength_shift[energy_index, index]),
                float(study.electron_beta[energy_index, index]),
                float(study.electron_recoil_angle_deg[energy_index, index]),
            )
            for marker, guide, value in zip(markers, guides, values):
                marker.set_data([angle], [value])
                guide.set_xdata([angle, angle])
            recoil_text = (
                "undefined (90° limit)"
                if index == 0
                else f"{values[2]:.2f}°"
            )
            status.set_text(
                f"θ {angle:5.1f}°   ·   Δλ/λ {values[0]:.4f}   ·   v/c {values[1]:.4f}   ·   φ {recoil_text}"
            )
            return (
                scattered_arrow,
                electron_arrow,
                scattered_label,
                electron_label,
                geometry_title,
                status,
                *markers,
                *guides,
            )

        animation = FuncAnimation(
            figure,
            update,
            frames=frame_count,
            interval=1000.0 / frames_per_second,
            blit=False,
            repeat=True,
        )
        update(0)
    return Task09AnimationScene(
        figure=figure,
        animation=animation,
        frame_indices=frame_indices,
        update=update,
    )


def _verify_animation(
    path: Path,
    *,
    width_px: int,
    height_px: int,
    frame_count: int,
    size_budget_bytes: int,
) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("animation file is missing or empty")
    if path.stat().st_size > size_budget_bytes:
        raise ValueError("animation exceeds its size budget")
    with Image.open(path) as image:
        if image.format != "GIF":
            raise ValueError("animation output must be GIF")
        if image.size != (width_px, height_px):
            raise ValueError("animation dimensions are invalid")
        if image.n_frames != frame_count:
            raise ValueError("animation frame count is invalid")
        if image.info.get("loop") != 0:
            raise ValueError("animation must loop continuously")
        for frame_index in range(image.n_frames):
            image.seek(frame_index)
            rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
            black_fraction = float(np.mean(np.all(rgb <= 4, axis=2)))
            if black_fraction > 0.001:
                raise ValueError(
                    f"animation frame {frame_index} contains a black disposal artifact"
                )


def write_task09_animation(
    study: Task09StudyResult,
    report: Task09ValidationReport,
    output_path: Path,
    *,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
    energy_kev: float = 200.0,
    frame_count: int | None = None,
    frames_per_second: int | None = None,
    width_px: int | None = None,
    height_px: int | None = None,
    dpi: int | None = None,
) -> Path:
    """Build, atomically save and verify the Task 9 animation."""

    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    output = Path(output_path)
    if output.suffix.lower() != ".gif":
        raise ValueError("animation output path must end in .gif")
    resolved_frame_count = (
        configuration.animation_frame_count if frame_count is None else frame_count
    )
    resolved_fps = (
        configuration.animation_frames_per_second
        if frames_per_second is None
        else frames_per_second
    )
    resolved_width = (
        configuration.animation_width_px if width_px is None else width_px
    )
    resolved_height = (
        configuration.animation_height_px if height_px is None else height_px
    )
    resolved_dpi = configuration.animation_dpi if dpi is None else dpi
    scene = build_task09_animation_scene(
        study,
        report,
        energy_kev=energy_kev,
        frame_count=resolved_frame_count,
        frames_per_second=resolved_fps,
        width_px=resolved_width,
        height_px=resolved_height,
        dpi=resolved_dpi,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output.stem}-",
            suffix=".gif",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        scene.animation.save(
            temporary_path,
            writer=_FullFramePillowWriter(
                fps=int(resolved_fps),
                metadata={"title": "BPhO Task 9 Compton angle sweep"},
            ),
            dpi=int(resolved_dpi),
        )
        _verify_animation(
            temporary_path,
            width_px=int(resolved_width),
            height_px=int(resolved_height),
            frame_count=int(resolved_frame_count),
            size_budget_bytes=configuration.evidence_size_budget_bytes,
        )
        os.replace(temporary_path, output)
        output.chmod(0o644)
        temporary_path = None
    finally:
        plt.close(scene.figure)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return output


def main(argv: list[str] | None = None) -> int:
    import argparse

    from task09_compton_scattering.analysis import build_task09_study
    from task09_compton_scattering.validation import validate_task09

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("figures/task09") / ANIMATION_FILENAME,
    )
    arguments = parser.parse_args(argv)
    study = build_task09_study()
    report = validate_task09(study)
    path = write_task09_animation(study, report, arguments.output)
    print(
        f"Task 9 animation generated: {path} "
        f"({DEFAULT_CONFIGURATION.animation_width_px}x{DEFAULT_CONFIGURATION.animation_height_px}, "
        f"{DEFAULT_CONFIGURATION.animation_frame_count} frames at "
        f"{DEFAULT_CONFIGURATION.animation_frames_per_second} fps)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ANIMATION_FILENAME",
    "Task09AnimationScene",
    "build_task09_animation_scene",
    "write_task09_animation",
]
