# Task 7 — Particle in a Box

## Objective

Solve the one-dimensional infinite square well, plot energy against quantum
number, plot probability density against position, and complete the official
extension by proving that the stationary states obey Heisenberg uncertainty.

The implementation uses an electron in a box of width
\(a=1.00\ \mathrm{nm}\) as its physical baseline while retaining configurable
mass and width parameters.

The official page evidence, source-file sizes and frozen SHA-256 digests are in
[`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md). The accepted environment,
complete build order and artifact contracts are in
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

## Model

For \(0<x<a\),

$$
\psi_n(x,t)=\sqrt{\frac{2}{a}}
\sin\left(\frac{n\pi x}{a}\right)e^{-iE_nt/\hbar},
$$

$$
E_n=\frac{n^2\pi^2\hbar^2}{2ma^2},
$$

and

$$
|\psi_n|^2=\frac{2}{a}\sin^2\left(\frac{n\pi x}{a}\right).
$$

The global phase changes with time, but a single energy eigenstate has a
stationary probability density.

The complete derivation and numerical assumptions are frozen in
[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md). The architecture decision is
recorded in
[`ADR-001`](architecture/ADR-001-analytical-box-with-numerical-validation.md).

## Run the complete study

From the repository root:

```bash
python3 -m pip install -r task07_particle_in_box/requirements-task07.txt
python3 -m task07_particle_in_box.generate_task07
```

This validates the study before atomically replacing all Task 7 data and
figures. Run the validation independently with:

```bash
python3 -m task07_particle_in_box.validate_task07
python3 -m task07_particle_in_box.validate_task07_documentation
python3 -m task07_particle_in_box.validate_task07_final
```

Run the focused tests with:

```bash
python3 -m unittest discover -s task07_particle_in_box -p 'test_*.py'
```

## Evidence package

Data:

- [`energy_levels.csv`](../data/task07/energy_levels.csv)
- [`stationary_states.csv`](../data/task07/stationary_states.csv)
- [`expectation_values.csv`](../data/task07/expectation_values.csv)
- [`numerical_eigenvalues.csv`](../data/task07/numerical_eigenvalues.csv)
- [`reference_anchors.json`](../data/task07/reference_anchors.json)
- [`validation_report.json`](../data/task07/validation_report.json)
- [`manifest.json`](../data/task07/manifest.json)

Figures:

- [`energy_spectrum`](../figures/task07/energy_spectrum.png)
- [`probability_densities`](../figures/task07/probability_densities.png)
- [`wavefunctions_and_density`](../figures/task07/wavefunctions_and_density.png)
- [`energy_level_wavefunctions`](../figures/task07/energy_level_wavefunctions.png)
- [`uncertainty_principle`](../figures/task07/uncertainty_principle.png)
- [`task07_summary`](../figures/task07/task07_summary.png)

Every figure also has an editable SVG version. Analytical figures are
2400 by 1500 pixels; the summary is 3840 by 2160 pixels.

## Uncertainty-principle extension

The completed LaTeX report is available as editable source and compiled PDF:

- [`particle_in_box_uncertainty.tex`](../reports/task07/particle_in_box_uncertainty.tex)
- [`particle_in_box_uncertainty.pdf`](../reports/task07/particle_in_box_uncertainty.pdf)
- [`particle_in_box_uncertainty_accessible.md`](../reports/task07/particle_in_box_uncertainty_accessible.md)
- [`report manifest`](../reports/task07/manifest.json)

The PDF is the visually accepted four-page A4 version. Because the original PDF
compiler did not produce structural tags, the semantic Markdown version with
descriptive figure alternatives is a required accessible companion.

The key result is

$$
\Delta x\Delta p
=\hbar\sqrt{\frac{n^2\pi^2}{12}-\frac12}
\geq\frac{\hbar}{2}.
$$

## Validation strategy

The analytical model is checked against high-precision scalar references and a
separate finite-difference Hamiltonian. The numerical eigensolver uses grids
from 100 to 1600 interior points and does not insert the analytical energy
formula. The acceptance suite covers energy scaling, boundary conditions,
normalisation, orthogonality, nodes, expectation values, uncertainty,
eigenvalue convergence, eigenfunction overlap, deterministic regeneration and
transaction rollback.

## Interpretation

This is an ideal one-dimensional, non-relativistic, single-particle model with
infinite walls. It does not claim to model finite-barrier tunnelling,
interactions, spin dynamics, external fields or relativistic effects.

See [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md) for the
numerical results, [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the complete
rebuild and validation route, and [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md)
for the completion checklist.
