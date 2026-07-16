# Task 4: Photoelectric Effect

## Status

All 12 stages are complete. The two official source files have been read,
and the mandatory model, reference inputs, baseline deliverables, optional
extension, exclusions, staged workflow, and final acceptance boundary are
frozen below. The complete equations, constants, units, physical domains,
reference cut-offs, grids, numerical conventions, serialization rules, and
pre-declared tolerances are fixed in the
[mathematical and numerical specification](MATHEMATICAL_MODEL.md). The exact
constants, frozen numerical configuration, immutable official material table,
complete vectorized photoelectric model, immutable in-memory study, independent
Decimal references, deterministic 43-check validation report, reproducible
CSV/JSON evidence, complete deterministic PNG/SVG figure package, and optional
validated GIF/storyboard extension are now implemented. The accepted
[architecture decision](architecture/ADR-001-deterministic-photoelectric-model.md)
now fixes module ownership, immutable records, public APIs, output schemas,
command-line contracts, tests, transaction rules, and cross-computer
reproducibility before implementation.

The evidence-based
[results and scientific interpretation](RESULTS_AND_INTERPRETATION.md) now
provide the approved explanation boundary for the later presentation.
The separate [animation decision](ANIMATION_DECISION.md) records why the
extension was implemented and the precise boundary between its schematic
motion and the quantitative model.
The finished one-slide [PowerPoint package](../presentation/task04/README.md)
contains the editable slide, selected assets, high-resolution preview, embedded
speaker notes, timed narration, rehearsal explanation, and question guide.
The [final acceptance report](FINAL_ACCEPTANCE.md) records the clean
regeneration, complete tests, presentation checks, repository hygiene, private
GitHub status, and accepted limitations.

## Official sources reviewed

The scope comes from both files in the official 2026 challenge download:

1. page 2 of **BPhO ComPhys Challenge 2026**, the three-page written brief; and
2. slides 25--28 of **BPhO CompPhys2026 Quantum**, the 76-slide presentation.

The Task 4 section ends on slide 28. Slide 29 begins Task 5 material, so it is
not part of this task.

## Official objective

The mandatory task is to plot the photoelectron stopping voltage against the
frequency, or the in-vacuum wavelength, of incident photons for various
metals.

The official extension is to create an animated simulation resembling the
PhET photoelectric-effect demonstration. The wording labels this as an
extension, so it is not required for the core Task 4 solution.

## Core physical model

Einstein's photoelectric equation gives the maximum kinetic energy of an
emitted electron:

$$
K_{\max}=hf-W,
$$

where $h$ is Planck's constant, $f$ is photon frequency, and $W$ is the metal's
work function. A reverse stopping voltage $V_s$ removes this maximum kinetic
energy:

$$
eV_s=K_{\max}=hf-W.
$$

Therefore the required frequency relation is

$$
V_s=\frac{h}{e}f-\frac{W}{e}.
$$

Using the in-vacuum relation $f=c/\lambda$ gives

$$
V_s=\frac{hc}{e\lambda}-\frac{W}{e}.
$$

The threshold values are

$$
f_0=\frac{W}{h},
\qquad
\lambda_0=\frac{hc}{W}.
$$

Photoemission occurs only when $f\geq f_0$, equivalently
$\lambda\leq\lambda_0$. Below threshold there are no photoelectrons, so the
stopping voltage is physically undefined rather than negative. We may show a
dashed negative extrapolation to explain the straight-line intercept, but it
must be labelled as an extrapolation and kept distinct from the physical
curve.

## Official work-function table

The presentation supplies these values:

| Material | Symbol | Work function / eV |
| --- | :---: | ---: |
| Silver | Ag | $4.3$ |
| Aluminium | Al | $4.3$ |
| Gold | Au | $5.1$ |
| Copper | Cu | $4.7$ |
| Tin | Sn | $4.4$ |
| Lead | Pb | $4.3$ |
| Tungsten | W | $4.5$ |
| Nickel | Ni | $4.6$ |
| Sodium | Na | $2.4$ |

These are fixed reference inputs, not parameters to be fitted. Silver,
aluminium, and lead share the displayed value $4.3\ \mathrm{eV}$, so their
ideal curves and cut-offs will coincide. The final visual must group or
otherwise label that overlap honestly rather than pretending that three
separate lines are visible.

## Frozen baseline scope

The core Task 4 package will:

1. use Python, NumPy, and Matplotlib;
2. store all nine official metals in one immutable source table;
3. calculate stopping voltage directly from Einstein's equation;
4. generate the required stopping-voltage-versus-frequency comparison;
5. generate a supporting in-vacuum-wavelength comparison;
6. mark every cut-off frequency and wavelength clearly;
7. distinguish the physical emission region from any dashed extrapolation;
8. save deterministic CSV and JSON evidence;
9. validate the model against independent analytical calculations;
10. explain the physical trends, assumptions, and limitations; and
11. prepare a concise slide and timed script for the final screencast.

This calculation is deterministic, vectorized, and computationally small. It
does not need random seeds, repeated trials, GPU acceleration, or the RTX 4090
laptop.

## Declared high-standard evidence

The final implementation will check that:

- every frequency curve has the common gradient $h/e$;
- the extrapolated voltage intercept is $-W/e$;
- each numerical zero crossing agrees with $f_0=W/h$;
- each wavelength cut-off agrees with $\lambda_0=hc/W$;
- frequency and wavelength calculations agree after $f=c/\lambda$;
- stopping voltage is non-negative throughout the physical emission domain;
- higher work function produces a higher threshold frequency and a shorter
  threshold wavelength;
- identical official work functions produce identical curves exactly;
- all numerical outputs are finite, deterministic, and unit-consistent; and
- deliberately corrupted inputs or results cause validation to fail.

These are checks of the mathematical model. They are not evidence that we have
performed a laboratory measurement of a real metal surface.

## Optional extension decision

After the complete baseline passed its scientific and visual checks, the
extension gate approved a compact four-scene sodium demonstration. It shows
below-threshold suppression, above-threshold emission, the effect of intensity
on illustrative electron count rather than maximum energy, and the stopping
potential suppressing the photocurrent.

The animation is explicitly schematic, reads its numerical values from the
validated immutable study, and remains separate from the required graph and
quantitative evidence. Its exact scientific and visual boundaries are recorded
in [`ANIMATION_DECISION.md`](ANIMATION_DECISION.md).

## Explicit exclusions from the baseline

The core solution will not attempt to model:

- microscopic electron trajectories inside the metal;
- a complete current--voltage characteristic or vacuum-tube circuit;
- surface contamination, crystal orientation, temperature, or oxide layers;
- a distribution of electron binding energies;
- multiphoton or relativistic photoemission;
- experimental uncertainty fitting; or
- a browser application before the validated graph package is complete.

## Staged delivery plan

| Stage | Deliverable | Completion evidence |
| ---: | --- | --- |
| 1 | Requirements and scope | Both official files read; baseline, extension, exclusions, and acceptance boundary frozen |
| 2 | Mathematical specification | Equations, constants, units, domains, grids, conventions, and tolerances fixed |
| 3 | Architecture | APIs, immutable records, output schemas, tests, and reproducibility rules accepted |
| 4 | Physical model | Constants, material records, and stable vectorized stopping-voltage functions implemented and tested |
| 5 | Complete studies | Frequency and wavelength comparisons plus all analytical cut-offs assembled immutably |
| 6 | Validation | Independent checks, tolerances, failure injection, and command-line reporting complete |
| 7 | Numerical evidence | Deterministic CSV and JSON outputs generated transactionally |
| 8 | Figures | Required and supporting PNG/SVG figures generated, tested, and visually inspected |
| 9 | Scientific explanation | Results, physical interpretation, assumptions, and limitations documented |
| 10 | Optional animation decision | Extension either implemented and validated or explicitly omitted with reasons |
| 11 | Presentation package | Editable slide, assets, preview, speaker notes, and timed script complete |
| 12 | Final acceptance | Clean regeneration, full tests, hygiene, private GitHub synchronization, and acceptance report pass |

## Acceptance boundary for the complete task

Task 4 will be accepted only when:

- the required stopping-voltage comparison is generated from our own code;
- all nine official work-function entries are represented correctly;
- physical and extrapolated domains are distinguished accurately;
- equations, notation, units, and constants are explicit and consistent;
- pre-declared analytical and numerical checks pass documented tolerances;
- data and figures regenerate deterministically from clean commands;
- every final figure is inspected at original resolution;
- the interpretation and limitations are scientifically clear;
- the final slide and narration are complete; and
- the repository is clean, private, and synchronized with GitHub.

## Stage 1 completion check

Stage 1 is complete because both official files have been read, the exact Task
4 slide range has been isolated, the mandatory graph has been separated from
the optional animation, all nine official material inputs have been recorded,
the below-threshold physical domain has been clarified, and the complete
delivery and acceptance structure has been fixed before coding.

## Stage 2 completion check

Stage 2 is complete because:

- the frequency and wavelength forms of Einstein's equation are defined with
  dimensionally consistent units;
- exact SI values of $h$, $e$, and $c$ and all derived conversions are fixed;
- all nine official work functions and their analytical cut-offs are recorded;
- the physical emission domain is separated explicitly from the signed
  mathematical extrapolation;
- inclusive frequency and wavelength grids are fixed before implementation;
- scalar anchors and independent analytical targets are recorded;
- validation tolerances, failure checks, output conventions, visual
  requirements, and portability budgets are pre-declared; and
- the assumptions and real-surface limitations are explicit.

The complete details are in
[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md).

## Stage 3 completion check

Stage 3 is complete because:

- a focused vectorized NumPy package was selected over a monolithic script,
  spreadsheet, or stateful notebook;
- model, reference, analysis, validation, serialization, plotting, and command
  responsibilities have one-way dependencies;
- exact public model and independent decimal-reference APIs are frozen;
- configuration, material, study, and validation records have immutable field,
  shape, unit, and missing-value contracts;
- all five data files and ten static figure files have exact schemas and
  filenames;
- command-line, transaction, error, plotting, testing, portability, and
  reproducibility contracts are explicit; and
- no empty module, physics implementation, placeholder result, or generated
  figure was added prematurely.

The complete decision is in
[`ADR-001`](architecture/ADR-001-deterministic-photoelectric-model.md). The
architecture remains the implementation contract.

## Stage 4 implementation and completion check

Stage 4 added:

- [`constants.py`](constants.py), containing exact SI definitions and derived
  photoelectric conversion constants;
- [`configuration.py`](configuration.py), protecting the frozen grids,
  visible-band convention, tolerances, and portability budgets;
- [`materials.py`](materials.py), containing immutable official records in the
  exact Ag, Al, Au, Cu, Sn, Pb, W, Ni, Na order;
- [`models.py`](models.py), containing all eight scalar/broadcast vectorized
  cut-off, signed-voltage, emission-mask, and physical-voltage functions;
- [`__init__.py`](__init__.py), exposing only the Stage 4 public API;
- [`test_constants_and_materials.py`](test_constants_and_materials.py); and
- [`test_models.py`](test_models.py).

Run the focused suite from the repository root with:

```bash
python3 -m unittest discover -s task04_photoelectric_effect -p 'test_*.py' -v
```

Stage 4 is complete because:

- the exact values of $h$, $e$, and $c$ and all derived identities are tested;
- the configuration rejects endpoint drift, invalid tolerances, and ambiguous
  types;
- all nine source records are immutable and duplicate symbols are rejected;
- both coordinate forms reproduce the frozen cut-offs and scalar anchors;
- scalar, array, explicit broadcasting, unit, dtype, and non-mutation
  contracts are tested;
- the physical functions return non-negative voltage only in the exact
  emission domain and `NaN` rather than zero below threshold;
- exact threshold neighbours, coincident work functions, and the sodium
  visible-light distinction are tested;
- booleans, text, complex numbers, non-finite values, invalid domains,
  incompatible shapes, and unrepresentable results fail explicitly;
- package import writes no files and does not import Matplotlib; and
- all 46 focused Task 4 tests pass.

No complete study, validation report, CSV, JSON, figure, animation, or
presentation output was added during this stage.

## Stage 5 implementation and completion check

Stage 5 added [`analysis.py`](analysis.py), containing the frozen
`Task04StudyResult` and side-effect-free `build_task04_study` entry point, plus
[`test_analysis.py`](test_analysis.py).

The default study contains:

- all nine immutable official material records;
- work functions in electronvolts and joules;
- nine analytical cut-off frequencies and wavelengths;
- the inclusive 2001-point frequency grid and three aligned `(9, 2001)`
  signed-voltage, mask, and physical-voltage arrays;
- the inclusive 2201-point metre/nanometre wavelength grids and three aligned
  `(9, 2201)` arrays; and
- `NaN` only where the corresponding exact mask declares no photoemission.

Stage 5 is complete because:

- source order, values, units, shapes, dtypes, endpoints, and intervals are
  tested;
- every stored scientific array equals the appropriate Stage 4 public model
  result;
- result construction makes defensive copies and marks every array read-only;
- invalid shapes, grids, masks, active values, inactive values, and metadata
  fail explicitly;
- structurally valid scientific perturbations remain representable so Stage 6
  can prove that validation detects them;
- repeated builds are exactly reproducible, including masks and `NaN`
  positions;
- custom material collections produce the correct outer shape;
- complete study construction remains below the two-second budget; and
- building a study writes no files and does not import Matplotlib.

All 71 current Task 4 tests pass. No independent reference module, validation
report, output file, figure, animation, or presentation was created in this
stage. The next milestone is **Stage 6: independent Decimal references,
structured validation, deliberate failure detection, and validation CLI**.

## Stage 6 implementation and completion check

Stage 6 added:

- [`reference.py`](reference.py), containing five independent scalar
  calculations built from standard-library `Decimal` and exact SI text;
- [`validation.py`](validation.py), containing immutable `ValidationCheck` and
  `Task04ValidationReport` records plus the stable `validate_task04` entry
  point;
- [`validate_task04.py`](validate_task04.py), a validation-only command that
  prints every observed value, target, unit, comparison, and tolerance;
- [`test_validation.py`](test_validation.py), covering analytical references,
  all report contracts, every check family, deliberate failures, command exit
  statuses, runtime, determinism, and side effects; and
- the expanded package API in [`__init__.py`](__init__.py).

Run the independent validation from the repository root with:

```bash
python3 -m task04_photoelectric_effect.validate_task04
```

The baseline passes all 43 checks. They cover exact constants and source
records, work-function conversion, both grids, finiteness, both energy
identities, the common gradient, all 18 metal-specific cut-offs, both threshold
forms, both masks, physical voltages and bounds, both monotonic trends,
coincident materials, cut-off ordering, cross-coordinate consistency, and both
frozen scalar anchors.

Stage 6 is complete because:

- the independent path imports neither NumPy nor the production model;
- all analytical targets originate from exact decimal strings rather than from
  the arrays being tested;
- check names, ordering, schemas, comparisons, and tolerances are immutable and
  deterministic;
- changing a work function, one curve value, one emission-mask value, or one
  analytical cut-off causes the intended checks to fail;
- validation never mutates the immutable study or repairs failed values;
- the command exits `0` only for a passing report and `1` for a failed report;
- validation writes no files and does not import Matplotlib; and
- all 95 focused Task 4 tests pass within the declared runtime budget.

No CSV, JSON, figure, animation, or presentation artifact was created during
this stage. The next milestone is **Stage 7: deterministic CSV and JSON
evidence, validation-first generation, and transactional output safety**.

## Stage 7 implementation and completion check

Stage 7 added [`generate_task04.py`](generate_task04.py), its 23 focused tests
in [`test_generation.py`](test_generation.py), and the five committed artifacts
in [`../data/task04`](../data/task04):

| Artifact | Contents | Data rows |
| --- | --- | ---: |
| `material_cutoffs.csv` | Official work functions and analytical cut-offs | 9 |
| `stopping_voltage_frequency.csv` | Long-form frequency curves and physical-domain flags | 18,009 |
| `stopping_voltage_wavelength.csv` | Long-form wavelength curves and physical-domain flags | 19,809 |
| `validation_report.json` | Complete ordered Stage 6 report | 43 checks |
| `reproducibility_manifest.json` | Constants, configuration, sources, units, tolerances, and filenames | one manifest |

Regenerate only the numerical evidence from any working directory with:

```bash
python3 -m task04_photoelectric_effect.generate_task04 --data-only
```

The default destination is resolved from the repository root, while
`--data-dir PATH` supports a deliberate alternative location. The
`--data-only` path remains available after Stage 8 and never imports
Matplotlib.

Stage 7 is complete because:

- generation validates the complete study before resolving or creating an
  output directory;
- all CSV headers, units, material order, grid order, row counts, lowercase
  booleans, and empty non-emission fields match the frozen contract;
- floating-point evidence uses 17 significant digits where round-trip
  precision is required, while official one-decimal work functions retain
  their source precision;
- both JSON files are sorted, indented, finite, schema-complete, and free of
  timestamps, user names, host names, absolute paths, or random identifiers;
- every temporary artifact is reparsed and checked before installation;
- pre-existing destinations are backed up, atomic replacement occurs in stable
  order, and an injected later replacement failure restores every prior byte;
- writer, verification, path, validation, and command-line failures leave no
  temporary, backup, or partial scientific output;
- repeated generation in new and existing directories is byte-identical;
- the `--data-only` path does not import Matplotlib and works independently of
  the caller's current directory;
- the complete evidence set is 2,118,299 bytes and regenerates in about 0.26
  seconds on the portable MacBook baseline; and
- all 118 focused Task 4 tests pass.

The next milestone is **Stage 8: deterministic PNG/SVG figures, required
scientific annotations, transactional plotting, and original-resolution visual
inspection**.

## Stage 8 implementation and completion check

Stage 8 added [`plotting.py`](plotting.py), its 19 focused tests in
[`test_plotting.py`](test_plotting.py), and five committed PNG/SVG pairs in
[`../figures/task04`](../figures/task04):

| Figure stem | Purpose | PNG dimensions |
| --- | --- | ---: |
| `stopping_voltage_frequency` | Required nine-metal frequency comparison | $3840\times2160$ |
| `stopping_voltage_wavelength` | Supporting wavelength and visible-band comparison | $3840\times2160$ |
| `copper_threshold_explanation` | Physical curve versus non-physical extrapolation | $3200\times1800$ |
| `photoelectric_validation` | Error-to-tolerance evidence for all numerical check families | $3840\times1920$ |
| `task04_summary` | Presentation-ready four-panel overview | $3840\times2160$ |

Regenerate validated data and all figures with:

```bash
python3 -m task04_photoelectric_effect.generate_task04
```

Use `--data-dir PATH` and `--figure-dir PATH` for deliberate alternative
destinations. Add `--data-only` when figures are not required.

The required frequency graph represents all nine official records using seven
visually distinct ideal curves: Ag, Al, and Pb are grouped because their
official $4.3\ \mathrm{eV}$ values produce exactly coincident results. Each
physical segment begins at a coloured analytical threshold marker; the graph
explicitly states that the absent region is no photoemission, not zero stopping
potential.

Stage 8 is complete because:

- every plot is built from the validated immutable study arrays rather than
  from a second plotting-only physics calculation;
- the wavelength graph marks the visible band and explains why only sodium
  reaches it in the ideal official table;
- the copper graph labels the dashed negative section exactly as a mathematical
  extrapolation with no photoemission;
- the validation graph normalizes observed errors by their pre-declared
  tolerances, with every ratio below one;
- the summary combines both coordinates, the copper threshold, the governing
  equation, the key conclusions, and the 43/43 validation result in 16:9;
- the palette is colour-blind-conscious, units are explicit, metadata is fixed,
  SVG dates are absent, and SVG IDs use a fixed hash salt;
- temporary PNG/SVG files are parsed and dimension-checked before installation;
- existing figures are backed up and fully restored after injected writer,
  verification, or later atomic-install failures;
- all ten outputs are byte-identical across clean and overwrite regeneration;
- the complete figure set is below the ten-megabyte portability budget;
- all five PNGs were inspected at original resolution, after which one
  legend/visible-band overlap was corrected and the affected figures were
  re-inspected; and
- all 137 focused Task 4 tests pass.

The next milestone is **Stage 9: concise scientific results, interpretation,
assumptions, limitations, and presentation-facing explanation**.

## Stage 9 implementation and completion check

Stage 9 added
[`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md), a complete
evidence-based explanation for later conversion into concise slide narration.

The report:

- derives the shared frequency gradient $h/e$ and both analytical threshold
  relations from Einstein's photoelectric equation;
- records all nine official work functions, cut-off frequencies, and cut-off
  wavelengths with units and source-appropriate precision;
- explains why frequency curves are parallel, why wavelength curves vary as
  $1/\lambda$, and why higher work function moves both thresholds;
- records the stopping potentials for all metals at the frozen frequency and
  wavelength anchors;
- explains the exact Ag/Al/Pb overlap without implying that more precise real
  surface values must coincide;
- states precisely that sodium emits only for the shorter-wavelength part of
  the visible range, up to $516.6\ \mathrm{nm}$ in this ideal table;
- distinguishes a dashed negative energy deficit from a physical stopping
  potential and explains why no photoemission is not the same as zero voltage;
- distinguishes maximum electron energy from photocurrent and light intensity;
- summarizes the largest observed numerical errors against every important
  pre-declared tolerance;
- states the one-photon, uniform-work-function, vacuum-wavelength, and ideal
  apparatus assumptions;
- identifies surface orientation, cleanliness, oxidation, contact potential,
  energy distributions, and measurement uncertainty as omitted real effects;
- separates internal numerical validation from experimental validation; and
- supplies supported presentation claims, explicit overclaims to avoid, and a
  one-sentence final takeaway.

Every numerical statement was checked against the committed CSV/JSON evidence
and immutable study arrays. All Markdown links resolve to tracked artifacts,
the report contains no machine-specific path, and all 137 Task 4 tests remain
passing.

No animation, PowerPoint, or speaker script was created during this stage. The
next milestone was **Stage 10: decide whether the optional PhET-style animation
adds enough explanatory value to justify its implementation and validation**.

## Stage 10 implementation and completion check

Stage 10 approved and implemented the optional extension after protecting the
completed baseline. It added:

- [`ANIMATION_DECISION.md`](ANIMATION_DECISION.md), recording the value gate,
  four-scene story, claims, omissions, and acceptance criteria;
- [`animation.py`](animation.py), containing immutable scene/configuration
  records and rollback-safe GIF/storyboard generation;
- [`test_animation.py`](test_animation.py), protecting physics, dimensions,
  reproducibility, transactions, direct and integrated command lines, and
  committed-output freshness;
- [`photoelectric_demo.gif`](../figures/task04/photoelectric_demo.gif), a
  six-second, 60-frame, $1920\times1080$ looping demonstration; and
- [`photoelectric_demo_storyboard.png`](../figures/task04/photoelectric_demo_storyboard.png),
  a $2400\times1350$ static four-panel preview.

The four scenes use sodium and compare $550\ \mathrm{nm}$ below threshold with
$450\ \mathrm{nm}$ above threshold. They then raise the illustrative intensity
without changing $K_{\max}$ or $V_s$, and finally apply the calculated reverse
stopping potential. Below threshold, the display explicitly marks both
$K_{\max}$ and $V_s$ as undefined.

Generate only the extension with:

```bash
python3 -m task04_photoelectric_effect.animation
```

Generate all Task 4 evidence, figures, and animation artifacts with:

```bash
python3 -m task04_photoelectric_effect.generate_task04 --with-animation
```

Stage 10 is complete because:

- the extension is generated only from a passing, exactly matched 43-check
  validation report;
- all displayed energy and voltage values come from immutable study-grid
  entries rather than duplicated physics;
- the below-threshold scene never represents an undefined quantity as a
  physical zero or negative stopping potential;
- intensity changes the illustrative photon/electron count while preserving
  maximum energy and stopping potential;
- the final scene applies $V=V_s$ and clearly reports zero photocurrent;
- motion, counts, trajectories, geometry, speed, and scale are labelled
  schematic rather than experimental predictions;
- both artifacts satisfy their declared format, dimensions, frame count,
  duration, loop, permissions, file-order, and portability contracts;
- repeated outputs are byte-identical and injected late failures preserve
  every pre-existing destination byte;
- the complete and extension-only command-line paths both pass; and
- the GIF's frames and the complete storyboard were visually inspected at
  original resolution after the right-edge status annotation was corrected;
- all 149 focused Task 4 tests and all 373 repository tests pass.

The next milestone is **Stage 11: editable presentation slide, selected assets,
preview, speaker notes, and timed narration script**.

## Stage 11 implementation and completion check

Stage 11 added the complete
[`presentation/task04`](../presentation/task04/README.md) package:

- [`Task04_Photoelectric_Effect.pptx`](../presentation/task04/Task04_Photoelectric_Effect.pptx),
  a reproducible editable 16:9 PowerPoint with one competition slide;
- the high-resolution
  [`2401x1350 preview`](../presentation/task04/preview/Task04_Photoelectric_Effect_preview.png);
- [`SPEAKER_SCRIPT.md`](../presentation/task04/SPEAKER_SCRIPT.md), containing a
  46-word competition script, timed cues, expanded and rehearsal versions,
  pronunciation guidance, and likely-question answers;
- [`SLIDE_CONTENT.md`](../presentation/task04/SLIDE_CONTENT.md), freezing the
  visible text, alternative text, and content boundary;
- [`deck-style.md`](../presentation/task04/deck-style.md), preserving visual
  continuity with Tasks 2 and 3;
- seven copied source assets in
  [`images`](../presentation/task04/images/), ordered for immediate manual use;
- a pinned PptxGenJS generator, lock file, preview renderer, and structural
  validator.

The required nine-metal frequency graph occupies the largest slide area. The
validated animated GIF remains a smaller supporting visual. A compact evidence
card displays $eV_s=hf-W$, the common-gradient form, sodium's
$516.6\ \mathrm{nm}$ visible cut-off, and the 43/43 validation result.

Regenerate and validate the presentation with:

```bash
cd presentation/task04
npm ci
npm run build
npm run preview
npm run validate
```

Stage 11 is complete because:

- the slide follows the established one-slide, 17--18-second format for the
  ten-task competition video;
- the required output is visually dominant and the optional extension cannot
  be mistaken for the official requirement;
- both embedded visuals are byte-identical to their validated source assets;
- the embedded GIF remains a continuous 60-frame animation rather than a
  flattened still;
- the slide has meaningful alternative text and editable text, equations,
  shapes, captions, and notes;
- the final narration is 46 words and explicitly states the common gradient,
  sodium result, undefined below-threshold domain, and 43-check validation;
- all seven convenient presentation assets remain exact copies of the source
  figures and animation;
- the PowerPoint archive has exactly one slide, one notes page, and two embedded
  visuals, with fixed portable metadata;
- two consecutive builds produced the same PowerPoint SHA-256 digest, and two
  consecutive renders produced the same preview digest;
- the validator passes with a $2401\times1350$ 16:9 preview; and
- the preview was inspected at original resolution with no overlap, clipping,
  cropping, or unreadable principal result.

The next milestone is **Stage 12: clean regeneration, full acceptance checks,
repository hygiene, private GitHub synchronization, and final acceptance
report**.

## Stage 12 final acceptance

Stage 12 added [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md) and closed every
item in the acceptance boundary.

The final audit confirms:

- the official mandatory graph and all nine source records are present;
- the physical model, domains, equations, constants, units, and cut-offs match
  the frozen specification;
- all 43 independent scientific checks pass;
- clean out-of-tree generation reproduces all 17 data, static-figure, GIF, and
  storyboard artifacts byte-for-byte;
- all final figures and animation states have been inspected at original
  resolution;
- the optional animation remains scientifically bounded and secondary;
- the editable one-slide PowerPoint, embedded GIF, preview, notes, selected
  assets, and 46-word script regenerate and validate deterministically;
- all 149 focused Task 4 tests and all 373 repository tests pass;
- syntax, whitespace, link, secret, portability, temporary-file, and hidden-file
  checks pass;
- GitHub reports the repository as private; and
- local `main` and `origin/main` are synchronized after the final acceptance
  commit.

**Task 4 is complete. No Task 4 stage remains pending.**
