"""Task 4: stopping voltage in the photoelectric effect."""

from task04_photoelectric_effect.configuration import (
    DEFAULT_CONFIGURATION,
    Task04Configuration,
)
from task04_photoelectric_effect.constants import (
    ELECTRONVOLT_J,
    ELEMENTARY_CHARGE_C,
    HC_OVER_CHARGE_V_M,
    METRES_PER_NANOMETRE,
    NANOMETRES_PER_METRE,
    PLANCK_CONSTANT_J_S,
    PLANCK_OVER_CHARGE_V_S,
    SPEED_OF_LIGHT_M_S,
)
from task04_photoelectric_effect.materials import (
    OFFICIAL_MATERIALS,
    PhotoelectricMaterial,
    validate_material_collection,
)
from task04_photoelectric_effect.models import (
    cutoff_frequency_hz,
    cutoff_wavelength_m,
    emission_possible_from_frequency,
    emission_possible_from_wavelength,
    linear_stopping_voltage_from_frequency,
    linear_stopping_voltage_from_wavelength,
    physical_stopping_voltage_from_frequency,
    physical_stopping_voltage_from_wavelength,
)


__all__ = [
    "DEFAULT_CONFIGURATION",
    "ELECTRONVOLT_J",
    "ELEMENTARY_CHARGE_C",
    "HC_OVER_CHARGE_V_M",
    "METRES_PER_NANOMETRE",
    "NANOMETRES_PER_METRE",
    "OFFICIAL_MATERIALS",
    "PLANCK_CONSTANT_J_S",
    "PLANCK_OVER_CHARGE_V_S",
    "PhotoelectricMaterial",
    "SPEED_OF_LIGHT_M_S",
    "Task04Configuration",
    "cutoff_frequency_hz",
    "cutoff_wavelength_m",
    "emission_possible_from_frequency",
    "emission_possible_from_wavelength",
    "linear_stopping_voltage_from_frequency",
    "linear_stopping_voltage_from_wavelength",
    "physical_stopping_voltage_from_frequency",
    "physical_stopping_voltage_from_wavelength",
    "validate_material_collection",
]
