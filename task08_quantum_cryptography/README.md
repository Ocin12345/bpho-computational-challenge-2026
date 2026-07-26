# Task 8 — Quantum mismatch calculator

## Objective

Build the visual calculator requested by BPhO Task 8 and compare the probability
that two photon-polarisation detectors give different outcomes under the supplied
classical and quantum models. Detector A uses angle \(\theta\); detector B uses
angle \(\phi\). Both angles are independently adjustable from \(-90^\circ\) to
\(+90^\circ\).

The required ideal probabilities are

$$
P_{\mathrm C}=1-\cos^2\theta\cos^2\phi-\sin^2\theta\sin^2\phi,
\qquad
P_{\mathrm Q}=\sin^2(\phi-\theta).
$$

The official reference setting is \(\theta=-30^\circ\), \(\phi=+30^\circ\):

$$
P_{\mathrm C}=\frac38=37.5\%,
\qquad
P_{\mathrm Q}=\frac34=75.0\%.
$$

## Open the calculator

From the repository root, start the local server:

```bash
python3 -m task08_quantum_cryptography.serve_task08
```

Then open [http://127.0.0.1:4178/](http://127.0.0.1:4178/). The calculator is a
self-contained static application: it makes no external network request and does
not require an account, build step or web framework.

## How to use it

1. Change either detector with its slider, number input or a named reference
   preset. The dials show the physical detector orientations and the relative
   angle.
2. Read the exact classical and quantum mismatch values on one fixed 0–100%
   scale. The signed card reports \(P_{\mathrm Q}-P_{\mathrm C}\) in percentage
   points.
3. Use the full-angle graph to see how both models change while detector A is
   fixed and detector B rotates. Solid orange is classical; dashed teal is
   quantum.
4. Optionally choose a photon count and reproducible seed. This produces one
   finite binomial sample for each model while keeping exact theory visibly
   separate.

The finite-photon panel is an educational extension, not part of the required
ideal-probability calculation and not a cryptographically secure random-number
generator.

## Why the curves differ

The supplied classical comparison combines the two Malus-law outcomes
independently. It retains the detectors' absolute orientations through
\(\cos(2\theta)\cos(2\phi)\). The quantum model depends only on the relative
angle \(\phi-\theta\). Their difference simplifies to

$$
P_{\mathrm Q}-P_{\mathrm C}
=-\frac12\sin(2\theta)\sin(2\phi).
$$

Consequently, equal settings always give zero quantum mismatch, whereas the
classical comparison can still give a non-zero value. The maximum possible
signed contrast is \(\pm 50\) percentage points. See
[`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md) for the full
derivation and careful physical interpretation.

## Reproduce the evidence

From the repository root:

```bash
python3 -m task08_quantum_cryptography.generate_task08
python3 -m task08_quantum_cryptography.generate_task08_statistics
python3 -m task08_quantum_cryptography.generate_task08_figures
python3 -m task08_quantum_cryptography.validate_task08
python3 -m task08_quantum_cryptography.validate_task08_statistics
python3 -m task08_quantum_cryptography.validate_task08_app
python3 -m task08_quantum_cryptography.validate_task08_documentation
python3 -m task08_quantum_cryptography.validate_task08_final
python3 -m unittest discover -s task08_quantum_cryptography -p 'test_*.py'
```

The accepted environment is frozen in [`requirements-task08.txt`](requirements-task08.txt).
Browser-test setup, determinism boundaries and the complete command sequence are
documented in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

## Evidence package

Validated data:

- [`angle_sweep.csv`](../data/task08/angle_sweep.csv) — 361 detector-B settings
  at 0.5° spacing with detector A fixed at −30°;
- [`mismatch_grid.csv`](../data/task08/mismatch_grid.csv) — 181 × 181 full-angle
  comparison grid;
- [`reference_cases.json`](../data/task08/reference_cases.json) — exact anchor
  cases;
- [`validation_report.json`](../data/task08/validation_report.json) — 42 core
  checks;
- [`finite_photon_reference.json`](../data/task08/finite_photon_reference.json)
  and [`statistical_validation_report.json`](../data/task08/statistical_validation_report.json)
  — the separately validated sampling extension;
- core and statistical manifests with SHA-256 hashes.

Publication figures:

- [`probability_sweep`](../figures/task08/probability_sweep.png);
- [`mismatch_landscape`](../figures/task08/mismatch_landscape.png);
- [`finite_photon_sampling`](../figures/task08/finite_photon_sampling.png);
- [`task08_summary`](../figures/task08/task08_summary.png).

Each publication figure has editable SVG and PDF companions. The three analytical
figures are 2400 × 1500 at 300 DPI; the summary is 3840 × 2160 at 300 DPI.
All labels and mathematics use embedded Times New Roman, with strict font checks
in the generator and an integrity manifest at
[`figures/task08/manifest.json`](../figures/task08/manifest.json). Accepted 4K
application captures use the same font and their digest manifest is in
[`figures/task08/screenshots`](../figures/task08/screenshots/).

The conclusion-led panel hierarchy, source-data mapping, export specification and
review-risk checks are recorded in [`FIGURE_CONTRACT.md`](FIGURE_CONTRACT.md).

## Validation strategy

The production equations are checked against algebraically independent
double-angle references on both the sweep and the two-dimensional grid. The
suite also checks probability complements and bounds, symmetry, periodicity,
the equal-setting quantum diagonal, exact named cases, immutable arrays,
cross-language agreement, deterministic regeneration and transactional rollback.
The final artifact gate then verifies eight groups spanning the core and
statistical reports, source provenance, publication and browser manifests,
documentation, the offline app and the competition presentation.

The optional statistical layer has separate Python and JavaScript tests for the
pseudo-random sequence, stream separation, binomial counting, boundary cases,
Wilson intervals, residuals and shared fixtures. Browser tests cover the live
361-point graph, all interaction routes, a 100,000-pair sample, keyboard use,
320 px reflow, 200% text resizing, contrast, reduced motion and forced colours.

## Scope boundary

This is the Task 8 comparison calculator, not a complete quantum-key-distribution
protocol. It assumes ideal entangled pairs, perfect two-outcome detectors, no
loss, no dark counts, no decoherence and no eavesdropper. It does not implement
key sifting, error correction, privacy amplification or security proofs. The
"classical" curve is specifically the comparison expression supplied by the
official task; it is not a claim about every classical or hidden-variable model.

The frozen equations and assumptions are in
[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md), and the completion evidence is
recorded in [`STAGE7_ACCEPTANCE.md`](STAGE7_ACCEPTANCE.md) and
[`STAGE8_ACCEPTANCE.md`](STAGE8_ACCEPTANCE.md). The competition slide and its
acceptance record are in [`presentation/task08`](../presentation/task08/README.md).
The complete requirement-by-requirement handoff is in
[`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md).
