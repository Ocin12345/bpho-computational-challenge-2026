"""Deterministic Task 5 transition enumeration and human-readable labels."""

from __future__ import annotations

import math
from numbers import Integral, Real


SERIES_NAMES: dict[int, str] = {
    1: "Lyman",
    2: "Balmer",
    3: "Paschen",
    4: "Brackett",
    5: "Pfund",
    6: "Humphreys",
}

LINE_SUFFIXES: dict[int, str] = {
    1: "alpha",
    2: "beta",
    3: "gamma",
    4: "delta",
}

HIGHER_SERIES_DISPLAY_GROUP = "Higher series (n_f>=6)"


def _positive_integer(value: Integral, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < 1:
        raise ValueError(f"{name} must be positive")
    return normalized


def enumerate_transition_pairs(maximum_level: Integral) -> tuple[tuple[int, int], ...]:
    """Return ``(initial_n, final_n)`` pairs in frozen final-first order."""

    maximum = _positive_integer(maximum_level, name="maximum_level")
    if maximum < 2:
        raise ValueError("maximum_level must be at least 2")
    return tuple(
        (initial_n, final_n)
        for final_n in range(1, maximum)
        for initial_n in range(final_n + 1, maximum + 1)
    )


def series_name_for_final(final_n: Integral) -> str:
    """Return the established or unambiguous series label."""

    final = _positive_integer(final_n, name="final_n")
    return SERIES_NAMES.get(final, f"n_f={final} series")


def display_group_for_final(final_n: Integral) -> str:
    """Return the principal-figure legend group for one final level."""

    final = _positive_integer(final_n, name="final_n")
    return (
        SERIES_NAMES[final]
        if final <= 5
        else HIGHER_SERIES_DISPLAY_GROUP
    )


def line_name_for_transition(
    initial_n: Integral,
    final_n: Integral,
) -> str | None:
    """Return a conventional alpha--delta label where declared."""

    initial = _positive_integer(initial_n, name="initial_n")
    final = _positive_integer(final_n, name="final_n")
    if initial <= final:
        raise ValueError("emission requires initial_n > final_n")
    offset = initial - final
    suffix = LINE_SUFFIXES.get(offset)
    if suffix is None or final > 6:
        return None
    prefix = "H" if final == 2 else series_name_for_final(final)
    return f"{prefix}-{suffix}"


def spectral_region_for_wavelength_nm(
    wavelength_nm: Real,
    *,
    visible_min_nm: Real,
    visible_max_nm: Real,
) -> str:
    """Classify a positive finite wavelength by the frozen band convention."""

    values = (wavelength_nm, visible_min_nm, visible_max_nm)
    if any(isinstance(value, bool) or not isinstance(value, Real) for value in values):
        raise TypeError("wavelength and visible limits must be real numbers")
    wavelength, lower, upper = (float(value) for value in values)
    if not all(math.isfinite(value) for value in (wavelength, lower, upper)):
        raise ValueError("wavelength and visible limits must be finite")
    if wavelength <= 0.0 or lower <= 0.0 or upper <= lower:
        raise ValueError("wavelength must be positive and visible limits ordered")
    if wavelength < lower:
        return "ultraviolet"
    if wavelength <= upper:
        return "visible"
    return "infrared"


__all__ = [
    "HIGHER_SERIES_DISPLAY_GROUP",
    "LINE_SUFFIXES",
    "SERIES_NAMES",
    "display_group_for_final",
    "enumerate_transition_pairs",
    "line_name_for_transition",
    "series_name_for_final",
    "spectral_region_for_wavelength_nm",
]
