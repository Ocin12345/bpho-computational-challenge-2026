# Task 6: Electron Diffraction

## Status

Stages 1--12 are locally complete. The approved deterministic model evaluates 401
voltages and 11,386 Bragg-order records; all 39 independent validation checks
and 29 focused tests pass; six data artifacts and six high-resolution PNG/SVG
figure pairs regenerate transactionally; and the figures have passed a
multi-pass scientific and visual review. Results and limitations are recorded
in [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md). The
required baseline remains accepted. A separate relativistic precision comparison is now
implemented in [`relativistic_extension.py`](relativistic_extension.py), while
automatic animation remains deferred in
[`EXTENSION_DECISION.md`](EXTENSION_DECISION.md). The editable one-slide
competition package is in
[`presentation/task06`](../presentation/task06/README.md), and the final local
acceptance evidence is in [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md).

Regenerate and verify the current baseline with:

```bash
python3 -m task06_electron_diffraction.generate_task06
python3 -m task06_electron_diffraction.validate_task06
python3 -m task06_electron_diffraction.generate_relativistic_extension
python3 -m unittest discover -s task06_electron_diffraction -p 'test_*.py' -q
```

## Official sources reviewed

The Task 6 scope comes from both files in the official 2026 challenge download:

1. page 2 of **BPhO ComPhys Challenge 2026**, the three-page written brief; and
2. slides 39--42 of **BPhO CompPhys2026 Quantum**, the 76-slide presentation.

Slide 39 begins the electron-diffraction section. Slides 40 and 41 derive the
electron wavelength, Bragg condition, scattering angle, spherical-screen
geometry, and maximum-order condition. Slide 42 gives Task 6a and the two
graphite spacings. Slide 43 starts the next teaching section, so it is outside
the Task 6 source range.

## Official objective

The mandatory task is to create a computer model of the electron-diffraction
rings on a spherical phosphor screen while the accelerating voltage varies
from 1 to 5 kV. The model must include the two nominal graphite layer spacings

$$
d_1=0.123\ \mathrm{nm},
\qquad
d_2=0.213\ \mathrm{nm},
$$

and use a tube radius of

$$
r=65\ \mathrm{mm}.
$$

The official check is a straight-line graph with
$1/\sqrt{V}$ on the vertical axis and $\sin(\phi/2)$ on the horizontal axis.
Its gradient must recover the corresponding atomic spacing.

## Required physical model

An electron accelerated from rest through a potential difference $V$ gains
non-relativistic kinetic energy

$$
eV=\frac{p^2}{2m_{\mathrm e}},
$$

so its de Broglie wavelength is

$$
\lambda(V)=\frac{h}{\sqrt{2m_{\mathrm e}eV}}.
$$

Bragg's law and the scattering geometry give

$$
2d\sin\theta=n\lambda,
\qquad
\phi=2\theta,
$$

and therefore

$$
q\equiv\sin\frac{\phi}{2}
=\frac{n\lambda}{2d}
=\frac{nh}{2d\sqrt{2m_{\mathrm e}eV}}.
$$

The official written brief defines the projected radius measured from a
photograph as

$$
x=r\sin(2\phi).
$$

The presentation separately derives the full caliper chord

$$
y=2r\sin\phi.
$$

These are different observables. The implementation will use $x$ for the
required ring model and retain $y$ only as an explicitly named supporting
quantity.

## Order and screen conventions

The official maximum Bragg order follows from $q\leq1$:

$$
n_{\mathrm{Bragg,max}}
=\left\lfloor\frac{2d}{\lambda}\right\rfloor.
$$

The pictured phosphor screen is on the forward hemisphere. A ring that lands
there also requires $0\leq\phi\leq90^\circ$, so

$$
q\leq\frac{1}{\sqrt2},
\qquad
n_{\mathrm{screen,max}}
=\left\lfloor\frac{\sqrt2d}{\lambda}\right\rfloor.
$$

The implementation will calculate and store both counts. This preserves the
official mathematical maximum while preventing backward-scattering orders
from being drawn as negative screen radii. The main phosphor-screen image will
show the forward-screen orders. The complete data table will retain every
Bragg-allowed order and label whether it is forward-screen visible.

Ring brightness will be declared schematic. The official equations determine
ring positions, not scattering intensity, structure factors, linewidths, or
detector response.

## Required figures

The baseline figure package will contain:

1. a clean phosphor-screen comparison at 1, 3, and 5 kV, showing both graphite
   families and every forward-screen order without claiming physical
   intensity;
2. a ring-radius-versus-voltage figure with separate panels for the two
   spacings and order encoded without an oversized legend;
3. the mandatory $1/\sqrt{V}$ versus $\sin(\phi/2)$ straight-line validation,
   with both first-order graphite series, fitted gradients, and recovered
   spacings;
4. an all-order normalized validation in which $n/\sqrt{V}$ collapses each
   spacing family onto one line;
5. a compact wavelength and maximum-order diagnostic; and
6. a 16:9 Task 6 summary figure for the final screencast.

The mandatory straight-line graph will remain visually dominant in the
presentation. The model will use the exact trigonometric geometry, not a
small-angle approximation.

## Figure-quality standard

Every analytical figure will be exported as both a high-resolution PNG and an
editable SVG. The PNG target is at least 2400 pixels on the long side at
300 dpi; the 16:9 summary target is 3840 by 2160 pixels. Final outputs must
have:

- readable axes, symbols, units, and legends at full size and slide size;
- a colourblind-safe analytical palette plus redundant line-style or panel
  separation where useful;
- restrained grid lines and no decorative effects that obscure data;
- no clipped text, collisions, hidden series, or unexplained encodings;
- consistent notation and significant figures across figures and tables;
- explicit labels distinguishing geometric visibility from physical
  intensity; and
- visual inspection at original resolution, 16:9 presentation resolution,
  and thumbnail size before acceptance.

The phosphor-screen visual may use a realistic green glow, but all fitted and
quantitative graphs will use a light, print-safe scientific theme.

## Frozen baseline scope

The Task 6 baseline will:

1. use Python, NumPy, SciPy, Matplotlib, and Pillow where needed;
2. implement the official non-relativistic electron wavelength directly;
3. accept voltages continuously on the closed interval 1--5 kV;
4. generate deterministic evidence on a 401-point grid from 1000 to 5000 V
   in 10 V increments;
5. include both nominal graphite spacings exactly as printed;
6. enumerate all valid Bragg orders and classify forward-screen visibility;
7. calculate $\lambda$, $q$, $\theta$, $\phi$, $x$, and $y$ with explicit
   units;
8. produce the required ring model and straight-line recovery of $d$;
9. validate the model through an independent high-precision reference path;
10. save deterministic CSV and JSON evidence transactionally;
11. explain the model, assumptions, branch choices, and limitations; and
12. prepare one concise Task 6 slide and narration segment.

This is a deterministic algebraic model. It requires no random seed, time
integration, GPU acceleration, or RTX 4090 laptop.

## Declared high-standard evidence

The completed model will verify that:

- $eV=p^2/(2m_{\mathrm e})$ and $p\lambda=h$ hold throughout the voltage grid;
- $\lambda\propto V^{-1/2}$ and decreases monotonically from 1 to 5 kV;
- every stored order satisfies the declared Bragg-domain condition;
- each forward-screen ring satisfies $0\leq\phi\leq90^\circ$ and
  $0\leq x\leq r$;
- the calculated angles satisfy both Bragg's law and $\phi=2\theta$;
- the two independent screen observables satisfy
  $x=r\sin(2\phi)$ and $y=2r\sin\phi$;
- the official maximum-order counts agree with independently calculated
  endpoint anchors;
- the first-order radii agree with frozen numerical reference anchors;
- each $1/\sqrt V$ fit is straight through the origin to numerical precision;
- the fitted gradients recover 0.123 nm and 0.213 nm within the declared
  tolerance;
- the all-order normalized data collapse onto two spacing-specific lines;
- invalid voltages, spacings, orders, shapes, or non-finite values fail
  explicitly; and
- deliberately corrupted angles, radii, order labels, or fit records make
  validation fail.

## Numerical evidence package

The planned generated evidence is:

- `data/task06/voltage_sweep.csv` for wavelength and first-order anchors;
- `data/task06/diffraction_orders.csv` for every voltage, spacing, and valid
  Bragg order;
- `data/task06/validation_fits.csv` for gradients, intercept diagnostics,
  goodness of fit, and recovered spacings;
- `data/task06/reference_anchors.json` for frozen endpoint targets;
- `data/task06/validation_report.json` for structured acceptance checks; and
- `data/task06/manifest.json` for output hashes and reproducibility metadata.

## Optional-extension boundary

The required deterministic baseline comes first. After its figures pass
scientific and visual acceptance, one extension may be considered:

- a short voltage-sweep animation of the geometric rings; or
- a separately labelled relativistic-wavelength comparison.

The animation must not invent physical ring intensities. The relativistic
comparison must not replace the official non-relativistic calculation. At
5 kV the correction is small but measurable in a numerical model, so it is a
useful extension only if it remains visually secondary and does not complicate
the three-minute presentation.

## Explicit exclusions from the baseline

The baseline will not model:

- quantitative diffraction-ring intensities;
- graphite structure factors or forbidden reflections;
- finite crystallite size, preferred orientation, or sample thickness;
- multiple scattering, inelastic scattering, or electron absorption;
- beam-energy spread, divergence, aberrations, or magnetic deflection;
- phosphor response, camera distortion, noise, or linewidth fitting;
- relativistic electron momentum; or
- comparison with measured laboratory images.

These are legitimate refinements, but the official data are not sufficient to
constrain them honestly.

## Staged delivery plan

| Stage | Deliverable | Completion evidence |
| ---: | --- | --- |
| 1 | Requirements and scope | Official pages read; mandatory model, graph, geometry, baseline, and exclusions fixed |
| 2 | Mathematical specification | Equations, constants, domains, order rules, anchors, and tolerances fixed |
| 3 | Architecture | Public APIs, immutable records, output schemas, tests, and reproducibility contract accepted |
| 4 | Physical model | Wavelength, Bragg angles, screen geometry, and focused tests implemented |
| 5 | Complete study | Voltage sweep and complete two-spacing order catalogue assembled immutably |
| 6 | Validation | Independent references, order checks, fits, recovery of $d$, and failure injection complete |
| 7 | Numerical evidence | Deterministic CSV and JSON outputs generated transactionally |
| 8 | Figures | Mandatory and supporting PNG/SVG figures generated and visually inspected |
| 9 | Scientific explanation | Results, interpretation, assumptions, branch choices, and limitations documented |
| 10 | Optional-extension decision | Animation or relativistic comparison approved or rejected explicitly |
| 11 | Presentation package | Editable slide, preview, assets, speaker notes, and timed script complete |
| 12 | Final acceptance | Clean regeneration, complete tests, visual review, hygiene, and synchronization pass |

## Acceptance boundary for the complete task

Task 6 will be accepted only when:

- the required ring model spans the full 1--5 kV interval;
- both graphite spacings and all declared orders appear in numerical evidence;
- the distinction between Bragg-allowed and forward-screen-visible orders is
  explicit;
- the exact official geometry is used and $x$ is not confused with $y$;
- the mandatory straight-line graph recovers both atomic spacings;
- equations, constants, units, domains, and model limitations are clear;
- all pre-declared analytical and numerical checks pass;
- data and figures regenerate deterministically from clean commands;
- every final figure passes original-size and presentation-size inspection;
- the final slide and narration are complete; and
- the repository is private, clean, and synchronized with GitHub.

## Stage 1 completion check

Stage 1 is complete because both official files have been read, slides 39--42
have been isolated as the Task 6 range, the two distinct screen measurements
have been resolved, the exact mandatory validation axes have been identified,
and the baseline, optional extensions, exclusions, evidence, and acceptance
boundary have been fixed before coding.

## Stage 2 completion check

Stage 2 is complete because the electron wavelength, Bragg condition,
scattering angle, screen geometry, voltage and spacing domains, order rules,
numerical anchors, fit equations, tolerances, serialization conventions, and
visual requirements are frozen in
[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md).

## Stage 3 completion check

Stage 3 is complete because
[`ADR-001`](architecture/ADR-001-deterministic-electron-diffraction.md)
records the accepted small deterministic NumPy package, immutable data and fit
records, one-way dependency structure, independent reference path,
validation-first transactional generation, six-figure contract, test
boundaries, trade-offs, and revisit triggers. The architecture skill kept the
design proportional to the small algebraic study and prevented unnecessary
service, database, notebook, or field-simulation infrastructure.

## Stages 4--10 completion check

- **Stages 4 and 5:** the exact vectorized model and complete 401-voltage,
  two-spacing, variable-order study are immutable and tested.
- **Stage 6:** 39 independent checks cover wavelengths, orders, angles,
  geometry, visibility, fits, anchors, and deliberate corruption.
- **Stage 7:** six CSV/JSON artifacts regenerate transactionally with stable
  schemas and SHA-256 provenance.
- **Stage 8:** six PNG/SVG figure pairs passed iterative original-size and
  presentation-size review after detected layout defects were corrected.
- **Stage 9:** numerical results, interpretation, geometry branches, and
  scientific limitations are documented in
  [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md).
- **Stage 10:** animation and relativistic correction are explicitly deferred
  in [`EXTENSION_DECISION.md`](EXTENSION_DECISION.md).

## Stages 11 and 12 completion check

- **Stage 11:**
  [`presentation/task06`](../presentation/task06/README.md) contains an
  editable 16:9 PowerPoint, six copied validated assets, a rendered preview,
  slide-content record, 50-word script, speaker notes, generator, and
  structural validator. The academic-presentations workflow kept the required
  graph dominant and reused the accepted scientific figures unchanged.
- **Stage 12:** clean regeneration, 29 tests, 39 scientific checks, artifact
  validation, PowerPoint validation, and visual inspection all pass. The
  detailed evidence and the explicit version-control hand-off are recorded in
  [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md).
