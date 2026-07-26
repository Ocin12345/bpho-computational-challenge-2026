# Task 9 — Compton scattering

## Objective

Task 9 asks for three quantities to be plotted against photon scattering angle
\(\theta\) for incident photon energies 50, 100, 200, 500 and 1000 keV:

1. fractional wavelength shift \(\Delta\lambda/\lambda\);
2. electron recoil speed \(v\); and
3. electron recoil angle \(\phi\).

This package solves the exact relativistic free-electron collision, validates
energy and two-component momentum conservation, and provides a separate optional
Klein–Nishina angular-weighting extension.

The core equations are

$$
\frac{\Delta\lambda}{\lambda}
=\frac{E}{m_ec^2}(1-\cos\theta),
\qquad
\frac{E'}{E}
=\frac{1}{1+\frac{E}{m_ec^2}(1-\cos\theta)},
$$

$$
\frac vc=\sqrt{1-\gamma^{-2}},
\qquad
\phi=\operatorname{atan2}\!\left(E'\sin\theta, E-E'\cos\theta\right).
$$

## Open the explorer

From the repository root:

```bash
python3 -m task09_compton_scattering.serve_task09
```

Then open [http://127.0.0.1:4209/](http://127.0.0.1:4209/). The explorer is a
self-contained static application with no account, build step, framework or
external runtime request.

## How to use it

1. Select one of the five official energies or enter any value from 1 to 5000
   keV.
2. Change \(\theta\) from 0° to 180° with the slider, number input or endpoint
   presets.
3. Read the exact wavelength shift, relativistic electron speed, recoil angle,
   scattered-photon energy and electron kinetic energy.
4. Inspect the momentum diagram. Every arrow uses the incident photon momentum
   as its common scale.
5. Compare the five official curves. Colour and line style both identify energy.
6. Treat the green Klein–Nishina section as an optional extension: it weights
   possible angles but does not alter the official kinematic curves.

At exactly \(\theta=0^\circ\), the electron momentum is zero and its direction is
undefined. The recoil-angle graph displays the continuous 90° limit and labels
that convention explicitly. At backscatter, \(\theta=180^\circ\) and
\(\phi=0^\circ\).

## Main result

The fractional shift increases monotonically with angle and is proportional to
incident energy. Electron speed also increases with angle and energy but remains
strictly below \(c\). The recoil angle descends from its undefined 90° forward
limit to 0° at backscatter; for a fixed non-zero \(\theta\), higher-energy photons
produce a smaller \(\phi\).

At the 200 keV, 90° reference view used in the summary:

- \(\Delta\lambda/\lambda=0.391390\);
- \(v/c=0.434186\);
- \(\phi=35.7050^\circ\);
- \(E'=143.741\) keV; and
- \(K=56.2589\) keV.

See [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md) for the full
energy tables, trend derivations and physical limitations.

## Reproduce the evidence

```bash
python3 -m task09_compton_scattering.generate_task09
python3 -m task09_compton_scattering.generate_task09_cross_section
python3 -m task09_compton_scattering.generate_task09_figures
python3 -m task09_compton_scattering.animation
python3 -m task09_compton_scattering.generate_task09_media_manifest
python3 -m task09_compton_scattering.validate_task09
python3 -m task09_compton_scattering.validate_task09_cross_section
python3 -m task09_compton_scattering.validate_task09_app
python3 -m task09_compton_scattering.validate_task09_documentation
python3 -m task09_compton_scattering.validate_task09_final
python3 -m unittest discover -s task09_compton_scattering -p 'test_*.py'
```

Pinned Python packages, browser-test setup and determinism boundaries are in
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) and
[`requirements-task09.txt`](requirements-task09.txt).

## Evidence package

Validated data in [`data/task09`](../data/task09/):

- [`compton_angle_study.csv`](../data/task09/compton_angle_study.csv) — 3605
  official energy-angle states at 0.25° spacing;
- [`energy_summary.csv`](../data/task09/energy_summary.csv) — one summary row per
  official energy;
- [`reference_anchors.json`](../data/task09/reference_anchors.json) — independent
  forward, 90° and backscatter anchors;
- [`validation_report.json`](../data/task09/validation_report.json) — 44 core
  scientific checks;
- [`klein_nishina_study.csv`](../data/task09/klein_nishina_study.csv),
  [`klein_nishina_summary.csv`](../data/task09/klein_nishina_summary.csv) and
  [`cross_section_validation_report.json`](../data/task09/cross_section_validation_report.json)
  — the separately validated 30-check extension; and
- core and extension manifests containing SHA-256 hashes and provenance.

Publication media in [`figures/task09`](../figures/task09/):

- [`required_kinematics`](../figures/task09/required_kinematics.png);
- [`energy_transfer_geometry`](../figures/task09/energy_transfer_geometry.png);
- [`klein_nishina_extension`](../figures/task09/klein_nishina_extension.png);
- [`task09_summary`](../figures/task09/task09_summary.png); and
- [`compton_angle_sweep.gif`](../figures/task09/compton_angle_sweep.gif).

Each static PNG has editable SVG and PDF companions. Every label, equation and
annotation uses Times New Roman; SVG text remains editable and each PDF embeds
the TrueType font. The first three PNGs are 2400 × 1500 at 300 DPI; the summary
is 3840 × 2160 at 300 DPI. The animation is 1600 × 900 with 73 full frames.
[`manifest.json`](../figures/task09/manifest.json) binds all 13 media files to
their dimensions, font contract and SHA-256 digests.

The finished one-slide competition deck, timed narration and inspected 300-DPI
preview are in the [`Task 9 PowerPoint pack`](../presentation/task09/README.md).

## Validation strategy

The production implementation is compared with an independent scalar reference
across all 3605 states. The suite also checks exact endpoints, bounds,
energy conservation, both momentum components, the electron mass shell,
immutable arrays, deterministic regeneration and rollback.

The Klein–Nishina total cross-section is checked against independent 256-node
Gauss–Legendre integration. JavaScript tests compare every core and extension
state with the Python data. Real-browser tests cover exact output states, five
breakpoints, keyboard use, contrast, 320 px reflow, 200% text size, display
preferences and the 100 ms latency budget.

## Scope boundary

The required model is one photon scattering from one initially stationary, free
electron. It does not model atomic binding, material attenuation, multiple
scattering, polarised beams, detector response, finite resolution or experimental
background. The optional Klein–Nishina section adds an ideal single-electron
angular cross-section only; it is not a material transport or detector simulation.

The frozen scope is in [`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md), the
derivation is in [`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md), and the visual
acceptance record is in [`STAGE8_ACCEPTANCE.md`](STAGE8_ACCEPTANCE.md). The
repository-wide closeout is in [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md).
