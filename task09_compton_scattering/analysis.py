"""Immutable multi-energy analytical study for Task 9."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task09_compton_scattering.configuration import (
    DEFAULT_CONFIGURATION,
    Task09Configuration,
)
from task09_compton_scattering.models import energy_angle_study


FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def _readonly_float_array(value: object, *, name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    array.setflags(write=False)
    return array


def _readonly_bool_array(value: object, *, name: str) -> BoolArray:
    raw = np.asarray(value)
    if raw.dtype != np.dtype(np.bool_):
        raise TypeError(f"{name} must contain boolean values")
    array = np.array(value, dtype=np.bool_, copy=True)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class Task09StudyResult:
    """Complete immutable exact kinematic evidence before serialization."""

    schema_version: str
    incident_energies_kev: FloatArray
    theta_axis_deg: FloatArray

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
        if self.schema_version != "task09-study-v1":
            raise ValueError("invalid Task 9 study schema")
        for field_name in (
            "incident_energies_kev",
            "theta_axis_deg",
            "incident_energy_kev",
            "theta_deg",
            "alpha",
            "incident_wavelength_m",
            "wavelength_shift_m",
            "fractional_wavelength_shift",
            "scattered_wavelength_m",
            "scattered_energy_kev",
            "electron_kinetic_energy_kev",
            "electron_gamma",
            "electron_beta",
            "electron_speed_m_s",
            "electron_pc_kev",
            "electron_recoil_angle_deg",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(getattr(self, field_name), name=field_name),
            )
        object.__setattr__(
            self,
            "electron_recoil_direction_defined",
            _readonly_bool_array(
                self.electron_recoil_direction_defined,
                name="electron_recoil_direction_defined",
            ),
        )

        if self.incident_energies_kev.ndim != 1 or not self.incident_energies_kev.size:
            raise ValueError("incident_energies_kev must be a non-empty axis")
        if self.theta_axis_deg.ndim != 1 or self.theta_axis_deg.size < 3:
            raise ValueError("theta_axis_deg must be a non-trivial axis")
        expected_shape = (
            int(self.incident_energies_kev.size),
            int(self.theta_axis_deg.size),
        )
        for field_name in (
            "incident_energy_kev",
            "theta_deg",
            "alpha",
            "incident_wavelength_m",
            "wavelength_shift_m",
            "fractional_wavelength_shift",
            "scattered_wavelength_m",
            "scattered_energy_kev",
            "electron_kinetic_energy_kev",
            "electron_gamma",
            "electron_beta",
            "electron_speed_m_s",
            "electron_pc_kev",
            "electron_recoil_angle_deg",
            "electron_recoil_direction_defined",
        ):
            if getattr(self, field_name).shape != expected_shape:
                raise ValueError(f"{field_name} has an invalid energy-by-angle shape")

    @property
    def energy_count(self) -> int:
        return int(self.incident_energies_kev.size)

    @property
    def angle_count(self) -> int:
        return int(self.theta_axis_deg.size)

    @property
    def row_count(self) -> int:
        return self.energy_count * self.angle_count


def build_task09_study(
    configuration: Task09Configuration = DEFAULT_CONFIGURATION,
) -> Task09StudyResult:
    """Build the complete official five-energy, full-angle kinematic study."""

    if not isinstance(configuration, Task09Configuration):
        raise TypeError("configuration must be a Task09Configuration")
    kinematics = energy_angle_study(configuration=configuration)
    energies = np.asarray(configuration.incident_energies_kev, dtype=np.float64)
    theta_axis = np.linspace(
        configuration.angle_minimum_deg,
        configuration.angle_maximum_deg,
        configuration.angle_point_count,
        dtype=np.float64,
    )
    return Task09StudyResult(
        schema_version="task09-study-v1",
        incident_energies_kev=energies,
        theta_axis_deg=theta_axis,
        incident_energy_kev=kinematics.incident_energy_kev,
        theta_deg=kinematics.theta_deg,
        alpha=kinematics.alpha,
        incident_wavelength_m=kinematics.incident_wavelength_m,
        wavelength_shift_m=kinematics.wavelength_shift_m,
        fractional_wavelength_shift=kinematics.fractional_wavelength_shift,
        scattered_wavelength_m=kinematics.scattered_wavelength_m,
        scattered_energy_kev=kinematics.scattered_energy_kev,
        electron_kinetic_energy_kev=kinematics.electron_kinetic_energy_kev,
        electron_gamma=kinematics.electron_gamma,
        electron_beta=kinematics.electron_beta,
        electron_speed_m_s=kinematics.electron_speed_m_s,
        electron_pc_kev=kinematics.electron_pc_kev,
        electron_recoil_angle_deg=kinematics.electron_recoil_angle_deg,
        electron_recoil_direction_defined=(
            kinematics.electron_recoil_direction_defined
        ),
    )


__all__ = ["Task09StudyResult", "build_task09_study"]
