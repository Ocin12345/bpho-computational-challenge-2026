# ADR-001: Deterministic Electron-Diffraction Model

- **Status:** Accepted
- **Date:** 16 July 2026
- **Scope:** Task 6 baseline architecture and reproducibility contract

## Context

Task 6 requires a model of electron-diffraction rings on a spherical phosphor
screen as accelerating voltage varies from 1 to 5 kV. The approved
specification adds two graphite spacings, complete Bragg-order enumeration,
forward-screen classification, the exact photographic geometry, an official
straight-line recovery of each spacing, independent reference checks,
deterministic evidence, publication-quality figures, and a short presentation
contribution.

The study is small: 401 voltage values, two spacings, and at most 24 Bragg
orders for any one voltage--spacing pair. Performance and scale are negligible.
The principal risks are scientific and communicative:

- confusing the electron's negative charge with the positive charge magnitude
  used in the energy gain $eV$;
- mixing volts and kilovolts inside the de Broglie or fit equations;
- using an order whose Bragg ratio exceeds unity;
- confusing all Bragg-allowed orders with rings landing on the pictured
  forward phosphor screen;
- confusing photographic radius $x=r\sin(2\phi)$ with caliper diameter
  $y=2r\sin\phi$;
- applying an inverse sine on the wrong geometric branch;
- validating the model through the same faulty expression that produced it;
- fitting different diffraction orders as if they shared an unnormalized
  gradient;
- implying that schematic brightness is a predicted diffraction intensity;
  and
- producing host-, time-, or render-dependent artifacts.

The project is a small educational scientific package under a fixed
competition deadline. It has no database, network service, real-time
multi-user state, or deployment requirement.

## Options considered

| Option | Strengths | Weaknesses | Complexity | Decision |
| --- | --- | --- | --- | --- |
| One plotting script | Fast initial image | Physics, branch rules, fitting, validation, output, and styling become inseparable | Low initially, high later | Rejected |
| Spreadsheet as source of truth | Permitted and easy to inspect | Awkward variable-order catalogue, weak type and branch contracts, limited automated testing | Medium | Rejected for the primary model |
| Jupyter notebook as source of truth | Convenient exploration | Hidden execution order, mutable state, and weaker clean regeneration | Medium | Rejected |
| Particle or wave-field simulation | Visually impressive | Requires unsupported assumptions about intensity and is unnecessary for Bragg ring positions | High | Rejected |
| Small vectorized NumPy package | Explicit units and domains, complete catalogue, reusable equations, independent tests, deterministic outputs | More files than a script | Low and controlled | **Selected** |

Exploratory notebooks or a later animation may call the tested package, but
they cannot become the authoritative calculation.

## Decision

The baseline will use a small dependency-directed Python package with:

- frozen decimal source constants and one immutable configuration;
- pure vectorized NumPy model functions;
- deterministic voltage, spacing, and order enumeration;
- immutable defensive study, fit, and validation records;
- an independent scalar reference path using `decimal.Decimal` and standard
  library scalar trigonometry without importing the public model;
- validation before any evidence or figure is accepted;
- standard-library CSV and JSON serialization;
- headless Matplotlib rendering from validated records only; and
- command-line runners with meaningful exit statuses.

There will be no network access, database, random-number generator,
GPU-specific path, import-time file write, notebook dependency, current-time
dependency, mutable module-level study, or hidden global model state.

## Frozen repository structure

```text
task06_electron_diffraction/
    README.md
    MATHEMATICAL_MODEL.md
    RESULTS_AND_INTERPRETATION.md
    EXTENSION_DECISION.md
    FINAL_ACCEPTANCE.md
    __init__.py
    constants.py
    configuration.py
    models.py
    orders.py
    reference.py
    analysis.py
    validation.py
    validate_task06.py
    generate_task06.py
    plotting.py
    test_constants_and_configuration.py
    test_models.py
    test_analysis.py
    test_validation.py
    test_generation.py
    test_plotting.py
    architecture/
        ADR-001-deterministic-electron-diffraction.md

data/task06/
    voltage_sweep.csv
    diffraction_orders.csv
    validation_fits.csv
    reference_anchors.json
    validation_report.json
    manifest.json

figures/task06/
    electron_diffraction_rings.png
    electron_diffraction_rings.svg
    ring_radius_vs_voltage.png
    ring_radius_vs_voltage.svg
    straight_line_validation.png
    straight_line_validation.svg
    normalized_order_collapse.png
    normalized_order_collapse.svg
    wavelength_and_orders.png
    wavelength_and_orders.svg
    task06_summary.png
    task06_summary.svg

presentation/task06/
    README.md
    SLIDE_CONTENT.md
    SPEAKER_SCRIPT.md
    Task06_Electron_Diffraction.pptx
```

Stage 3 creates only this ADR and updates the plan status. Later stages own
their declared source and output files and may not add placeholder figures.

## Module responsibilities

| Module | Responsibility | Must not do |
| --- | --- | --- |
| `__init__.py` | Re-export the approved scientific API | Calculate studies, draw figures, or write files |
| `constants.py` | Exact SI source strings, frozen electron mass, and conversions | Define the voltage grid, spacing catalogue, or plot style |
| `configuration.py` | Voltage grid, spacings, tube radius, tolerances, budgets, and schemas | Evaluate diffraction equations |
| `models.py` | Vectorized momentum, wavelength, Bragg, angle, geometry, and maximum-order equations | Know filenames, family labels, expected anchors, or plot choices |
| `orders.py` | Deterministic spacing labels and complete variable-order enumeration | Recalculate wavelength, angles, or radii |
| `reference.py` | Independent scalar wavelength, order, gradient, and anchor targets | Import `models.py`, `analysis.py`, or generated data |
| `analysis.py` | Assemble the immutable complete study and fit records | Write files, choose tolerances, or draw figures |
| `validation.py` | Compare one completed study with independent and structural targets | Repair, filter, or relabel a study |
| `validate_task06.py` | Print validation results and expose pass/fail by exit status | Generate evidence or figures |
| `generate_task06.py` | Validation-first transactional evidence and figure orchestration | Duplicate scientific equations |
| `plotting.py` | Render only a validated study and matching passing report | Recompute diffraction physics or silently filter records |

The dependency direction is one-way:

```text
constants ──> configuration ──> models ──┐
     │                │                  │
     └──> reference ──┼──> validation   │
                      ├──> orders        │
                      └──> analysis <────┘
                         │
                         ├──> plotting
                         └──> command-line runners
```

`reference.py` may import constant source strings, but it may not call public
model functions. `plotting.py` receives a study and the exactly matching
passing report; it cannot rebuild values from raw voltages.

## Immutable records

### `Task06Configuration`

The frozen configuration owns:

- schema version `task06-v1`;
- voltage limits 1000 and 5000 V and 10 V evidence step;
- ordered spacing identifiers `d1` and `d2` with nominal values;
- tube radius 65 mm;
- numerical, fit, and visual tolerances;
- figure dimensions and dpi;
- runtime and output-size budgets; and
- the expected voltage count derived as 401.

Construction rejects booleans, non-finite or non-positive values, a reversed
voltage interval, a step that does not exactly partition the interval,
duplicate spacing identifiers, duplicate or unsorted spacings, negative
tolerances, and non-positive budgets.

### `Task06StudyResult`

The complete study stores read-only arrays for:

- the 401 voltages, electron momenta, and wavelengths;
- the two ordered spacing identifiers and values;
- per-voltage, per-spacing Bragg and screen order maxima;
- one flattened record for every Bragg-allowed order;
- the record's voltage index, spacing index, and integer order;
- Bragg ratio, Bragg angle, scattering angle, photographic radius, and
  caliper diameter;
- immutable order-status labels; and
- the two first-order fit records plus all-order normalized fit records.

The record checks shapes, dtypes, finiteness, positivity, catalogue ordering,
read-only copying, label lengths, index bounds, and unit-array consistency. It
does not decide whether scientifically plausible values pass the independent
report.

### `SpacingFitResult`

Each immutable fit stores spacing identifier, order convention, point count,
constrained gradient, unconstrained gradient and intercept, $R^2$, recovered
spacing, maximum residual, and axis units. The primary fits use first order;
the normalized fits use every Bragg-allowed order for the family.

### Validation records

Every validation check stores a stable name, pass state, observed and expected
values, unit, comparison, tolerance, and explanation. The immutable report
stores the schema and ordered checks. No record contains timestamps, absolute
paths, host names, random identifiers, or mutable mappings.

## Public numerical API

`models.py` will expose:

```python
electron_momentum_kg_m_s(voltage_v) -> numpy.ndarray
electron_wavelength_m(voltage_v) -> numpy.ndarray
bragg_ratio(voltage_v, spacing_m, order_n) -> numpy.ndarray
bragg_angle_rad(voltage_v, spacing_m, order_n) -> numpy.ndarray
scattering_angle_rad(voltage_v, spacing_m, order_n) -> numpy.ndarray
photo_ring_radius_m(voltage_v, spacing_m, order_n, tube_radius_m) -> numpy.ndarray
caliper_diameter_m(voltage_v, spacing_m, order_n, tube_radius_m) -> numpy.ndarray
maximum_bragg_order(voltage_v, spacing_m) -> numpy.ndarray
maximum_screen_order(voltage_v, spacing_m) -> numpy.ndarray
screen_visible(voltage_v, spacing_m, order_n) -> numpy.ndarray
```

Real inputs accept scalar or broadcast-compatible arrays. Orders accept only
positive integer scalars or integer arrays; booleans are rejected. Voltages
must lie within 1000--5000 V for this task API. Requested orders outside the
Bragg domain fail before inverse trigonometry. Numerical outputs are
`float64`; maximum-order outputs are `int64`; visibility outputs are boolean.
Scalar inputs still return zero-dimensional arrays.

## Independent reference API

`reference.py` will expose strict scalar functions for momentum, wavelength,
maximum orders, fit gradients, recovered spacings, and the frozen first-order
anchors. Energy, momentum, wavelength, and gradients will use
`decimal.Decimal` constructed from source strings. The scalar trigonometric
anchor path will be independently structured with `math` and will not import
NumPy or `models.py`.

## Output and transaction contract

Generation must construct and validate the complete study in memory. It then
writes all six data artifacts and twelve figure files to one temporary tree,
parses and verifies them, and only then replaces destinations in frozen order.
A late failure must preserve every pre-existing destination byte.

CSV files must have frozen column and row ordering. JSON uses sorted keys and
stable indentation. PNG signatures and dimensions and SVG structure must be
verified before replacement. Matplotlib metadata, font choice, SVG hash salt,
and any compression settings must be frozen so repeated clean generation is
byte-identical.

## Figure contract

The six approved figure families are generated only from the validated study:

1. three-voltage phosphor-screen comparison;
2. exact projected ring radius versus voltage;
3. official first-order straight-line validation;
4. normalized all-order collapse;
5. wavelength and maximum-order diagnostics; and
6. 16:9 competition summary.

Every figure is saved as both PNG and SVG. Quantitative figures use a
colourblind-safe light theme. The screen visual uses monochrome green rings
with text stating that brightness is schematic. Orders use a colour scale or
direct annotation rather than an oversized legend. Plotting may reduce the
number of visible markers, but may not discard evidence or change a fitted
result.

## Test boundaries

The focused test suite will cover:

- exact source constants and immutable configuration;
- voltage, spacing, radius, order, boolean, complex, non-finite, and shape
  rejection;
- scalar and broadcast array return contracts;
- wavelength monotonicity and $V^{-1/2}$ scaling;
- Bragg identities, angle relations, geometry identities, and domain failure;
- exact endpoint maximum-order anchors;
- deterministic complete catalogue ordering and counts;
- fit gradients, origin diagnostics, recovered spacings, and normalized
  collapse;
- defensive immutability of study and report arrays;
- independent-anchor agreement and deliberate corruption detection;
- CSV/JSON schemas, row order, hashes, and byte reproducibility;
- transactional rollback after a forced late failure;
- PNG and SVG pairs, dimensions, signatures, and deterministic rendering; and
- command-line success and failure exit statuses.

## Trade-offs accepted

- Multiple focused modules cost more initial code than one plotting script,
  but isolate units, branches, validation, and rendering.
- The official 1--5 kV boundary is enforced in the public Task 6 API, reducing
  generality but preventing out-of-scope evidence from entering the study.
- Storing every Bragg order creates more rows than the screen renderer uses,
  but preserves the official maximum-order calculation.
- A separate forward-screen flag adds a geometric convention not named in the
  one-line brief, but matches the pictured screen and prevents negative
  projected radii from being presented as rings.
- Independent reference code repeats some algebra, but avoids a shared
  numerical failure path.
- No intensity model makes the phosphor image schematic, but is more honest
  than inventing unprovided structure factors or detector response.

## Consequences and revisit triggers

The selected architecture is easy to test, regenerate, explain, and extend.
Its main cost is explicit records and validation code, which is acceptable for
a high-standard competition submission.

Revisit this decision only if the project later requires measured image
fitting, graphite structure factors, an interactive application, calibrated
intensities, a general crystallography library, or substantially larger
datasets. None is part of the approved Task 6 baseline.

## Stage 3 completion checklist

Stage 3 is complete because:

- the project context, constraints, and scientific risks are explicit;
- script, spreadsheet, notebook, and field-simulation alternatives were
  considered;
- the selected package is the simplest architecture that protects units,
  branches, validation, and reproducibility;
- module ownership and dependency direction are frozen;
- APIs, immutable records, filenames, transactions, figures, and test
  boundaries are explicit;
- trade-offs and revisit triggers are documented; and
- no physics module, generated evidence, or figure was created during the
  architecture stage.
