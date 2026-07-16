"""Exact SI constants and unit conversions for Task 4."""

from __future__ import annotations

from typing import Final


PLANCK_CONSTANT_J_S: Final[float] = 6.62607015e-34
ELEMENTARY_CHARGE_C: Final[float] = 1.602176634e-19
SPEED_OF_LIGHT_M_S: Final[float] = 299_792_458.0

ELECTRONVOLT_J: Final[float] = ELEMENTARY_CHARGE_C
PLANCK_OVER_CHARGE_V_S: Final[float] = (
    PLANCK_CONSTANT_J_S / ELEMENTARY_CHARGE_C
)
HC_OVER_CHARGE_V_M: Final[float] = (
    PLANCK_CONSTANT_J_S * SPEED_OF_LIGHT_M_S / ELEMENTARY_CHARGE_C
)
METRES_PER_NANOMETRE: Final[float] = 1.0e-9
NANOMETRES_PER_METRE: Final[float] = 1.0e9


__all__ = [
    "ELECTRONVOLT_J",
    "ELEMENTARY_CHARGE_C",
    "HC_OVER_CHARGE_V_M",
    "METRES_PER_NANOMETRE",
    "NANOMETRES_PER_METRE",
    "PLANCK_CONSTANT_J_S",
    "PLANCK_OVER_CHARGE_V_S",
    "SPEED_OF_LIGHT_M_S",
]
