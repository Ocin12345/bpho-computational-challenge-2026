# Task 4 Mathematical and Numerical Specification

## Status and purpose

This document completes Stage 2. It freezes the equations, notation, units,
constants, official material inputs, physical domains, numerical grids,
display conventions, analytical reference values, and validation tolerances
before software architecture or physics implementation begins.

The future implementation must follow this specification unless a change is
supported by evidence and documented explicitly. A result produced by the
model must never be used as its own independent validation target.

## Modelling conventions

Task 4 uses Einstein's ideal one-photon photoelectric equation. It is a
deterministic energy-balance model with no random variables, fitted
parameters, time stepping, or dependence on photon intensity.

All calculations will use IEEE 754 double precision and SI units internally.
Electronvolts and nanometres are accepted or displayed only through explicit
conversions. Values shown in tables may be rounded, but stored calculations
must retain full double-precision values.

## Symbols and units

| Symbol | Meaning | SI unit |
| :---: | --- | :---: |
| $K_{\max}$ | Maximum emitted-electron kinetic energy | $\mathrm J$ |
| $h$ | Planck constant | $\mathrm{J\,s}$ |
| $e$ | Elementary charge magnitude | $\mathrm C$ |
| $c$ | Speed of light in vacuum | $\mathrm{m\,s^{-1}}$ |
| $f$ | Incident-photon frequency | $\mathrm{Hz}$ |
| $\lambda$ | Incident-photon vacuum wavelength | $\mathrm m$ |
| $W$ | Metal work function | $\mathrm J$ |
| $W_{\mathrm{eV}}$ | Numerical work function expressed in electronvolts | $\mathrm{eV}$ |
| $V_s$ | Reverse stopping-potential magnitude | $\mathrm V$ |
| $f_0$ | Threshold or cut-off frequency | $\mathrm{Hz}$ |
| $\lambda_0$ | Threshold or cut-off vacuum wavelength | $\mathrm m$ |

The letter $W$ is both the conventional symbol for work function and the
chemical symbol for tungsten. Tables and code fields must use
`work_function_ev` and `symbol` so the two meanings cannot be confused.

## Physical constants

The implementation will use the exact defining SI values rather than the
rounded electron charge printed in the official slides.

| Constant | Value used | Status |
| :---: | ---: | --- |
| $h$ | $6.62607015\times10^{-34}\ \mathrm{J\,s}$ | Exact SI definition |
| $e$ | $1.602176634\times10^{-19}\ \mathrm C$ | Exact SI definition |
| $c$ | $299792458\ \mathrm{m\,s^{-1}}$ | Exact SI definition |
| $1\ \mathrm{eV}$ | $1.602176634\times10^{-19}\ \mathrm J$ | Exact from $e$ |

Useful derived constants are

$$
\frac{h}{e}
=4.1356676969238586\times10^{-15}\ \mathrm{V\,s},
$$

$$
\frac{hc}{e}
=1.2398419843320026\times10^{-6}\ \mathrm{V\,m}
=1239.8419843320026\ \mathrm{V\,nm},
$$

and

$$
\frac{e}{h}
=2.4179892420849182\times10^{14}\ \mathrm{Hz\,eV^{-1}}.
$$

Derived constants will be calculated from $h$, $e$, and $c$ rather than
stored as independent rounded inputs.

## Official material inputs

The official presentation supplies the following one-decimal work functions,
which are frozen in the displayed order:

| Material | Symbol | $W_{\mathrm{eV}}$ / eV |
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

The mathematical work function in joules is

$$
W=eW_{\mathrm{eV}}.
$$

The one-decimal values are authoritative challenge inputs for this model, not
claims that real surfaces have exact, universal work functions. They will be
stored once in immutable material records and will not be adjusted to improve
the appearance of a graph.

## Energy balance and stopping voltage

For one incident photon interacting with one electron,

$$
K_{\max}=hf-W.
$$

The stopping potential is the reverse potential whose electrical work equals
that maximum kinetic energy:

$$
eV_s=K_{\max}.
$$

Therefore,

$$
V_s=\frac{hf-W}{e}.
$$

The stopping voltage is a **magnitude**. The applied electrode voltage may be
described as negative relative to the collector, but the required graph and
this specification report the non-negative magnitude $V_s$.

## Frequency form

Substituting $W=eW_{\mathrm{eV}}$ gives

$$
V_{\mathrm{linear}}(f,W_{\mathrm{eV}})
=\frac{h}{e}f-W_{\mathrm{eV}}.
$$

The numerical value of a work function in electronvolts appears directly as
volts after division by $e$. This does not mean electronvolts and volts are the
same unit: an electronvolt is energy, whereas a volt is energy per unit
charge.

For a fixed metal, the extrapolated graph is a straight line with

$$
\frac{dV_{\mathrm{linear}}}{df}=\frac{h}{e}
$$

and vertical intercept

$$
V_{\mathrm{linear}}(0)=-W_{\mathrm{eV}}\ \mathrm V.
$$

All metals therefore have the same gradient but different horizontal and
vertical intercepts.

## Wavelength form

For vacuum wavelength,

$$
f=\frac{c}{\lambda},
$$

so

$$
V_{\mathrm{linear}}(\lambda,W_{\mathrm{eV}})
=\frac{hc}{e\lambda}-W_{\mathrm{eV}}.
$$

When wavelength is supplied in nanometres,

$$
V_{\mathrm{linear}}(\lambda_{\mathrm{nm}},W_{\mathrm{eV}})
=\frac{1239.8419843320026}{\lambda_{\mathrm{nm}}}
-W_{\mathrm{eV}}.
$$

Unlike the frequency graph, this graph is not linear. Shorter wavelength
means greater photon energy and therefore a larger stopping voltage.

## Thresholds and the physical domain

Photoemission requires

$$
hf\geq W.
$$

The threshold frequency and longest photoemitting wavelength are

$$
f_0=\frac{W}{h}=\frac{eW_{\mathrm{eV}}}{h}
$$

and

$$
\lambda_0=\frac{c}{f_0}
=\frac{hc}{eW_{\mathrm{eV}}}.
$$

The physical emission domains are

$$
f\geq f_0
$$

and

$$
0<\lambda\leq\lambda_0.
$$

At the threshold, $V_s=0$. Below threshold, no photoelectrons are emitted and
the stopping voltage is undefined. The implementation will therefore retain
two distinct quantities:

1. `linear_stopping_voltage_v`, the signed mathematical extrapolation; and
2. `physical_stopping_voltage_v`, equal to the non-negative result in the
   emission domain and missing outside that domain.

A below-threshold value must never be silently replaced by a physical zero,
because zero volts at threshold and no emitted electron below threshold are
different states. In arrays, the internal missing value will be `NaN`; CSV
output will use an empty field plus an explicit emission flag, and JSON must
not contain non-standard `NaN` tokens.

## Independent threshold reference table

Using the exact constants and the official work functions gives:

| Material | $W_{\mathrm{eV}}$ / eV | $f_0$ / Hz | $\lambda_0$ / nm |
| --- | ---: | ---: | ---: |
| Ag | $4.3$ | $1.039735374097\times10^{15}$ | $288.335345193$ |
| Al | $4.3$ | $1.039735374097\times10^{15}$ | $288.335345193$ |
| Au | $5.1$ | $1.233174513463\times10^{15}$ | $243.106271438$ |
| Cu | $4.7$ | $1.136454943780\times10^{15}$ | $263.796166879$ |
| Sn | $4.4$ | $1.063915266517\times10^{15}$ | $281.782269166$ |
| Pb | $4.3$ | $1.039735374097\times10^{15}$ | $288.335345193$ |
| W | $4.5$ | $1.088095158938\times10^{15}$ | $275.520440963$ |
| Ni | $4.6$ | $1.112275051359\times10^{15}$ | $269.530866159$ |
| Na | $2.4$ | $5.803174181004\times10^{14}$ | $516.600826805$ |

These values are analytical targets. Future tests must calculate them through
a reference path separate from the vectorized model implementation.

Silver, aluminium, and lead are exact duplicates within the supplied ideal
table. Their calculated arrays, cut-offs, and validation summaries must be
identical. In figures they will be labelled as one coincident group where
needed for clarity, while the machine-readable output will retain all three
material records.

## Intensity convention

Increasing light intensity at fixed photon frequency increases the expected
number of incident photons and therefore the possible photocurrent. It does
not change the energy $hf$ of each photon, $K_{\max}$, or $V_s$ in this ideal
model.

Intensity is consequently excluded from the baseline stopping-voltage
calculation. If Stage 10 implements the optional animation, intensity may
control an illustrative electron emission rate but must not alter electron
maximum energy or stopping voltage.

## Input domains and error behaviour

The mathematical functions will support scalar and NumPy-broadcastable array
inputs subject to these rules:

- frequency must be finite and $f\geq0$;
- wavelength must be finite and $\lambda>0$;
- work function must be finite and $W_{\mathrm{eV}}>0$;
- material names and symbols must be non-empty and unique by symbol;
- booleans are not accepted as numerical inputs; and
- results that cannot be represented as finite `float64` values must fail
  explicitly.

Frequency zero is valid only for evaluating the signed extrapolated line. It
is outside the photoemission domain for every material in the official table.
Wavelength zero is invalid because the wavelength form is singular there.

## Frozen numerical grids

The following inclusive, uniformly spaced grids are part of the baseline:

| Purpose | Domain | Step | Number of points |
| --- | --- | ---: | ---: |
| Required frequency study | $4.0\times10^{14}$--$2.4\times10^{15}\ \mathrm{Hz}$ | $1.0\times10^{12}\ \mathrm{Hz}$ | $2001$ |
| Supporting wavelength study | $150$--$700\ \mathrm{nm}$ | $0.25\ \mathrm{nm}$ | $2201$ |

The frequency domain includes part of the visible band, the sodium threshold,
all ultraviolet thresholds in the official table, and several volts of
physical stopping potential above every threshold. The wavelength domain
contains every threshold and enough sub-threshold context to show why most of
the supplied metals require ultraviolet light.

For visual context, the visible band is frozen as

$$
380\leq\lambda_{\mathrm{nm}}\leq750,
$$

corresponding in vacuum to approximately

$$
3.9972\times10^{14}\leq f
\leq7.8893\times10^{14}\ \mathrm{Hz}.
$$

This band is an explanatory convention rather than a sharp biological
boundary. It will be shown as a lightly shaded region and will not enter any
photoelectric calculation or pass/fail check.

The grids are for plots and stored evidence. Analytical cut-offs will be
calculated directly from the equations, not estimated from the nearest grid
point. The implementation must construct the inclusive grids from a declared
start, step, and point count so floating endpoint drift cannot change the
output shape between computers.

With the nine official material records, the frequency and wavelength studies
will therefore contain $9\times2001$ and $9\times2201$ model points,
respectively.

## Numerical boundary convention

For frequency calculations, emission is determined by $f\geq f_0$. For
wavelength calculations, emission is determined by
$\lambda\leq\lambda_0$. On the active domain, round-off that produces a tiny
negative value no smaller than $-5\times10^{-12}\ \mathrm V$ may be clamped to
zero. A more negative active-domain value is a validation failure.

This tolerance is only a floating-point boundary convention. It must not turn
a genuinely below-threshold point into photoemission or be used to loosen any
work-function input.

## Frozen analytical anchors

At $f=1.5\times10^{15}\ \mathrm{Hz}$, all nine metals emit in the ideal model.
The expected voltages include:

| Material or group | Expected $V_s$ / V |
| --- | ---: |
| Ag, Al, Pb | $1.903501545386$ |
| Au | $1.103501545386$ |
| Cu | $1.503501545386$ |
| Sn | $1.803501545386$ |
| W | $1.703501545386$ |
| Ni | $1.603501545386$ |
| Na | $3.803501545386$ |

At $\lambda=200\ \mathrm{nm}$, all nine metals also emit. The expected values
include:

| Material or group | Expected $V_s$ / V |
| --- | ---: |
| Ag, Al, Pb | $1.899209921660$ |
| Au | $1.099209921660$ |
| Cu | $1.499209921660$ |
| Sn | $1.799209921660$ |
| W | $1.699209921660$ |
| Ni | $1.599209921660$ |
| Na | $3.799209921660$ |

These values provide simple scalar checks in addition to whole-grid
identities. They are calculated from exact constants and rounded here only for
display.

## Pre-declared validation checks and tolerances

All checks below must be implemented before final evidence is accepted.

| Check | Required criterion |
| --- | --- |
| Constant values | Exact equality to the declared decimal SI definitions |
| Work-function table | Exact material order, names, symbols, and one-decimal values |
| Frequency energy identity | Maximum absolute residual in $eV=hf-W$ no greater than $5\times10^{-12}\ \mathrm{eV}$ when expressed numerically in eV |
| Wavelength energy identity | Maximum absolute residual no greater than $5\times10^{-12}\ \mathrm{eV}$ |
| Common frequency gradient | Relative error from $h/e$ no greater than $5\times10^{-13}$ |
| Frequency cut-offs | Relative error from $eW_{\mathrm{eV}}/h$ no greater than $5\times10^{-13}$ |
| Wavelength cut-offs | Relative error from $hc/(eW_{\mathrm{eV}})$ no greater than $5\times10^{-13}$ |
| Threshold voltage | Absolute value no greater than $5\times10^{-12}\ \mathrm V$ |
| Frequency--wavelength consistency | Maximum absolute difference after $f=c/\lambda$ no greater than $1\times10^{-11}\ \mathrm V$ |
| Physical-domain mask | Exact agreement with the analytical threshold inequalities |
| Physical voltage bounds | Finite and $V_s\geq-1\times10^{-12}\ \mathrm V$ on the active domain |
| Frequency monotonicity | No decrease greater than $1\times10^{-12}\ \mathrm V$ |
| Wavelength monotonicity | No increase greater than $1\times10^{-12}\ \mathrm V$ as wavelength rises |
| Duplicate materials | Ag, Al, and Pb results exactly equal |
| Scalar anchors | Absolute error no greater than $5\times10^{-12}\ \mathrm V$ |
| Reproducibility | Repeated runs produce byte-identical numerical outputs |

Validation code must report observed values, expected values, units,
comparisons, tolerances, and pass/fail status. At least one test must perturb a
work function, one must perturb a voltage curve, and one must corrupt a domain
mask to prove that validation fails for the intended reasons.

## Figure requirements fixed for Stage 8

The required frequency figure will:

- include all nine official material records;
- group Ag, Al, and Pb visually because their ideal curves coincide;
- show only solid physical curve segments at and above threshold;
- mark or label cut-off frequencies without nine unreadable vertical lines;
- label frequency in hertz, normally scaled by $10^{15}$ on the axis;
- label stopping-potential magnitude in volts; and
- state that all physical curves have the common gradient $h/e$.

The supporting wavelength figure will:

- use in-vacuum wavelength in nanometres;
- show physical emission only for $\lambda\leq\lambda_0$;
- identify the visible band for context;
- show that sodium reaches the visible range while the higher-work-function
  examples require ultraviolet light; and
- avoid implying that a missing below-threshold curve is zero voltage.

A separate explanatory figure may use copper, matching the official
$4.7\ \mathrm{eV}$ example, to show a dashed signed extrapolation and the
physical segment. The dashed section must be labelled “mathematical
extrapolation: no photoemission.”

All final figures will use explicit units, fixed dimensions, a
colour-blind-conscious palette, deterministic metadata, and both PNG and SVG
formats.

## Data and serialization conventions

The numerical evidence will retain full precision and include:

- one immutable material table with joule and electronvolt work functions;
- analytical cut-off frequency and wavelength for every material;
- ordered frequency-grid rows for every material;
- ordered wavelength-grid rows for every material;
- signed linear voltage, emission-possible flag, and physical voltage;
- a structured validation report; and
- a reproducibility manifest containing constants, grids, material inputs,
  tolerances, units, and ordered filenames.

CSV floating-point fields will use enough significant digits to round-trip a
`float64`. Physical voltage will be an empty CSV field outside the emission
domain. JSON will be UTF-8, key-sorted, indented, finite, and written with
non-standard `NaN` values forbidden. Files will use LF endings and contain no
timestamps, host names, user names, absolute paths, random identifiers, or
machine-dependent metadata.

## Physical assumptions and limitations

The baseline assumes:

- one photon transfers energy to one electron;
- the photon travels in vacuum before reaching the surface;
- the work function is a single uniform value for each ideal metal;
- the electron with maximum kinetic energy originates at the surface without
  additional energy loss;
- contact potentials and apparatus effects are absent; and
- the stopping potential exactly balances the maximum kinetic energy.

Real measured work functions depend on surface crystal face, cleanliness,
adsorbates, oxidation, and experimental conditions. Real emitted electrons
also have an energy distribution, so the model predicts the maximum energy
rather than every electron having the same speed. The supplied one-decimal
values and our ideal lines must therefore be described as a theoretical
comparison, not fitted experimental data.

The baseline does not model photocurrent magnitude, electron trajectories,
space charge, electric-field geometry, contact potentials, multiphoton
effects, or relativistic corrections. These omissions do not prevent the
model from satisfying the official stopping-voltage task.

## Performance and reproducibility budgets

The frequency and wavelength studies are small array calculations. The future
implementation must meet these conservative budgets on the MacBook Air:

- complete in-memory study and validation: less than $2$ seconds;
- complete data and figure regeneration: less than $15$ seconds;
- numerical evidence: less than $10\ \mathrm{MiB}$;
- complete figure set: less than $10\ \mathrm{MiB}$; and
- no GPU, network request, nondeterministic seed, or current-time dependency.

## Stage 2 completion checklist

Stage 2 is complete when this specification has been checked for:

- agreement with both official Task 4 sources;
- dimensional consistency of every equation;
- exact SI constants and explicit unit conversions;
- all nine official material inputs and duplicate-value behaviour;
- correct treatment of threshold, physical, and extrapolated domains;
- fixed frequency and wavelength grids;
- independent reference cut-offs and scalar anchors;
- validation tolerances declared before implementation;
- deterministic data, figure, and serialization rules; and
- explicit assumptions, exclusions, and performance budgets.

No software architecture or Task 4 physics implementation belongs to Stage 2.
