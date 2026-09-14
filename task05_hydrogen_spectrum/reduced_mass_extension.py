"""Optional reduced-mass refinement for the Task 5 hydrogen spectrum.

The accepted competition baseline uses an infinitely massive nucleus.  This
module keeps that result untouched and applies the leading finite-proton-mass
correction as a separate, deterministic extension.
"""

from __future__ import annotations

import math
from numbers import Real

import numpy as np
from numpy.typing import ArrayLike, NDArray

from task05_hydrogen_spectrum.models import (
    transition_energy_ev,
    transition_frequency_hz,
    transition_wavelength_m,
)


ELECTRON_PROTON_MASS_RATIO_TEXT = "5.446170214889e-4"
ELECTRON_PROTON_MASS_RATIO = float(ELECTRON_PROTON_MASS_RATIO_TEXT)
CONSTANT_SOURCE = "NIST 2022 CODATA recommended values"

FloatArray = NDArray[np.float64]


def _finite_non_negative_ratio(value: Real) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("electron_nucleus_mass_ratio must be a real number")
    ratio = float(value)
    if not math.isfinite(ratio):
        raise ValueError("electron_nucleus_mass_ratio must be finite")
    if ratio < 0.0:
        raise ValueError("electron_nucleus_mass_ratio must be non-negative")
    return ratio


def reduced_mass_factor(
    electron_nucleus_mass_ratio: Real = ELECTRON_PROTON_MASS_RATIO,
) -> float:
    """Return ``mu / m_e = 1 / (1 + m_e / M)``.

    A zero ratio is the infinite-nuclear-mass limit and therefore returns one.
    """

    ratio = _finite_non_negative_ratio(electron_nucleus_mass_ratio)
    return 1.0 / (1.0 + ratio)


def reduced_mass_transition_energy_ev(
    initial_n: ArrayLike,
    final_n: ArrayLike,
    *,
    electron_nucleus_mass_ratio: Real = ELECTRON_PROTON_MASS_RATIO,
) -> FloatArray:
    """Return photon energies after the leading reduced-mass correction."""

    factor = reduced_mass_factor(electron_nucleus_mass_ratio)
    return np.asarray(
        transition_energy_ev(initial_n, final_n) * factor,
        dtype=np.float64,
    )


def reduced_mass_transition_frequency_hz(
    initial_n: ArrayLike,
    final_n: ArrayLike,
    *,
    electron_nucleus_mass_ratio: Real = ELECTRON_PROTON_MASS_RATIO,
) -> FloatArray:
    """Return corrected emitted-photon frequencies."""

    factor = reduced_mass_factor(electron_nucleus_mass_ratio)
    return np.asarray(
        transition_frequency_hz(initial_n, final_n) * factor,
        dtype=np.float64,
    )


def reduced_mass_transition_wavelength_m(
    initial_n: ArrayLike,
    final_n: ArrayLike,
    *,
    electron_nucleus_mass_ratio: Real = ELECTRON_PROTON_MASS_RATIO,
) -> FloatArray:
    """Return corrected vacuum wavelengths.

    Since the reduced-mass factor decreases the Rydberg wavenumber, every
    wavelength is longer than its infinite-mass baseline by ``1 + m_e / M``.
    """

    factor = reduced_mass_factor(electron_nucleus_mass_ratio)
    return np.asarray(
        transition_wavelength_m(initial_n, final_n) / factor,
        dtype=np.float64,
    )


__all__ = [
    "CONSTANT_SOURCE",
    "ELECTRON_PROTON_MASS_RATIO",
    "ELECTRON_PROTON_MASS_RATIO_TEXT",
    "reduced_mass_factor",
    "reduced_mass_transition_energy_ev",
    "reduced_mass_transition_frequency_hz",
    "reduced_mass_transition_wavelength_m",
]
