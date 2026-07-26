# Task 6 Mathematical and Numerical Specification

## Status and purpose

This document completes the proposed Stage 2. It freezes the equations,
notation, units, constants, input domains, diffraction-order conventions,
screen geometry, reference anchors, graph definitions, tolerances, output
rules, and figure requirements before architecture or physics implementation
begins.

The future implementation must follow this specification unless a later
change is supported by evidence and recorded explicitly. A result calculated
by the main model must never be reused as its own independent reference.

## Modelling convention

The authoritative baseline is the non-relativistic de Broglie--Bragg model
derived in the official slides. Electrons begin at negligible kinetic energy,
are accelerated through a positive potential difference $V$, and diffract
elastically from ideal graphite plane families. SI units are authoritative
internally. Kilovolts, picometres, nanometres, degrees, and millimetres are
presentation units reached only through explicit conversion.

The calculation is deterministic and uses IEEE 754 double precision in the
main path. It contains no random variables, fitting to experimental images,
time integration, or intensity model.

## Symbols and units

| Symbol | Meaning | SI unit |
| :---: | --- | :---: |
| $V$ | Accelerating potential difference | $\mathrm V$ |
| $e$ | Elementary charge magnitude | $\mathrm C$ |
| $m_{\mathrm e}$ | Electron mass | $\mathrm{kg}$ |
| $h$ | Planck constant | $\mathrm{J\,s}$ |
| $p$ | Electron momentum | $\mathrm{kg\,m\,s^{-1}}$ |
| $\lambda$ | Electron de Broglie wavelength | $\mathrm m$ |
| $d$ | Graphite plane spacing | $\mathrm m$ |
| $n$ | Diffraction order | positive dimensionless integer |
| $\theta$ | Bragg angle | $\mathrm{rad}$ |
| $\phi$ | Scattering angle, $2\theta$ | $\mathrm{rad}$ |
| $r$ | Spherical tube radius | $\mathrm m$ |
| $x$ | Photographic projected ring radius | $\mathrm m$ |
| $y$ | Full caliper chord across the ring | $\mathrm m$ |
| $q$ | $\sin(\phi/2)=n\lambda/(2d)$ | dimensionless |

Variable names will include unit suffixes where the unit is not otherwise
unambiguous, for example `voltage_v`, `spacing_m`, `wavelength_m`,
`phi_rad`, `photo_radius_m`, and `caliper_diameter_m`.

## Frozen physical constants and configuration

| Quantity | Value used | Status |
| :--- | ---: | --- |
| $h$ | $6.62607015\times10^{-34}\ \mathrm{J\,s}$ | Exact SI definition |
| $e$ | $1.602176634\times10^{-19}\ \mathrm C$ | Exact SI definition |
| $m_{\mathrm e}$ | $9.1093837139\times10^{-31}\ \mathrm{kg}$ | Frozen 2022 CODATA central value |
| $r$ | $65\times10^{-3}\ \mathrm m$ | Official Task 6 value |
| $d_1$ | $0.123\times10^{-9}\ \mathrm m$ | Official rounded graphite spacing |
| $d_2$ | $0.213\times10^{-9}\ \mathrm m$ | Official rounded graphite spacing |
| $V_{\min}$ | $1000\ \mathrm V$ | Official lower bound |
| $V_{\max}$ | $5000\ \mathrm V$ | Official upper bound |

The fundamental-constant source is the
[NIST 2022 CODATA recommended-values table](https://physics.nist.gov/cuu/pdf/wall_2022.pdf).
The electron mass is not exact; its displayed standard uncertainty is
$2.8\times10^{-40}\ \mathrm{kg}$. The central value is frozen for
reproducibility. The official spacings are nominal rounded inputs, not
precision crystallographic measurements.

The slides relate these spacings to the rounded graphite C--C bond length
$s=0.142\ \mathrm{nm}$ through

$$
d_1\approx\frac{\sqrt3}{2}s,
\qquad
d_2\approx\frac32s,
\qquad
\frac{d_2}{d_1}\approx\sqrt3.
$$

The baseline will use the explicitly printed values 0.123 nm and 0.213 nm,
not silently replace them with values recomputed from rounded $s$.

## Electron wavelength

The positive energy gain is

$$
K=eV.
$$

The official non-relativistic momentum and wavelength are

$$
p=\sqrt{2m_{\mathrm e}eV},
$$

$$
\lambda=\frac{h}{p}
=\frac{h}{\sqrt{2m_{\mathrm e}eV}}.
$$

Therefore

$$
\lambda\propto V^{-1/2}.
$$

The baseline wavelength must be positive, finite, and strictly decreasing for
increasing positive voltage.

## Bragg condition and scattering angle

For positive integer order $n$,

$$
2d\sin\theta=n\lambda.
$$

The total scattering angle is

$$
\phi=2\theta.
$$

Define

$$
q=\frac{n\lambda}{2d}.
$$

Then

$$
q=\sin\theta=\sin\frac{\phi}{2},
$$

$$
\theta=\arcsin q,
\qquad
\phi=2\arcsin q.
$$

An order is mathematically Bragg allowed exactly when

$$
0<q\leq1.
$$

The largest positive integer satisfying this condition is

$$
n_{\mathrm{Bragg,max}}(V,d)
=\left\lfloor\frac{2d}{\lambda(V)}\right\rfloor.
$$

Floating-point code must not add an arbitrary epsilon before flooring. The
implementation will compare candidate integers through the dimensionless
condition $n\lambda\leq2d$ using a declared scale-aware tolerance only in the
validator. The high-precision reference path will resolve threshold cases.

## Spherical-screen geometry

The written brief defines the radius observed in a photograph as

$$
x=r\sin(2\phi).
$$

Substituting the Bragg result gives the exact forward model

$$
x(V,d,n)
=r\sin\left(4\arcsin\frac{n\lambda(V)}{2d}\right).
$$

No small-angle approximation will be used in authoritative calculations.

The presentation also derives the full chord measured by calipers:

$$
y=2r\sin\phi
=2r\sin\left(2\arcsin\frac{n\lambda}{2d}\right).
$$

`photo_radius_m` and `caliper_diameter_m` are therefore separate fields. The
implementation must never label $y$ as the photographic ring radius or use it
in place of $x$.

## Forward-screen visibility

The official $q\leq1$ rule defines possible Bragg orders, including
back-scattering solutions. The phosphor surface pictured in the slides is on
the forward hemisphere. A ring on that surface satisfies

$$
0<\phi\leq\frac{\pi}{2},
$$

equivalently

$$
0<q\leq\sin\frac{\pi}{4}=\frac{1}{\sqrt2}.
$$

The largest forward-screen order is thus

$$
n_{\mathrm{screen,max}}(V,d)
=\left\lfloor\frac{\sqrt2d}{\lambda(V)}\right\rfloor.
$$

Every Bragg-allowed record will be retained and classified with
`screen_visible`. The main geometric screen renderer will draw only records
with `screen_visible=true`. This is a declared geometry rule, not an
intensity threshold.

For $0\leq\phi\leq90^\circ$, $x$ is non-negative and bounded by $r$.
Because the spherical projection contains $\sin(2\phi)$, $x$ reaches its
maximum at $\phi=45^\circ$ and is not globally monotonic in angle. This is a
feature of the specified geometry, not a numerical error.

## Inverse geometry and branch convention

The map $x=r\sin(2\phi)$ is two-to-one over the forward hemisphere except at
its maximum. An observed $x<r$ alone therefore does not distinguish a
low-angle ring from its high-angle counterpart.

The authoritative forward model calculates $\phi$ from Bragg's law and then
calculates $x$; it does not infer $\phi$ from $x$. The mandatory straight-line
validation will use first-order rings, for which the complete 1--5 kV range
has $\phi<19^\circ$ and lies safely on the principal low-angle branch. If an
inverse-photo demonstration is added, it must state the restriction
$0\leq\phi\leq45^\circ$ and use

$$
\phi=\frac12\arcsin\frac{x}{r}.
$$

The caliper relation has no two-branch ambiguity over
$0\leq\phi\leq90^\circ$:

$$
\phi=\arcsin\frac{y}{2r}.
$$

## Mandatory straight-line validation

Starting from

$$
\sin\frac{\phi}{2}
=\frac{nh}{2d\sqrt{2m_{\mathrm e}eV}},
$$

rearrangement gives

$$
\frac{1}{\sqrt V}
=\frac{2d\sqrt{2m_{\mathrm e}e}}{nh}
\sin\frac{\phi}{2}.
$$

The official axes are therefore fixed as

$$
Y=\frac{1}{\sqrt V}
\quad\text{in}\quad\mathrm{V^{-1/2}},
$$

$$
X=\sin\frac{\phi}{2}
\quad\text{dimensionless}.
$$

For fixed $d$ and $n$, the ideal line passes through the origin with gradient

$$
k(d,n)=\frac{2d\sqrt{2m_{\mathrm e}e}}{nh}.
$$

The spacing recovered from a fitted gradient is

$$
d_{\mathrm{fit}}
=\frac{nhk}{2\sqrt{2m_{\mathrm e}e}}.
$$

The primary validation figure will use $n=1$ for both graphite spacings. It
will show constrained-through-origin fits as the physical result and report an
ordinary unconstrained intercept as a diagnostic. Voltage is inserted in
volts, not kilovolts, so the gradient and recovery equation remain
unit-consistent.

The expected first-order gradients are

| Spacing | $k$ / $\mathrm{V^{-1/2}}$ |
| --- | ---: |
| $d_1=0.123\ \mathrm{nm}$ | $0.200582837411736$ |
| $d_2=0.213\ \mathrm{nm}$ | $0.347350767225202$ |

If a display uses kilovolts instead, its numerical gradient changes by
$\sqrt{1000}$ and must be labelled accordingly. The baseline graph will avoid
that unnecessary conversion.

## All-order normalized validation

Different orders of the same spacing have gradients proportional to $1/n$.
Multiplying the vertical variable by $n$ gives

$$
\frac{n}{\sqrt V}
=\frac{2d\sqrt{2m_{\mathrm e}e}}{h}
\sin\frac{\phi}{2}.
$$

All valid orders for a given spacing must therefore collapse onto one straight
line. This will be a supporting validation, not a replacement for the exact
official graph.

## Frozen voltage grids

The public physical functions will accept scalar or NumPy-broadcastable
voltages anywhere on the closed interval

$$
1000\leq V\leq5000\ \mathrm V.
$$

The deterministic evidence grid is

$$
V_j=1000+10j\ \mathrm V,
\qquad
j=0,1,\ldots,400,
$$

for 401 voltage values. Final plots may display a visually reduced subset, but
fits and saved evidence will use the complete declared grid unless a figure
caption says otherwise.

## Reference wavelength anchors

Using the frozen constants, the non-relativistic electron wavelengths are:

| Voltage / kV | $\lambda$ / pm |
| ---: | ---: |
| 1 | $38.782994320$ |
| 2 | $27.423718278$ |
| 3 | $22.391372211$ |
| 4 | $19.391497160$ |
| 5 | $17.344282334$ |

These are rounded display anchors. Stored calculations retain full `float64`
precision.

## Reference maximum-order anchors

The independently calculated endpoint order counts are:

| Voltage | Spacing / nm | $n_{\mathrm{Bragg,max}}$ | $n_{\mathrm{screen,max}}$ |
| ---: | ---: | ---: | ---: |
| 1 kV | 0.123 | 6 | 4 |
| 1 kV | 0.213 | 10 | 7 |
| 5 kV | 0.123 | 14 | 10 |
| 5 kV | 0.213 | 24 | 17 |

The implementation will also check the 2, 3, and 4 kV anchors in the generated
reference file. Counts may change only when a voltage crosses an analytical
order threshold.

## Reference first-order ring anchors

For $n=1$ and the exact photographic geometry $x=r\sin(2\phi)$:

| Voltage | Spacing / nm | $\phi$ / degree | $x$ / mm |
| ---: | ---: | ---: | ---: |
| 1 kV | 0.123 | $18.141556308$ | $38.465414872$ |
| 1 kV | 0.213 | $10.446868344$ | $23.181331826$ |
| 5 kV | 0.123 | $8.086010947$ | $18.103939862$ |
| 5 kV | 0.213 | $4.666802494$ | $10.541869105$ |

These anchors deliberately differ from values obtained with
$2r\sin\phi$, which is the caliper diameter $y$, not the photographic radius
$x$.

## Input domains and error behaviour

Public numerical functions will follow these rules:

- voltage must be real, finite, and within 1000--5000 V inclusive;
- spacing must be real, finite, and strictly positive;
- tube radius must be real, finite, and strictly positive;
- diffraction order must be a positive integer and must not be a boolean;
- non-integer, complex, non-finite, zero, and negative orders are invalid;
- a requested order outside the Bragg domain must fail explicitly rather than
  return `nan` from `arcsin`;
- incompatible broadcast shapes must fail explicitly;
- scalar inputs return zero-dimensional NumPy arrays for a consistent public
  model API; and
- authoritative numerical outputs use `float64`, with integer orders stored
  in a fixed signed integer dtype selected in Stage 3.

Classification functions may accept any positive spacing for unit tests, but
the complete competition study uses only the two frozen graphite spacings.

## Numerical tolerances

The following initial tolerances are frozen before implementation:

- exact integer order counts: exact equality;
- physical identities and independent `float64` references:
  relative tolerance $5\times10^{-12}$ and scale-aware absolute tolerance;
- wavelength and first-order anchor comparisons:
  relative tolerance $5\times10^{-10}$;
- angle and radius anchor comparisons:
  relative tolerance $5\times10^{-10}$;
- constrained-fit recovery of each spacing:
  relative error no greater than $1\times10^{-10}$;
- coefficient of determination for ideal validation lines:
  $R^2\geq1-10^{-12}$;
- unconstrained intercept magnitude:
  no greater than $10^{-12}\ \mathrm{V^{-1/2}}$; and
- normalized all-order collapse residual:
  relative maximum no greater than $1\times10^{-10}$.

Absolute comparisons near zero will use an explicitly scaled bound rather
than division by a near-zero reference. A tolerance may be revised only when
the reason is documented and the new value remains scientifically meaningful.

## Independent reference path

The validator will not call the public model functions to generate expected
values. A separate reference module will use Python `decimal.Decimal` with at
least 50 digits for constants, energy, momentum, wavelength, order thresholds,
and straight-line gradients. Trigonometric reference anchors may use a
separate scalar high-precision or independently structured path selected in
Stage 3.

The independent validator must catch deliberate corruption of at least:

- one wavelength;
- one order maximum;
- one Bragg angle;
- one photographic radius;
- one screen-visibility flag;
- one spacing label; and
- one validation gradient.

## Record and serialization requirements

Each diffraction-order record will contain at least:

- `voltage_v` and `voltage_kv`;
- `spacing_id`, `spacing_m`, and `spacing_nm`;
- `order_n`;
- `wavelength_m` and `wavelength_pm`;
- `bragg_ratio_q`;
- `theta_rad`, `theta_deg`, `phi_rad`, and `phi_deg`;
- `photo_radius_m` and `photo_radius_mm`;
- `caliper_diameter_m` and `caliper_diameter_mm`;
- `bragg_allowed`;
- `screen_visible`; and
- `order_status` with a controlled value such as `forward_screen` or
  `back_scattering`.

CSV output will use a fixed column order, decimal formatting, row order, and
UTF-8 line ending convention. Rows will be ordered first by increasing
voltage, then spacing identifier, then increasing order. JSON will use sorted
keys and stable indentation. Generated timestamps will not appear inside
content-hashed scientific artifacts.

Output generation will be transactional: all files are written to a temporary
location, validated as a complete set, and moved into place only after every
calculation and figure succeeds. A late failure must leave the previous valid
artifact set unchanged.

## Figure conventions

The figure package will use these rules:

- analytical outputs are saved in matched PNG and SVG pairs;
- PNG figures are at least 2400 pixels on the long side at 300 dpi;
- the 16:9 summary is 3840 by 2160 pixels;
- equations and axis labels use the same symbols as this specification;
- volts are used in the mandatory linearization and kilovolts only on clearly
  labelled voltage-display axes;
- analytical family colours are colourblind safe and not the sole carrier of
  meaning;
- the phosphor screen uses green monochrome rings but includes an adjacent
  family/order explanation;
- ring brightness and width are labelled as schematic;
- order is encoded with a continuous colour scale or direct annotation rather
  than a 24-entry legend;
- first-order series are visually emphasized in the validation figure;
- no output relies on a screenshot of a plotting window; and
- every final figure is inspected at full resolution, 1920 by 1080 slide
  resolution, and thumbnail size.

The planned static screen comparison uses 1, 3, and 5 kV. It shows every
forward-screen order but directly labels only the two first-order rings and
the total family counts, preventing label collisions.

## Interpretation boundary

The model predicts geometric ring positions for ideal wavelengths and plane
spacings. It does not predict which mathematically allowed rings are bright
enough to observe. Equal line opacity in a schematic screen is a visibility
choice, not a scattering probability.

The non-relativistic wavelength is the official baseline. A possible
relativistic extension would use

$$
\lambda_{\mathrm{rel}}
=\frac{hc}{\sqrt{eV\left(eV+2m_{\mathrm e}c^2\right)}},
$$

but it must remain in a separate configuration and figure. It changes the
non-relativistic wavelength by about $-0.049\%$ at 1 kV and $-0.244\%$ at
5 kV. No relativistic value may be mixed into the authoritative Task 6
validation line.

## Stage 2 acceptance statement

Stage 2 is complete when this plan is approved. The baseline equations,
constants, units, voltage grid, two spacings, Bragg and forward-screen order
rules, exact screen geometry, inverse branch convention, straight-line fit,
reference anchors, tolerances, record schema, reproducibility rules, visual
standards, and scientific limitations are all defined before implementation.
