"""Precision hydrogen spectroscopy extension for BPhO Task 5.

The official Bohr-level calculation is retained unchanged.  This separate
module adds four layers that explain why a real spectrum contains more than
forty-five infinitely sharp lines:

* exact one-electron Dirac binding energies (fine structure);
* a clearly labelled, 2s-2p anchored pedagogical Lamb-shift scaling;
* electric-dipole selection rules and calculated Einstein A coefficients; and
* natural plus thermal-Doppler linewidths.

The QED scaling is not a precision bound-state-QED calculation.  It reproduces
the hydrogen 2s_1/2 anchor and the leading n^-3 s-state trend so the size and
direction of the Lamb correction can be explored without overstating scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.integrate import quad
from scipy.special import eval_genlaguerre, gammaln

from task05_hydrogen_spectrum.constants import (
    ELECTRONVOLT_J,
    ELEMENTARY_CHARGE_C,
    PLANCK_CONSTANT_J_S,
    SPEED_OF_LIGHT_M_S,
)


FINE_STRUCTURE_CONSTANT = 7.2973525643e-3
ELECTRON_MASS_KG = 9.1093837139e-31
PROTON_MASS_KG = 1.67262192595e-27
VACUUM_PERMITTIVITY_F_M = 8.8541878188e-12
BOLTZMANN_CONSTANT_J_K = 1.380649e-23
BOHR_RADIUS_M = 5.29177210544e-11
HYDROGEN_ATOM_MASS_KG = 1.673532838e-27
LAMB_2S_2P_FREQUENCY_HZ = 1_057_844_000.0


@dataclass(frozen=True)
class SpectralLineProfile:
    """One allowed E1 transition and its idealized linewidth components."""

    wavelength_nm: float
    transition_frequency_hz: float
    einstein_a_per_s: float
    natural_fwhm_hz: float
    doppler_fwhm_hz: float
    voigt_fwhm_hz: float
    radial_matrix_element_m: float
    angular_strength: float


def _validate_state(n: int, l: int, j: float) -> tuple[int, int, float]:
    if isinstance(n, bool) or isinstance(l, bool):
        raise TypeError("n and l must be integers")
    n_value, l_value, j_value = int(n), int(l), float(j)
    if n_value < 1 or l_value < 0 or l_value >= n_value:
        raise ValueError("state requires n >= 1 and 0 <= l < n")
    allowed_j = {l_value - 0.5, l_value + 0.5}
    allowed_j.discard(-0.5)
    if not np.isfinite(j_value) or not any(
        np.isclose(j_value, allowed, atol=1.0e-12, rtol=0.0)
        for allowed in allowed_j
    ):
        raise ValueError("j must equal l-1/2 or l+1/2 (and be non-negative)")
    return n_value, l_value, j_value


def reduced_electron_mass_kg(nuclear_mass_kg: float = PROTON_MASS_KG) -> float:
    mass = float(nuclear_mass_kg)
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("nuclear_mass_kg must be finite and positive")
    return ELECTRON_MASS_KG * mass / (ELECTRON_MASS_KG + mass)


def dirac_binding_energy_ev(
    n: int,
    l: int,
    j: float,
    *,
    atomic_number: int = 1,
    nuclear_mass_kg: float = PROTON_MASS_KG,
) -> float:
    """Return the point-Coulomb Dirac binding energy including reduced mass."""

    n_value, _, j_value = _validate_state(n, l, j)
    if isinstance(atomic_number, bool) or int(atomic_number) < 1:
        raise ValueError("atomic_number must be a positive integer")
    z = int(atomic_number)
    kappa_abs = j_value + 0.5
    za = z * FINE_STRUCTURE_CONSTANT
    if za >= kappa_abs:
        raise ValueError("point-Coulomb state lies beyond the Dirac domain")
    radial_index = n_value - kappa_abs
    denominator = radial_index + np.sqrt(kappa_abs**2 - za**2)
    reduced_mass = reduced_electron_mass_kg(nuclear_mass_kg)
    total_fraction = 1.0 / np.sqrt(1.0 + (za / denominator) ** 2)
    binding_j = reduced_mass * SPEED_OF_LIGHT_M_S**2 * (total_fraction - 1.0)
    return float(binding_j / ELECTRONVOLT_J)


def pedagogical_lamb_shift_ev(n: int, l: int, j: float) -> float:
    """Return an anchored leading s-state Lamb shift, zero for l > 0.

    The calibration is +h*1057.844 MHz for 2s_1/2 relative to 2p_1/2 and
    scales as (2/n)^3.  This is suitable for a scale study, not metrology.
    """

    n_value, l_value, _ = _validate_state(n, l, j)
    if l_value != 0:
        return 0.0
    return float(
        PLANCK_CONSTANT_J_S
        * LAMB_2S_2P_FREQUENCY_HZ
        * (2.0 / n_value) ** 3
        / ELECTRONVOLT_J
    )


def corrected_level_energy_ev(n: int, l: int, j: float) -> float:
    """Return Dirac plus anchored Lamb energy for ordinary hydrogen."""

    return dirac_binding_energy_ev(n, l, j) + pedagogical_lamb_shift_ev(n, l, j)


def e1_transition_allowed(
    initial: tuple[int, int, float],
    final: tuple[int, int, float],
) -> bool:
    """Apply one-electron E1 orbital/parity and total-j selection rules."""

    ni, li, ji = _validate_state(*initial)
    nf, lf, jf = _validate_state(*final)
    if corrected_level_energy_ev(ni, li, ji) <= corrected_level_energy_ev(nf, lf, jf):
        return False
    if abs(li - lf) != 1:
        return False
    delta_j = abs(ji - jf)
    if delta_j > 1.0 + 1.0e-12:
        return False
    if np.isclose(ji, 0.0) and np.isclose(jf, 0.0):
        return False
    return True


def _radial_wavefunction_m_neg_three_halves(
    radius_m: float,
    n: int,
    l: int,
    *,
    bohr_radius_m: float,
) -> float:
    rho = 2.0 * radius_m / (n * bohr_radius_m)
    log_normalization = 0.5 * (
        3.0 * np.log(2.0 / (n * bohr_radius_m))
        + gammaln(n - l)
        - np.log(2.0 * n)
        - gammaln(n + l + 1)
    )
    return float(
        np.exp(log_normalization - rho / 2.0)
        * rho**l
        * eval_genlaguerre(n - l - 1, 2 * l + 1, rho)
    )


@lru_cache(maxsize=256)
def radial_dipole_matrix_element_m(
    initial_n: int,
    initial_l: int,
    final_n: int,
    final_l: int,
) -> float:
    """Return absolute radial integral |integral Rf Ri r^3 dr|."""

    if abs(int(initial_l) - int(final_l)) != 1:
        return 0.0
    if int(initial_n) < 1 or int(final_n) < 1:
        raise ValueError("principal quantum numbers must be positive")
    if not 0 <= int(initial_l) < int(initial_n):
        raise ValueError("invalid initial orbital state")
    if not 0 <= int(final_l) < int(final_n):
        raise ValueError("invalid final orbital state")
    reduced_mass = reduced_electron_mass_kg()
    effective_bohr = BOHR_RADIUS_M * ELECTRON_MASS_KG / reduced_mass

    def integrand(radius_over_a: float) -> float:
        radius = radius_over_a * effective_bohr
        return (
            _radial_wavefunction_m_neg_three_halves(
                radius, int(final_n), int(final_l), bohr_radius_m=effective_bohr
            )
            * _radial_wavefunction_m_neg_three_halves(
                radius, int(initial_n), int(initial_l), bohr_radius_m=effective_bohr
            )
            * radius_over_a**3
            * effective_bohr**4
        )

    value, _ = quad(integrand, 0.0, np.inf, epsabs=1.0e-18, epsrel=2.0e-11, limit=300)
    return abs(float(value))


def shell_averaged_angular_strength(initial_l: int, final_l: int) -> float:
    """Return magnetic-sublevel averaged angular strength for E1 emission."""

    li, lf = int(initial_l), int(final_l)
    if lf == li - 1:
        return li / (2.0 * li + 1.0)
    if lf == li + 1:
        return (li + 1.0) / (2.0 * li + 1.0)
    return 0.0


def transition_profile(
    initial: tuple[int, int, float],
    final: tuple[int, int, float],
    *,
    gas_temperature_k: float = 300.0,
) -> SpectralLineProfile:
    """Calculate E1 rate and natural/Doppler/Voigt FWHM for one line."""

    ni, li, ji = _validate_state(*initial)
    nf, lf, jf = _validate_state(*final)
    if not e1_transition_allowed(initial, final):
        raise ValueError("transition is not electric-dipole allowed")
    temperature = float(gas_temperature_k)
    if not np.isfinite(temperature) or temperature < 0.0:
        raise ValueError("gas_temperature_k must be finite and non-negative")
    energy_ev = corrected_level_energy_ev(ni, li, ji) - corrected_level_energy_ev(nf, lf, jf)
    frequency = energy_ev * ELECTRONVOLT_J / PLANCK_CONSTANT_J_S
    wavelength = SPEED_OF_LIGHT_M_S / frequency
    radial = radial_dipole_matrix_element_m(ni, li, nf, lf)
    angular = shell_averaged_angular_strength(li, lf)
    omega = 2.0 * np.pi * frequency
    einstein_a = (
        omega**3
        * ELEMENTARY_CHARGE_C**2
        * radial**2
        * angular
        / (
            3.0
            * np.pi
            * VACUUM_PERMITTIVITY_F_M
            * (PLANCK_CONSTANT_J_S / (2.0 * np.pi))
            * SPEED_OF_LIGHT_M_S**3
        )
    )
    natural = einstein_a / (2.0 * np.pi)
    doppler = frequency * np.sqrt(
        8.0
        * BOLTZMANN_CONSTANT_J_K
        * temperature
        * np.log(2.0)
        / (HYDROGEN_ATOM_MASS_KG * SPEED_OF_LIGHT_M_S**2)
    )
    voigt = 0.5346 * natural + np.sqrt(0.2166 * natural**2 + doppler**2)
    return SpectralLineProfile(
        wavelength_nm=float(wavelength * 1.0e9),
        transition_frequency_hz=float(frequency),
        einstein_a_per_s=float(einstein_a),
        natural_fwhm_hz=float(natural),
        doppler_fwhm_hz=float(doppler),
        voigt_fwhm_hz=float(voigt),
        radial_matrix_element_m=radial,
        angular_strength=float(angular),
    )


__all__ = [
    "LAMB_2S_2P_FREQUENCY_HZ",
    "SpectralLineProfile",
    "corrected_level_energy_ev",
    "dirac_binding_energy_ev",
    "e1_transition_allowed",
    "pedagogical_lamb_shift_ev",
    "radial_dipole_matrix_element_m",
    "reduced_electron_mass_kg",
    "shell_averaged_angular_strength",
    "transition_profile",
]
