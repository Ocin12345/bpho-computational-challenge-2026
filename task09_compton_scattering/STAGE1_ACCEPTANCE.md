# Task 9 Stages 0–1 acceptance

Status: **PASS**

## Stage 0: official scope

The Task 9 pages were read from the official BPhO 2026 course ZIP. The source
file, page range, file sizes and SHA-256 digests are recorded in
[`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md). The required five-energy
study and all three outputs are frozen without adding an extension to the core
scope.

## Stage 1: mathematical model

[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md) derives the wavelength shift,
scattered photon energy, relativistic recoil speed and recoil angle from
energy–momentum conservation. It includes independent formulations for each
requested quantity, explicit units, modern SI/CODATA constants, exact endpoints,
low-energy limits and a complete conservation-residual matrix.

The forward endpoint is handled honestly: at exactly $\theta=0^\circ$ the electron
has zero momentum and no defined direction, while the continuous plotted limit is
$\phi=90^\circ$. The later data format must preserve this distinction.

## Frozen acceptance evidence

- Official independent variable: $0^\circ\leq\theta\leq180^\circ$.
- Official example energies: 50, 100, 200, 500 and 1000 keV.
- Required outputs: $\Delta\lambda/\lambda$, $v$ and $\phi$.
- Relativistic speed model retained for the complete energy range.
- Quadrant-safe recoil-angle definition selected.
- Energy, both momentum components and the electron mass shell designated as
  pointwise validation invariants.
- Five-energy backscatter and right-angle anchors independently calculated and
  recorded.
- Optional cross-section physics explicitly excluded from the core curves.

Stages 0 and 1 are complete. Implementation can proceed without unresolved
scientific conventions.
