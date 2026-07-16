# ADR-001: Deterministic Photoelectric-Effect Model

- **Status:** Accepted
- **Date:** 16 July 2026
- **Scope:** Task 4 baseline architecture and reproducibility contract

## Context

Task 4 requires a deterministic family of stopping-potential curves for the
nine work functions supplied in the official presentation. The program must
represent both incident-photon frequency and vacuum wavelength, distinguish
the physical emission domain from a signed mathematical extrapolation, check
analytical cut-offs independently, save machine-readable evidence, produce
clear figures, and support a short competition explanation.

The calculations are small. The main architectural risks are scientific and
reproducibility errors rather than performance:

- confusing a stopping-potential magnitude with a signed electrode voltage;
- plotting negative extrapolated values as if photoelectrons existed below
  threshold;
- mixing joules, electronvolts, metres, and nanometres;
- hiding the only implementation of the physics inside plotting code;
- validating a calculation through the same faulty code path;
- silently merging Ag, Al, and Pb instead of retaining all source records;
- serializing non-standard `NaN` values; and
- creating files that vary with clock time, host, user, or local path.

The mathematical requirements are frozen in
[`MATHEMATICAL_MODEL.md`](../MATHEMATICAL_MODEL.md). This decision specifies
how later stages will implement them without changing the model.

## Options considered

| Option | Strengths | Weaknesses | Decision |
| --- | --- | --- | --- |
| One plotting script | Short initial implementation | Equations, masking, validation, data output, and styling become inseparable | Rejected |
| Spreadsheet as the authoritative model | Visually accessible and permitted | Harder to enforce units, immutable inputs, automated checks, and byte reproducibility | Rejected for the primary implementation |
| Jupyter notebook as the authoritative model | Useful for exploration | Hidden execution order and mutable state weaken reproducibility | Rejected |
| Small vectorized NumPy package | Explicit units and dependencies, reusable equations, fast tests, deterministic output | More source files | **Selected** |
| Object instance for every photon or electron | Resembles the optional animation | Unnecessary for the required curve model and obscures the analytical physics | Rejected for the baseline |

Exploratory notebooks or a later animation may call the tested package, but
they cannot become the source of truth for the required graph.

## Decision summary

The baseline will use a small Python package with:

- immutable constants, configuration, material, study, and validation records;
- vectorized NumPy model functions;
- scalar analytical references evaluated through a separate code path;
- in-memory study construction before any file output;
- standard-library CSV and JSON serialization;
- headless Matplotlib rendering only after validation passes; and
- command-line runners with meaningful exit statuses.

There will be no network access, random-number generator, GPU-specific path,
mutable module-level scientific state, file write during import, notebook
dependency, SciPy requirement, or current-time dependency.

## Frozen repository structure

Later stages own the following paths:

```text
task04_photoelectric_effect/
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
    validate_task04.py
    generate_task04.py
    plotting.py
    test_constants_and_materials.py
    test_models.py
    test_analysis.py
    test_validation.py
    test_generation.py
    test_plotting.py
    architecture/
        ADR-001-deterministic-photoelectric-model.md

data/task04/
    material_cutoffs.csv
    stopping_voltage_frequency.csv
    stopping_voltage_wavelength.csv
    validation_report.json
    reproducibility_manifest.json

figures/task04/
    stopping_voltage_frequency.png
    stopping_voltage_frequency.svg
    stopping_voltage_wavelength.png
    stopping_voltage_wavelength.svg
    copper_threshold_explanation.png
    copper_threshold_explanation.svg
    photoelectric_validation.png
    photoelectric_validation.svg
    task04_summary.png
    task04_summary.svg

presentation/task04/
    README.md
    SLIDE_CONTENT.md
    SPEAKER_SCRIPT.md
    Task04_Photoelectric_Effect.pptx
```

Files are added only by the stage responsible for them. Stage 3 records this
contract but does not create empty modules, placeholder data, or fake figures.
The optional Stage 10 animation may add a separately documented module and
artifact only after the validated baseline is complete.

## Module responsibilities

| Module | Responsibility | Must not do |
| --- | --- | --- |
| `__init__.py` | Re-export only the stage-approved public scientific API | Run calculations, write files, or import Matplotlib |
| `constants.py` | Exact SI definitions and derived unit-conversion constants | Define work functions, grids, output paths, or plots |
| `configuration.py` | Frozen grids, visible-band convention, schema version, tolerances, and budgets | Evaluate the photoelectric equations |
| `materials.py` | Immutable nine-material official source table | Calculate cut-offs or alter duplicate values |
| `models.py` | Vectorized cut-offs, signed voltages, physical masks, and physical voltages | Know source-material names, output paths, or expected validation values |
| `reference.py` | Independent scalar cut-offs, gradient, and anchor values using decimal arithmetic | Import `models.py` or `analysis.py` |
| `analysis.py` | Construct the complete immutable frequency/wavelength study | Write files, draw figures, or choose validation tolerances |
| `validation.py` | Compare a completed study with independent references and return checks | Repair results or change thresholds after observing errors |
| `validate_task04.py` | Run the in-memory validation and expose the result by exit status | Generate figures or data files |
| `generate_task04.py` | Orchestrate validation-first transactional data and figure generation | Duplicate physical equations or import Matplotlib for `--data-only` |
| `plotting.py` | Render validated records into fixed PNG/SVG figures | Recalculate cut-offs, masks, or voltages |

The dependency direction is one-way:

```text
constants ──> models ────────────────┐
     │                               │
     └──> reference ──> validation  │
                          ▲          │
configuration ──> analysis ──────────┤
materials ───────> analysis          │
                          │          │
                          ├──> plotting
                          └──> command-line runners
```

`reference.py` may use exact constant strings but may not import a model
function. Plotting accepts a study and a passing report; it does not receive
raw parameters from which it could silently recalculate the science.

## Immutable records

All records use frozen dataclasses. Array-owning result records make defensive
copies, normalize to `float64` or `bool`, verify shapes, and mark arrays
read-only.

### `Task04Configuration`

The configuration owns:

- schema version `task04-v1`;
- frequency start, step, and point count;
- wavelength start, step, and point count;
- visible-band wavelength limits;
- boundary clamp tolerance;
- energy-identity, gradient, cut-off, consistency, monotonicity, and anchor
  tolerances; and
- time and output-size budgets.

The default instance exactly matches Stage 2. Construction rejects non-finite
values, non-positive intervals, reversed bands, invalid counts, negative
tolerances, and configuration combinations whose calculated endpoint differs
from the declared Stage 2 endpoint.

### `PhotoelectricMaterial`

Each material record contains only:

- full material name;
- chemical symbol; and
- official work function in electronvolts.

The official collection is an immutable tuple in the exact order Ag, Al, Au,
Cu, Sn, Pb, W, Ni, Na. Material construction rejects empty text, non-finite or
non-positive work functions, duplicate symbols in a collection, and booleans
used as numbers. Derived joule work functions and cut-offs are not duplicated
in source records.

### `Task04StudyResult`

The complete study stores:

- immutable material records, length `n_material`;
- work functions in eV and J, shape `(n_material,)`;
- analytical cut-off frequencies and wavelengths, shape `(n_material,)`;
- frequency grid, shape `(n_frequency,)`;
- signed frequency voltages, shape `(n_material, n_frequency)`;
- frequency emission mask with the same shape;
- physical frequency voltages with `NaN` only outside the mask;
- wavelength grids in metres and nanometres, shape `(n_wavelength,)`;
- signed wavelength voltages, shape `(n_material, n_wavelength)`;
- wavelength emission mask with the same shape; and
- physical wavelength voltages with `NaN` only outside the mask.

With the default configuration, the main voltage arrays have shapes
`(9, 2001)` and `(9, 2201)`. The record verifies that every active physical
value is finite, every inactive physical value is `NaN`, masks are boolean,
grids are strictly increasing, and every array is consistent in shape. It does
not decide whether the scientific values pass validation.

### `ValidationCheck` and `Task04ValidationReport`

Each validation check contains:

- a stable machine-readable name;
- pass/fail state;
- observed and expected numerical values;
- physical unit or `dimensionless`;
- comparison name;
- tolerance; and
- a concise scientific explanation.

The report stores schema version, overall pass state, and an immutable ordered
tuple of checks. It contains no time, user, host, absolute path, random ID, or
mutable mapping.

## Public numerical API

The following names and contracts are frozen for `models.py`:

```python
cutoff_frequency_hz(work_function_ev) -> numpy.ndarray
cutoff_wavelength_m(work_function_ev) -> numpy.ndarray
linear_stopping_voltage_from_frequency(frequency_hz, work_function_ev) \
    -> numpy.ndarray
linear_stopping_voltage_from_wavelength(wavelength_m, work_function_ev) \
    -> numpy.ndarray
emission_possible_from_frequency(frequency_hz, work_function_ev) \
    -> numpy.ndarray
emission_possible_from_wavelength(wavelength_m, work_function_ev) \
    -> numpy.ndarray
physical_stopping_voltage_from_frequency(frequency_hz, work_function_ev) \
    -> numpy.ndarray
physical_stopping_voltage_from_wavelength(wavelength_m, work_function_ev) \
    -> numpy.ndarray
```

Contract shared by all model functions:

- inputs accept scalars or NumPy-compatible arrays;
- explicit NumPy broadcasting determines output shape;
- outputs are NumPy arrays, including zero-dimensional arrays for scalar
  inputs;
- numerical outputs use `float64`, and masks use `bool`;
- work functions must be finite and strictly positive;
- frequency must be finite and non-negative;
- wavelength must be finite and strictly positive;
- booleans are rejected as numerical inputs;
- non-broadcast-compatible inputs raise a NumPy `ValueError`; and
- model functions do not mutate their inputs.

The two cut-off functions accept only the work-function input. Frequency and
wavelength functions reshape nothing implicitly: the study builder will use a
material array of shape `(n_material, 1)` and a grid of shape `(1, n_grid)` to
request an outer comparison.

Signed voltage functions return finite values throughout their mathematical
input domains. Emission-mask functions compare against analytical cut-offs.
Physical-voltage functions return a copy with `NaN` outside the exact mask and
use `maximum(linear_voltage, 0)` inside the mask. Validation separately checks
the pre-clamp signed values against the Stage 2 boundary tolerance, so a faulty
mask cannot be concealed by clipping.

## Independent reference API

`reference.py` exposes scalar functions:

```python
reference_common_gradient_v_s() -> float
reference_cutoff_frequency_hz(work_function_ev: float) -> float
reference_cutoff_wavelength_nm(work_function_ev: float) -> float
reference_voltage_at_frequency_v(
    frequency_hz: float,
    work_function_ev: float,
) -> float
reference_voltage_at_wavelength_v(
    wavelength_nm: float,
    work_function_ev: float,
) -> float
```

These functions use standard-library `decimal.Decimal` values constructed
from the exact SI strings and from decimal text representations of scalar
inputs. They do not call NumPy model functions. This is deliberately a
different numerical path, not a second vectorized copy of `models.py`.

## Study and validation API

```python
build_task04_study(
    configuration=DEFAULT_CONFIGURATION,
    materials=OFFICIAL_MATERIALS,
) -> Task04StudyResult

validate_task04(
    study,
    configuration=DEFAULT_CONFIGURATION,
) -> Task04ValidationReport
```

Study construction is deterministic and side-effect free. It generates
grids from start, step, and count; reshapes inputs explicitly; calls only the
public models; and returns one immutable result.

Validation consumes a completed result and never mutates it. Check ordering is
stable: structure and finiteness, energy identities, common gradient, each
material's frequency and wavelength cut-offs, threshold voltage, masks and
bounds, monotonicity, duplicate materials, cross-coordinate consistency, and
scalar anchors.

## Error-handling contract

- Public numerical functions raise `ValueError` for invalid physical values.
- Type conversion failures remain `TypeError` or `ValueError`; they are not
  replaced by zeros or missing values.
- Public validation uses explicit exceptions, not `assert` statements.
- Floating-point warning handling is local; no import changes global NumPy
  error settings.
- The validation CLI exits `0` only when all required checks pass and `1`
  when any check fails.
- Data and figure generation are refused before creating or modifying an
  output directory when validation fails.
- A failed write removes temporary siblings and preserves pre-existing
  destinations.

## Machine-readable output contracts

All CSV files use UTF-8, a header row, comma delimiters, LF line endings, and
long-form records. Floating fields use 17 significant digits where required
for `float64` round trips. Material order follows the official tuple; rows
within each material follow ascending grid order.

### `material_cutoffs.csv`

| Column | Unit or type |
| --- | --- |
| `material` | text |
| `symbol` | text |
| `work_function_ev` | eV |
| `work_function_j` | J |
| `cutoff_frequency_hz` | Hz |
| `cutoff_wavelength_nm` | nm |

The file contains nine data rows.

### `stopping_voltage_frequency.csv`

| Column | Unit or type |
| --- | --- |
| `material` | text |
| `symbol` | text |
| `frequency_hz` | Hz |
| `linear_stopping_voltage_v` | V |
| `emission_possible` | lowercase `true` or `false` |
| `physical_stopping_voltage_v` | V or an empty field outside the emission domain |

The default file contains `9 * 2001 = 18009` data rows.

### `stopping_voltage_wavelength.csv`

| Column | Unit or type |
| --- | --- |
| `material` | text |
| `symbol` | text |
| `wavelength_nm` | nm |
| `linear_stopping_voltage_v` | V |
| `emission_possible` | lowercase `true` or `false` |
| `physical_stopping_voltage_v` | V or an empty field outside the emission domain |

The default file contains `9 * 2201 = 19809` data rows.

### `validation_report.json`

Contains schema version, overall pass state, and the ordered structured check
records. JSON numbers are finite; `NaN` and infinity are forbidden.

### `reproducibility_manifest.json`

Contains exact constants, derived constants, configuration, units, material
source records, tolerance definitions, output schema version, and ordered data
and figure filenames. It excludes generated measurements that already belong
in CSV or validation output and excludes machine-specific metadata.

## Generation command contract

From the repository root:

```bash
python3 -m task04_photoelectric_effect.validate_task04
python3 -m task04_photoelectric_effect.generate_task04
python3 -m task04_photoelectric_effect.generate_task04 --data-only
```

`generate_task04.py` also supports:

```text
--data-dir PATH
--figure-dir PATH
```

Defaults are `data/task04` and `figures/task04`, resolved from the repository
root rather than the current working directory. `--data-only` must not import
Matplotlib. Unknown options and invalid paths produce non-zero exit statuses
without partial scientific output.

The generation transaction is:

1. build studies in memory;
2. run all validation checks;
3. refuse output if any check fails;
4. serialize every requested artifact to temporary siblings;
5. verify all temporary files can be parsed and have expected names;
6. preserve existing destinations as temporary backup siblings;
7. replace final destinations in stable order;
8. restore every prior destination if any replacement fails; and
9. remove all temporary and backup artifacts on success or failure.

## Plotting contract

`plotting.py` uses the non-interactive `Agg` backend and fixed centralized
style. It accepts only a `Task04StudyResult`, a passing
`Task04ValidationReport`, and output paths.

The five frozen figure stems are:

1. `stopping_voltage_frequency` — required physical frequency curves;
2. `stopping_voltage_wavelength` — supporting physical wavelength curves;
3. `copper_threshold_explanation` — official $4.7\ \mathrm{eV}$ example with
   a dashed non-physical extrapolation;
4. `photoelectric_validation` — quantitative gradient and cut-off errors
   against pre-declared tolerances; and
5. `task04_summary` — presentation-ready 16:9 overview.

Each is written as deterministic PNG and SVG. Figures must use source arrays
rather than recalculated values, preserve Ag/Al/Pb as source records while
grouping their coincident visual line, and label every missing below-threshold
segment as no photoemission rather than zero voltage.

## Testing strategy and stage ownership

Tests use `unittest`, NumPy assertions, standard-library temporary
directories, subprocesses, and ZIP or image-header inspection where needed.
No test depends on network access or a display server.

### Stage 4 tests

- exact constants and derived identities;
- exact official material order and values;
- dataclass immutability and invalid material rejection;
- scalar and broadcast shapes and dtypes;
- frequency and wavelength model reference values;
- exact cut-off behaviour and below-threshold masks;
- duplicate work-function equality;
- invalid domains, booleans, non-finite values, and incompatible shapes; and
- no side effects or file writes during import.

### Stage 5 tests

- exact configured grid shapes and endpoints;
- immutable defensive result arrays;
- all source records retained;
- physical/linear/mask consistency;
- deterministic repeated study construction;
- frequency--wavelength conversion agreement; and
- in-memory runtime below the budget.

### Stage 6 tests

- independent decimal reference values;
- every pre-declared check and tolerance;
- stable check names and ordering;
- deliberate work-function, curve, and mask failure detection;
- CLI success and failure exit statuses; and
- no mutation during validation.

### Stage 7 tests

- exact filenames, headers, row counts, units, ordering, precision, and empty
  physical fields;
- finite, parseable, schema-complete JSON;
- byte-identical repeated and committed outputs;
- validation-before-output and transactional cleanup;
- custom output directories and working-directory independence; and
- proof that `--data-only` does not import Matplotlib.

### Stage 8 tests

- exact figure names, formats, dimensions, and deterministic bytes;
- correct curve, group, threshold, visible-band, extrapolation, tolerance, and
  summary content;
- refusal to plot a failed report;
- transactional output safety; and
- comparison with committed figure artifacts.

Stage 10 tests are added only if the optional animation is approved by its
value gate. Stage 11 owns presentation-specific structural and visual tests.

## Reproducibility contract

- Source values and ordered filenames are declared once.
- Arrays are generated from exact start, step, and count values.
- Repeated in-memory studies are exactly equal, including masks and `NaN`
  positions.
- CSV and JSON ordering and float formatting are fixed.
- SVG metadata omits dates and uses a fixed hash salt.
- PNG dimensions, DPI, compression path, fonts, and metadata are fixed.
- No generated file contains time, host, user, absolute path, random ID, or
  nondeterministic iteration order.
- NumPy and Matplotlib versions remain pinned in `requirements.txt`.
- The MacBook Air is the reference machine; the model has no 4090-specific
  branch.

## Consequences

### Benefits

- Physics functions can be read and tested independently of presentation
  code.
- Physical absence below threshold is represented explicitly rather than
  hidden by clipping.
- Decimal references provide genuine numerical separation from NumPy models.
- All nine official records remain auditable even where ideal curves overlap.
- Data, figures, and slides reuse one validated immutable result.
- Clean regeneration is small enough for the everyday MacBook Air.

### Costs

- The package contains more files than the equation alone appears to require.
- Empty physical CSV fields require an explicit boolean mask when data are
  consumed.
- Deterministic and transactional output tests add code beyond the scientific
  formula.

These costs are accepted because the challenge assesses computational work
and explanation, not merely whether a straight line can be drawn once.

## Stage 3 acceptance checklist

Stage 3 is complete when this ADR has been checked for:

- agreement with the frozen Stage 2 specification;
- one-way module dependencies and independent reference calculations;
- exact public model, study, validation, CLI, and output contracts;
- immutable records with units and shapes;
- explicit handling of the physical domain and missing values;
- deterministic data and figure filenames and schemas;
- test ownership for every implementation stage;
- transaction, error, portability, and performance rules; and
- no premature physics implementation or generated output.
