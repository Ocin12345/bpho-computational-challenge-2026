"""Generate the integrated Tasks 1--10 advanced-extension evidence bundle."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.integrate import trapezoid

from task02_brownian_motion.brownian_motion import BrownianParameters
from task02_brownian_motion.thermal_bath_extension import (
    run_maxwellian_hard_disc_simulation,
)
from task03_thermal_radiation.experimental_fit_extension import (
    COPPER_REFERENCE_CP_J_MOL_K,
    COPPER_REFERENCE_TEMPERATURE_K,
    fit_copper_heat_capacity,
)
from task04_photoelectric_effect.measurement_extension import (
    millikan_1916_planck_estimate,
    run_recovery_study,
)
from task05_hydrogen_spectrum.precision_spectroscopy_extension import (
    corrected_level_energy_ev,
    dirac_binding_energy_ev,
    pedagogical_lamb_shift_ev,
    transition_profile,
)
from task06_electron_diffraction.intensity_extension import (
    powder_profile,
    powder_ring,
)
from task07_particle_in_box.constants import (
    ELECTRON_MASS_KG,
    REDUCED_PLANCK_CONSTANT_J_S,
)
from task07_particle_in_box.finite_well_extension import (
    finite_square_well_states,
    gaussian_wavepacket_evolution,
    rectangular_barrier_transmission,
)
from task08_quantum_cryptography.bb84_extension import (
    BB84Configuration,
    simulate_bb84,
)
from task09_compton_scattering.detector_extension import (
    DetectorResponseConfiguration,
    simulate_detector_response,
)
from task10_hydrogenic_orbitals.constants import CONSTANTS
from task10_hydrogenic_orbitals.molecular_hybrid_extension import (
    SCREENED_ATOMS,
    electron_count,
    h2plus_overlap,
    hybrid_coefficients,
    independent_electron_density_m_neg_three,
    m_state_morph,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_OUTPUT = ROOT / "data/advanced_extensions.json"
DEFAULT_SITE_OUTPUT = ROOT / "site/data/advanced-extensions.json"


def _native(value: Any) -> Any:
    """Recursively convert NumPy/dataclass values into strict JSON values."""

    if hasattr(value, "__dataclass_fields__"):
        return _native(asdict(value))
    if isinstance(value, dict):
        return {str(key): _native(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_native(item) for item in value]
    if isinstance(value, np.ndarray):
        return _native(value.tolist())
    if isinstance(value, (np.floating, float)):
        result = float(value)
        if not np.isfinite(result):
            raise ValueError("advanced evidence contains a non-finite float")
        return result
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def _task01() -> dict[str, Any]:
    source = ROOT / "site/data/task-01-dimensions-validation.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    dimensions = payload["dimensions"]
    return {
        "title": "Dimensional random walks",
        "status": "complete",
        "summary": "Exact isotropic fixed-step walks in 1D, 2D and 3D.",
        "metrics": [
            {
                "dimension": item["dimension"],
                "msd_slope": item["fit"]["slope"],
                "rms_exponent": item["fit"]["exponent"],
                "sample_count": item["distribution"]["sample_count"],
            }
            for item in dimensions
        ],
        "checks": {
            "source_evidence_accepted": payload.get("accepted") is True,
            "three_dimensions_present": [item["dimension"] for item in dimensions]
            == [1, 2, 3],
        },
    }


def _task02() -> dict[str, Any]:
    diagnostics = run_maxwellian_hard_disc_simulation(
        BrownianParameters(
            n_small=64,
            box_size_nm=8.0,
            max_time_ps=2.0,
            max_collision_passes=32,
            seed=2026,
        )
    )
    return {
        "title": "Maxwellian many-particle Brownian bath",
        "status": "complete",
        "summary": "Every gas-gas and gas-tracer contact is resolved without random direction resets.",
        "metrics": _native(diagnostics),
        "checks": {
            "gas_gas_collisions": diagnostics.gas_gas_impulses > 0,
            "gas_tracer_collisions": diagnostics.gas_tracer_contacts > 0,
            "energy_conservation": abs(diagnostics.relative_kinetic_energy_drift) < 2.0e-12,
            "exact_target_temperature": abs(
                diagnostics.initial_temperature_k / diagnostics.target_temperature_k - 1.0
            )
            < 1.0e-12,
        },
    }


def _task03() -> dict[str, Any]:
    debye = fit_copper_heat_capacity(model="debye")
    einstein = fit_copper_heat_capacity(model="einstein")
    low = COPPER_REFERENCE_TEMPERATURE_K <= 50.0
    debye_low = float(np.sqrt(np.mean(debye.residuals_j_mol_k[low] ** 2)))
    einstein_low = float(np.sqrt(np.mean(einstein.residuals_j_mol_k[low] ** 2)))
    return {
        "title": "Copper calorimetry fit",
        "status": "complete",
        "summary": "Debye, electronic and dilation terms fitted to critically evaluated 1-300 K copper data.",
        "source": {
            "citation": "G. K. White and S. J. Collocott, J. Phys. Chem. Ref. Data 13, 1251 (1984)",
            "doi": "10.1063/1.555728",
            "data_kind": "critically evaluated calorimetry reference table",
        },
        "reference": {
            "temperature_k": COPPER_REFERENCE_TEMPERATURE_K,
            "cp_j_mol_k": COPPER_REFERENCE_CP_J_MOL_K,
        },
        "debye_fit": _native(debye),
        "einstein_fit": _native(einstein),
        "checks": {
            "copper_scale_recovered": 250.0 < debye.characteristic_temperature_k < 450.0,
            "debye_rmse_below_0_45": debye.rms_error_j_mol_k < 0.45,
            "debye_better_below_50_k": debye_low < 0.5 * einstein_low,
        },
    }


def _task04() -> dict[str, Any]:
    planck, planck_sem, relative = millikan_1916_planck_estimate()
    recovery = run_recovery_study(experiment_count=600, seed=91)
    return {
        "title": "Inverse photoelectric metrology",
        "status": "complete",
        "summary": "Weighted inference recovers h and work function with covariance and Monte Carlo coverage.",
        "source": {
            "citation": "R. A. Millikan, Physical Review 7, 355-388 (1916), Table II",
            "doi": "10.1103/PhysRev.7.355",
            "data_kind": "nine historical measured h/e slopes",
        },
        "millikan": {
            "planck_estimate_j_s_using_modern_e": planck,
            "standard_error_j_s": planck_sem,
            "relative_difference_from_modern_h": relative,
        },
        "synthetic_recovery": _native(recovery),
        "checks": {
            "historical_estimate_within_one_percent": abs(relative) < 0.01,
            "monte_carlo_bias_below_0_25_percent": abs(recovery.relative_planck_bias) < 0.0025,
            "coverage_above_90_percent": recovery.planck_95_percent_coverage > 0.90,
        },
    }


def _task05() -> dict[str, Any]:
    lyman = transition_profile((2, 1, 1.5), (1, 0, 0.5), gas_temperature_k=300.0)
    balmer = transition_profile((3, 1, 1.5), (2, 0, 0.5), gas_temperature_k=300.0)
    fine_split = dirac_binding_energy_ev(2, 1, 1.5) - dirac_binding_energy_ev(2, 1, 0.5)
    lamb_shift = pedagogical_lamb_shift_ev(2, 0, 0.5)
    return {
        "title": "Precision hydrogen spectrum",
        "status": "complete",
        "summary": "Dirac fine structure, anchored Lamb scale, E1 rates and natural/Doppler line widths.",
        "source": {
            "selection_rules": "NIST Atomic Spectroscopy Compendium, spectral-line selection rules",
            "lamb_anchor": "hydrogen 2s1/2-2p1/2 frequency scale, 1057.844 MHz",
        },
        "lyman_alpha": _native(lyman),
        "balmer_alpha_component": _native(balmer),
        "fine_structure_2p_ev": fine_split,
        "lamb_2s_ev": lamb_shift,
        "corrected_2s_ev": corrected_level_energy_ev(2, 0, 0.5),
        "checks": {
            "lyman_rate_anchor": 6.0e8 < lyman.einstein_a_per_s < 6.6e8,
            "lyman_wavelength_anchor": 121.4 < lyman.wavelength_nm < 121.7,
            "fine_structure_positive": 1.0e-5 < fine_split < 1.0e-4,
            "thermal_width_exceeds_natural": lyman.voigt_fwhm_hz > lyman.natural_fwhm_hz,
        },
    }


def _task06() -> dict[str, Any]:
    rings = (
        powder_ring(4000.0, 1, 0, 0),
        powder_ring(4000.0, 1, 1, 0),
        powder_ring(4000.0, 0, 0, 2),
    )
    maximum = max(ring.radius_mm + 6.0 * ring.radial_fwhm_mm for ring in rings)
    radius = np.linspace(0.0, maximum, 1200)
    profile = powder_profile(radius, rings)
    return {
        "title": "Graphite ring intensity and width",
        "status": "complete",
        "summary": "AB structure factors, multiplicity, Debye-Waller damping and finite detector/crystallite widths.",
        "rings": [_native(ring) for ring in rings],
        "profile": {"radius_mm": radius, "normalized_intensity_per_mm": profile},
        "checks": {
            "official_100_spacing": abs(rings[0].spacing_nm - 0.213) < 0.001,
            "official_110_spacing": abs(rings[1].spacing_nm - 0.123) < 0.001,
            "profile_normalized": abs(float(trapezoid(profile, radius)) - 1.0) < 1.0e-6,
            "finite_widths": all(ring.radial_fwhm_mm > 0.0 for ring in rings),
        },
    }


def _task07() -> dict[str, Any]:
    states = finite_square_well_states(1.0e-9, 20.0)
    energies = np.linspace(0.5, 24.0, 240)
    transmission = rectangular_barrier_transmission(energies, 10.0, 0.45e-9)
    width = 1.0e-9
    revival = 4.0 * ELECTRON_MASS_KG * width**2 / (
        np.pi * REDUCED_PLANCK_CONSTANT_J_S
    )
    position = np.linspace(0.0, width, 1201)
    times = np.asarray([0.0, 0.125 * revival, 0.25 * revival, 0.5 * revival, revival])
    packet = gaussian_wavepacket_evolution(
        position,
        times,
        box_width_m=width,
        centre_m=0.32e-9,
        spatial_sigma_m=0.06e-9,
        mean_wavenumber_per_m=35.0e9,
        maximum_state=160,
    )
    return {
        "title": "Finite confinement and wave packets",
        "status": "complete",
        "summary": "Finite-well bound states, evanescent tunnelling and basis-exact packet revival.",
        "finite_well": [_native(state) for state in states],
        "barrier": {"energy_ev": energies, "transmission": transmission},
        "wavepacket": {
            "time_fraction_of_revival": times / revival,
            "expected_position_nm": packet.expected_position_m * 1.0e9,
            "norm": packet.norm,
            "revival_time_fs": revival * 1.0e15,
        },
        "checks": {
            "seven_or_more_bound_states": len(states) >= 7,
            "all_bound_below_barrier": all(state.energy_above_bottom_ev < 20.0 for state in states),
            "packet_norm": float(np.max(np.abs(packet.norm - 1.0))) < 2.0e-9,
            "tunnelling_bounded": bool(np.all((transmission >= 0.0) & (transmission <= 1.0))),
        },
    }


def _task08() -> dict[str, Any]:
    scenarios = {}
    for label, eve in (("secure", 0.0), ("partial_eve", 0.20), ("full_eve", 1.0)):
        result = simulate_bb84(
            BB84Configuration(
                photon_count=80_000,
                eve_intercept_probability=eve,
                seed=2026,
            )
        )
        scenarios[label] = {
            "eve_intercept_probability": eve,
            "sifted_bits": result.sifted_bits,
            "qber_test": result.qber_test,
            "phase_error_upper_bound": result.phase_error_upper_bound,
            "reconciliation_leakage_bits": result.reconciliation_leakage_bits,
            "secret_key_bits": result.secret_key_bits,
            "eve_known_fraction_before_privacy": result.eve_known_fraction_before_privacy_amplification,
            "aborted": result.aborted,
            "key_match": bool(np.array_equal(result.alice_secret_key, result.bob_secret_key)),
        }
    return {
        "title": "Finite-key BB84",
        "status": "complete",
        "summary": "Prepare-measure BB84 with Eve, loss/dark-count hooks, sifting, QBER, leakage and Toeplitz privacy amplification.",
        "scenarios": scenarios,
        "checks": {
            "secure_key_generated": scenarios["secure"]["secret_key_bits"] > 1000,
            "partial_eve_key_matches": scenarios["partial_eve"]["key_match"],
            "full_eve_quarter_qber": 0.23 < scenarios["full_eve"]["qber_test"] < 0.27,
            "full_eve_aborts": scenarios["full_eve"]["aborted"],
        },
    }


def _histogram(values: np.ndarray, edges: np.ndarray) -> dict[str, Any]:
    density, _ = np.histogram(values, bins=edges, density=True)
    return {
        "centres_kev": 0.5 * (edges[:-1] + edges[1:]),
        "density_per_kev": density,
    }


def _task09() -> dict[str, Any]:
    ideal = simulate_detector_response(
        DetectorResponseConfiguration(
            event_count=25_000,
            binding_energy_kev=0.0,
            doppler_sigma_fraction=0.0,
            multiple_scatter_probability=0.0,
            detector_noise_fwhm_kev=0.0,
            detector_stochastic_fwhm_sqrt_kev=0.0,
            detector_constant_fwhm_fraction=0.0,
            seed=2026,
        )
    )
    response = simulate_detector_response(
        DetectorResponseConfiguration(event_count=25_000, seed=2026)
    )
    edges = np.linspace(20.0, 205.0, 150)
    return {
        "title": "Compton material and detector response",
        "status": "complete",
        "summary": "Klein-Nishina events with binding/Doppler width, second scatters and detector resolution.",
        "ideal": {
            "mean_energy_kev": ideal.measured_mean_energy_kev,
            "standard_deviation_kev": ideal.measured_standard_deviation_kev,
            "histogram": _histogram(ideal.measured_energy_kev, edges),
        },
        "response": {
            "mean_energy_kev": response.measured_mean_energy_kev,
            "standard_deviation_kev": response.measured_standard_deviation_kev,
            "multiple_scatter_fraction": response.multiple_scatter_fraction,
            "histogram": _histogram(response.measured_energy_kev, edges),
        },
        "checks": {
            "response_broadens_spectrum": response.measured_standard_deviation_kev > ideal.measured_standard_deviation_kev,
            "multiple_scatter_fraction": 0.15 < response.multiple_scatter_fraction < 0.21,
            "mean_energy_reduced": response.measured_mean_energy_kev < ideal.measured_mean_energy_kev,
        },
    }


def _task10() -> dict[str, Any]:
    hybrid_metrics = {}
    for kind in ("sp", "sp2", "sp3"):
        _, coefficients = hybrid_coefficients(kind)
        gram = coefficients @ coefficients.conjugate().T
        hybrid_metrics[kind] = {
            "count": len(coefficients),
            "maximum_orthogonality_error": float(np.max(np.abs(gram - np.eye(len(gram))))),
            "coefficients": np.real(coefficients),
        }
    separations = np.linspace(0.0, 8.0, 81)
    overlaps = np.asarray([h2plus_overlap(value) for value in separations])
    radius = np.linspace(0.0, 60.0 * CONSTANTS.bohr_radius_m, 80_001)
    atom_counts = {}
    for element in SCREENED_ATOMS:
        density = independent_electron_density_m_neg_three(element, radius)
        integrated = float(trapezoid(4.0 * np.pi * radius**2 * density, radius))
        atom_counts[element] = {
            "expected_electrons": electron_count(element),
            "integrated_electrons": integrated,
            "subshells": _native(SCREENED_ATOMS[element]),
        }
    morph = []
    for progress in np.linspace(0.0, 1.0, 41):
        states, coefficients = m_state_morph(2, float(progress))
        morph.append(
            {
                "progress": float(progress),
                "m_values": [state.m for state in states],
                "coefficients": np.real(coefficients),
            }
        )
    return {
        "title": "Beyond one stationary orbital",
        "status": "complete",
        "summary": "Real-m morphs, sp/sp2/sp3 hybrids, H2+ LCAO and screened independent-electron atoms.",
        "hybrids": hybrid_metrics,
        "h2plus": {"separation_over_a0": separations, "overlap": overlaps},
        "screened_atoms": atom_counts,
        "m_morph": morph,
        "checks": {
            "hybrids_orthonormal": all(
                item["maximum_orthogonality_error"] < 3.0e-15
                for item in hybrid_metrics.values()
            ),
            "electron_counts_normalized": all(
                abs(item["integrated_electrons"] - item["expected_electrons"]) < 1.0e-5
                for item in atom_counts.values()
            ),
            "h2_overlap_limits": abs(overlaps[0] - 1.0) < 1.0e-15 and overlaps[-1] < 0.02,
            "actual_state_morph_frames": len(morph) == 41,
        },
    }


def build_payload() -> dict[str, Any]:
    tasks = {
        "01": _task01(),
        "02": _task02(),
        "03": _task03(),
        "04": _task04(),
        "05": _task05(),
        "06": _task06(),
        "07": _task07(),
        "08": _task08(),
        "09": _task09(),
        "10": _task10(),
    }
    checks = [
        bool(passed)
        for task in tasks.values()
        for passed in task["checks"].values()
    ]
    return _native(
        {
            "schema_version": "bpho-advanced-extensions-v1",
            "title": "BPhO Computational Challenge 2026 advanced extensions",
            "core_filming_path_unchanged": True,
            "accepted": all(checks),
            "task_count": len(tasks),
            "check_count": len(checks),
            "passed_check_count": sum(checks),
            "tasks": tasks,
            "scope": [
                "These models extend rather than replace the ten official task models.",
                "Experimental/reference and synthetic data are labelled separately.",
                "BB84 is an educational finite-key model, not a composable security proof.",
                "Compton detector and multi-electron atomic layers are controlled approximations.",
            ],
        }
    )


def write_payload(payload: dict[str, Any], paths: tuple[Path, ...]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-output", type=Path, default=DEFAULT_DATA_OUTPUT)
    parser.add_argument("--site-output", type=Path, default=DEFAULT_SITE_OUTPUT)
    arguments = parser.parse_args()
    payload = build_payload()
    write_payload(payload, (arguments.data_output, arguments.site_output))
    print(
        "Advanced extension evidence: "
        f"{payload['passed_check_count']}/{payload['check_count']} checks pass"
    )
    return 0 if payload["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
