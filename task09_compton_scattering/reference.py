"""Independent scalar energy–momentum references for Task 9."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from task09_compton_scattering.constants import ELECTRON_REST_ENERGY_KEV


def _finite_scalar(value: Real, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _energy(value: Real) -> float:
    energy = _finite_scalar(value, name="incident_energy_kev")
    if energy <= 0.0:
        raise ValueError("incident_energy_kev must be greater than zero")
    return energy


def _theta(value: Real) -> float:
    theta = _finite_scalar(value, name="theta_deg")
    if not 0.0 <= theta <= 180.0:
        raise ValueError("theta_deg must lie within 0 to 180 degrees")
    return theta


@dataclass(frozen=True)
class ReferenceKinematics:
    """One independently calculated scalar collision state."""

    incident_energy_kev: float
    theta_deg: float
    fractional_wavelength_shift: float
    scattered_energy_kev: float
    electron_kinetic_energy_kev: float
    electron_gamma: float
    electron_beta: float
    electron_pc_kev: float
    electron_recoil_angle_deg: float
    electron_recoil_direction_defined: bool


def reference_kinematics(
    incident_energy_kev: Real,
    theta_deg: Real,
) -> ReferenceKinematics:
    """Use dimensionless ratios and momentum, not wavelength-first production code."""

    energy = _energy(incident_energy_kev)
    theta = _theta(theta_deg)
    theta_rad = math.radians(theta)
    cosine = math.cos(theta_rad)
    sine = 0.0 if theta in (0.0, 180.0) else math.sin(theta_rad)
    alpha = energy / ELECTRON_REST_ENERGY_KEV
    angular_factor = 1.0 - cosine
    fractional_shift = alpha * angular_factor
    energy_ratio = 1.0 / (1.0 + fractional_shift)
    scattered_energy = energy * energy_ratio
    kinetic_energy = energy * fractional_shift * energy_ratio
    if theta == 0.0:
        kinetic_energy = 0.0
        scattered_energy = energy
    gamma = 1.0 + kinetic_energy / ELECTRON_REST_ENERGY_KEV

    electron_pc = math.hypot(
        energy - scattered_energy * cosine,
        scattered_energy * sine,
    )
    beta = electron_pc / (ELECTRON_REST_ENERGY_KEV + kinetic_energy)
    direction_defined = theta != 0.0
    if direction_defined:
        recoil_angle = math.degrees(
            math.atan2(
                sine,
                1.0 + alpha * angular_factor - cosine,
            )
        )
        if theta == 180.0:
            recoil_angle = 0.0
    else:
        recoil_angle = 90.0

    return ReferenceKinematics(
        incident_energy_kev=energy,
        theta_deg=theta,
        fractional_wavelength_shift=fractional_shift,
        scattered_energy_kev=scattered_energy,
        electron_kinetic_energy_kev=kinetic_energy,
        electron_gamma=gamma,
        electron_beta=beta,
        electron_pc_kev=electron_pc,
        electron_recoil_angle_deg=recoil_angle,
        electron_recoil_direction_defined=direction_defined,
    )


__all__ = ["ReferenceKinematics", "reference_kinematics"]
