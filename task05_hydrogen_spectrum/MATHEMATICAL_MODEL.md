# Task 5 Mathematical and Numerical Specification

## Status and purpose

This document completes Stage 2. It freezes the equations, notation, units,
constant values, physical domains, transition enumeration, reference targets,
figure conventions, serialization rules, performance budgets, and validation
tolerances before software architecture or physics implementation begins.

The future implementation must follow this specification unless a later change
is supported by evidence and recorded explicitly. A vectorized model result
must never be reused as its own independent validation target.

## Modelling convention

The baseline is the non-relativistic Bohr model for hydrogen with an
effectively stationary nucleus. It uses the infinite-nuclear-mass Rydberg
constant $R_\infty$, matching the ideal derivation and approximately
$91.13\ \mathrm{nm}$ Lyman series limit shown in the official slides.

The model is deterministic. It contains no random variables, fitted
parameters, particle trajectories, numerical integration, or time stepping.
All calculations will use IEEE 754 double precision. SI units are authoritative
internally; electronvolts and nanometres are presentation units reached only
through explicit conversions.

## Symbols and units

| Symbol | Meaning | SI unit |
| :---: | --- | :---: |
| $n$ | Principal quantum number | dimensionless integer |
| $n_i$ | Initial principal quantum number | dimensionless integer |
| $n_f$ | Final principal quantum number | dimensionless integer |
| $E_n$ | Bound-state energy at level $n$ | $\mathrm J$ |
| $E_{\mathrm R}$ | Ideal Rydberg energy $hcR_\infty$ | $\mathrm J$ |
| $E_\gamma$ | Emitted-photon energy | $\mathrm J$ |
| $h$ | Planck constant | $\mathrm{J\,s}$ |
| $c$ | Speed of light in vacuum | $\mathrm{m\,s^{-1}}$ |
| $e$ | Elementary charge magnitude | $\mathrm C$ |
| $R_\infty$ | Infinite-nuclear-mass Rydberg constant | $\mathrm{m^{-1}}$ |
| $f$ | Emitted-photon frequency | $\mathrm{Hz}$ |
| $\lambda$ | Emitted-photon vacuum wavelength | $\mathrm m$ |

Variables ending in `_ev` will contain numerical energies expressed in
electronvolts. Variables ending in `_nm` will contain numerical wavelengths in
nanometres. Those suffixes are mandatory where the unit is not otherwise
unambiguous.

## Frozen physical constants

The implementation will use the following decimal definitions:

| Constant | Value used | Status |
| :---: | ---: | --- |
| $h$ | $6.62607015\times10^{-34}\ \mathrm{J\,s}$ | Exact SI definition |
| $c$ | $299792458\ \mathrm{m\,s^{-1}}$ | Exact SI definition |
| $e$ | $1.602176634\times10^{-19}\ \mathrm C$ | Exact SI definition |
| $1\ \mathrm{eV}$ | $1.602176634\times10^{-19}\ \mathrm J$ | Exact from $e$ |
| $R_\infty$ | $10973731.568157\ \mathrm{m^{-1}}$ | Frozen 2022 CODATA central value |

The Rydberg constant is not exact. Its CODATA standard uncertainty is
$0.000012\ \mathrm{m^{-1}}$. The baseline freezes the displayed central value
as a reproducible model input; this scientific uncertainty must not be
confused with floating-point error.

The source is the
[NIST 2022 CODATA recommended-values table](https://physics.nist.gov/cuu/pdf/wall_2022.pdf),
which also confirms the exact status of $h$, $c$, and $e$.

Useful derived constants are

$$
\frac{hc}{e}
=1.2398419843320026\times10^{-6}\ \mathrm{eV\,m}
=1239.8419843320026\ \mathrm{eV\,nm},
$$

$$
E_{\mathrm R}=hcR_\infty
=2.1798723611030\times10^{-18}\ \mathrm J
=13.6056931229905\ \mathrm{eV},
$$

and

$$
\lambda_{\mathrm R}=\frac{1}{R_\infty}
=91.1267050583\ \mathrm{nm}.
$$

Derived constants will be calculated from the frozen source constants rather
than stored as independently rounded inputs.

## Bohr energy levels

For ideal hydrogen with nuclear charge $Z=1$,

$$
E_n=-\frac{E_{\mathrm R}}{n^2}.
$$

Every finite bound-state energy is negative. As $n$ increases, $E_n$ rises
monotonically toward the ionization limit,

$$
\lim_{n\rightarrow\infty}E_n=0^-.
$$

The first ten levels are the only finite levels stored in the baseline study.
The infinite limit is analytical and must not be represented by a fabricated
large integer.

| $n$ | Ideal $E_n$ / eV |
| ---: | ---: |
| 1 | $-13.605693122991$ |
| 2 | $-3.401423280748$ |
| 3 | $-1.511743680332$ |
| 4 | $-0.850355820187$ |
| 5 | $-0.544227724920$ |
| 6 | $-0.377935920083$ |
| 7 | $-0.277667206592$ |
| 8 | $-0.212588955047$ |
| 9 | $-0.167971520037$ |
| 10 | $-0.136056931230$ |

The displayed values are rounded reference anchors. Stored calculations will
retain full `float64` precision.

## Emission transitions

An emitted photon corresponds to a downward transition satisfying

$$
n_i>n_f\geq1.
$$

The positive photon energy is

$$
E_\gamma=E_{n_i}-E_{n_f}
=E_{\mathrm R}\left(\frac{1}{n_f^2}-\frac{1}{n_i^2}\right).
$$

The sign convention is fixed: `transition_energy_ev` is always the positive
emitted-photon energy. The negative change in the atom's energy is
$E_{n_f}-E_{n_i}=-E_\gamma$ and must not be stored under the photon-energy
name.

The frequency and vacuum wavelength are

$$
f=\frac{E_\gamma}{h},
$$

$$
\lambda=\frac{c}{f}=\frac{hc}{E_\gamma}.
$$

The equivalent Rydberg form is

$$
\frac{1}{\lambda}
=R_\infty\left(\frac{1}{n_f^2}-\frac{1}{n_i^2}\right).
$$

The energy-difference path and Rydberg-wavenumber path are mathematically
equivalent. The future validator will evaluate them through separate numerical
implementations.

## Frozen finite transition catalogue

The baseline includes every pair

$$
(n_i,n_f)\quad\text{such that}\quad1\leq n_f<n_i\leq10.
$$

The order is fixed as follows:

1. increasing final level $n_f=1,2,\ldots,9$; then
2. increasing initial level $n_i=n_f+1,\ldots,10$ within each final level.

The total count is

$$
\sum_{n_f=1}^{9}(10-n_f)=45.
$$

The first five final levels contain 35 transitions:

| Final level | Series | Transition count |
| ---: | --- | ---: |
| 1 | Lyman | 9 |
| 2 | Balmer | 8 |
| 3 | Paschen | 7 |
| 4 | Brackett | 6 |
| 5 | Pfund | 5 |

The remaining counts are $4$, $3$, $2$, and $1$ for $n_f=6$, $7$, $8$, and
$9$, respectively. These ten records will use their exact quantum numbers and
the display group `Higher series ($n_f\geq6$)` rather than invented names.

Each finite transition record will contain:

- `initial_n`;
- `final_n`;
- `series_name`;
- optional `line_name`;
- `initial_energy_ev` and `final_energy_ev`;
- `photon_energy_ev` and `photon_energy_j`;
- `frequency_hz`;
- `wavelength_m` and `wavelength_nm`; and
- `spectral_region`.

## Series and line naming

The authoritative series mapping is:

| $n_f$ | Series |
| ---: | --- |
| 1 | Lyman |
| 2 | Balmer |
| 3 | Paschen |
| 4 | Brackett |
| 5 | Pfund |
| 6 | Humphreys |

Humphreys may appear in data as its correct name, but the primary legend will
group all $n_f\geq6$ transitions for clarity. Final levels $7$--$9$ will be
stored with an unambiguous generated label such as `n_f=7 series` rather than
an unsupported proper name.

Within a named series, the conventional Greek suffix is determined by
$n_i-n_f$: $1\mapsto\alpha$, $2\mapsto\beta$, $3\mapsto\gamma$, and
$4\mapsto\delta$. Higher offsets may use the quantum-number transition rather
than a long Greek sequence.

## Analytical series limits

For fixed $n_f$, letting $n_i\rightarrow\infty$ gives

$$
E_{\mathrm{limit}}(n_f)=\frac{E_{\mathrm R}}{n_f^2},
$$

$$
\lambda_{\mathrm{limit}}(n_f)=\frac{n_f^2}{R_\infty}.
$$

The first five analytical limits are:

| Series | $n_f$ | Limit energy / eV | Limit wavelength / nm |
| --- | ---: | ---: | ---: |
| Lyman | 1 | $13.605693122991$ | $91.126705058$ |
| Balmer | 2 | $3.401423280748$ | $364.506820233$ |
| Paschen | 3 | $1.511743680332$ | $820.140345524$ |
| Brackett | 4 | $0.850355820187$ | $1458.027280932$ |
| Pfund | 5 | $0.544227724920$ | $2278.167626457$ |

Within a fixed series, increasing $n_i$ must increase $E_\gamma$ and decrease
$\lambda$, approaching these limits without crossing them.

## Frozen named-line anchors

The following values belong to the ideal stationary-nucleus model, not to a
table of measured air wavelengths:

| Line | Transition | Energy / eV | Vacuum wavelength / nm |
| --- | :---: | ---: | ---: |
| Lyman-$\alpha$ | $2\rightarrow1$ | $10.204269842243$ | $121.502273411$ |
| Lyman-$\beta$ | $3\rightarrow1$ | $12.093949442658$ | $102.517543191$ |
| H-$\alpha$ | $3\rightarrow2$ | $1.889679600415$ | $656.112276419$ |
| H-$\beta$ | $4\rightarrow2$ | $2.551067460561$ | $486.009093644$ |
| H-$\gamma$ | $5\rightarrow2$ | $2.857195555828$ | $433.936690754$ |
| H-$\delta$ | $6\rightarrow2$ | $3.023487360665$ | $410.070172762$ |
| Paschen-$\alpha$ | $4\rightarrow3$ | $0.661387860145$ | $1874.606504056$ |
| Brackett-$\alpha$ | $5\rightarrow4$ | $0.306128095267$ | $4050.075780367$ |
| Pfund-$\alpha$ | $6\rightarrow5$ | $0.166291804837$ | $7455.821322949$ |

The longest-wavelength transition in the finite catalogue is
$10\rightarrow9$:

$$
E_\gamma=0.0319145888070\ \mathrm{eV},
\qquad
\lambda=38848.7532090\ \mathrm{nm}.
$$

The shortest-wavelength finite transition is $10\rightarrow1$:

$$
E_\gamma=13.4696361918\ \mathrm{eV},
\qquad
\lambda=92.0471768265\ \mathrm{nm}.
$$

These anchors fix the complete primary-graph range before plotting begins.

## Visible-band convention

For explanatory classification, the visible band is frozen as

$$
380\leq\lambda_{\mathrm{nm}}\leq750.
$$

This convention is not a sharp biological boundary and does not alter the
transition calculation. The classification rules are:

- `ultraviolet` for $\lambda_{\mathrm{nm}}<380$;
- `visible` for $380\leq\lambda_{\mathrm{nm}}\leq750$; and
- `infrared` for $\lambda_{\mathrm{nm}}>750$.

Under the ideal model, Balmer transitions $3\rightarrow2$ through
$9\rightarrow2$ fall inside this declared visible interval. The
$10\rightarrow2$ line is $379.694604409\ \mathrm{nm}$ and is therefore
classified as ultraviolet under the frozen boundary.

The supporting Balmer spectrum may map visible wavelengths to approximate
display colours, but colour is illustrative. No display colour may be used as
input to a physical calculation.

## Input domains and error behaviour

Future numerical functions will accept scalar or NumPy-broadcastable integer
quantum numbers subject to these rules:

- every quantum number must be an integer value and must not be a boolean;
- every level must satisfy $n\geq1$;
- every finite-study level must satisfy $n\leq10$;
- emission-transition functions require $n_i>n_f$ element by element;
- equal, upward, zero, negative, non-integer, complex, and non-finite quantum
  numbers are invalid; and
- non-broadcast-compatible input shapes must fail explicitly.

Scalar inputs will still return zero-dimensional NumPy arrays so the public
model API has one consistent return type. Numerical outputs use `float64`, and
quantum-number arrays use a fixed signed integer dtype selected in Stage 3.

The analytical series-limit functions accept a positive integer final level
without an initial level. Infinity will never be passed as a floating-point
sentinel.

## Frozen numerical and display domains

No uniform wavelength or energy grid is needed to calculate the discrete
transitions. The authoritative numerical study consists of the 10 levels, 45
transition records, and analytical series-limit records.

The required graph will use these frozen display boundaries:

| Axis | Display domain | Scale |
| --- | --- | --- |
| Wavelength | $80$--$50000\ \mathrm{nm}$ | logarithmic |
| Photon energy | $0$--$14.2\ \mathrm{eV}$ | linear |

The lower wavelength boundary leaves space for the Lyman limit, while the
upper boundary contains the $10\rightarrow9$ transition. Analytical limit
markers may be shown without representing them as finite emitted lines.

The energy-level diagram will show $n=1$--$6$ for legibility while clearly
stating that the stored study extends through $n=10$. The Balmer-spectrum
figure will show $360$--$700\ \mathrm{nm}$ so the series limit and all visible
study lines are in context.

## Pre-declared validation checks and tolerances

All checks below must exist before Task 5 evidence is accepted.

| Check | Required criterion |
| --- | --- |
| Source constants | Exact equality to the frozen decimal strings for $h$, $c$, $e$, and the selected $R_\infty$ central value |
| Level enumeration | Exact integer sequence $1$--$10$ |
| Level energies | Maximum absolute error from an independent decimal $-E_{\mathrm R}/n^2$ reference no greater than $5\times10^{-12}\ \mathrm{eV}$ |
| Level ordering | Strict increase toward zero with no non-negative finite level |
| Transition enumeration | Exact 45 unique ordered pairs in the declared order |
| Transition energy difference | Maximum absolute residual in $E_\gamma-(E_{n_i}-E_{n_f})$ no greater than $5\times10^{-12}\ \mathrm{eV}$ |
| Transition positivity | Every photon energy and wavelength strictly positive and finite |
| Photon energy--wavelength identity | Maximum relative error in $E_\gamma\lambda/(hc)-1$ no greater than $5\times10^{-13}$ |
| Frequency--wavelength identity | Maximum relative error in $f\lambda/c-1$ no greater than $5\times10^{-13}$ |
| Rydberg wavelength identity | Maximum relative error from the independent wavenumber form no greater than $5\times10^{-13}$ |
| Named-line anchors | Relative error no greater than $5\times10^{-12}$ for every frozen named energy and wavelength |
| Series limits | Relative error no greater than $5\times10^{-12}$ for each first-five analytical limit |
| Series convergence | Strict energy increase and wavelength decrease with rising $n_i$ for fixed $n_f$ |
| Series membership | Exact mapping between final level, series name, and transition count |
| Spectral classification | Exact agreement with the frozen $380$--$750\ \mathrm{nm}$ inequalities |
| Finite bounds | Exact 45 finite energies, frequencies, and wavelengths; no `NaN` or infinity |
| Reproducibility | Repeated runs produce byte-identical numerical outputs |

Validation reports must contain stable check names, observed and expected
values, units, comparison rules, tolerances, explanations, and pass/fail
states. Tests must prove failure after at least these corruptions:

1. changing one level energy;
2. reversing or duplicating one transition pair;
3. changing one wavelength while retaining its energy; and
4. assigning an incorrect series or spectral-region label.

## Figure requirements fixed for Stage 8

### Required energy-versus-wavelength figure

The mandatory figure will:

- contain all 45 finite transitions;
- use vacuum wavelength in nanometres on a logarithmic horizontal axis;
- use positive emitted-photon energy in electronvolts vertically;
- distinguish Lyman, Balmer, Paschen, Brackett, and Pfund;
- group $n_f\geq6$ transitions in a subdued but visible category;
- show individual markers without connecting them into a false continuous
  hydrogen spectrum;
- include a thin $E_\gamma=hc/\lambda$ reference guide;
- shade exactly $380$--$750\ \mathrm{nm}$ as the visible band;
- label a small set of representative lines; and
- include a concise note that discrete allowed transitions lie on the general
  photon energy--wavelength relation.

### Supporting figures

The energy-level diagram will use the negative atomic level energies and
downward arrows. It must not place photon energy on the same signed axis
without an explicit label.

The Balmer spectrum will place line markers at calculated ideal vacuum
wavelengths. Equal display heights will mean “position only,” not equal
physical intensity. The figure must say that transition probabilities and
linewidths are outside the model.

The series-convergence figure will compare energy or wavelength with initial
level for the first five series and show the analytical limit without treating
the limit as a finite transition.

The validation and summary figures will report only checks produced by the
passing validation object. No figure may invent a pass count or recalculate
the physics independently in plotting code.

All final figures will use explicit units, fixed dimensions, a
colour-blind-conscious palette, deterministic metadata, and both PNG and SVG
formats. Every figure must be inspected at original resolution and at its
intended slide size.

## Data and serialization conventions

The deterministic evidence package will include:

1. `energy_levels.csv`, with the 10 level energies in joules and electronvolts;
2. `emission_transitions.csv`, with the 45 ordered transition records;
3. `series_limits.csv`, with at least the first five analytical limits;
4. `validation_report.json`, with every structured numerical check; and
5. `reproducibility_manifest.json`, with constants, conventions, counts,
   tolerances, units, schema versions, and ordered filenames.

CSV floating-point fields will use enough significant digits to round-trip a
`float64`. JSON will be UTF-8, key-sorted, indented, finite, and written with
non-standard `NaN` values forbidden. Files will use LF endings and contain no
timestamps, host names, user names, absolute paths, random identifiers, or
machine-dependent metadata.

Transition rows will follow the frozen $(n_f,n_i)$ ordering. Human-readable
series and line labels are evidence fields but may never replace the integer
quantum numbers as the scientific identity of a record.

## Physical assumptions and limitations

The baseline assumes:

- an isolated hydrogen atom with nuclear charge $Z=1$;
- a stationary point nucleus of effectively infinite mass;
- non-relativistic Bohr energy levels;
- exact energy conservation for one emitted photon;
- vacuum propagation of the emitted photon; and
- a transition catalogue determined only by principal-level energy
  differences.

Real hydrogen differs slightly because the electron and proton orbit their
common centre of mass. Reduced mass lengthens the wavelengths relative to the
ideal $R_\infty$ model. Fine structure, Lamb shift, hyperfine structure,
external fields, Doppler motion, collisions, and finite lifetimes create
additional shifts, splittings, or widths.

The Bohr principal-level model also does not contain orbital angular momentum,
spin, dipole selection rules, or transition probabilities. The 45 catalogue
entries are therefore energy differences between principal levels, not a
prediction that all lines have equal intensity or identical experimental
visibility.

The model's ideal H-$\alpha$ wavelength is consequently not expected to equal
the familiar measured air wavelength exactly. Presentation text must call the
results “ideal Bohr-model vacuum wavelengths” whenever that distinction
matters.

## Optional-extension gate

After the validated baseline is complete, Stage 10 may evaluate one of two
extensions:

1. a reduced-mass comparison showing the small wavelength correction; or
2. a compact energy-level transition animation using only validated records.

Neither extension is pre-approved. It must have a clear explanatory benefit,
remain secondary to the required graph, and add its own validation and visual
acceptance criteria. Fine structure and intensity modelling remain outside
scope unless the project is deliberately re-planned.

## Performance and reproducibility budgets

The complete study is small. The future implementation must meet these
conservative budgets on the MacBook Air:

- complete in-memory study and validation: less than $2$ seconds;
- complete data and static-figure regeneration: less than $15$ seconds;
- numerical evidence: less than $10\ \mathrm{MiB}$;
- complete static figure set: less than $15\ \mathrm{MiB}$; and
- no GPU, network request, nondeterministic seed, or current-time dependency.

## Stage 2 completion checklist

Stage 2 is complete when this specification has been checked for:

- agreement with both official Task 5 sources;
- dimensional consistency of the level, energy, frequency, wavelength, and
  limit equations;
- exact SI constants and the frozen CODATA Rydberg central value;
- explicit ideal stationary-nucleus assumptions;
- complete and deterministic enumeration of 10 levels and 45 transitions;
- correct series, line, visible-band, and higher-series conventions;
- independent anchors and series limits;
- validation tolerances declared before implementation;
- fixed data, figure, serialization, performance, and reproducibility rules;
  and
- explicit exclusions and optional-extension boundaries.

No software architecture or Task 5 physics implementation belongs to Stage 2.
