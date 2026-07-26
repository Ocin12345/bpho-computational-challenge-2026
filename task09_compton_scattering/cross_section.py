"""Unpolarized Klein–Nishina angular weighting for the Task 9 extension."""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task09_compton_scattering.constants import (
    BARN_M2,
    CLASSICAL_ELECTRON_RADIUS_M,
    ELECTRON_REST_ENERGY_KEV,
    THOMSON_CROSS_SECTION_M2,
)


FloatArray = NDArray[np.float64]


def _real_array(value: ArrayLike, *, name: str) -> FloatArray:
    object_array = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in object_array.flat):
        raise TypeError(f"{name} must contain real numbers, not booleans")
    raw = np.asarray(value)
    if not np.issubdtype(raw.dtype, np.number) or np.issubdtype(
        raw.dtype,
        np.complexfloating,
    ):
        raise TypeError(f"{name} must contain real numbers")
    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def _broadcast_energy_angle(
    incident_energy_kev: ArrayLike,
    theta_deg: ArrayLike,
) -> tuple[FloatArray, FloatArray]:
    energy = _real_array(incident_energy_kev, name="incident_energy_kev")
    theta = _real_array(theta_deg, name="theta_deg")
    if np.any(energy <= 0.0):
        raise ValueError("incident_energy_kev must be greater than zero")
    if np.any(theta < 0.0) or np.any(theta > 180.0):
        raise ValueError("theta_deg must lie within 0 to 180 degrees")
    try:
        energy_b, theta_b = np.broadcast_arrays(energy, theta)
    except ValueError as exc:
        raise ValueError(
            "incident_energy_kev and theta_deg must be broadcast-compatible"
        ) from exc
    return np.asarray(energy_b, dtype=np.float64), np.asarray(theta_b, dtype=np.float64)


def _positive_energy(incident_energy_kev: ArrayLike) -> FloatArray:
    energy = _real_array(incident_energy_kev, name="incident_energy_kev")
    if np.any(energy <= 0.0):
        raise ValueError("incident_energy_kev must be greater than zero")
    return energy


def _readonly(value: ArrayLike) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(array)):
        raise ValueError("cross-section arrays must be finite")
    array.setflags(write=False)
    return array


def klein_nishina_differential_cross_section_m2_sr(
    incident_energy_kev: ArrayLike,
    theta_deg: ArrayLike,
) -> FloatArray:
    """Return d-sigma/d-Omega for an unpolarized free electron."""

    energy, theta = _broadcast_energy_angle(incident_energy_kev, theta_deg)
    theta_rad = np.radians(theta)
    cosine = np.cos(theta_rad)
    sine_squared = np.square(np.sin(theta_rad))
    alpha = energy / ELECTRON_REST_ENERGY_KEV
    energy_ratio = 1.0 / (1.0 + alpha * (1.0 - cosine))
    differential = (
        0.5
        * CLASSICAL_ELECTRON_RADIUS_M**2
        * np.square(energy_ratio)
        * (energy_ratio + 1.0 / energy_ratio - sine_squared)
    )
    if np.any(differential < 0.0) or not np.all(np.isfinite(differential)):
        raise ArithmeticError("Klein–Nishina differential cross-section is invalid")
    return np.asarray(differential, dtype=np.float64)


def klein_nishina_total_cross_section_m2(
    incident_energy_kev: ArrayLike,
) -> FloatArray:
    """Return the analytical solid-angle integral of Klein–Nishina scattering."""

    energy = _positive_energy(incident_energy_kev)
    alpha = energy / ELECTRON_REST_ENERGY_KEV
    logarithm = np.log1p(2.0 * alpha)
    bracket = (
        (1.0 + alpha)
        / np.square(alpha)
        * (
            2.0 * (1.0 + alpha) / (1.0 + 2.0 * alpha)
            - logarithm / alpha
        )
        + logarithm / (2.0 * alpha)
        - (1.0 + 3.0 * alpha) / np.square(1.0 + 2.0 * alpha)
    )
    total = 2.0 * np.pi * CLASSICAL_ELECTRON_RADIUS_M**2 * bracket

    # The closed form loses digits as alpha tends to zero.  The known Thomson
    # expansion keeps the public function well-conditioned outside the task range.
    low_energy = alpha < 1.0e-3
    series_ratio = (
        1.0
        - 2.0 * alpha
        + 26.0 / 5.0 * np.square(alpha)
        - 133.0 / 10.0 * np.power(alpha, 3)
    )
    total = np.where(low_energy, THOMSON_CROSS_SECTION_M2 * series_ratio, total)
    if np.any(total <= 0.0) or not np.all(np.isfinite(total)):
        raise ArithmeticError("Klein–Nishina total cross-section is invalid")
    return np.asarray(total, dtype=np.float64)


def klein_nishina_theta_density_m2_rad(
    incident_energy_kev: ArrayLike,
    theta_deg: ArrayLike,
) -> FloatArray:
    """Return d-sigma/d-theta after integrating over azimuth."""

    energy, theta = _broadcast_energy_angle(incident_energy_kev, theta_deg)
    differential = klein_nishina_differential_cross_section_m2_sr(energy, theta)
    density = 2.0 * np.pi * np.sin(np.radians(theta)) * differential
    density = np.where(np.logical_or(theta == 0.0, theta == 180.0), 0.0, density)
    return np.asarray(density, dtype=np.float64)


def klein_nishina_theta_pdf_rad_inv(
    incident_energy_kev: ArrayLike,
    theta_deg: ArrayLike,
) -> FloatArray:
    """Return the normalized polar-angle probability density per radian."""

    energy, theta = _broadcast_energy_angle(incident_energy_kev, theta_deg)
    density = klein_nishina_theta_density_m2_rad(energy, theta)
    total = klein_nishina_total_cross_section_m2(energy)
    return np.asarray(density / total, dtype=np.float64)


@dataclass(frozen=True)
class KleinNishinaStudy:
    """Complete extension state on one broadcast energy–angle grid."""

    incident_energy_kev: FloatArray
    theta_deg: FloatArray
    scattered_to_incident_energy_ratio: FloatArray
    differential_cross_section_m2_sr: FloatArray
    differential_cross_section_barn_sr: FloatArray
    relative_differential_cross_section: FloatArray
    theta_density_m2_rad: FloatArray
    theta_pdf_rad_inv: FloatArray
    total_cross_section_m2: FloatArray
    total_cross_section_barn: FloatArray

    def __post_init__(self) -> None:
        expected_shape = np.asarray(self.incident_energy_kev).shape
        for field in fields(self):
            value = _readonly(getattr(self, field.name))
            if value.shape != expected_shape:
                raise ValueError("all cross-section arrays must share one shape")
            object.__setattr__(self, field.name, value)


def build_klein_nishina_study(
    incident_energy_kev: ArrayLike,
    theta_deg: ArrayLike,
) -> KleinNishinaStudy:
    """Return all differential, total and normalized extension quantities."""

    energy, theta = _broadcast_energy_angle(incident_energy_kev, theta_deg)
    alpha = energy / ELECTRON_REST_ENERGY_KEV
    ratio = 1.0 / (1.0 + alpha * (1.0 - np.cos(np.radians(theta))))
    differential = klein_nishina_differential_cross_section_m2_sr(energy, theta)
    density = klein_nishina_theta_density_m2_rad(energy, theta)
    total = klein_nishina_total_cross_section_m2(energy)
    return KleinNishinaStudy(
        incident_energy_kev=energy,
        theta_deg=theta,
        scattered_to_incident_energy_ratio=ratio,
        differential_cross_section_m2_sr=differential,
        differential_cross_section_barn_sr=differential / BARN_M2,
        relative_differential_cross_section=(
            differential / CLASSICAL_ELECTRON_RADIUS_M**2
        ),
        theta_density_m2_rad=density,
        theta_pdf_rad_inv=density / total,
        total_cross_section_m2=total,
        total_cross_section_barn=total / BARN_M2,
    )


__all__ = [
    "KleinNishinaStudy",
    "build_klein_nishina_study",
    "klein_nishina_differential_cross_section_m2_sr",
    "klein_nishina_theta_density_m2_rad",
    "klein_nishina_theta_pdf_rad_inv",
    "klein_nishina_total_cross_section_m2",
]
