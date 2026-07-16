# ADR-001: Deterministic Vectorized Scientific Model

- **Status:** Accepted
- **Date:** 16 July 2026
- **Scope:** Task 3 baseline architecture and reproducibility contract

## Context

Task 3 requires two deterministic families of curves rather than a stochastic
or time-dependent simulation. The program must calculate Planck spectra for
three reference temperatures and Einstein molar heat capacities for seven
reference solids. It must also produce independent analytical checks, saved
numerical evidence, polished figures, and material for a very short final
screencast.

The architecture must remain understandable to a Year 12 student, run quickly
on a MacBook Air, and behave consistently on the user's second computer. Its
main risks are not computational cost but scientific ambiguity:

- confusing spectral radiance with spectral exitance;
- mixing metres and nanometres inside the equations;
- allowing plotting code to become the only implementation of the physics;
- validating a model with expected values calculated by the same code path;
- silently rounding source data before calculations are complete;
- producing machine-dependent files containing timestamps or local paths; and
- placing all work in one script that cannot be tested in isolation.

The mathematical and numerical requirements are frozen in
[`MATHEMATICAL_MODEL.md`](../MATHEMATICAL_MODEL.md). This decision describes
how the software will implement that specification without changing it.

## Options considered

| Option | Strengths | Weaknesses | Decision |
| --- | --- | --- | --- |
| One procedural plotting script | Short and initially easy to run | Physics, validation, file output, and styling become inseparable; difficult to test | Rejected |
| Jupyter notebook as the main implementation | Useful for exploration and teaching | Execution order can be hidden; generated state is easy to confuse with source; awkward automated testing | Rejected |
| Small NumPy package with focused modules and command-line runners | Explicit dependencies; reusable equations; straightforward tests; deterministic outputs | More files than a single script | **Selected** |
| SciPy-based numerical integration and optimization | Convenient high-level routines | Unnecessary dependency for fixed grids and simple analytical targets; bundled runtime may not include SciPy | Rejected for the baseline |
| Object per temperature or wavelength | Visually object-oriented | Adds Python-level loops and obscures array units and shapes | Rejected |

Exploratory notebooks may be added later, but they must call the tested package
and cannot become the authoritative implementation.

## Decision summary

The baseline will use a small Python package built around vectorized NumPy
functions, immutable configuration and result records, independent reference
relationships, standard-library CSV and JSON output, and Matplotlib figures.

There will be:

- no network access during a calculation;
- no random-number generator;
- no mutable module-level scientific state;
- no file writes during import;
- no dependency on a notebook kernel;
- no SciPy requirement for Task 3; and
- no GPU-specific execution path.

## Planned repository structure

The following paths are frozen for later implementation stages:

```text
task03_thermal_radiation/
    README.md
    MATHEMATICAL_MODEL.md
    __init__.py
    constants.py
    configuration.py
    materials.py
    models.py
    reference.py
    analysis.py
    validation.py
    plotting.py
    validate_task03.py
    generate_task03.py
    test_constants_and_materials.py
    test_planck_model.py
    test_einstein_model.py
    test_analysis_and_validation.py
    test_generation.py
    architecture/
        ADR-001-deterministic-vectorized-model.md

data/task03/
    planck_spectra.csv
    planck_validation.csv
    einstein_materials.csv
    einstein_heat_capacity.csv
    einstein_normalized.csv
    validation_report.json
    reproducibility_manifest.json

figures/task03/
    planck_spectra.png
    planck_spectra.svg
    planck_validation.png
    planck_validation.svg
    einstein_heat_capacity.png
    einstein_heat_capacity.svg
    einstein_normalized.png
    einstein_normalized.svg
    task03_summary.png
    task03_summary.svg

presentation/task03/
    README.md
    SLIDE_CONTENT.md
    SPEAKER_SCRIPT.md
    Task03_Planck_Einstein.pptx
```

Files will be added only in the stage that owns them. Stage 3 records the
contract but does not create empty Python modules or placeholder results.

## Module responsibilities

| Module | Responsibility | Must not do |
| --- | --- | --- |
| `constants.py` | Exact SI constants and derived constant identities | Construct grids, write files, or import Matplotlib |
| `configuration.py` | Frozen baseline grids, temperatures, tolerances, and schema version | Evaluate either physical model |
| `materials.py` | Immutable official solid records in official display order | Calculate heat capacities or alter source values |
| `models.py` | Vectorized Planck and Einstein equations plus unit conversion | Know output paths, draw figures, or define expected validation answers |
| `reference.py` | Independent analytical targets such as Wien, Stefan--Boltzmann, and $3R$ | Call numerical model functions |
| `analysis.py` | Build complete immutable Planck and Einstein study results | Write files or set plotting styles |
| `validation.py` | Compare study results with independent targets and return structured checks | Change thresholds after observing results |
| `plotting.py` | Convert validated result records into Matplotlib figures | Recalculate the underlying physics |
| `validate_task03.py` | Run validation from the command line and set an exit status | Generate presentation figures |
| `generate_task03.py` | Orchestrate validated data and figure generation | Contain duplicate equations |

The dependency direction is one-way:

```text
constants ──> models ───────────────┐
     │                              │
     ├──> reference ──> validation │
     │                    ▲         │
configuration ──> analysis ─────────┤
materials ───────> analysis         │
                         │          │
                         ├──> plotting
                         └──> command-line runners
```

`reference.py` may import physical constants, but it may not import
`models.py`. This prevents a numerical implementation error from being copied
into its own expected result.

## Immutable data records

The package will use frozen dataclasses for records with named scientific
fields.

### `Task03Configuration`

Owns the complete reproducible baseline:

- schema version;
- Planck temperatures;
- display wavelength start, stop, and interval;
- peak-search start, stop, and interval;
- integration wavelength bounds and point count;
- Einstein plot temperature start, stop, and interval;
- normalized-temperature bounds and point count; and
- all pre-declared validation tolerances.

Construction validates finite values, correct ordering, positive intervals,
and valid point counts. The default instance exactly matches the Stage 2
specification.

### `EinsteinMaterial`

Contains only source and identity data:

- full material name;
- chemical symbol;
- official Debye temperature in kelvin; and
- official displayed Einstein frequency in units of $10^{13}\ \mathrm{Hz}$.

The official seven-material collection is an immutable tuple in the order Au,
Cu, Ti, Al, Fe, Si, C. Derived temperature and frequency remain calculations,
not duplicated source fields.

### `PlanckStudyResult`

Contains read-only arrays for:

- temperatures, shape `(n_temperature,)`;
- display wavelengths in metres and nanometres, shape `(n_wavelength,)`;
- spectral radiance per metre, shape `(n_temperature, n_wavelength)`;
- spectral exitance per nanometre, same shape;
- numerical peak wavelengths;
- independent Wien target wavelengths;
- numerical integrated exitances; and
- independent Stefan--Boltzmann targets.

### `EinsteinStudyResult`

Contains:

- the immutable material tuple;
- calculated Einstein temperatures and frequencies;
- the principal temperature grid;
- molar heat capacities with shape `(n_material, n_temperature)`;
- the reduced-temperature grid; and
- normalized heat capacities with shape
  `(n_material, n_reduced_temperature)`.

### `ValidationCheck` and `Task03ValidationReport`

Each check records:

- a stable machine-readable name;
- pass or fail;
- observed value;
- expected value or condition;
- tolerance and comparison type;
- physical unit where applicable; and
- a short scientific explanation.

The report contains the schema version, overall pass state, and an immutable
tuple of checks. It cannot contain a timestamp, absolute path, random identifier,
or host name.

All arrays stored in result records will be copied when the record is created
and marked read-only. Plotting or output code must not be able to change the
scientific results after validation.

## Public numerical API

The following function names and contracts are frozen.

### Planck functions in `models.py`

```python
planck_spectral_radiance(wavelength_m, temperature_k) -> numpy.ndarray
planck_spectral_exitance(wavelength_m, temperature_k) -> numpy.ndarray
spectral_density_per_nanometre(density_per_metre) -> numpy.ndarray
```

- Inputs may be scalars or NumPy-compatible arrays.
- Wavelength and temperature inputs must be finite and broadcast-compatible.
- All wavelengths and temperatures must be strictly positive.
- Output shape is the NumPy broadcast shape of the inputs.
- Output dtype is `float64` and values are finite and non-negative.
- Scalar inputs return a zero-dimensional NumPy array, preserving one
  consistent return type.
- The exitance function is exactly $\pi$ times the radiance function.

Study construction will reshape the temperature vector to `(n_temperature, 1)`
and the wavelength vector to `(1, n_wavelength)` before calling the API. The
model function itself will not guess an outer-product interpretation for two
one-dimensional arrays.

### Einstein functions in `models.py`

```python
einstein_temperature_from_debye(debye_temperature_k) -> numpy.ndarray
einstein_frequency_from_temperature(einstein_temperature_k) -> numpy.ndarray
einstein_molar_heat_capacity(temperature_k, einstein_temperature_k) -> numpy.ndarray
```

- Debye and Einstein temperature and frequency inputs must be finite and
  strictly positive.
- Heat-capacity temperature may be zero but not negative.
- Inputs follow explicit NumPy broadcasting.
- Output dtype is `float64`.
- The heat-capacity function returns exactly zero where $T=0$ and finite values
  within $0\leq C_V\leq3R$ elsewhere.

### Reference functions in `reference.py`

```python
wien_peak_wavelength(temperature_k) -> numpy.ndarray
stefan_boltzmann_exitance(temperature_k) -> numpy.ndarray
dulong_petit_limit() -> float
einstein_anchor_ratio() -> float
```

These functions implement closed-form analytical targets only. They never call
the numerical spectrum or heat-capacity functions.

### Study and validation functions

```python
build_planck_study(configuration) -> PlanckStudyResult
build_einstein_study(configuration, materials) -> EinsteinStudyResult
validate_task03(planck_result, einstein_result, configuration) \
    -> Task03ValidationReport
```

Study builders perform calculations in memory and have no file-system side
effects. Validation consumes completed immutable results and never mutates
them.

## Error-handling contract

- Public functions raise `ValueError` for invalid physical values.
- Non-broadcast-compatible inputs propagate a clear NumPy `ValueError`.
- Type conversion failures raise `TypeError` or `ValueError`; they are not
  converted into zeros.
- `assert` statements are reserved for developer invariants and are not used
  for public input validation.
- Floating-point warnings are handled locally; global NumPy error settings are
  never changed on import.
- The validation command exits with status `0` only when every required check
  passes and status `1` when any check fails.
- Data generation is refused when validation fails.

## Machine-readable output contracts

All CSV files use UTF-8, a header row, comma delimiters, `\n` line endings,
and long-form records. Numerical fields retain at least 17 significant decimal
digits where needed for round-trip double precision.

### `planck_spectra.csv`

| Column | Unit or type |
| --- | --- |
| `temperature_k` | K |
| `wavelength_nm` | nm |
| `spectral_exitance_w_m2_nm` | $\mathrm{W\,m^{-2}nm^{-1}}$ |

Rows are ordered first by temperature in configured order ($4000$, $5000$,
$6000\ \mathrm K$ by default), then by ascending wavelength.

### `planck_validation.csv`

| Column | Unit or type |
| --- | --- |
| `temperature_k` | K |
| `numerical_peak_nm` | nm |
| `wien_peak_nm` | nm |
| `peak_relative_error` | dimensionless |
| `numerical_exitance_w_m2` | $\mathrm{W\,m^{-2}}$ |
| `stefan_boltzmann_w_m2` | $\mathrm{W\,m^{-2}}$ |
| `integral_relative_error` | dimensionless |

### `einstein_materials.csv`

| Column | Unit or type |
| --- | --- |
| `material` | text |
| `symbol` | text |
| `debye_temperature_k` | K |
| `einstein_temperature_k` | K |
| `einstein_frequency_hz` | Hz |
| `official_frequency_1e13_hz` | displayed reference value |

### `einstein_heat_capacity.csv`

| Column | Unit or type |
| --- | --- |
| `material` | text |
| `symbol` | text |
| `temperature_k` | K |
| `molar_heat_capacity_j_mol_k` | $\mathrm{J\,mol^{-1}K^{-1}}$ |

### `einstein_normalized.csv`

| Column | Unit or type |
| --- | --- |
| `material` | text |
| `symbol` | text |
| `reduced_temperature` | $T/T_E$ |
| `normalized_heat_capacity` | $C_V/(3R)$ |

### `validation_report.json`

The top-level schema is:

```json
{
  "schema_version": 1,
  "passed": true,
  "checks": []
}
```

Each check follows the immutable validation-record fields above. JSON writing
uses indentation, sorted keys, and `allow_nan=False` so invalid floating-point
values cannot enter the evidence file.

### `reproducibility_manifest.json`

The manifest records:

- schema version;
- exact constants;
- complete configuration;
- official material inputs;
- ordered expected output filenames; and
- mathematical-specification path.

It does not record generation time, computer name, user name, absolute path,
or runtime-specific temporary information. Package versions remain bounded
through `requirements.txt` and are printed by the command-line runner for
diagnosis rather than inserted into deterministic scientific outputs.

## Output transaction and ownership

Generation follows this order:

1. construct both studies entirely in memory;
2. run all required validation checks;
3. stop without changing committed evidence if validation fails;
4. serialize each new file to a temporary sibling;
5. replace the destination only after that individual file is complete; and
6. print the ordered list of generated paths and validation summary.

The physics package never writes outside explicitly supplied output
directories. Tests use temporary directories and must not alter `data/`,
`figures/`, or `presentation/`.

CSV and JSON data are the numerical source of truth. Figures are derived views
and must not be read back as data.

## Command-line contracts

From the repository root:

```bash
python3 -m task03_thermal_radiation.validate_task03
python3 -m task03_thermal_radiation.generate_task03 --data-only
python3 -m task03_thermal_radiation.generate_task03
```

The default output locations are `data/task03/` and `figures/task03/`.
Optional directory arguments may redirect outputs for tests or local review.

`--data-only` writes numerical evidence and the manifest without importing
Matplotlib. The complete command writes both data and figures after validation.
No command downloads data or prompts for interactive input.

## Reproducibility rules

The following rules apply to all later stages:

1. Exact constants and official material inputs exist in one authoritative
   module each.
2. The default configuration is immutable and fully serializable.
3. Every array is generated from explicit inclusive bounds and point counts or
   intervals; no hidden adaptive grid is used.
4. Material and temperature ordering is fixed.
5. No random seed is accepted because the model is deterministic.
6. Calculations remain `float64`; display rounding never feeds back into a
   model.
7. JSON contains no `NaN`, infinity, timestamps, or absolute paths.
8. Matplotlib uses fixed dimensions, DPI, colours, DejaVu Sans, and centralized
   style settings.
9. SVG generation sets a fixed hash salt and omits date metadata where the
   backend permits it.
10. Numerical CSV and JSON outputs must match across the MacBook Air and 4090
    laptop within the declared validation tolerances; byte-identical figures
    are not required across different Matplotlib patch versions.
11. Imports are side-effect free.
12. One documented command regenerates all final Task 3 evidence.

## Testing strategy

Tests use the standard-library `unittest` framework already used by Tasks 1
and 2.

| Test module | Scope |
| --- | --- |
| `test_constants_and_materials.py` | Exact constants, official ordering, immutable records, source validation |
| `test_planck_model.py` | Domains, broadcasting, units, stable branches, radiance/exitance identity, limiting behaviour |
| `test_einstein_model.py` | Material conversions, $T=0$, broadcasting, stable branches, bounds and anchor values |
| `test_analysis_and_validation.py` | Frozen grids, independent targets, all pre-declared tolerances, immutable result arrays |
| `test_generation.py` | Temporary-directory output schemas, deterministic ordering, invalid-output refusal, CLI exit codes |

Tests will include scalar, vector, two-dimensional broadcast, invalid, and
extreme-value cases. A test that merely calls a model twice and compares it
with itself is not accepted as physical validation.

## Performance and portability budgets

The baseline is expected to remain below:

- 5 seconds for numerical validation;
- 15 seconds for complete data and figure generation;
- 100 MB peak memory for Task 3; and
- 10 MB of committed numerical Task 3 data.

These are portability budgets, not competition requirements. Exceeding one is
a reason to investigate accidental duplication or an inappropriate grid, not
to move the calculation to the 4090 laptop automatically.

## Consequences

### Positive

- The code will be compact but independently testable.
- Physics functions can be shown clearly in the screencast or supporting
  explanation.
- Units and array shapes are explicit.
- Validation cannot silently reuse the model's own numerical calculation.
- Results are deterministic and portable between both computers.
- Plot design can change without changing scientific results.
- The absence of a SciPy dependency keeps the baseline easy to run.

### Costs

- Several small files replace one short plotting script.
- Immutable result construction requires deliberate array copying.
- Long-form CSV repeats temperature and material identifiers.
- Fixed output schemas require intentional versioning if columns change.

These costs are small for the amount of auditability and presentation evidence
they provide.

## Revisit triggers

This architecture should be reconsidered only if:

- a required validation target cannot be met with the frozen grids;
- output data exceed the declared size budget;
- the optional Debye extension becomes part of the accepted baseline;
- an interactive application becomes a deliberate later extension;
- a new official source changes the required equations or materials; or
- tests reveal that one of the public contracts prevents correct physical
  behaviour.

Convenience alone is not sufficient reason to add a framework, database,
notebook dependency, GPU path, or network service.

## Stage 3 completion check

Stage 3 is complete when this accepted decision is committed and:

- module responsibilities and dependency direction are explicit;
- public numerical APIs and broadcasting rules are frozen;
- immutable result and validation records are defined;
- all CSV and JSON schemas are fixed;
- command-line and error-handling contracts are recorded;
- deterministic output and plotting rules are declared;
- testing, performance, and portability budgets are defined; and
- no Stage 4 Planck implementation has begun.

The next stage is **Stage 4: Planck-model implementation and unit tests**.
