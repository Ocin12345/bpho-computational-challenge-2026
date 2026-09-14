"""Generate one publication-style extension figure for every BPhO task."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "figures" / "advanced"
EVIDENCE = ROOT / "data" / "advanced_extensions.json"
COLORS = ("#2a776e", "#bb5f48", "#b28a36", "#5275a9")


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "figure.dpi": 160,
            "savefig.dpi": 220,
            "savefig.bbox": "tight",
        }
    )


def _save(figure: plt.Figure, number: str) -> None:
    figure.suptitle(f"Task {number} advanced extension", fontsize=16, x=0.08, ha="left")
    figure.savefig(OUTPUT / f"task{number}_extension.png", facecolor="white")
    figure.savefig(OUTPUT / f"task{number}_extension.svg", facecolor="white")
    plt.close(figure)


def _morph_density(coefficients: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    axis = np.linspace(-5.0, 5.0, 320)
    x, z = np.meshgrid(axis, axis)
    y = 0.42 * z
    r2 = x * x + y * y + z * z + 0.08
    basis = np.stack(
        (
            x * y,
            y * z,
            (2.0 * z * z - x * x - y * y) / np.sqrt(3.0),
            x * z,
            (x * x - y * y) / 2.0,
        )
    ) / r2
    amplitude = np.einsum("i,ijk->jk", coefficients, basis)
    density = amplitude**2 * r2 * np.exp(-0.78 * np.sqrt(r2))
    return axis, axis, density


def generate() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    tasks = payload["tasks"]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _style()

    task = tasks["01"]
    figure, axis = plt.subplots(figsize=(8.2, 4.8))
    dimension = [row["dimension"] for row in task["metrics"]]
    axis.plot(dimension, [row["msd_slope"] for row in task["metrics"]], "o-", label="MSD slope")
    axis.plot(dimension, [2 * row["rms_exponent"] for row in task["metrics"]], "s--", label="2 × RMS exponent")
    axis.axhline(1, color="0.45", lw=1, ls=":", label="diffusive prediction")
    axis.set(xlabel="dimension", ylabel="fitted scaling quantity", xticks=dimension, ylim=(0.97, 1.025))
    axis.legend(frameon=False)
    _save(figure, "01")

    task = tasks["02"]; figure, axes = plt.subplots(1, 2, figsize=(9.2, 4.6))
    axes[0].bar(["target", "initial", "final"], [task["metrics"][key] for key in ("target_temperature_k", "initial_temperature_k", "final_temperature_k")], color=COLORS[:3]); axes[0].set_ylabel("kinetic temperature / K")
    axes[1].bar(["gas–gas", "gas–tracer"], [task["metrics"]["gas_gas_impulses"], task["metrics"]["gas_tracer_contacts"]], color=COLORS[:2]); axes[1].set_ylabel("resolved impulses")
    axes[0].set_title(f"energy drift = {task['metrics']['relative_kinetic_energy_drift']:.2e}")
    axes[1].set_title("all contacts resolved")
    _save(figure, "02")

    task = tasks["03"]; figure, axis = plt.subplots(figsize=(8.2, 4.8)); temperature = task["reference"]["temperature_k"]
    axis.scatter(temperature, task["reference"]["cp_j_mol_k"], s=20, c="black", label="White–Collocott reference", zorder=3)
    axis.plot(temperature, task["debye_fit"]["predicted_cp_j_mol_k"], color=COLORS[0], label=f"Debye, RMSE {task['debye_fit']['rms_error_j_mol_k']:.3f}")
    axis.plot(temperature, task["einstein_fit"]["predicted_cp_j_mol_k"], color=COLORS[1], ls="--", label=f"Einstein, RMSE {task['einstein_fit']['rms_error_j_mol_k']:.3f}")
    axis.set(xlabel="temperature / K", ylabel=r"$C_p$ / J mol$^{-1}$ K$^{-1}$"); axis.legend(frameon=False)
    _save(figure, "03")

    task = tasks["04"]; figure, axes = plt.subplots(1, 2, figsize=(9.2, 4.6))
    axes[0].bar(["synthetic", "Millikan 1916"], np.abs([100*task["synthetic_recovery"]["relative_planck_bias"], 100*task["millikan"]["relative_difference_from_modern_h"]]), color=COLORS[:2]); axes[0].set(ylabel="absolute difference from modern h / %", title="constant recovery")
    axes[1].bar(["h", "work function"], 100*np.array([task["synthetic_recovery"]["planck_95_percent_coverage"], task["synthetic_recovery"]["work_function_95_percent_coverage"]]), color=COLORS[:2]); axes[1].axhline(95, color="0.35", ls=":"); axes[1].set(ylabel="95% interval coverage / %", ylim=(88, 100), title="600 seeded experiments")
    _save(figure, "04")

    task = tasks["05"]; figure, axis = plt.subplots(figsize=(8.2, 4.8)); labels = ["Lyman-α", "Balmer-α"]; natural = np.array([task["lyman_alpha"]["natural_fwhm_hz"], task["balmer_alpha_component"]["natural_fwhm_hz"]]); doppler = np.array([task["lyman_alpha"]["doppler_fwhm_hz"], task["balmer_alpha_component"]["doppler_fwhm_hz"]]); x = np.arange(2); width = 0.34
    axis.bar(x-width/2, natural/1e6, width, label="natural", color=COLORS[0]); axis.bar(x+width/2, doppler/1e6, width, label="Doppler", color=COLORS[1]); axis.set(xticks=x, xticklabels=labels, ylabel="FWHM / MHz", yscale="log"); axis.legend(frameon=False)
    _save(figure, "05")

    task = tasks["06"]; figure, axis = plt.subplots(figsize=(8.2, 4.8)); axis.plot(task["profile"]["radius_mm"], task["profile"]["normalized_intensity_per_mm"], color=COLORS[0]); axis.set(xlabel="detector radius / mm", ylabel="normalised intensity / mm$^{-1}$");
    for ring in task["rings"]: axis.axvline(ring["radius_mm"], color=COLORS[1], lw=.8, alpha=.55); axis.text(ring["radius_mm"], axis.get_ylim()[1]*.88, f"({ring['h']}{ring['k']}{ring['l']})", rotation=90, va="top", ha="right", fontsize=9)
    _save(figure, "06")

    task = tasks["07"]; figure, axes = plt.subplots(1, 2, figsize=(9.2, 4.6)); axes[0].plot(task["barrier"]["energy_ev"], task["barrier"]["transmission"], color=COLORS[0]); axes[0].axvline(10, color=COLORS[1], ls="--", label="barrier"); axes[0].set(xlabel="energy / eV", ylabel="transmission", title="rectangular barrier"); axes[0].legend(frameon=False)
    states = task["finite_well"]; axes[1].hlines([row["energy_above_bottom_ev"] for row in states], 0, 1, colors=[COLORS[0] if row["parity"] == "even" else COLORS[1] for row in states]); axes[1].axhline(20, color="black", ls=":"); axes[1].set(xlim=(0,1), xticks=[], ylabel="energy above well bottom / eV", title=f"{len(states)} bound states")
    _save(figure, "07")

    task = tasks["08"]; figure, axes = plt.subplots(1, 2, figsize=(9.2, 4.6)); scenarios = list(task["scenarios"]); labels = [x.replace("_", " ") for x in scenarios]; axes[0].bar(labels, [100*task["scenarios"][x]["qber_test"] for x in scenarios], color=COLORS[:3]); axes[0].set(ylabel="test QBER / %", title="eavesdropping signature"); axes[1].bar(labels, [task["scenarios"][x]["secret_key_bits"]/1000 for x in scenarios], color=COLORS[:3]); axes[1].set(ylabel="secret key / kbit", title="after leakage and privacy amplification")
    _save(figure, "08")

    task = tasks["09"]; figure, axis = plt.subplots(figsize=(8.2, 4.8)); axis.plot(task["ideal"]["histogram"]["centres_kev"], task["ideal"]["histogram"]["density_per_kev"], color=COLORS[0], label="free-electron ideal"); axis.plot(task["response"]["histogram"]["centres_kev"], task["response"]["histogram"]["density_per_kev"], color=COLORS[1], label="material + detector"); axis.set(xlabel="measured photon energy / keV", ylabel="probability density / keV$^{-1}$"); axis.legend(frameon=False)
    _save(figure, "09")

    task = tasks["10"]; figure, axes = plt.subplots(1, 3, figsize=(11.2, 4.2)); frame_indices = (0, len(task["m_morph"])//2, len(task["m_morph"])-1)
    for axis, index in zip(axes, frame_indices):
        frame = task["m_morph"][index]; x, z, density = _morph_density(np.asarray(frame["coefficients"])); axis.imshow(density, extent=(x[0], x[-1], z[0], z[-1]), origin="lower", cmap="magma"); axis.set(title=f"morph {frame['progress']:.0%}", xlabel=r"$x/a_0$", ylabel=r"$z/a_0$", xticks=[], yticks=[])
    _save(figure, "10")

    manifest = {
        "schema_version": "advanced-figures-v1",
        "task_count": 10,
        "source": str(EVIDENCE.relative_to(ROOT)),
        "files": [f"task{number:02d}_extension.png" for number in range(1, 11)],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Advanced figures: {len(manifest['files'])} PNG/SVG pairs generated")


if __name__ == "__main__":
    generate()
