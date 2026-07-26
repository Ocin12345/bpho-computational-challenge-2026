"""Independent scalar Decimal references for Task 5 validation."""

from __future__ import annotations

from decimal import Decimal, localcontext
from numbers import Integral

from task05_hydrogen_spectrum.constants import (
    ELEMENTARY_CHARGE_TEXT,
    PLANCK_CONSTANT_TEXT,
    RYDBERG_CONSTANT_TEXT,
    SPEED_OF_LIGHT_TEXT,
)


def _positive_integer(value: Integral, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < 1:
        raise ValueError(f"{name} must be positive")
    return normalized


def _constants() -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    h = Decimal(PLANCK_CONSTANT_TEXT)
    c = Decimal(SPEED_OF_LIGHT_TEXT)
    e = Decimal(ELEMENTARY_CHARGE_TEXT)
    rydberg = Decimal(RYDBERG_CONSTANT_TEXT)
    energy_ev = h * c * rydberg / e
    return h, c, e, rydberg, energy_ev


def reference_level_energy_ev(n: Integral) -> float:
    """Return one ideal Bohr level through the independent Decimal path."""

    level = _positive_integer(n, name="n")
    with localcontext() as context:
        context.prec = 50
        *_, energy_ev = _constants()
        return float(-energy_ev / (Decimal(level) ** 2))


def _transition_factor(initial_n: Integral, final_n: Integral) -> Decimal:
    initial = _positive_integer(initial_n, name="initial_n")
    final = _positive_integer(final_n, name="final_n")
    if initial <= final:
        raise ValueError("emission requires initial_n > final_n")
    return Decimal(1) / (Decimal(final) ** 2) - Decimal(1) / (
        Decimal(initial) ** 2
    )


def reference_transition_energy_ev(
    initial_n: Integral,
    final_n: Integral,
) -> float:
    """Return positive photon energy from exact decimal level factors."""

    with localcontext() as context:
        context.prec = 50
        *_, energy_ev = _constants()
        return float(energy_ev * _transition_factor(initial_n, final_n))


def reference_transition_frequency_hz(
    initial_n: Integral,
    final_n: Integral,
) -> float:
    """Return frequency from the independent Rydberg wavenumber form."""

    with localcontext() as context:
        context.prec = 50
        _, c, _, rydberg, _ = _constants()
        return float(c * rydberg * _transition_factor(initial_n, final_n))


def reference_transition_wavelength_nm(
    initial_n: Integral,
    final_n: Integral,
) -> float:
    """Return wavelength from the independent Rydberg wavenumber form."""

    with localcontext() as context:
        context.prec = 50
        *_, rydberg, _ = _constants()
        factor = _transition_factor(initial_n, final_n)
        return float(Decimal("1e9") / (rydberg * factor))


def reference_series_limit_energy_ev(final_n: Integral) -> float:
    """Return the analytical series-limit energy in electronvolts."""

    final = _positive_integer(final_n, name="final_n")
    with localcontext() as context:
        context.prec = 50
        *_, energy_ev = _constants()
        return float(energy_ev / (Decimal(final) ** 2))


def reference_series_limit_wavelength_nm(final_n: Integral) -> float:
    """Return the analytical series-limit wavelength in nanometres."""

    final = _positive_integer(final_n, name="final_n")
    with localcontext() as context:
        context.prec = 50
        *_, rydberg, _ = _constants()
        return float(Decimal("1e9") * (Decimal(final) ** 2) / rydberg)


__all__ = [
    "reference_level_energy_ev",
    "reference_series_limit_energy_ev",
    "reference_series_limit_wavelength_nm",
    "reference_transition_energy_ev",
    "reference_transition_frequency_hz",
    "reference_transition_wavelength_nm",
]
