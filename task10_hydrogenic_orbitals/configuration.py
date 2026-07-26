"""Immutable state and rendering configuration for Task 10."""

from __future__ import annotations

from dataclasses import dataclass


ORBITAL_FAMILY_LABELS = ("S", "P", "D", "F", "G", "H", "I", "K")
MAXIMUM_N = 8
MAXIMUM_ATOMIC_NUMBER = 20
MAXIMUM_MASS_TO_CHARGE_RATIO = 3


def _require_integer(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


@dataclass(frozen=True)
class HydrogenicState:
    """One normalized real hydrogenic basis state."""

    n: int
    l: int
    m: int
    atomic_number: int = 1
    mass_number: int = 1

    def __post_init__(self) -> None:
        n = _require_integer("n", self.n)
        l = _require_integer("l", self.l)
        m = _require_integer("m", self.m)
        atomic_number = _require_integer("atomic_number", self.atomic_number)
        mass_number = _require_integer("mass_number", self.mass_number)

        if not 1 <= n <= MAXIMUM_N:
            raise ValueError(f"n must be in [1, {MAXIMUM_N}]")
        if not 0 <= l < n:
            raise ValueError("l must satisfy 0 <= l < n")
        if not -l <= m <= l:
            raise ValueError("m must satisfy -l <= m <= l")
        if not 1 <= atomic_number <= MAXIMUM_ATOMIC_NUMBER:
            raise ValueError(
                f"atomic_number must be in [1, {MAXIMUM_ATOMIC_NUMBER}]"
            )
        if not atomic_number <= mass_number:
            raise ValueError("mass_number must be at least atomic_number")
        if mass_number > MAXIMUM_MASS_TO_CHARGE_RATIO * atomic_number:
            raise ValueError(
                "mass_number must not exceed three times atomic_number"
            )

    @property
    def family(self) -> str:
        return ORBITAL_FAMILY_LABELS[self.l]

    @property
    def label(self) -> str:
        return f"{self.n}{self.family.lower()} (m={self.m:+d})"

    @property
    def radial_node_count(self) -> int:
        return self.n - self.l - 1

    @property
    def angular_node_count(self) -> int:
        return self.l


@dataclass(frozen=True)
class HydrogenicConfiguration:
    """Frozen numerical and visual domain."""

    maximum_n: int = MAXIMUM_N
    maximum_atomic_number: int = MAXIMUM_ATOMIC_NUMBER
    display_threshold: float = 0.15
    probability_containment: float = 0.9995
    radial_profile_points: int = 2001
    slice_resolution: int = 161
    slice_count: int = 17
    animation_width_px: int = 3840
    animation_height_px: int = 2160
    animation_dpi: int = 240
    animation_frames_per_second: int = 20
    animation_frame_count: int = 80
    animation_quality: int = 93
    animation_size_budget_bytes: int = 100 * 1024 * 1024

    def __post_init__(self) -> None:
        maximum_n = _require_integer("maximum_n", self.maximum_n)
        maximum_atomic_number = _require_integer(
            "maximum_atomic_number", self.maximum_atomic_number
        )
        radial_profile_points = _require_integer(
            "radial_profile_points", self.radial_profile_points
        )
        slice_resolution = _require_integer("slice_resolution", self.slice_resolution)
        slice_count = _require_integer("slice_count", self.slice_count)
        animation_width_px = _require_integer(
            "animation_width_px", self.animation_width_px
        )
        animation_height_px = _require_integer(
            "animation_height_px", self.animation_height_px
        )
        animation_dpi = _require_integer("animation_dpi", self.animation_dpi)
        animation_frames_per_second = _require_integer(
            "animation_frames_per_second", self.animation_frames_per_second
        )
        animation_frame_count = _require_integer(
            "animation_frame_count", self.animation_frame_count
        )
        animation_quality = _require_integer(
            "animation_quality", self.animation_quality
        )
        animation_size_budget_bytes = _require_integer(
            "animation_size_budget_bytes", self.animation_size_budget_bytes
        )

        if not 1 <= maximum_n <= MAXIMUM_N:
            raise ValueError(f"maximum_n must be in [1, {MAXIMUM_N}]")
        if not 1 <= maximum_atomic_number <= MAXIMUM_ATOMIC_NUMBER:
            raise ValueError(
                "maximum_atomic_number must be in "
                f"[1, {MAXIMUM_ATOMIC_NUMBER}]"
            )
        if not 0.0 <= self.display_threshold < 1.0:
            raise ValueError("display_threshold must be in [0, 1)")
        if not 0.99 <= self.probability_containment < 1.0:
            raise ValueError("probability_containment must be in [0.99, 1)")
        if radial_profile_points < 501 or radial_profile_points % 2 == 0:
            raise ValueError("radial_profile_points must be odd and at least 501")
        if slice_resolution < 81 or slice_resolution % 2 == 0:
            raise ValueError("slice_resolution must be odd and at least 81")
        if slice_count < 7 or slice_count % 2 == 0:
            raise ValueError("slice_count must be odd and at least 7")
        if animation_width_px < 640 or animation_height_px < 360:
            raise ValueError("animation dimensions must be at least 640x360")
        if animation_width_px * 9 != animation_height_px * 16:
            raise ValueError("animation dimensions must have an exact 16:9 ratio")
        if animation_dpi < 72:
            raise ValueError("animation_dpi must be at least 72")
        if animation_frames_per_second < 1:
            raise ValueError("animation_frames_per_second must be positive")
        if animation_frame_count < 8:
            raise ValueError("animation_frame_count must be at least eight")
        if not 1 <= animation_quality <= 100:
            raise ValueError("animation_quality must be in [1, 100]")
        if animation_size_budget_bytes < 1024 * 1024:
            raise ValueError("animation_size_budget_bytes must be at least 1 MiB")


DEFAULT_CONFIGURATION = HydrogenicConfiguration()


def official_gallery_states(
    *,
    atomic_number: int = 1,
    mass_number: int = 1,
) -> tuple[HydrogenicState, ...]:
    """Return the complete official 1s/2p/3d/4f/5g real-orbital gallery."""

    states = []
    for l in range(5):
        n = l + 1
        states.extend(
            HydrogenicState(
                n=n,
                l=l,
                m=m,
                atomic_number=atomic_number,
                mass_number=mass_number,
            )
            for m in range(-l, l + 1)
        )
    return tuple(states)
