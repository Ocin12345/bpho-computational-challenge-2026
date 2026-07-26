# Task 6 Results and Interpretation

## Result summary

The approved non-relativistic de Broglie--Bragg model has been evaluated on
401 accelerating voltages from 1 to 5 kV for both nominal graphite spacings,
$d_1=0.123\ \mathrm{nm}$ and $d_2=0.213\ \mathrm{nm}$. The complete evidence
contains 11,386 Bragg-allowed voltage--spacing--order records, of which 7,927
land on the declared forward phosphor screen.

All 39 independent structural and numerical validation checks pass. The 29
focused software tests also pass, including deliberately corrupted values,
deterministic regeneration, figure dimensions, and rollback after a forced
late output failure.

## Electron wavelength

The official non-relativistic relation is

$$
\lambda=\frac{h}{\sqrt{2m_{\mathrm e}eV}}.
$$

The wavelength falls from

$$
\lambda(1\ \mathrm{kV})=38.782994320\ \mathrm{pm}
$$

to

$$
\lambda(5\ \mathrm{kV})=17.344282334\ \mathrm{pm}.
$$

The stored product $\lambda\sqrt V$ is constant to floating-point precision,
and every momentum--wavelength pair independently satisfies $p\lambda=h$.
The shorter wavelength at higher voltage allows more diffraction orders.

## First-order rings

For first order,

$$
\sin\frac{\phi}{2}=\frac{\lambda}{2d},
\qquad
x=r\sin(2\phi).
$$

The exact endpoint results are:

| Voltage | Spacing / nm | $\phi$ / degree | Photographic radius $x$ / mm |
| ---: | ---: | ---: | ---: |
| 1 kV | 0.123 | 18.141556308 | 38.465414872 |
| 1 kV | 0.213 | 10.446868344 | 23.181331826 |
| 5 kV | 0.123 | 8.086010947 | 18.103939862 |
| 5 kV | 0.213 | 4.666802494 | 10.541869105 |

Both first-order rings contract continuously as voltage rises. The smaller
spacing $d_1$ produces the larger Bragg and scattering angle, so its
first-order ring has the larger projected radius over this voltage range.

## Maximum orders

The official mathematical maximum is

$$
n_{\mathrm{Bragg,max}}
=\left\lfloor\frac{2d}{\lambda}\right\rfloor.
$$

For the pictured forward screen, the declared geometric maximum is

$$
n_{\mathrm{screen,max}}
=\left\lfloor\frac{\sqrt2d}{\lambda}\right\rfloor.
$$

The endpoint counts are:

| Voltage | Spacing / nm | Bragg maximum | Forward-screen maximum |
| ---: | ---: | ---: | ---: |
| 1 kV | 0.123 | 6 | 4 |
| 1 kV | 0.213 | 10 | 7 |
| 5 kV | 0.123 | 14 | 10 |
| 5 kV | 0.213 | 24 | 17 |

These are geometric possibilities, not predicted visible intensities. Real
graphite diffraction patterns can suppress or broaden orders through crystal
structure factors, finite crystallite size, sample properties, beam spread,
and detector response. None of those data were supplied by the challenge.

## Exact spherical projection

The written brief specifies

$$
x=r\sin(2\phi)
$$

for the photographic radius. The presentation separately gives

$$
y=2r\sin\phi
$$

for a full caliper chord. The implementation stores and validates both
quantities under different names.

Because $x$ contains $\sin(2\phi)$, high-order radius tracks are not globally
monotonic in angle. A ring entering the forward hemisphere can grow toward
$x=r$ at $\phi=45^\circ$ and then contract. This behaviour in the
radius-versus-voltage figure is a consequence of the specified spherical
projection, not a plotting error.

## Required straight-line check

The official rearrangement is

$$
\frac{1}{\sqrt V}
=\frac{2d\sqrt{2m_{\mathrm e}e}}{nh}
\sin\frac{\phi}{2}.
$$

For $n=1$, the fitted gradients are:

| Series | Gradient / $\mathrm{V^{-1/2}}$ | Recovered $d$ / nm | $R^2$ |
| --- | ---: | ---: | ---: |
| $d_1$ | 0.200582837411736 | 0.123000000 | 1.000000000000 |
| $d_2$ | 0.347350767225202 | 0.213000000 | 1.000000000000 |

The unconstrained diagnostic intercept magnitudes are below
$7\times10^{-18}\ \mathrm{V^{-1/2}}$. The fits therefore recover both input
spacings to numerical precision and satisfy the required straight-line check.

Multiplying the vertical coordinate by order $n$ removes the $1/n$ gradient
dependence. All 4,113 $d_1$ records and 7,273 $d_2$ records collapse onto one
line per spacing in the supporting normalized validation.

## Figure package

The accepted figure package is:

1. [`electron_diffraction_rings`](../figures/task06/electron_diffraction_rings.png),
   a three-voltage forward-screen comparison;
2. [`ring_radius_vs_voltage`](../figures/task06/ring_radius_vs_voltage.png),
   the exact projected tracks for all forward-screen orders;
3. [`straight_line_validation`](../figures/task06/straight_line_validation.png),
   the mandatory first-order recovery of both spacings;
4. [`normalized_order_collapse`](../figures/task06/normalized_order_collapse.png),
   the all-order validation;
5. [`wavelength_and_orders`](../figures/task06/wavelength_and_orders.png),
   the wavelength and maximum-order diagnostics; and
6. [`task06_summary`](../figures/task06/task06_summary.png), the 4K 16:9
   competition summary.

Each figure also has an editable SVG version. The analytical figures are
2400 by 1500 pixels; the summary is 3840 by 2160 pixels. They were inspected
for clipping, title collisions, unreadable units, misleading encodings, and
slide-size clarity. Layout defects found during the first review were fixed
and the complete package was regenerated.

## Scientific limitations

The baseline does not predict:

- quantitative ring intensity or experimental visibility;
- graphite structure factors or forbidden reflections;
- finite crystallite-size broadening or preferred orientation;
- inelastic or multiple scattering;
- electron-beam divergence, energy spread, or magnetic deflection;
- phosphor or camera response; or
- relativistic momentum corrections.

The model should therefore be interpreted as a validated geometric prediction
of ideal ring positions and order domains, not a calibrated synthetic
experiment.
