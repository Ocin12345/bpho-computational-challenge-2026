# Task 3: Planck Radiation and Einstein Heat Capacity

## Status

Stage 1 is complete: the official requirements, reference examples, project
scope, planned evidence, and exclusions are recorded below. No Task 3 physics
code has been implemented yet. Stage 2 will define the complete mathematical
model, notation, units, constants, and numerical conventions before
implementation begins.

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

The next stage is **Stage 2: complete mathematical specification**.
