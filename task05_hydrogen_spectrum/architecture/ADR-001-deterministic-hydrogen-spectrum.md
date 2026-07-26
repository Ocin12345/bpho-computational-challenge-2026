# ADR-001: Deterministic Hydrogen-Spectrum Model

- **Status:** Accepted
- **Date:** 16 July 2026
- **Scope:** Task 5 baseline architecture and reproducibility contract

## Context

Task 5 requires a graph of emitted-photon energy against vacuum wavelength for
hydrogen transitions between Bohr energy levels. The frozen specification adds
a complete $n=1$--$10$ catalogue, named spectral series, analytical limits,
independent reference checks, deterministic evidence, supporting figures, and
a short presentation contribution.

The calculation contains only 10 levels and 45 transitions. Performance and
scale are negligible; the principal risks are scientific and communicative:

- reversing the sign of emitted-photon energy;
- confusing negative atomic level energy with positive photon energy;
- accepting upward or equal-level pairs as emissions;
- mixing joules, electronvolts, metres, and nanometres;
- omitting higher-series transitions from the declared 45-record catalogue;
- validating wavelengths through the same faulty formula that produced them;
- presenting discrete lines as a continuous hydrogen spectrum;
- implying equal line intensities or real-hydrogen precision; and
- producing host- or time-dependent artifacts.

The project is a small, solo, educational scientific package under a fixed
competition deadline. It has no user service, database, network, real-time, or
deployment requirement.

## Options considered

| Option | Strengths | Weaknesses | Complexity | Decision |
| --- | --- | --- | --- | --- |
| One plotting script | Fast initial draft | Equations, enumeration, validation, output, and styling become inseparable | Low initially, high later | Rejected |
| Spreadsheet as source of truth | Permitted and visually accessible | Weak unit contracts, hard-to-test pair enumeration, poor reproducibility | Medium | Rejected for the primary model |
| Jupyter notebook as source of truth | Convenient exploration | Hidden execution order and mutable state | Medium | Rejected |
| Object simulation of orbiting electrons | Visually engaging | Physically misleading and unrelated to the required discrete calculation | High | Rejected |
| Small vectorized NumPy package | Explicit units, reusable equations, deterministic tests and outputs | More files than a script | Low and controlled | **Selected** |

Exploratory notebooks or a later animation may call the tested package, but
they cannot become the authoritative calculation.

## Decision

The baseline will use a small dependency-directed Python package with:

- frozen decimal source constants and configuration;
- pure vectorized NumPy model functions;
- deterministic integer transition enumeration;
- immutable, defensive, read-only study and validation records;
- independent scalar `decimal.Decimal` references;
- validation before any evidence or figure is accepted;
- standard-library CSV and JSON serialization;
- headless Matplotlib rendering from validated records only; and
- command-line runners with meaningful exit statuses.

There will be no network access, database, random-number generator,
GPU-specific path, mutable module-level study, import-time file write,
notebook dependency, current-time dependency, or hidden state.

## Frozen repository structure

```text
task05_hydrogen_spectrum/
    README.md
    MATHEMATICAL_MODEL.md
    __init__.py
    constants.py
    configuration.py
    models.py
    transitions.py
    reference.py
    analysis.py
    validation.py
    validate_task05.py
    generate_task05.py
    plotting.py
    test_constants_and_configuration.py
    test_models.py
    test_analysis.py
    test_validation.py
    test_generation.py
    test_plotting.py
    architecture/
        ADR-001-deterministic-hydrogen-spectrum.md

data/task05/
    energy_levels.csv
    emission_transitions.csv
    series_limits.csv
    validation_report.json
    reproducibility_manifest.json

figures/task05/
    photon_energy_vs_wavelength.png
    photon_energy_vs_wavelength.svg
    bohr_energy_level_diagram.png
    bohr_energy_level_diagram.svg
    balmer_visible_spectrum.png
    balmer_visible_spectrum.svg
    hydrogen_series_convergence.png
    hydrogen_series_convergence.svg
    hydrogen_validation.png
    hydrogen_validation.svg
    task05_summary.png
    task05_summary.svg

presentation/task05/
    README.md
    SLIDE_CONTENT.md
    SPEAKER_SCRIPT.md
    Task05_Hydrogen_Spectrum.pptx
```

Stage 3 creates only this ADR. Later stages own their declared files and may
not add placeholder outputs or figures.

## Module responsibilities

| Module | Responsibility | Must not do |
| --- | --- | --- |
| `__init__.py` | Re-export the approved scientific API | Calculate studies, draw figures, or write files |
| `constants.py` | Exact SI strings, frozen $R_\infty$, and derived conversions | Define quantum-number scope or plotting choices |
| `configuration.py` | Level bound, visible convention, tolerances, budgets, and schema | Evaluate Bohr equations |
| `models.py` | Vectorized level, transition, frequency, wavelength, and limit equations | Know labels, filenames, or expected reference values |
| `transitions.py` | Deterministic pair enumeration and series/line labels | Recalculate energies or wavelengths |
| `reference.py` | Independent scalar Decimal targets | Import `models.py` or `analysis.py` |
| `analysis.py` | Assemble the immutable complete study | Write files, choose tolerances, or draw figures |
| `validation.py` | Compare one completed study with independent targets | Repair or relabel a study |
| `validate_task05.py` | Print validation results and expose pass/fail by exit status | Generate evidence or figures |
| `generate_task05.py` | Validation-first transactional evidence and figure orchestration | Duplicate scientific equations |
| `plotting.py` | Render only validated study/report records | Recompute transition physics |

The dependency direction is one-way:

```text
constants ──> models ────────────────┐
     │                               │
     └──> reference ──> validation  │
configuration ─> transitions        │
       │              │              │
       └────────> analysis <─────────┘
                         │
                         ├──> plotting
                         └──> command-line runners
```

`reference.py` may use the exact constant strings but may not call public
model functions. Plotting receives a study and the exactly matching passing
report, not raw quantum numbers from which it could silently rebuild results.

## Immutable records

### `Task05Configuration`

The frozen configuration owns:

- schema version `task05-v1`;
- maximum finite level $n=10$;
- maximum individually highlighted final level $n_f=5$;
- visible limits $380$ and $750\ \mathrm{nm}$;
- numerical tolerances;
- runtime and output-size budgets; and
- the expected transition count derived as $n_{\max}(n_{\max}-1)/2=45$.

Construction rejects booleans, invalid integers, reversed visible limits,
negative tolerances, and non-positive budgets.

### `Task05StudyResult`

The complete study stores read-only arrays for:

- 10 integer levels and their energies in eV and J;
- 45 initial and final integers in frozen order;
- 45 initial and final level energies;
- 45 photon energies in eV and J;
- 45 frequencies and wavelengths in metres and nanometres;
- immutable series, line, and spectral-region label tuples; and
- analytical limit arrays for final levels 1--5.

The record checks shapes, dtypes, finiteness, positivity, pair ordering,
read-only copying, label lengths, and unit-array consistency. It does not
decide whether scientifically plausible values pass the independent report.

### Validation records

Every validation check stores a stable name, pass state, observed and expected
values, unit, comparison, tolerance, and explanation. The immutable report
stores the schema and ordered checks. Neither record contains timestamps,
paths, host names, random identifiers, or mutable mappings.

## Public numerical API

`models.py` will expose:

```python
bohr_energy_ev(n) -> numpy.ndarray
bohr_energy_j(n) -> numpy.ndarray
transition_energy_ev(initial_n, final_n) -> numpy.ndarray
transition_energy_j(initial_n, final_n) -> numpy.ndarray
transition_frequency_hz(initial_n, final_n) -> numpy.ndarray
transition_wavelength_m(initial_n, final_n) -> numpy.ndarray
series_limit_energy_ev(final_n) -> numpy.ndarray
series_limit_wavelength_m(final_n) -> numpy.ndarray
```

Inputs accept integer scalars or broadcast-compatible integer arrays. Booleans,
floats, complex numbers, non-positive levels, and non-downward transitions are
rejected. Outputs are `float64` NumPy arrays, including zero-dimensional arrays
for scalar inputs. Model functions do not mutate inputs or know the finite
study's $n\leq10$ presentation boundary; `analysis.py` owns that boundary.

## Independent reference API

`reference.py` will expose scalar functions for level energy, transition
energy, frequency, wavelength, and series limits using `decimal.Decimal`.
Inputs are strict Python integers. This path will construct Decimal values
from the frozen source strings and will not import NumPy model functions.

## Output and transaction contract

Data generation must first construct and validate the complete study in
memory. It then writes all five artifacts to one temporary directory, parses
and verifies them, and only then replaces destinations in frozen order. A late
failure must preserve every pre-existing destination byte.

Figure generation follows the same validation-first and temporary-output
contract. PNG dimensions and signatures and SVG structure must be verified
before replacement. Repeated clean generation must be byte-identical.

## Trade-offs accepted

- Multiple focused modules cost more initial code than one script, but isolate
  the scientific paths and make review possible.
- Strict integer-only APIs reject convenient `3.0` inputs, but prevent silent
  quantum-number coercion.
- The ideal $R_\infty$ model does not reproduce measured hydrogen exactly, but
  matches the official derivation and keeps refinements honest.
- All 45 transitions expand the evidence beyond the five named series, but
  guarantee that the approved finite catalogue is complete.
- Independent Decimal checks repeat some algebra, but deliberately avoid a
  shared numerical failure path.

## Consequences and revisit triggers

The selected architecture is easy to test, regenerate, explain, and extend.
Its main cost is additional source files and explicit validation code, which is
acceptable for a high-standard competition submission.

Revisit this decision only if the project later requires measured spectra,
transition probabilities, interactive controls, substantially larger atomic
systems, or performance beyond small NumPy arrays. None of those conditions is
part of the approved Task 5 baseline.

## Stage 3 completion checklist

Stage 3 is complete because:

- the project context and risks are explicit;
- simpler script, spreadsheet, notebook, and trajectory alternatives were
  considered;
- the selected package remains the simplest architecture that protects units,
  validation, and reproducibility;
- module ownership and dependency direction are frozen;
- public APIs, records, filenames, transactions, and test boundaries are
  explicit;
- trade-offs and revisit triggers are documented; and
- no physics module, generated evidence, or figure was created during the
  architecture stage.
