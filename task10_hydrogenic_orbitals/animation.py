"""Deterministic high-resolution view-rotation animation for Task 10."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.figure import Figure

from task10_hydrogenic_orbitals.analysis import build_radial_profile
from task10_hydrogenic_orbitals.configuration import (
    DEFAULT_CONFIGURATION,
    HydrogenicConfiguration,
    HydrogenicState,
)
from task10_hydrogenic_orbitals.models import orbital_summary, scaled_density_cartesian
from task10_hydrogenic_orbitals.plotting import (
    BLUE,
    GRID,
    NAVY,
    ORANGE,
    PALE,
    SLATE,
    TEAL,
    configure_plot_style,
    draw_coloured_glass,
)
from task10_hydrogenic_orbitals.validation import (
    Task10ValidationReport,
    task10_state_digest,
)


ANIMATION_FILENAME = "orbital_view_rotation.webp"
POSTER_FILENAME = "orbital_view_rotation_poster.png"
ANIMATION_TITLE = "BPhO Task 10 stationary hydrogen 3d orbital view rotation"
ANIMATION_XMP = (
    b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
    b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
    b'<dc:title><rdf:Alt><rdf:li xml:lang="x-default">'
    + ANIMATION_TITLE.encode("utf-8")
    + b'</rdf:li></rdf:Alt></dc:title>'
    b'<dc:description><rdf:Alt><rdf:li xml:lang="x-default">'
    b'Camera rotation around a stationary normalized probability density; not electron motion.'
    b'</rdf:li></rdf:Alt></dc:description>'
    b'</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>'
)


@dataclass
class Task10AnimationScene:
    """Complete fixed-scale scene and deterministic camera schedule."""

    figure: Figure
    state: HydrogenicState
    camera_azimuth_deg: np.ndarray
    camera_elevation_deg: np.ndarray
    update: Callable[[int], tuple[object, ...]]


def _require_validated(report: Task10ValidationReport) -> None:
    if not isinstance(report, Task10ValidationReport):
        raise TypeError("report must be a Task10ValidationReport")
    if not report.passed:
        raise RuntimeError("animation requires a passing Task 10 scientific report")
    if report.state_digest != task10_state_digest():
        raise ValueError("validation report belongs to a different Task 10 state")


def _integer(value: int, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return normalized


def build_task10_animation_scene(
    report: Task10ValidationReport,
    *,
    state: HydrogenicState = HydrogenicState(3, 2, 0),
    threshold: float = DEFAULT_CONFIGURATION.display_threshold,
    frame_count: int = DEFAULT_CONFIGURATION.animation_frame_count,
    width_px: int = DEFAULT_CONFIGURATION.animation_width_px,
    height_px: int = DEFAULT_CONFIGURATION.animation_height_px,
    dpi: int = DEFAULT_CONFIGURATION.animation_dpi,
    resolution: int = 61,
    slice_count: int = DEFAULT_CONFIGURATION.slice_count,
) -> Task10AnimationScene:
    """Build the complete animation scene without encoding it."""

    _require_validated(report)
    if not isinstance(state, HydrogenicState):
        raise TypeError("state must be HydrogenicState")
    frame_count = _integer(frame_count, name="frame_count", minimum=8)
    width_px = _integer(width_px, name="width_px", minimum=640)
    height_px = _integer(height_px, name="height_px", minimum=360)
    dpi = _integer(dpi, name="dpi", minimum=72)
    resolution = _integer(resolution, name="resolution", minimum=31)
    slice_count = _integer(slice_count, name="slice_count", minimum=7)
    if width_px * 9 != height_px * 16:
        raise ValueError("animation dimensions must have an exact 16:9 ratio")
    if resolution % 2 == 0:
        raise ValueError("resolution must be odd")
    if slice_count % 2 == 0:
        raise ValueError("slice_count must be odd")
    if not np.isfinite(threshold) or not 0.0 <= threshold < 1.0:
        raise ValueError("threshold must be finite and in [0, 1)")

    phase = np.arange(frame_count, dtype=float) / frame_count
    camera_azimuth = -54.0 + 360.0 * phase
    camera_elevation = 24.0 + 5.0 * np.sin(2.0 * np.pi * phase)
    camera_azimuth.setflags(write=False)
    camera_elevation.setflags(write=False)

    configure_plot_style()
    figure = plt.figure(
        figsize=(width_px / dpi, height_px / dpi),
        dpi=dpi,
        facecolor="white",
    )
    figure.text(
        0.04,
        0.955,
        "Hydrogenic orbital · stationary probability density",
        fontsize=24,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    summary = orbital_summary(state)
    figure.text(
        0.04,
        0.905,
        f"Hydrogen {state.label} · normalized real tesseral state · E = {summary.energy_ev:.6f} eV · "
        f"threshold = {threshold:.2f} · coordinates in n²a",
        fontsize=11.5,
        color=SLATE,
        ha="left",
        va="top",
    )
    figure.text(
        0.955,
        0.945,
        f"22/22 SCIENCE CHECKS · {width_px}×{height_px}",
        fontsize=9.5,
        fontweight="bold",
        color=TEAL,
        ha="right",
        va="top",
        fontstyle="italic",
    )

    glass_axis = figure.add_axes((0.025, 0.105, 0.61, 0.73), projection="3d")
    x, y, z_values, relative = draw_coloured_glass(
        glass_axis,
        state,
        threshold=float(threshold),
        resolution=resolution,
        slice_count=slice_count,
    )
    glass_axis.set_title(
        f"(a) Semi-transparent coloured glass · {slice_count} x-y planes",
        loc="left",
        fontsize=13,
        pad=10,
    )
    glass_axis.tick_params(labelsize=8, pad=0)

    extent = float(np.max(np.abs(x)))
    central_density = relative[slice_count // 2]
    xy_axis = figure.add_axes((0.65, 0.55, 0.14, 0.265))
    xy_image = xy_axis.imshow(
        central_density,
        origin="lower",
        extent=(-extent, extent, -extent, extent),
        cmap="magma",
        vmin=0.0,
        vmax=1.0,
        interpolation="bilinear",
        rasterized=True,
    )
    xy_axis.contour(x, y, central_density, levels=(threshold,), colors=("white",), linewidths=1.1)
    xy_axis.set_title("(b) x-y at z = 0", loc="left", fontsize=10.5)
    xy_axis.set(xlabel="x/(n²a)", ylabel="y/(n²a)")
    xy_axis.grid(False)

    coordinate = np.linspace(-extent, extent, resolution)
    x_grid, z_grid = np.meshgrid(coordinate, coordinate, indexing="xy")
    xz_density = np.array(
        scaled_density_cartesian(
            state,
            state.n**2 * x_grid,
            np.zeros_like(x_grid),
            state.n**2 * z_grid,
        ),
        dtype=float,
        copy=True,
    )
    xz_density /= float(np.max(xz_density))
    xz_axis = figure.add_axes((0.81, 0.55, 0.14, 0.265))
    xz_axis.imshow(
        xz_density,
        origin="lower",
        extent=(-extent, extent, -extent, extent),
        cmap="magma",
        vmin=0.0,
        vmax=1.0,
        interpolation="bilinear",
        rasterized=True,
    )
    xz_axis.contour(x_grid, z_grid, xz_density, levels=(threshold,), colors=("white",), linewidths=1.1)
    xz_axis.set_title("(c) x-z at y = 0", loc="left", fontsize=10.5)
    xz_axis.set(xlabel="x/(n²a)", ylabel="z/(n²a)")
    xz_axis.grid(False)
    colour_axis = figure.add_axes((0.963, 0.55, 0.008, 0.265))
    colourbar = figure.colorbar(xy_image, cax=colour_axis, orientation="vertical")
    colourbar.set_ticks((0.0, 0.5, 1.0))
    colourbar.set_label("relative |ψ|² / max |ψ|²", fontsize=8)
    colourbar.ax.tick_params(labelsize=7)

    profile = build_radial_profile(state)
    radial_axis = figure.add_axes((0.67, 0.16, 0.29, 0.25))
    probability_per_scaled_radius = profile.scaled_radial_probability * state.n**2
    radial_axis.plot(
        profile.radius_over_n_squared_a,
        probability_per_scaled_radius,
        color=BLUE,
        linewidth=3.0,
    )
    radial_axis.fill_between(
        profile.radius_over_n_squared_a,
        probability_per_scaled_radius,
        color=BLUE,
        alpha=0.10,
    )
    peak_index = int(np.argmax(probability_per_scaled_radius))
    radial_axis.scatter(
        [profile.radius_over_n_squared_a[peak_index]],
        [probability_per_scaled_radius[peak_index]],
        s=55,
        color=ORANGE,
        edgecolor="white",
        linewidth=1.2,
        zorder=4,
    )
    radial_axis.set_title("(d) Normalized radial probability", loc="left", fontsize=11)
    radial_axis.set(
        xlabel="scaled radius, r/(n²a)",
        ylabel="probability per d[r/(n²a)]",
        xlim=(0.0, float(profile.radius_over_n_squared_a[-1])),
        ylim=(0.0, 1.08 * float(np.max(probability_per_scaled_radius))),
    )
    radial_axis.grid(True, color=GRID)
    radial_axis.spines["top"].set_visible(False)
    radial_axis.spines["right"].set_visible(False)

    figure.text(
        0.67,
        0.445,
        "0 radial nodes · 2 angular nodes\n"
        "bright regions are more probable, not trajectories",
        fontsize=9.2,
        color=NAVY,
        ha="left",
        va="top",
        linespacing=1.4,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": PALE,
            "edgecolor": "#CBD6E4",
        },
    )
    status = figure.text(
        0.955,
        0.085,
        "",
        ha="right",
        va="bottom",
        color=TEAL,
        fontsize=9.5,
        fontweight="bold",
    )
    figure.text(
        0.04,
        0.045,
        "VIEW ROTATION ONLY — the normalized state is stationary; camera motion is not electron motion or time evolution.",
        fontsize=9.5,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="bottom",
    )
    figure.text(
        0.04,
        0.018,
        "The 0.15 display cutoff changes visibility only. The complete unthresholded field remains normalized: ∫|ψ|²dV = 1.",
        fontsize=8.3,
        color=SLATE,
        ha="left",
        va="bottom",
    )

    def update(frame_number: int) -> tuple[object, ...]:
        frame = int(frame_number)
        if frame < 0 or frame >= frame_count:
            raise IndexError("animation frame is outside the frozen schedule")
        glass_axis.view_init(
            elev=float(camera_elevation[frame]),
            azim=float(camera_azimuth[frame]),
        )
        rotation = (360.0 * frame / frame_count) % 360.0
        status.set_text(
            f"camera azimuth {rotation:05.1f}° · frame {frame + 1:02d}/{frame_count:02d} · seamless loop"
        )
        return glass_axis, status

    update(0)
    return Task10AnimationScene(
        figure=figure,
        state=state,
        camera_azimuth_deg=camera_azimuth,
        camera_elevation_deg=camera_elevation,
        update=update,
    )


def render_scene_frame(scene: Task10AnimationScene, frame_number: int) -> Image.Image:
    """Render one opaque RGB frame at the scene's exact pixel dimensions."""

    if not isinstance(scene, Task10AnimationScene):
        raise TypeError("scene must be Task10AnimationScene")
    scene.update(frame_number)
    scene.figure.canvas.draw()
    width, height = scene.figure.canvas.get_width_height()
    rgba = np.asarray(scene.figure.canvas.buffer_rgba(), dtype=np.uint8)
    if rgba.shape != (height, width, 4):
        raise RuntimeError("Matplotlib returned an unexpected animation buffer")
    return Image.fromarray(rgba[..., :3].copy())


class _StreamingFrameSequence:
    """Pillow-compatible lazy frame sequence that retains only one 4K frame."""

    def __init__(self, scene: Task10AnimationScene, first_frame_number: int, count: int):
        self.scene = scene
        self.first_frame_number = first_frame_number
        self.n_frames = count
        self._index = -1
        self._image: Image.Image | None = None

    def tell(self) -> int:
        return max(0, self._index)

    def seek(self, index: int) -> None:
        if not 0 <= index < self.n_frames:
            raise EOFError("animation frame is outside the lazy sequence")
        if index != self._index:
            self._image = render_scene_frame(self.scene, self.first_frame_number + index)
            self._index = index

    @property
    def mode(self) -> str:
        if self._image is None:
            self.seek(0)
        assert self._image is not None
        return self._image.mode

    @property
    def has_transparency_data(self) -> bool:
        return False

    def convert(self, mode: str) -> Image.Image:
        if self._image is None:
            self.seek(0)
        assert self._image is not None
        return self._image.convert(mode)

    def getim(self):  # Pillow's encoder consumes the internal imaging core.
        if self._image is None:
            self.seek(0)
        assert self._image is not None
        return self._image.getim()


def verify_task10_animation(
    path: Path,
    *,
    width_px: int,
    height_px: int,
    frame_count: int,
    frame_duration_ms: int,
    size_budget_bytes: int,
) -> dict[str, float | int | str | bool]:
    """Verify dimensions, timing, loop, metadata, budget and frame integrity."""

    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("animation file is missing or empty")
    if path.stat().st_size > size_budget_bytes:
        raise ValueError("animation exceeds its size budget")
    sampled = []
    with Image.open(path) as image:
        if image.format != "WEBP":
            raise ValueError("animation output must be WebP")
        if image.size != (width_px, height_px):
            raise ValueError("animation dimensions are invalid")
        if image.n_frames != frame_count:
            raise ValueError("animation frame count is invalid")
        if image.info.get("loop") != 0:
            raise ValueError("animation must loop continuously")
        xmp = image.info.get("xmp", b"")
        if ANIMATION_TITLE.encode("utf-8") not in xmp:
            raise ValueError("animation title metadata is missing")
        durations = []
        sample_indices = sorted({0, frame_count // 4, frame_count // 2, 3 * frame_count // 4, frame_count - 1})
        for frame_index in range(frame_count):
            image.seek(frame_index)
            image.load()
            durations.append(int(image.info.get("duration", 0)))
            if frame_index in sample_indices:
                frame = image.convert("RGB")
                thumbnail = np.asarray(frame.resize((160, 90), Image.Resampling.LANCZOS), dtype=np.int16)
                if float(np.mean(np.all(thumbnail <= 4, axis=2))) > 0.20:
                    raise ValueError(f"animation frame {frame_index} contains a black disposal artifact")
                sampled.append(thumbnail)
        if any(duration != frame_duration_ms for duration in durations):
            raise ValueError("animation frame timing is inconsistent")
    differences = [float(np.mean(np.abs(sampled[index] - sampled[0]))) for index in range(1, len(sampled))]
    if min(differences[:-1]) <= 0.4:
        raise ValueError("sampled view-rotation frames are visually indistinguishable")
    return {
        "format": "WEBP",
        "width_px": width_px,
        "height_px": height_px,
        "frame_count": frame_count,
        "frame_duration_ms": frame_duration_ms,
        "duration_ms": frame_count * frame_duration_ms,
        "continuous_loop": True,
        "bytes": path.stat().st_size,
        "minimum_sampled_frame_difference": min(differences[:-1]),
    }


def write_task10_animation(
    report: Task10ValidationReport,
    output_path: Path,
    *,
    poster_path: Path | None = None,
    configuration: HydrogenicConfiguration = DEFAULT_CONFIGURATION,
    frame_count: int | None = None,
    frames_per_second: int | None = None,
    width_px: int | None = None,
    height_px: int | None = None,
    dpi: int | None = None,
    quality: int | None = None,
    resolution: int = 61,
    slice_count: int | None = None,
) -> tuple[Path, Path | None, dict[str, float | int | str | bool]]:
    """Build, atomically save and verify the Task 10 animated WebP."""

    if not isinstance(configuration, HydrogenicConfiguration):
        raise TypeError("configuration must be HydrogenicConfiguration")
    output = Path(output_path)
    if output.suffix.lower() != ".webp":
        raise ValueError("animation output path must end in .webp")
    resolved_frame_count = configuration.animation_frame_count if frame_count is None else _integer(frame_count, name="frame_count", minimum=8)
    resolved_fps = configuration.animation_frames_per_second if frames_per_second is None else _integer(frames_per_second, name="frames_per_second", minimum=1)
    resolved_width = configuration.animation_width_px if width_px is None else _integer(width_px, name="width_px", minimum=640)
    resolved_height = configuration.animation_height_px if height_px is None else _integer(height_px, name="height_px", minimum=360)
    resolved_dpi = configuration.animation_dpi if dpi is None else _integer(dpi, name="dpi", minimum=72)
    resolved_quality = configuration.animation_quality if quality is None else _integer(quality, name="quality", minimum=1)
    resolved_slice_count = configuration.slice_count if slice_count is None else _integer(slice_count, name="slice_count", minimum=7)
    if resolved_quality > 100:
        raise ValueError("quality must not exceed 100")
    if 1000 % resolved_fps != 0:
        raise ValueError("frames_per_second must divide 1000 for exact millisecond timing")
    frame_duration_ms = 1000 // resolved_fps
    scene = build_task10_animation_scene(
        report,
        frame_count=resolved_frame_count,
        width_px=resolved_width,
        height_px=resolved_height,
        dpi=resolved_dpi,
        resolution=resolution,
        slice_count=resolved_slice_count,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    temporary_poster: Path | None = None
    resolved_poster = Path(poster_path) if poster_path is not None else None
    try:
        first_frame = render_scene_frame(scene, 0)
        if first_frame.size != (resolved_width, resolved_height):
            raise RuntimeError("animation renderer did not produce the requested dimensions")
        if resolved_poster is not None:
            if resolved_poster.suffix.lower() != ".png":
                raise ValueError("poster path must end in .png")
            resolved_poster.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                prefix=f".{resolved_poster.stem}-",
                suffix=".png",
                dir=resolved_poster.parent,
                delete=False,
            ) as temporary:
                temporary_poster = Path(temporary.name)
            first_frame.save(
                temporary_poster,
                format="PNG",
                dpi=(resolved_dpi, resolved_dpi),
                compress_level=9,
                optimize=False,
            )
        with tempfile.NamedTemporaryFile(
            prefix=f".{output.stem}-",
            suffix=".webp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        sequence = _StreamingFrameSequence(scene, 1, resolved_frame_count - 1)
        first_frame.save(
            temporary_path,
            format="WEBP",
            save_all=True,
            append_images=[sequence],
            duration=frame_duration_ms,
            loop=0,
            background=(255, 255, 255, 255),
            lossless=False,
            quality=resolved_quality,
            method=6,
            minimize_size=True,
            allow_mixed=False,
            xmp=ANIMATION_XMP,
        )
        evidence = verify_task10_animation(
            temporary_path,
            width_px=resolved_width,
            height_px=resolved_height,
            frame_count=resolved_frame_count,
            frame_duration_ms=frame_duration_ms,
            size_budget_bytes=configuration.animation_size_budget_bytes,
        )
        os.replace(temporary_path, output)
        output.chmod(0o644)
        temporary_path = None
        if resolved_poster is not None and temporary_poster is not None:
            os.replace(temporary_poster, resolved_poster)
            resolved_poster.chmod(0o644)
            temporary_poster = None
        return output, resolved_poster, evidence
    finally:
        plt.close(scene.figure)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        if temporary_poster is not None:
            temporary_poster.unlink(missing_ok=True)


__all__ = [
    "ANIMATION_FILENAME",
    "POSTER_FILENAME",
    "Task10AnimationScene",
    "build_task10_animation_scene",
    "render_scene_frame",
    "verify_task10_animation",
    "write_task10_animation",
]
