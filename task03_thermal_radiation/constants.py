"""Exact physical constants for Task 3.

The defining SI constants are kept in one side-effect-free module. Derived
constants are calculated from those values so the implementation and its
documented identities cannot drift apart.
"""

from __future__ import annotations

import math
from typing import Final


PLANCK_CONSTANT_J_S: Final[float] = 6.62607015e-34
SPEED_OF_LIGHT_M_S: Final[float] = 299_792_458.0
BOLTZMANN_CONSTANT_J_K: Final[float] = 1.380649e-23
MOLAR_GAS_CONSTANT_J_MOL_K: Final[float] = 8.31446261815324

EINSTEIN_DEBYE_FACTOR: Final[float] = (math.pi / 6.0) ** (1.0 / 3.0)

PLANCK_RADIANCE_PREFACTOR: Final[float] = (
    2.0 * PLANCK_CONSTANT_J_S * SPEED_OF_LIGHT_M_S**2
)
PLANCK_EXPONENT_CONSTANT_M_K: Final[float] = (
    PLANCK_CONSTANT_J_S * SPEED_OF_LIGHT_M_S / BOLTZMANN_CONSTANT_J_K
)

STEFAN_BOLTZMANN_CONSTANT_W_M2_K4: Final[float] = (
    2.0
    * math.pi**5
    * BOLTZMANN_CONSTANT_J_K**4
    / (15.0 * PLANCK_CONSTANT_J_S**3 * SPEED_OF_LIGHT_M_S**2)
)

WIEN_PEAK_EXPONENT: Final[float] = 4.965114231744277
WIEN_DISPLACEMENT_CONSTANT_M_K: Final[float] = (
    PLANCK_EXPONENT_CONSTANT_M_K / WIEN_PEAK_EXPONENT
)

METRES_PER_NANOMETRE: Final[float] = 1.0e-9


__all__ = [
    "BOLTZMANN_CONSTANT_J_K",
    "EINSTEIN_DEBYE_FACTOR",
    "METRES_PER_NANOMETRE",
    "MOLAR_GAS_CONSTANT_J_MOL_K",
    "PLANCK_CONSTANT_J_S",
    "PLANCK_EXPONENT_CONSTANT_M_K",
    "PLANCK_RADIANCE_PREFACTOR",
    "SPEED_OF_LIGHT_M_S",
    "STEFAN_BOLTZMANN_CONSTANT_W_M2_K4",
    "WIEN_DISPLACEMENT_CONSTANT_M_K",
    "WIEN_PEAK_EXPONENT",
]
