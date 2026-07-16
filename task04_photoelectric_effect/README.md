# Task 4: Photoelectric Effect

## Status

Stage 1 is complete. The two official source files have been read, and the
mandatory model, reference inputs, baseline deliverables, optional extension,
exclusions, staged workflow, and final acceptance boundary are frozen below.
No Task 4 physics code has been written yet. Stage 2 will define the complete
mathematical and numerical specification before implementation begins.

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

## Optional extension gate

After the complete baseline passes its scientific and visual checks, we will
decide whether a small PhET-style animation materially improves the final
submission. A worthwhile extension could show:

- a selectable metal;
- adjustable photon wavelength or frequency;
- adjustable intensity affecting the number of emitted electrons but not
  their maximum energy;
- electron emission turning on at the threshold; and
- a stopping-potential control suppressing the photocurrent.

The extension cannot delay or destabilize the required graph, evidence, or
three-minute presentation. If it does not add enough explanatory value, Stage
10 will record a justified decision to omit it.

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

The next milestone is **Stage 2: the mathematical and numerical
specification**.
