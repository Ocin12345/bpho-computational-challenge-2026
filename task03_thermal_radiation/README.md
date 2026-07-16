# Task 3: Planck Radiation and Einstein Heat Capacity

## Status

Stages 1 through 5 are complete. The official requirements, reference
examples, project scope, planned evidence, and exclusions are recorded below.
The complete equations, notation, units, constants, numerical conventions,
reference targets, and pre-declared validation tolerances are frozen in the
[mathematical and numerical specification](MATHEMATICAL_MODEL.md). The
[accepted architecture decision](architecture/ADR-001-deterministic-vectorized-model.md)
now fixes module ownership, public APIs, output schemas, command-line
contracts, tests, and reproducibility rules. The exact physical constants,
vectorized Planck spectral-radiance and spectral-exitance functions, unit
conversion, and focused Stage 4 tests are implemented. The complete in-memory
Planck study now passes the pre-declared Wien, Stefan--Boltzmann,
radiance-integral, finiteness, and exitance-identity checks. Einstein modelling,
saved result files, and figures remain for later stages.

## Official sources reviewed

The scope is based on both files supplied in the official 2026 download:

1. page 2 of the three-page **BPhO ComPhys Challenge 2026** written brief; and
2. slides 17--24 of the 76-slide **BPhO CompPhys2026 Quantum** presentation.

The presentation file is a PDF exported from PowerPoint. The official ZIP does
not contain a separate `.pptx` version.

## Official objective

The written brief asks entrants to plot the Planck black-body radiation
spectrum $B(\lambda,T)$ for several temperatures and to plot Einstein's model
of the molar heat capacity of solids against temperature for various atomic
crystals, with gold, copper, and iron given as examples.

The presentation states the same two-part task more compactly:

> Plot the Planck spectrum $B(\lambda,T)$ and Einstein's model of the heat
> capacity $C$ of solids.

Task 3 therefore has two mandatory scientific outputs:

1. a family of Planck-spectrum curves as functions of wavelength for several
   absolute temperatures; and
2. a family of Einstein molar-heat-capacity curves as functions of temperature
   for several solids.

Unlike Tasks 1 and 2, Task 3 does not require a random simulation, repeated
trials, particle animation, or a long time-stepping calculation.

## What is required and what is illustrative

The official brief requires **several temperatures** and **various solids**, but
does not prescribe one compulsory numerical grid or a single compulsory set of
values. The detailed slides provide worked examples that we will use as the
reference case.

| Item | Official requirement | Official demonstration | Our frozen baseline |
| --- | --- | --- | --- |
| Planck temperatures | Several temperatures | $4000$, $5000$, and $6000\ \mathrm K$ | Use all three as the principal comparison |
| Planck wavelength range | Plot against wavelength | Approximately $0$--$2500\ \mathrm{nm}$ | Use a range that fully displays all three peaks and tails |
| Heat-capacity materials | Various atomic crystals | Au, Cu, Ti, Al, Fe, Si, and C | Use all seven materials |
| Heat-capacity range | Plot against temperature | Approximately $0$--$800\ \mathrm K$ | Use $0$--$800\ \mathrm K$ for the principal figure |
| Dulong--Petit limit | Discussed in the presentation | Horizontal limit at $3R$ | Display and test the limit |
| Solar comparison | Background example only | Sun at about $5778\ \mathrm K$ and ASTM E490 data | Optional context; not part of the required baseline |

The values in the demonstration guide our reference calculation, but the
challenge is asking us to construct and explain the models rather than to copy
the appearance of the example graphs.

## Official solid reference data

The presentation supplies the following material values. Stage 2 will define
the exact equations connecting the Debye temperature, Einstein temperature,
and Einstein frequency.

| Material | Symbol | Debye temperature / K | Einstein frequency / $10^{13}\ \mathrm{Hz}$ |
| --- | :---: | ---: | ---: |
| Gold | Au | $170$ | $0.2855$ |
| Copper | Cu | $343.5$ | $0.5769$ |
| Titanium | Ti | $420$ | $0.7054$ |
| Aluminium | Al | $428$ | $0.7188$ |
| Iron | Fe | $470$ | $0.7893$ |
| Silicon | Si | $645$ | $1.0832$ |
| Carbon | C | $2230$ | $3.7451$ |

These are reference inputs for the Einstein model. They are not experimental
heat-capacity measurements to which we will fit free parameters.

## Frozen baseline scope

The Task 3 baseline will:

1. use Python, NumPy, and Matplotlib;
2. calculate both physical models directly from their equations;
3. use SI units internally and presentation-friendly units on graphs;
4. reproduce the official $4000$, $5000$, and $6000\ \mathrm K$ Planck
   comparison;
5. calculate Einstein curves for all seven solids in the official table;
6. save deterministic, machine-readable numerical results;
7. generate publication-quality PNG and SVG figures;
8. explain the physical trends and model limitations; and
9. prepare a concise Task 3 slide and speaker script for the final screencast.

The calculation is deterministic. It will not need random seeds, ensembles,
GPU acceleration, or repeated Monte Carlo runs. It should run comfortably on
the MacBook Air.

## Declared high-standard evidence

The following checks go beyond merely drawing curves and are part of our
planned Task 3 evidence:

- verify the Planck peak positions using Wien's displacement law;
- verify the integrated spectral exitance using the Stefan--Boltzmann law;
- state clearly the distinction between spectral radiance and spectral
  exitance, including the associated factor of $\pi$;
- verify that the Einstein heat capacity tends to zero at low temperature;
- verify that it approaches the Dulong--Petit value $3R$ at high temperature;
- reproduce the official Einstein-frequency table from the supplied material
  temperatures within its displayed rounding;
- use numerically stable forms of both models at extreme arguments; and
- show the universal Einstein-model behaviour using a normalized comparison
  if it remains clear enough for the supporting figure set.

These checks are validation of the requested models, not replacements for the
two required primary plots.

## Explicit exclusions from the baseline

To prevent Task 3 from expanding beyond its role in a ten-task, three-minute
submission, the baseline will not include:

- an atmospheric absorption or radiative-transfer model;
- a downloaded ASTM solar-spectrum dataset or a fit to observational data;
- a graphical user interface or animation;
- a derivation of Planck's law from statistical mechanics;
- a full microscopic lattice-dynamics simulation;
- experimental heat-capacity fitting;
- a Debye heat-capacity implementation; or
- GPU-specific code.

The presentation mentions Debye's model as a later improvement. A small
Einstein--Debye comparison may be considered only after the complete baseline
passes every acceptance check. It is an optional extension and cannot block
completion of the official task.

## Planned deliverables

Later stages will produce the following evidence:

| Deliverable | Purpose |
| --- | --- |
| Tested Python model | Reproducible implementation of both official equations |
| Planck-spectrum figure | Required comparison across several temperatures |
| Einstein heat-capacity figure | Required comparison across several solids |
| Validation figure or table | Evidence for Wien, Stefan--Boltzmann, and limiting behaviour |
| CSV and JSON results | Machine-readable parameters, results, errors, and pass/fail checks |
| Scientific explanation | Interpretation, assumptions, units, and limitations |
| Presentation package | Final slide, optional supporting figures, and timed narration |

Exact filenames and module interfaces will be frozen in Stage 3, after the
mathematical specification is complete.

## Acceptance boundary for the complete task

Task 3 will eventually be considered complete only when all of the following
are true:

- the two official families of curves have been generated from our own code;
- all three reference Planck temperatures and all seven reference solids are
  included;
- notation and units are explicit and internally consistent;
- declared analytical and numerical validation checks pass documented
  tolerances;
- numerical results and figures can be regenerated from a clean command;
- every final figure has been visually inspected;
- the physical interpretation and limitations are written clearly;
- the presentation slide and narration are complete; and
- the committed repository is clean and synchronized with GitHub.

## Stage 1 completion check

Stage 1 is complete because:

- both official files have been read;
- the mandatory task has been separated from illustrative examples;
- the baseline, validation work, optional extension, and exclusions are
  explicit;
- the expected deliverables and final acceptance boundary are recorded; and
- no mathematical or software implementation has begun prematurely.

## Stage 2 completion check

Stage 2 is complete because:

- both official models have precise definitions, units, and domains;
- spectral radiance and spectral exitance are distinguished explicitly;
- exact SI constants and independent analytical targets are recorded;
- all seven official material conversions reproduce the displayed table;
- stable numerical forms and fixed calculation grids are declared;
- assumptions, limitations, and output rules are explicit; and
- validation tolerances were fixed before implementation.

The complete details are in
[MATHEMATICAL_MODEL.md](MATHEMATICAL_MODEL.md). Stage 3 records how that frozen
specification will be implemented reproducibly.

## Stage 3 completion check

Stage 3 is complete because:

- a deterministic vectorized NumPy architecture has been accepted;
- modules have single, explicit scientific responsibilities;
- public APIs, units, broadcasting, and error behaviour are frozen;
- immutable configuration, material, result, and validation records are
  defined;
- CSV, JSON, figure, and presentation paths have fixed ownership;
- output transactions and cross-computer reproducibility rules are explicit;
- tests and portability budgets are pre-declared; and
- no physics implementation has begun.

The complete design is in
[ADR-001](architecture/ADR-001-deterministic-vectorized-model.md). Stage 4
implements its first physical-model boundary.

## Stage 4 implementation and completion check

Stage 4 added:

- [`constants.py`](constants.py), containing the exact SI and derived constants;
- [`models.py`](models.py), containing the vectorized Planck radiance,
  exitance, and per-nanometre conversion functions;
- [`__init__.py`](__init__.py), exposing the Stage 4 public API;
- [`test_constants_and_materials.py`](test_constants_and_materials.py),
  protecting the authoritative constants; and
- [`test_planck_model.py`](test_planck_model.py), testing reference values,
  domains, broadcasting, units, both numerical branches, and asymptotic
  behaviour.

Run the current Task 3 suite from the repository root with:

```bash
python3 -m unittest discover -s task03_thermal_radiation -p 'test_*.py' -v
```

Stage 4 is complete because:

- all three planned Planck/unit-conversion APIs are implemented;
- scalar and broadcast array contracts are tested;
- invalid and non-finite physical inputs fail explicitly;
- the short-wavelength branch underflows cleanly instead of producing `NaN`;
- the long-wavelength result approaches the Rayleigh--Jeans law;
- the full declared integration domain evaluates without runtime warnings;
- all 21 Task 3 tests pass; and
- all 117 earlier Task 1 and Task 2 tests still pass.

No Einstein, study-building, validation-report, output, or plotting code was
added during Stage 4. Stage 5 implements the Planck-spectrum validation
specified by that architecture.

## Stage 5 implementation and completion check

Stage 5 added:

- [`configuration.py`](configuration.py), containing immutable grids and
  pre-declared tolerances;
- [`reference.py`](reference.py), containing independent Wien and
  Stefan--Boltzmann targets without importing the numerical model;
- [`analysis.py`](analysis.py), constructing immutable spectra, peak searches,
  and wavelength integrals;
- [`validation.py`](validation.py), returning structured, serializable checks;
- [`validate_task03.py`](validate_task03.py), providing a validation-only
  command with a meaningful exit status; and
- [`test_analysis_and_validation.py`](test_analysis_and_validation.py),
  testing configuration, references, immutability, reproducibility, deliberate
  failure detection, runtime, and command-line behaviour.

Run the current validation with:

```bash
python3 -m task03_thermal_radiation.validate_task03
```

The reference Stage 5 results are:

| $T$ / K | Numerical peak / nm | Wien target / nm | Peak relative error | Exitance-integral relative error |
| ---: | ---: | ---: | ---: | ---: |
| $4000$ | $724.440$ | $724.442989$ | $4.13\times10^{-6}$ | $1.08\times10^{-9}$ |
| $5000$ | $579.550$ | $579.554391$ | $7.58\times10^{-6}$ | $1.08\times10^{-9}$ |
| $6000$ | $482.960$ | $482.961993$ | $4.13\times10^{-6}$ | $1.08\times10^{-9}$ |

The allowed relative errors are $10^{-3}$ for Wien peaks and $2\times10^{-3}$
for the Stefan--Boltzmann and radiance integrals. All 13 Stage 5 checks pass
without changing those thresholds. A complete study takes about $0.08$ seconds
on the MacBook Air, well below the five-second portability budget.

Stage 5 is complete because:

- analytical references and numerical model paths are separated;
- all spectrum and integral arrays are finite and non-negative;
- all three numerical peaks satisfy Wien's displacement law;
- all three exitance integrals satisfy the Stefan--Boltzmann law;
- all three radiance integrals satisfy $\sigma T^4/\pi$;
- the $M_\lambda=\pi B_\lambda$ identity passes point by point;
- immutable results reproduce exactly across repeated runs;
- a deliberately incorrect peak causes validation to fail; and
- all 40 Task 3 tests and all 117 earlier tests pass.

No CSV, JSON, figure, presentation, or Einstein-model output was created in
this stage. The next stage is **Stage 6: Einstein heat-capacity implementation
and unit tests for the seven official solids**.
