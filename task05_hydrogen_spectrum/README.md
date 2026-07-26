# Task 5: Hydrogen Spectrum and the Bohr Model

## Status

Stages 1--12 are complete. The official scope and numerical specification are
frozen; the deterministic package implements all ten levels and 45 declared
downward level pairs; all 30 independent validation checks pass; five data
artifacts and six publication-quality PNG/SVG figure pairs regenerate
transactionally; and the complete figure set has been inspected for scientific
accuracy, legibility, and label collisions.

The full acceptance evidence is recorded in
[`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md). The scientific conclusions and
limitations are documented in
[`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md). The optional
extension was explicitly deferred in
[`EXTENSION_DECISION.md`](EXTENSION_DECISION.md) so the official graph remains
the focus. The one-slide competition package is available in
[`presentation/task05`](../presentation/task05/README.md).

## Completed implementation

- `constants.py`, `models.py`, `transitions.py`, and `analysis.py` build the
  immutable stationary-nucleus Bohr study;
- `reference.py` and `validation.py` provide the independent Decimal/Rydberg
  comparison and structured 30-check report;
- `generate_task05.py` writes deterministic CSV/JSON evidence and coordinates
  complete generation;
- `plotting.py` builds the validated figure package in both PNG and SVG; and
- 42 focused tests cover physics, structure, corrupted inputs, output schemas,
  byte reproducibility, figure dimensions, and rollback after late failure.

Regenerate and verify the current baseline with:

```bash
python3 -m task05_hydrogen_spectrum.generate_task05
python3 -m task05_hydrogen_spectrum.validate_task05
python3 -m unittest discover -s task05_hydrogen_spectrum -p 'test_*.py' -q
```

## Official sources reviewed

The Task 5 scope comes from both files in the official 2026 challenge download:

1. page 2 of **BPhO ComPhys Challenge 2026**, the three-page written brief; and
2. slides 29--38 of **BPhO CompPhys2026 Quantum**, the 76-slide presentation.

Slide 29 begins the hydrogen-spectrum material. Slide 38 contains the Task 5
instruction. Slide 39 begins Task 6, so it is outside this task.

## Official objective

The mandatory task is to create a graph of photon energy against wavelength
for photons emitted by hydrogen atoms when electrons move between energy
levels.

The accompanying slides derive the ideal Bohr energy levels, connect the
emission wavelengths to the Rydberg/Balmer relationship, and explain the
standing-wave interpretation of quantized angular momentum. The required
computational output is the discrete emission-transition graph, not a
classical electron-orbit simulation.

## Core physical model

For the ideal stationary-nucleus Bohr model of hydrogen,

$$
E_n=-\frac{E_{\mathrm R}}{n^2},
\qquad n=1,2,3,\ldots,
$$

where $E_{\mathrm R}=hcR_\infty\approx13.606\ \mathrm{eV}$ is the Rydberg
energy. For a downward transition from $n_i$ to $n_f$, with $n_i>n_f$,

$$
E_\gamma=E_{n_i}-E_{n_f}
=E_{\mathrm R}\left(\frac{1}{n_f^2}-\frac{1}{n_i^2}\right)>0.
$$

The emitted photon's vacuum wavelength and frequency are

$$
\lambda=\frac{hc}{E_\gamma},
\qquad
f=\frac{E_\gamma}{h}=\frac{c}{\lambda}.
$$

Equivalently,

$$
\frac{1}{\lambda}
=R_\infty\left(\frac{1}{n_f^2}-\frac{1}{n_i^2}\right).
$$

All emitted photons therefore obey $E_\gamma=hc/\lambda$, but hydrogen emits
only at the discrete points selected by integer energy-level differences.

## Frozen transition scope

The baseline study will include the first ten Bohr levels and every valid
downward transition between them:

$$
1\leq n_f<n_i\leq10.
$$

This gives

$$
\binom{10}{2}=45
$$

unique emissions. The main named series are:

| Series | Final level | Initial levels in the study | Main region |
| --- | :---: | :---: | --- |
| Lyman | $n_f=1$ | $2$--$10$ | Ultraviolet |
| Balmer | $n_f=2$ | $3$--$10$ | Ultraviolet and visible |
| Paschen | $n_f=3$ | $4$--$10$ | Infrared |
| Brackett | $n_f=4$ | $5$--$10$ | Infrared |
| Pfund | $n_f=5$ | $6$--$10$ | Infrared |

These five series contain 35 transitions. The remaining ten transitions end
at $n_f=6$--$9$ and will remain in the machine-readable evidence and appear as
one subdued “higher series” group on the complete graph. They will not be
silently discarded or given more visual prominence than the official
Lyman--Pfund teaching sequence.

## Required graph design

The principal figure will plot the 45 discrete emitted-photon energies in
electronvolts against vacuum wavelength in nanometres. It will:

1. use a logarithmic wavelength axis so ultraviolet, visible, and infrared
   transitions remain legible together;
2. colour points by final-level series;
3. show, but not connect, the discrete transition points;
4. include a restrained $E_\gamma=hc/\lambda$ guide;
5. shade the declared $380$--$750\ \mathrm{nm}$ visible band;
6. label selected named lines without overcrowding the graph;
7. distinguish the 35 Lyman--Pfund transitions from the ten higher-series
   transitions; and
8. state explicitly that the vertical position is photon energy, not the
   electron's negative bound-state energy.

## Frozen baseline scope

The Task 5 baseline will:

1. use Python, NumPy, and Matplotlib;
2. implement the ideal Bohr and Rydberg equations directly;
3. calculate all 45 downward transitions among $n=1$--$10$;
4. retain joules, electronvolts, hertz, metres, and nanometres with explicit
   conversions;
5. generate the required photon-energy-versus-wavelength comparison;
6. create supporting Bohr-level, Balmer-spectrum, series-convergence, and
   validation figures;
7. save deterministic CSV and JSON evidence;
8. validate the model through a numerically independent reference path;
9. explain the ideal model, physical interpretation, and limitations; and
10. prepare a concise one-slide contribution to the final screencast.

This is a deterministic calculation over 45 transitions. It does not require
random seeds, repeated trials, time stepping, GPU acceleration, or the RTX
4090 laptop.

## Declared high-standard evidence

The completed model will check that:

- every stored level follows the $-E_{\mathrm R}/n^2$ law;
- the 45 ordered level pairs are unique and complete;
- every downward transition has positive photon energy;
- the photon energy equals the difference between the two Bohr levels;
- $E_\gamma\lambda=hc$ and $f\lambda=c$ throughout the study;
- the transition wavelengths independently satisfy the Rydberg equation;
- Lyman-$\alpha$, Lyman-$\beta$, H-$\alpha$, H-$\beta$, H-$\gamma$, and
  H-$\delta$ agree with frozen ideal-model reference values;
- each series converges monotonically toward its analytical limit;
- the visible-band classification is consistent with the declared
  $380$--$750\ \mathrm{nm}$ convention;
- all results are finite, deterministic, and unit-consistent; and
- deliberately corrupted levels, transitions, or labels make validation fail.

These checks validate the ideal Bohr calculation. They are not a claim that
the model reproduces fine structure or every measured hydrogen wavelength.

## Supporting figure package

After the mandatory graph passes validation, the baseline will add:

- a Bohr energy-level diagram with representative downward transitions;
- a wavelength-accurate Balmer line spectrum with no invented intensity
  scale;
- a series-convergence comparison showing the analytical limits;
- a quantitative validation figure; and
- a 16:9 Task 5 summary figure.

The one-slide competition presentation will keep the required graph dominant.
Supporting material will be included only when it adds explanatory value at
final video resolution.

## Optional-extension boundary

The official brief does not require a Task 5 animation. A reduced-mass
comparison or a compact energy-level transition animation may be considered
only after the entire deterministic baseline is complete and visually
accepted.

Any extension must remain separate from the authoritative ideal Bohr model.
It must not delay the required graph or imply that the Bohr model predicts
line intensity, selection rules, linewidth, fine structure, or a literal
classical orbit.

## Explicit exclusions from the baseline

The baseline will not model:

- reduced electron--proton mass corrections;
- fine, hyperfine, or Lamb-shift structure;
- Zeeman or Stark splitting;
- transition probabilities or spectral-line intensities;
- Doppler, pressure, or natural linewidths;
- orbital angular-momentum and spin selection rules;
- many-electron atoms or molecular spectra;
- classical radiative electron trajectories; or
- experimental fitting.

These are real refinements, but they are not needed to satisfy the official
Bohr-model emission task.

## Staged delivery plan

| Stage | Deliverable | Completion evidence |
| ---: | --- | --- |
| 1 | Requirements and scope | Official files read; mandatory graph, baseline, extensions, and exclusions fixed |
| 2 | Mathematical specification | Equations, constants, domains, transition catalogue, anchors, and tolerances fixed |
| 3 | Architecture | Public APIs, immutable records, output schemas, tests, and reproducibility contract accepted |
| 4 | Physical model | Constants, levels, transition equations, and focused tests implemented |
| 5 | Complete study | All 10 levels and 45 downward transitions assembled immutably |
| 6 | Validation | Independent references, named-line checks, limits, and failure injection complete |
| 7 | Numerical evidence | Deterministic CSV and JSON outputs generated transactionally |
| 8 | Figures | Mandatory and supporting PNG/SVG figures generated and visually inspected |
| 9 | Scientific explanation | Results, interpretation, assumptions, and limitations documented |
| 10 | Optional-extension decision | Animation or reduced-mass comparison approved or rejected explicitly |
| 11 | Presentation package | Editable slide, preview, assets, speaker notes, and timed script complete |
| 12 | Final acceptance | Clean regeneration, complete tests, visual review, hygiene, and synchronization pass |

## Acceptance boundary for the complete task

Task 5 will be accepted only when:

- the required energy-versus-wavelength graph is generated from our own code;
- all 45 declared transitions are represented in numerical evidence;
- the named spectral series and higher-series group are labelled honestly;
- equations, quantum numbers, constants, units, and model boundaries are
  explicit and consistent;
- all pre-declared analytical and numerical checks pass;
- data and figures regenerate deterministically from clean commands;
- every final figure is inspected at original and presentation resolution;
- the physical interpretation and limitations are scientifically clear;
- the final slide and narration are complete; and
- the repository is clean, private, and synchronized with GitHub.

## Stage 1 completion check

Stage 1 is complete because both official files have been read, slides 29--38
have been isolated as the Task 5 range, the exact mandatory graph has been
identified, the ideal Bohr baseline has been separated from optional
refinements, the finite transition catalogue and supporting evidence are
defined, and the acceptance boundary is fixed before coding.

## Stage 2 completion check

Stage 2 is complete because:

- the Bohr levels, transition energies, frequencies, wavelengths, and series
  limits are dimensionally defined;
- exact SI values and the frozen 2022 CODATA Rydberg constant are recorded;
- the ideal stationary-nucleus convention is explicit;
- all 45 finite-study transitions and their ordering are fixed;
- reference energies, named wavelengths, series limits, visible-band rules,
  and graph domains are frozen;
- validation tolerances were declared before implementation;
- serialization, visual, performance, and reproducibility requirements are
  explicit; and
- the assumptions and excluded real-hydrogen refinements are documented.

The full details are in
[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md).

## Stages 3--10 completion check

- **Stage 3:**
  [`ADR-001`](architecture/ADR-001-deterministic-hydrogen-spectrum.md) records
  a small deterministic NumPy package with immutable records, validation-first
  outputs, and transactional generation.
- **Stages 4 and 5:** ten exact integer levels and all 45 ordered downward
  pairs are implemented without mutation or hidden filtering.
- **Stage 6:** the 30-check validation report covers independent energies,
  wavelengths, frequencies, identities, named anchors, series limits, labels,
  ordering, completeness, positivity, and region classification.
- **Stage 7:** energy levels, transitions, limits, validation, and a
  reproducibility manifest are exported deterministically in `data/task05/`.
- **Stage 8:** the mandatory graph and five supporting figures are available
  in `figures/task05/` as presentation-resolution PNG and editable SVG; every
  final PNG has been visually inspected.
- **Stage 9:** the scientific interpretation distinguishes photon energy from
  bound-state energy, finite lines from analytical limits, and computational
  verification from experimental validation.
- **Stage 10:** animation and reduced-mass work were deferred because neither
  improves the required result enough to justify extra competition-video time.

## Stages 11 and 12 completion check

- **Stage 11:** the editable 16:9 PowerPoint, two embedded validated visuals,
  47-word narration, speaker notes, six copied assets, and 2401-by-1350 preview
  pass the presentation validator and reproduce byte for byte.
- **Stage 12:** 30/30 scientific checks, 42 focused tests, and all 415 repository
  tests pass; clean out-of-tree data and figure regeneration is byte-identical;
  visual, link, syntax, whitespace, and credential-pattern checks pass.

Task 5 is ready for review and a user-directed commit/push. No Git release
action is performed automatically by the local acceptance run.
