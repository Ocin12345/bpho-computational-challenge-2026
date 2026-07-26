"""Frozen SI and atomic constants for Task 10.

Values follow the 2022 CODATA recommended values. The elementary charge is an
exact SI defining constant; the remaining tabulated quantities retain the
published significant digits.
"""

from __future__ import annotations

from dataclasses import dataclass


CODATA_2022_SOURCE = "https://physics.nist.gov/cuu/pdf/wall_2022.pdf"
SI_DEFINING_CONSTANTS_SOURCE = (
    "https://www.bipm.org/en/measurement-units/si-defining-constants"
)


@dataclass(frozen=True)
class PhysicalConstants:
    """Constants required by the hydrogenic model."""

    electron_mass_kg: float = 9.109_383_713_9e-31
    atomic_mass_constant_kg: float = 1.660_539_068_92e-27
    bohr_radius_m: float = 5.291_772_105_44e-11
    hartree_energy_j: float = 4.359_744_722_206_0e-18
    hartree_energy_ev: float = 27.211_386_245_981
    elementary_charge_c: float = 1.602_176_634e-19
    angstrom_m: float = 1.0e-10


CONSTANTS = PhysicalConstants()
