"""Deterministic in-memory studies for Task 3."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from task03_thermal_radiation.configuration import (
    DEFAULT_CONFIGURATION,
    Task03Configuration,
)
from task03_thermal_radiation.constants import MOLAR_GAS_CONSTANT_J_MOL_K
from task03_thermal_radiation.materials import (
    EinsteinMaterial,
    OFFICIAL_MATERIALS,
)
from task03_thermal_radiation.models import (
    einstein_frequency_from_temperature,
    einstein_molar_heat_capacity,
    einstein_temperature_from_debye,
    planck_spectral_exitance,
    planck_spectral_radiance,
    spectral_density_per_nanometre,
)
from task03_thermal_radiation.reference import (
    stefan_boltzmann_exitance,
    wien_peak_wavelength,
)


FloatArray = NDArray[np.float64]


def _readonly_float_array(
    values: object,
    *,
    name: str,
    shape: tuple[int, ...] | None = None,
    non_negative: bool = True,
) -> FloatArray:
    """Copy one result array, validate it, and make it immutable."""

    array = np.array(values, dtype=np.float64, copy=True)
    if shape is not None and array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    if non_negative and np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    array.setflags(write=False)
    return array


def _inclusive_grid(minimum: float, maximum: float, interval: float) -> FloatArray:
    """Construct a closed uniform grid from an already validated definition."""

    intervals = int(round((maximum - minimum) / interval))
    return np.linspace(minimum, maximum, intervals + 1, dtype=np.float64)


def _trapezoidal_integral(values: FloatArray, coordinates: FloatArray) -> float:
    """Integrate on a non-uniform grid across supported NumPy versions."""

    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(values, coordinates))
    return float(np.trapz(values, coordinates))  # pragma: no cover - NumPy < 2


@dataclass(frozen=True)
class PlanckStudyResult:
    """Immutable spectra, peak locations, integrals, and analytical targets."""

    configuration: Task03Configuration
    temperatures_k: FloatArray
    wavelengths_m: FloatArray
    wavelengths_nm: FloatArray
    spectral_radiance_w_m3_sr: FloatArray
    spectral_exitance_w_m2_nm: FloatArray
    numerical_peak_wavelength_m: FloatArray
    wien_peak_wavelength_m: FloatArray
    numerical_integrated_radiance_w_m2_sr: FloatArray
    expected_integrated_radiance_w_m2_sr: FloatArray
    numerical_integrated_exitance_w_m2: FloatArray
    stefan_boltzmann_exitance_w_m2: FloatArray

    def __post_init__(self) -> None:
        """Validate the complete scientific record and freeze every array."""

        if not isinstance(self.configuration, Task03Configuration):
            raise TypeError("configuration must be a Task03Configuration")

        n_temperature = len(self.configuration.planck_temperatures_k)
        n_wavelength = int(
            round(
                (
                    self.configuration.planck_display_max_nm
                    - self.configuration.planck_display_min_nm
                )
                / self.configuration.planck_display_interval_nm
            )
        ) + 1

        shapes = {
            "temperatures_k": (n_temperature,),
            "wavelengths_m": (n_wavelength,),
            "wavelengths_nm": (n_wavelength,),
            "spectral_radiance_w_m3_sr": (n_temperature, n_wavelength),
            "spectral_exitance_w_m2_nm": (n_temperature, n_wavelength),
            "numerical_peak_wavelength_m": (n_temperature,),
            "wien_peak_wavelength_m": (n_temperature,),
            "numerical_integrated_radiance_w_m2_sr": (n_temperature,),
            "expected_integrated_radiance_w_m2_sr": (n_temperature,),
            "numerical_integrated_exitance_w_m2": (n_temperature,),
            "stefan_boltzmann_exitance_w_m2": (n_temperature,),
        }
        for field_name, expected_shape in shapes.items():
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(
                    getattr(self, field_name),
                    name=field_name,
                    shape=expected_shape,
                ),
            )

        if not np.array_equal(
            self.temperatures_k,
            np.asarray(self.configuration.planck_temperatures_k),
        ):
            raise ValueError("temperatures_k must match the configuration")
        if not np.all(np.diff(self.wavelengths_m) > 0.0):
            raise ValueError("wavelengths_m must be strictly increasing")
        if not np.all(np.diff(self.wavelengths_nm) > 0.0):
            raise ValueError("wavelengths_nm must be strictly increasing")
        if not np.allclose(
            self.wavelengths_m,
            self.wavelengths_nm * 1.0e-9,
            rtol=0.0,
            atol=2.0e-22,
        ):
            raise ValueError(
                "wavelengths_m and wavelengths_nm must describe one grid"
            )


@dataclass(frozen=True)
class EinsteinStudyResult:
    """Immutable material conversions and Einstein heat-capacity curves."""

    configuration: Task03Configuration
    materials: tuple[EinsteinMaterial, ...]
    einstein_temperatures_k: FloatArray
    einstein_frequencies_hz: FloatArray
    temperatures_k: FloatArray
    molar_heat_capacity_j_mol_k: FloatArray
    reduced_temperatures: FloatArray
    normalized_heat_capacity: FloatArray

    def __post_init__(self) -> None:
        """Validate the complete scientific record and freeze every array."""

        if not isinstance(self.configuration, Task03Configuration):
            raise TypeError("configuration must be a Task03Configuration")

        materials = tuple(self.materials)
        if not materials:
            raise ValueError("materials must not be empty")
        if not all(isinstance(item, EinsteinMaterial) for item in materials):
            raise TypeError("materials must contain EinsteinMaterial records")
        if len({item.name for item in materials}) != len(materials):
            raise ValueError("material names must be unique")
        if len({item.symbol for item in materials}) != len(materials):
            raise ValueError("material symbols must be unique")
        object.__setattr__(self, "materials", materials)

        n_material = len(materials)
        n_temperature = int(
            round(
                (
                    self.configuration.einstein_temperature_max_k
                    - self.configuration.einstein_temperature_min_k
                )
                / self.configuration.einstein_temperature_interval_k
            )
        ) + 1
        n_reduced_temperature = (
            self.configuration.einstein_reduced_temperature_points
        )
        shapes = {
            "einstein_temperatures_k": (n_material,),
            "einstein_frequencies_hz": (n_material,),
            "temperatures_k": (n_temperature,),
            "molar_heat_capacity_j_mol_k": (n_material, n_temperature),
            "reduced_temperatures": (n_reduced_temperature,),
            "normalized_heat_capacity": (
                n_material,
                n_reduced_temperature,
            ),
        }
        for field_name, expected_shape in shapes.items():
            object.__setattr__(
                self,
                field_name,
                _readonly_float_array(
                    getattr(self, field_name),
                    name=field_name,
                    shape=expected_shape,
                ),
            )

        if np.any(self.einstein_temperatures_k <= 0.0):
            raise ValueError("einstein_temperatures_k must be strictly positive")
        if np.any(self.einstein_frequencies_hz <= 0.0):
            raise ValueError("einstein_frequencies_hz must be strictly positive")

        expected_temperatures = _inclusive_grid(
            self.configuration.einstein_temperature_min_k,
            self.configuration.einstein_temperature_max_k,
            self.configuration.einstein_temperature_interval_k,
        )
        if not np.array_equal(self.temperatures_k, expected_temperatures):
            raise ValueError("temperatures_k must match the configuration")

        expected_reduced_temperatures = np.linspace(
            self.configuration.einstein_reduced_temperature_min,
            self.configuration.einstein_reduced_temperature_max,
            self.configuration.einstein_reduced_temperature_points,
            dtype=np.float64,
        )
        if not np.array_equal(
            self.reduced_temperatures,
            expected_reduced_temperatures,
        ):
            raise ValueError(
                "reduced_temperatures must match the configuration"
            )


def build_planck_study(
    configuration: Task03Configuration = DEFAULT_CONFIGURATION,
) -> PlanckStudyResult:
    """Calculate all Stage 5 spectra, peaks, integrals, and references."""

    if not isinstance(configuration, Task03Configuration):
        raise TypeError("configuration must be a Task03Configuration")

    temperatures = np.asarray(
        configuration.planck_temperatures_k,
        dtype=np.float64,
    )
    wavelengths_nm = _inclusive_grid(
        configuration.planck_display_min_nm,
        configuration.planck_display_max_nm,
        configuration.planck_display_interval_nm,
    )
    wavelengths_m = wavelengths_nm * 1.0e-9

    spectral_radiance = planck_spectral_radiance(
        wavelengths_m[None, :],
        temperatures[:, None],
    )
    spectral_exitance_nm = spectral_density_per_nanometre(
        planck_spectral_exitance(
            wavelengths_m[None, :],
            temperatures[:, None],
        )
    )

    peak_grid_nm = _inclusive_grid(
        configuration.planck_peak_min_nm,
        configuration.planck_peak_max_nm,
        configuration.planck_peak_interval_nm,
    )
    peak_grid_m = peak_grid_nm * 1.0e-9
    numerical_peaks = np.empty(temperatures.shape, dtype=np.float64)
    for index, temperature in enumerate(temperatures):
        peak_spectrum = planck_spectral_radiance(peak_grid_m, temperature)
        numerical_peaks[index] = peak_grid_m[int(np.argmax(peak_spectrum))]

    integration_grid_m = np.geomspace(
        configuration.planck_integration_min_m,
        configuration.planck_integration_max_m,
        configuration.planck_integration_points,
        dtype=np.float64,
    )
    integrated_radiance = np.empty(temperatures.shape, dtype=np.float64)
    integrated_exitance = np.empty(temperatures.shape, dtype=np.float64)
    for index, temperature in enumerate(temperatures):
        radiance = planck_spectral_radiance(integration_grid_m, temperature)
        exitance = planck_spectral_exitance(integration_grid_m, temperature)
        integrated_radiance[index] = _trapezoidal_integral(
            radiance,
            integration_grid_m,
        )
        integrated_exitance[index] = _trapezoidal_integral(
            exitance,
            integration_grid_m,
        )

    wien_targets = wien_peak_wavelength(temperatures)
    stefan_targets = stefan_boltzmann_exitance(temperatures)

    return PlanckStudyResult(
        configuration=configuration,
        temperatures_k=temperatures,
        wavelengths_m=wavelengths_m,
        wavelengths_nm=wavelengths_nm,
        spectral_radiance_w_m3_sr=spectral_radiance,
        spectral_exitance_w_m2_nm=spectral_exitance_nm,
        numerical_peak_wavelength_m=numerical_peaks,
        wien_peak_wavelength_m=wien_targets,
        numerical_integrated_radiance_w_m2_sr=integrated_radiance,
        expected_integrated_radiance_w_m2_sr=stefan_targets / math.pi,
        numerical_integrated_exitance_w_m2=integrated_exitance,
        stefan_boltzmann_exitance_w_m2=stefan_targets,
    )


def build_einstein_study(
    configuration: Task03Configuration = DEFAULT_CONFIGURATION,
    materials: tuple[EinsteinMaterial, ...] = OFFICIAL_MATERIALS,
) -> EinsteinStudyResult:
    """Calculate all material conversions and Einstein heat-capacity curves."""

    if not isinstance(configuration, Task03Configuration):
        raise TypeError("configuration must be a Task03Configuration")
    material_records = tuple(materials)
    if not material_records:
        raise ValueError("materials must not be empty")
    if not all(
        isinstance(material, EinsteinMaterial) for material in material_records
    ):
        raise TypeError("materials must contain EinsteinMaterial records")

    debye_temperatures = np.asarray(
        [material.debye_temperature_k for material in material_records],
        dtype=np.float64,
    )
    einstein_temperatures = einstein_temperature_from_debye(
        debye_temperatures
    )
    einstein_frequencies = einstein_frequency_from_temperature(
        einstein_temperatures
    )

    temperatures = _inclusive_grid(
        configuration.einstein_temperature_min_k,
        configuration.einstein_temperature_max_k,
        configuration.einstein_temperature_interval_k,
    )
    heat_capacity = einstein_molar_heat_capacity(
        temperatures[None, :],
        einstein_temperatures[:, None],
    )

    reduced_temperatures = np.linspace(
        configuration.einstein_reduced_temperature_min,
        configuration.einstein_reduced_temperature_max,
        configuration.einstein_reduced_temperature_points,
        dtype=np.float64,
    )
    reduced_physical_temperatures = (
        einstein_temperatures[:, None] * reduced_temperatures[None, :]
    )
    normalized_heat_capacity = einstein_molar_heat_capacity(
        reduced_physical_temperatures,
        einstein_temperatures[:, None],
    ) / (3.0 * MOLAR_GAS_CONSTANT_J_MOL_K)

    return EinsteinStudyResult(
        configuration=configuration,
        materials=material_records,
        einstein_temperatures_k=einstein_temperatures,
        einstein_frequencies_hz=einstein_frequencies,
        temperatures_k=temperatures,
        molar_heat_capacity_j_mol_k=heat_capacity,
        reduced_temperatures=reduced_temperatures,
        normalized_heat_capacity=normalized_heat_capacity,
    )


__all__ = [
    "EinsteinStudyResult",
    "PlanckStudyResult",
    "build_einstein_study",
    "build_planck_study",
]
