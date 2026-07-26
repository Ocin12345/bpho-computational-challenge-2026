# Task 10 — Hydrogenic Orbitals

## Objective

Task 10 asks for probability-density representations of hydrogenic orbitals,
including the S, P, D, F and G families and a semitransparent three-dimensional
“coloured glass” construction. This package computes normalized one-electron
Coulomb eigenstates, validates the radial and angular functions independently,
and presents the result as data, publication figures, an offline explorer and a
4K view-rotation animation.

The separated wavefunction is

$$
\psi_{nlm}(r,\vartheta,\varphi)
=R_{nl}(r)\,\mathcal Y_{lm}(\vartheta,\varphi),
\qquad
\int |\psi_{nlm}|^2\,dV=1,
$$

where \(\mathcal Y_{lm}\) is a normalized real tesseral harmonic. The displayed
field is the probability density \(|\psi|^2\), not a classical electron path.

## Open the explorer

From the repository root:

```bash
python3 -m task10_hydrogenic_orbitals.serve_task10
```

Then open [http://127.0.0.1:4210/](http://127.0.0.1:4210/). The application is
self-contained: it needs no account, framework build, remote font, WebGL layer
or external request.

## How to use it

1. Choose atomic number \(Z\), principal number \(n\), angular number \(l\) and
   magnetic number \(m\). Invalid \(l,m\) combinations are removed automatically.
2. Use the named presets to reach every official 1s, 2p, 3d, 4f and 5g real
   state. There are 25 presets in total.
3. Drag or use the keyboard to orbit the coloured-glass stack. This rotates the
   camera only; the selected energy eigenstate remains stationary.
4. Change the physical half-extent, plane count, relative cutoff and maximum
   opacity. Cutoff and opacity change visibility only and never alter
   \(\int|\psi|^2dV=1\).
5. Compare the three orthogonal slices with the normalized radial probability.
6. Read the energy, effective Bohr length, node counts, parity and \(m\)
   degeneracy from the result cards.

The coordinate convention is standard spherical polar:

$$
x=r\sin\vartheta\cos\varphi,\quad
y=r\sin\vartheta\sin\varphi,\quad
z=r\cos\vartheta,
$$

with polar colatitude \(\vartheta\in[0,\pi]\) and azimuth
\(\varphi\in(-\pi,\pi]\).

## Main result

The complete official gallery contains

- one 1s state;
- three 2p states;
- five 3d states;
- seven 4f states; and
- nine 5g states.

This gives \(1+3+5+7+9=25\); the complete set therefore comprises 25 normalized
real basis states. For the hydrogen 3d, \(m=0\) state used in the required
coloured-glass view:

- \(E_3=-1.510914822816\) eV;
- the effective Bohr length is \(0.529467506530\) Å;
- there are zero radial nodes and two angular nodes;
- parity is even; and
- all five \(m\) states are energy-degenerate in this model.

See [Results and Interpretation](RESULTS_AND_INTERPRETATION.md) for the family
table, scaling laws, node interpretation and limitations of each renderer.

## Reproduce the evidence

```bash
python3 -m task10_hydrogenic_orbitals.generate_task10
python3 -m task10_hydrogenic_orbitals.validate_task10
python3 -m task10_hydrogenic_orbitals.generate_task10_figures
python3 -m task10_hydrogenic_orbitals.validate_task10_app
python3 -m task10_hydrogenic_orbitals.generate_task10_motion
python3 -m task10_hydrogenic_orbitals.validate_task10_motion
python3 -m task10_hydrogenic_orbitals.validate_task10_documentation
python3 -m task10_hydrogenic_orbitals.validate_task10_final
python3 -m unittest discover -s task10_hydrogenic_orbitals -p 'test_*.py'
```

Pinned packages, browser setup, deterministic build order and artifact checks are
in [Reproducibility](REPRODUCIBILITY.md) and
[requirements-task10.txt](requirements-task10.txt).

## Evidence package

Validated data in [data/task10](../data/task10/):

- [orbital_state_catalog.csv](../data/task10/orbital_state_catalog.csv) — all
  204 real basis states through \(n=8\);
- [official_gallery.csv](../data/task10/official_gallery.csv) — the exact 25-state
  S–G gallery;
- [radial_profiles.csv](../data/task10/radial_profiles.csv) and
  [radial_nodes.csv](../data/task10/radial_nodes.csv) — normalized radial evidence;
- [reference_anchors.json](../data/task10/reference_anchors.json) — analytic and
  numerical anchors;
- [validation_report.json](../data/task10/validation_report.json) — 22 independent
  science checks; and
- [manifest.json](../data/task10/manifest.json) — configuration, provenance and
  SHA-256 integrity.

Publication media in [figures/task10](../figures/task10/):

- [required_orbital_gallery](../figures/task10/required_orbital_gallery.png) —
  all 25 states at 3840×2400 and 300 DPI;
- [radial_and_nodal_structure](../figures/task10/radial_and_nodal_structure.png) —
  radial structure at 2400×1500 and 300 DPI;
- [coloured_glass_density](../figures/task10/coloured_glass_density.png) — the
  required semitransparent stack at 3000×1875 and 300 DPI;
- [rendering_comparison](../figures/task10/rendering_comparison.png) — slices,
  isosurface and coloured-glass comparison at 3000×1800 and 300 DPI;
- [task10_summary](../figures/task10/task10_summary.png) — the accepted 4K
  competition plate; and
- [orbital_view_rotation](../figures/task10/orbital_view_rotation.webp) — an
  80-frame, 3840×2160 animated WebP with a
  [reduced-motion poster](../figures/task10/orbital_view_rotation_poster.png)
  and [offline viewer](../figures/task10/orbital_view_rotation_viewer.html).

Vector-safe static graphics have editable SVG and embedded-font PDF companions.
Layered three-dimensional transparency remains raster by design. Times New
Roman is enforced throughout the static figures, motion, explorer and
PowerPoint. The figure and motion manifests bind the media to the passing
scientific-state digest.

## Validation strategy

Production Laguerre, Ferrers, radial, angular and Cartesian wavefunction
calculations are compared with independent formulations. The suite checks radial
and angular normalization, orthogonality, analytic 1s/2s/2p densities, nodes,
parity, expectation values, energy and length scaling, invalid inputs,
immutability, deterministic regeneration and transactional rollback.

JavaScript then matches all 204 Python state summaries. Real-browser acceptance
covers all 25 presets, the \(Z=20,n=8,l=7,m=7\) endpoint, five responsive widths,
keyboard operation, 200% text, forced colours, reduced motion, zero external
requests and a 450 ms interaction budget. The measured maximum gallery update is
67.60 ms in the final acceptance audit.

## Scope boundary

The model is one non-relativistic electron in a point-Coulomb field with reduced
nuclear mass. It excludes electron screening, many-electron correlation,
spin-orbit coupling, fine and hyperfine structure, Lamb shifts and other
radiative effects, finite nuclear size, external electric or magnetic fields,
ionization dynamics, measurement collapse and detector response.

The frozen source interpretation is in
[Official Requirements](OFFICIAL_REQUIREMENTS.md), the derivation is in
[Mathematical Model](MATHEMATICAL_MODEL.md), and motion acceptance is in
[Stage 8 Acceptance](STAGE8_ACCEPTANCE.md). The complete requirement-by-
requirement handoff is in [Final Acceptance](FINAL_ACCEPTANCE.md).
