"""Kinematic graphite-ring intensity and broadening extension for Task 6.

The official task needs ring radii only.  This module adds a transparent
powder-diffraction layer: graphite lattice spacings, the four-atom AB-stacked
structure factor, a Debye--Waller envelope, hexagonal multiplicity and a peak
width assembled from crystallite size, beam divergence, voltage spread and
detector resolution.  The result is a kinematic teaching model; dynamical
multiple scattering and a calibrated detector response remain outside scope.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task06_electron_diffraction.relativistic_extension import (
    relativistic_wavelength_m,
)


FloatArray = NDArray[np.float64]
GRAPHITE_A_M = 0.246e-9
GRAPHITE_C_M = 0.671e-9
GRAPHITE_BASIS = np.asarray(
    [
        [0.0, 0.0, 0.0],
        [1.0 / 3.0, 2.0 / 3.0, 0.0],
        [0.0, 0.0, 0.5],
        [2.0 / 3.0, 1.0 / 3.0, 0.5],
    ],
    dtype=np.float64,
)


@dataclass(frozen=True)
class PowderRing:
    """One graphite reflection mapped onto a flat detector."""

    h: int
    k: int
    l: int
    spacing_nm: float
    bragg_angle_rad: float
    radius_mm: float
    radial_fwhm_mm: float
    structure_factor_squared: float
    multiplicity: int
    relative_integrated_intensity: float


def graphite_spacing_m(
    h: int,
    k: int,
    l: int,
    *,
    lattice_a_m: float = GRAPHITE_A_M,
    lattice_c_m: float = GRAPHITE_C_M,
) -> float:
    """Return d_hkl for the conventional hexagonal graphite cell."""

    if any(isinstance(value, bool) for value in (h, k, l)):
        raise TypeError("Miller indices must be integers")
    h_value, k_value, l_value = int(h), int(k), int(l)
    if h_value == 0 and k_value == 0 and l_value == 0:
        raise ValueError("(0,0,0) is not a reflection")
    a, c = float(lattice_a_m), float(lattice_c_m)
    if not np.isfinite(a) or not np.isfinite(c) or a <= 0.0 or c <= 0.0:
        raise ValueError("lattice constants must be finite and positive")
    inverse_squared = (
        4.0
        * (h_value**2 + h_value * k_value + k_value**2)
        / (3.0 * a**2)
        + l_value**2 / c**2
    )
    return float(1.0 / np.sqrt(inverse_squared))


def graphite_structure_factor(h: int, k: int, l: int) -> complex:
    """Return the dimensionless four-carbon geometric structure factor."""

    indices = np.asarray([int(h), int(k), int(l)], dtype=np.float64)
    phases = 2.0j * np.pi * (GRAPHITE_BASIS @ indices)
    return complex(np.sum(np.exp(phases)))


def hexagonal_multiplicity(h: int, k: int, l: int) -> int:
    """Count distinct sixfold basal rotations and plus/minus l partners."""

    h_value, k_value, l_value = int(h), int(k), int(l)
    basal = {
        (h_value, k_value),
        (-k_value, h_value + k_value),
        (-h_value - k_value, h_value),
        (-h_value, -k_value),
        (k_value, -h_value - k_value),
        (h_value + k_value, -h_value),
    }
    return len(basal) * (1 if l_value == 0 else 2)


def scherrer_fwhm_rad(
    wavelength_m: float,
    bragg_angle_rad: float,
    crystallite_size_m: float,
    *,
    shape_factor: float = 0.9,
) -> float:
    """Return the Scherrer FWHM in scattering angle 2 theta."""

    wavelength = float(wavelength_m)
    theta = float(bragg_angle_rad)
    size = float(crystallite_size_m)
    factor = float(shape_factor)
    if wavelength <= 0.0 or size <= 0.0 or factor <= 0.0:
        raise ValueError("wavelength, size and shape factor must be positive")
    if not 0.0 <= theta < np.pi / 2.0:
        raise ValueError("bragg_angle_rad must lie in [0, pi/2)")
    return float(factor * wavelength / (size * np.cos(theta)))


def powder_ring(
    voltage_v: float,
    h: int,
    k: int,
    l: int,
    *,
    screen_distance_m: float = 0.135,
    crystallite_size_nm: float = 25.0,
    beam_divergence_mrad: float = 0.25,
    relative_voltage_fwhm: float = 0.002,
    detector_fwhm_mm: float = 0.15,
    debye_waller_b_angstrom2: float = 0.8,
) -> PowderRing:
    """Map one reflection to an intensity and radial peak width."""

    voltage = float(voltage_v)
    if not 1000.0 <= voltage <= 5000.0:
        raise ValueError("voltage_v must lie between 1000 and 5000 V")
    distance = float(screen_distance_m)
    if distance <= 0.0:
        raise ValueError("screen_distance_m must be positive")
    wavelength = float(relativistic_wavelength_m(voltage))
    spacing = graphite_spacing_m(h, k, l)
    ratio = wavelength / (2.0 * spacing)
    if ratio >= 1.0:
        raise ValueError("reflection is outside the Bragg domain")
    theta = float(np.arcsin(ratio))
    scattering_angle = 2.0 * theta
    radius_m = distance * np.tan(scattering_angle)

    size_width_2theta = scherrer_fwhm_rad(
        wavelength, theta, crystallite_size_nm * 1.0e-9
    )
    beam_width = beam_divergence_mrad * 1.0e-3
    # lambda propto V^-1/2, hence |d theta| = tan(theta)|dV|/(2V).
    voltage_width_2theta = np.tan(theta) * relative_voltage_fwhm
    angular_fwhm = np.sqrt(
        size_width_2theta**2 + beam_width**2 + voltage_width_2theta**2
    )
    radial_from_angle = distance / np.cos(scattering_angle) ** 2 * angular_fwhm
    radial_fwhm_m = np.sqrt(radial_from_angle**2 + (detector_fwhm_mm * 1.0e-3) ** 2)

    structure_squared = abs(graphite_structure_factor(h, k, l)) ** 2
    multiplicity = hexagonal_multiplicity(h, k, l)
    reciprocal_angstrom = 1.0 / (2.0 * spacing * 1.0e10)
    thermal_factor = np.exp(-2.0 * debye_waller_b_angstrom2 * reciprocal_angstrom**2)
    # Powder Lorentz-polarisation factor for a kinematic scale comparison.
    lorentz = 1.0 / max(np.sin(theta) * np.sin(2.0 * theta), 1.0e-15)
    intensity = multiplicity * structure_squared * thermal_factor * lorentz
    return PowderRing(
        h=int(h),
        k=int(k),
        l=int(l),
        spacing_nm=spacing * 1.0e9,
        bragg_angle_rad=theta,
        radius_mm=radius_m * 1.0e3,
        radial_fwhm_mm=radial_fwhm_m * 1.0e3,
        structure_factor_squared=float(structure_squared),
        multiplicity=multiplicity,
        relative_integrated_intensity=float(intensity),
    )


def powder_profile(
    radius_mm: ArrayLike,
    rings: tuple[PowderRing, ...],
) -> FloatArray:
    """Return an area-normalized sum of Gaussian powder rings."""

    radius = np.asarray(radius_mm, dtype=np.float64)
    if radius.ndim != 1 or radius.size < 2 or np.any(~np.isfinite(radius)):
        raise ValueError("radius_mm must be a finite one-dimensional grid")
    if not rings:
        raise ValueError("rings must not be empty")
    profile = np.zeros_like(radius)
    for ring in rings:
        if not isinstance(ring, PowderRing):
            raise TypeError("rings must contain PowderRing records")
        sigma = ring.radial_fwhm_mm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
        profile += (
            ring.relative_integrated_intensity
            * np.exp(-0.5 * ((radius - ring.radius_mm) / sigma) ** 2)
            / (sigma * np.sqrt(2.0 * np.pi))
        )
    area = float(np.trapezoid(profile, radius))
    if area <= 0.0:
        raise FloatingPointError("powder profile has zero area")
    return np.asarray(profile / area, dtype=np.float64)


__all__ = [
    "GRAPHITE_A_M",
    "GRAPHITE_BASIS",
    "GRAPHITE_C_M",
    "PowderRing",
    "graphite_spacing_m",
    "graphite_structure_factor",
    "hexagonal_multiplicity",
    "powder_profile",
    "powder_ring",
    "scherrer_fwhm_rad",
]
