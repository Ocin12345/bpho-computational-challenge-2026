"""Pure vectorised relativistic kinematics for Task 9."""

from __future__ import annotations

from dataclasses import dataclass, fields
from numbers import Integral
from typing import Optional

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.constants import (
    BACKSCATTER_RECOIL_ANGLE_DEG,
    DEGREES_PER_RADIAN,
    ELECTRON_COMPTON_WAVELENGTH_M,
    ELECTRON_REST_ENERGY_KEV,
    FORWARD_RECOIL_ANGLE_LIMIT_DEG,
    JOULES_PER_KEV,
    PLANCK_CONSTANT_J_S,
    RADIANS_PER_DEGREE,
    SPEED_OF_LIGHT_M_S,
)


FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def _readonly_float(value: ArrayLike) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    array.setflags(write=False)
    return array


def _readonly_bool(value: ArrayLike) -> BoolArray:
    array = np.asarray(value, dtype=np.bool_)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class ComptonKinematics:
    """Complete photon/electron state on one broadcast energy–angle shape."""

    incident_energy_kev: FloatArray
    theta_deg: FloatArray
    alpha: FloatArray
    incident_wavelength_m: FloatArray
    wavelength_shift_m: FloatArray
    fractional_wavelength_shift: FloatArray
    scattered_wavelength_m: FloatArray
    scattered_energy_kev: FloatArray
    electron_kinetic_energy_kev: FloatArray
    electron_gamma: FloatArray
    electron_beta: FloatArray
    electron_speed_m_s: FloatArray
    electron_pc_kev: FloatArray
    electron_recoil_angle_deg: FloatArray
    electron_recoil_direction_defined: BoolArray

    def __post_init__(self) -> None:
        expected_shape = np.asarray(self.incident_energy_kev).shape
        for field in fields(self):
            value = np.asarray(getattr(self, field.name))
            if value.shape != expected_shape:
                raise ValueError("all kinematic arrays must share one broadcast shape")
            if field.name == "electron_recoil_direction_defined":
                if value.dtype != np.dtype(np.bool_):
                    raise TypeError("direction-defined flags must be boolean")
            elif not np.issubdtype(value.dtype, np.floating):
                raise TypeError("kinematic values must be floating-point arrays")


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
    *,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> tuple[FloatArray, FloatArray]:
    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    energy = _real_array(incident_energy_kev, name="incident_energy_kev")
    theta = _real_array(theta_deg, name="theta_deg")
    if np.any(energy <= 0.0):
        raise ValueError("incident_energy_kev must be greater than zero")
    if np.any(energy < configuration.minimum_interactive_energy_kev) or np.any(
        energy > configuration.maximum_interactive_energy_kev
    ):
        raise ValueError("incident_energy_kev lies outside the configured range")
    if np.any(theta < configuration.angle_minimum_deg) or np.any(
        theta > configuration.angle_maximum_deg
    ):
        raise ValueError("theta_deg must lie within 0 to 180 degrees")
    try:
        energy_b, theta_b = np.broadcast_arrays(energy, theta)
    except ValueError as exc:
        raise ValueError(
            "incident_energy_kev and theta_deg must be broadcast-compatible"
        ) from exc
    return (
        np.asarray(energy_b, dtype=np.float64),
        np.asarray(theta_b, dtype=np.float64),
    )


def degrees_to_radians(angle_deg: ArrayLike) -> FloatArray:
    """Convert finite real angles from degrees to radians."""

    return np.asarray(
        _real_array(angle_deg, name="angle_deg") * RADIANS_PER_DEGREE,
        dtype=np.float64,
    )


def radians_to_degrees(angle_rad: ArrayLike) -> FloatArray:
    """Convert finite real angles from radians to degrees."""

    return np.asarray(
        _real_array(angle_rad, name="angle_rad") * DEGREES_PER_RADIAN,
        dtype=np.float64,
    )


def compton_kinematics(
    incident_energy_kev: ArrayLike,
    theta_deg: ArrayLike,
    *,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> ComptonKinematics:
    """Return the complete exact two-body state using wavelength-first equations."""

    energy, theta = _broadcast_energy_angle(
        incident_energy_kev,
        theta_deg,
        configuration=configuration,
    )
    theta_rad = theta * RADIANS_PER_DEGREE
    cosine = np.cos(theta_rad)
    sine = np.sin(theta_rad)
    forward = theta == configuration.angle_minimum_deg
    backscatter = theta == configuration.angle_maximum_deg

    energy_j = energy * JOULES_PER_KEV
    incident_wavelength = PLANCK_CONSTANT_J_S * SPEED_OF_LIGHT_M_S / energy_j
    wavelength_shift = ELECTRON_COMPTON_WAVELENGTH_M * (1.0 - cosine)
    scattered_wavelength = incident_wavelength + wavelength_shift
    # E - E' loses relative precision for small non-zero recoil energies.  The
    # wavelength-equivalent K = E Delta-lambda/lambda' avoids that cancellation.
    kinetic_energy = energy * wavelength_shift / scattered_wavelength
    kinetic_energy = np.where(forward, 0.0, kinetic_energy)
    scattered_energy = energy - kinetic_energy
    kinetic_over_rest = kinetic_energy / ELECTRON_REST_ENERGY_KEV
    gamma = 1.0 + kinetic_over_rest
    beta_squared = np.maximum(
        kinetic_over_rest
        * (kinetic_over_rest + 2.0)
        / np.square(kinetic_over_rest + 1.0),
        0.0,
    )
    beta = np.sqrt(beta_squared)
    beta = np.minimum(beta, np.nextafter(1.0, 0.0))

    photon_x_difference_kev = energy - scattered_energy * cosine
    scattered_photon_y_kev = scattered_energy * sine
    scattered_photon_y_kev = np.where(
        np.logical_or(forward, backscatter),
        0.0,
        scattered_photon_y_kev,
    )
    electron_pc = np.hypot(photon_x_difference_kev, scattered_photon_y_kev)
    direction_defined = np.logical_not(forward)
    recoil_angle = np.degrees(
        np.arctan2(scattered_photon_y_kev, photon_x_difference_kev)
    )
    recoil_angle = np.where(
        forward,
        FORWARD_RECOIL_ANGLE_LIMIT_DEG,
        recoil_angle,
    )
    recoil_angle = np.where(
        backscatter,
        BACKSCATTER_RECOIL_ANGLE_DEG,
        recoil_angle,
    )

    values = {
        "incident_energy_kev": energy,
        "theta_deg": theta,
        "alpha": energy / ELECTRON_REST_ENERGY_KEV,
        "incident_wavelength_m": incident_wavelength,
        "wavelength_shift_m": wavelength_shift,
        "fractional_wavelength_shift": wavelength_shift / incident_wavelength,
        "scattered_wavelength_m": scattered_wavelength,
        "scattered_energy_kev": scattered_energy,
        "electron_kinetic_energy_kev": kinetic_energy,
        "electron_gamma": gamma,
        "electron_beta": beta,
        "electron_speed_m_s": beta * SPEED_OF_LIGHT_M_S,
        "electron_pc_kev": electron_pc,
        "electron_recoil_angle_deg": recoil_angle,
    }
    if any(not np.all(np.isfinite(value)) for value in values.values()):
        raise ArithmeticError("Compton calculation produced a non-finite value")
    if np.any(values["fractional_wavelength_shift"] < 0.0):
        raise ArithmeticError("fractional wavelength shift became negative")
    if np.any(scattered_energy <= 0.0) or np.any(scattered_energy > energy):
        raise ArithmeticError("scattered photon energy fell outside (0, E]")
    if np.any(beta < 0.0) or np.any(beta >= 1.0):
        raise ArithmeticError("electron recoil speed fell outside [0, c)")
    if np.any(recoil_angle < 0.0) or np.any(recoil_angle > 90.0):
        raise ArithmeticError("electron recoil angle fell outside [0, 90] degrees")

    return ComptonKinematics(
        **{name: _readonly_float(value) for name, value in values.items()},
        electron_recoil_direction_defined=_readonly_bool(direction_defined),
    )


def angle_samples(
    point_count: Optional[Integral] = None,
    *,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> FloatArray:
    """Return the inclusive 0–180 degree axis with a sampled 90-degree point."""

    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    count_value = configuration.angle_point_count if point_count is None else point_count
    if isinstance(count_value, bool) or not isinstance(count_value, Integral):
        raise TypeError("point_count must be an integer")
    count = int(count_value)
    if count < 3:
        raise ValueError("point_count must be at least 3")
    if count % 2 == 0:
        raise ValueError("point_count must be odd so 90 degrees is sampled")
    return _readonly_float(
        np.linspace(
            configuration.angle_minimum_deg,
            configuration.angle_maximum_deg,
            count,
            dtype=np.float64,
        )
    )


def energy_angle_study(
    incident_energies_kev: Optional[ArrayLike] = None,
    *,
    point_count: Optional[Integral] = None,
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> ComptonKinematics:
    """Return an energy-by-angle study for the official curves or a custom set."""

    energies = _real_array(
        configuration.incident_energies_kev
        if incident_energies_kev is None
        else incident_energies_kev,
        name="incident_energies_kev",
    )
    if energies.ndim != 1 or energies.size == 0:
        raise ValueError("incident_energies_kev must be a non-empty one-dimensional axis")
    if np.any(np.diff(energies) <= 0.0):
        raise ValueError("incident_energies_kev must be strictly increasing")
    theta = angle_samples(point_count, configuration=configuration)
    return compton_kinematics(
        energies[:, np.newaxis],
        theta[np.newaxis, :],
        configuration=configuration,
    )


__all__ = [
    "BoolArray",
    "ComptonKinematics",
    "FloatArray",
    "angle_samples",
    "compton_kinematics",
    "degrees_to_radians",
    "energy_angle_study",
    "radians_to_degrees",
]
