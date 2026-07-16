"""Task 3: Planck radiation and Einstein heat capacity."""

from task03_thermal_radiation.analysis import (
    PlanckStudyResult,
    build_planck_study,
)
from task03_thermal_radiation.constants import (
    BOLTZMANN_CONSTANT_J_K,
    EINSTEIN_DEBYE_FACTOR,
    METRES_PER_NANOMETRE,
    MOLAR_GAS_CONSTANT_J_MOL_K,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
    STEFAN_BOLTZMANN_CONSTANT_W_M2_K4,
    WIEN_DISPLACEMENT_CONSTANT_M_K,
)
from task03_thermal_radiation.configuration import (
    DEFAULT_CONFIGURATION,
    Task03Configuration,
)
from task03_thermal_radiation.models import (
    einstein_frequency_from_temperature,
    einstein_molar_heat_capacity,
    einstein_temperature_from_debye,
    planck_spectral_exitance,
    planck_spectral_radiance,
    spectral_density_per_nanometre,
)
from task03_thermal_radiation.materials import (
    EinsteinMaterial,
    OFFICIAL_MATERIALS,
)
from task03_thermal_radiation.reference import (
    stefan_boltzmann_exitance,
    wien_peak_wavelength,
)
from task03_thermal_radiation.validation import (
    Task03ValidationReport,
    ValidationCheck,
    validate_planck_study,
)


__all__ = [
    "BOLTZMANN_CONSTANT_J_K",
    "DEFAULT_CONFIGURATION",
    "EINSTEIN_DEBYE_FACTOR",
    "EinsteinMaterial",
    "METRES_PER_NANOMETRE",
    "MOLAR_GAS_CONSTANT_J_MOL_K",
    "OFFICIAL_MATERIALS",
    "PLANCK_CONSTANT_J_S",
    "PlanckStudyResult",
    "SPEED_OF_LIGHT_M_S",
    "STEFAN_BOLTZMANN_CONSTANT_W_M2_K4",
    "Task03ValidationReport",
    "Task03Configuration",
    "ValidationCheck",
    "WIEN_DISPLACEMENT_CONSTANT_M_K",
    "build_planck_study",
    "einstein_frequency_from_temperature",
    "einstein_molar_heat_capacity",
    "einstein_temperature_from_debye",
    "planck_spectral_exitance",
    "planck_spectral_radiance",
    "spectral_density_per_nanometre",
    "stefan_boltzmann_exitance",
    "validate_planck_study",
    "wien_peak_wavelength",
]
