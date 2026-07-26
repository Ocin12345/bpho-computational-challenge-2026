"""Scientific API for BPhO Computational Challenge Task 6."""

from task06_electron_diffraction.analysis import (
    SpacingFitResult,
    Task06StudyResult,
    build_task06_study,
)
from task06_electron_diffraction.configuration import (
    DEFAULT_CONFIGURATION,
    SpacingDefinition,
    Task06Configuration,
)
from task06_electron_diffraction.models import (
    bragg_angle_rad,
    bragg_ratio,
    caliper_diameter_m,
    electron_momentum_kg_m_s,
    electron_wavelength_m,
    maximum_bragg_order,
    maximum_screen_order,
    photo_ring_radius_m,
    scattering_angle_rad,
    screen_visible,
)

__all__ = [
    "DEFAULT_CONFIGURATION",
    "SpacingDefinition",
    "SpacingFitResult",
    "Task06Configuration",
    "Task06StudyResult",
    "bragg_angle_rad",
    "bragg_ratio",
    "build_task06_study",
    "caliper_diameter_m",
    "electron_momentum_kg_m_s",
    "electron_wavelength_m",
    "maximum_bragg_order",
    "maximum_screen_order",
    "photo_ring_radius_m",
    "scattering_angle_rad",
    "screen_visible",
]
