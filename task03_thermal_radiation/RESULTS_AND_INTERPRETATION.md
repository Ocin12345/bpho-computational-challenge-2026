# Task 3 Results and Scientific Interpretation

## Purpose and evidence base

This report explains the physical meaning of the completed Task 3 results. It
does not introduce a new model or fit any experimental data. Every numerical
claim below comes from the validated result records produced by
`python3 -m task03_thermal_radiation.generate_task03`.

The principal evidence is:

- [`planck_spectra.csv`](../data/task03/planck_spectra.csv) and the
  [Planck-spectrum figure](../figures/task03/planck_spectra.png);
- [`planck_validation.csv`](../data/task03/planck_validation.csv) and the
  [Planck-validation figure](../figures/task03/planck_validation.png);
- [`einstein_materials.csv`](../data/task03/einstein_materials.csv),
  [`einstein_heat_capacity.csv`](../data/task03/einstein_heat_capacity.csv),
  and the
  [Einstein heat-capacity figure](../figures/task03/einstein_heat_capacity.png);
- [`einstein_normalized.csv`](../data/task03/einstein_normalized.csv) and the
  [normalized Einstein figure](../figures/task03/einstein_normalized.png); and
- the complete [`validation_report.json`](../data/task03/validation_report.json),
  which records 27 passing checks.

The equations, constants, units, domains, stable numerical forms, and
pre-declared tolerances are defined in
[`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md).

## Main conclusion

The two models show how one characteristic temperature controls a family of
thermal curves:

1. For an ideal black body, increasing the absolute temperature increases the
   emitted power very strongly and moves the wavelength peak towards shorter
   wavelengths.
2. For an Einstein solid, increasing the material's Einstein temperature
   delays the thermal excitation of its vibrational modes, so the molar heat
   capacity approaches the classical value $3R$ more slowly.

Both conclusions follow from the equations and are supported by independent
analytical checks. They describe the declared idealized models, not exact
observations of every star or solid.

## Part A: Planck black-body radiation

### What was calculated

The official presentation writes the Planck spectral-radiance equation
$B_{\lambda}$. Our principal graph displays the corresponding hemispherical
spectral exitance

$$
M_{\lambda}=\pi B_{\lambda},
$$

in $\mathrm{W\,m^{-2}nm^{-1}}$. This distinction matters: integrating
$B_{\lambda}$ gives power per unit area per steradian, whereas integrating
$M_{\lambda}$ gives the total power emitted into the outward hemisphere per
unit surface area.

The displayed spectra cover $100$--$3000\ \mathrm{nm}$ at $1\ \mathrm{nm}$
intervals for $4000$, $5000$, and $6000\ \mathrm K$. A separate much broader
wavelength grid was used for the total-power integration, so the validation is
not biased by the display limits.

### Numerical results

| $T$ / K | Numerical peak / nm | Wien prediction / nm | Peak relative error | Numerical total exitance / $\mathrm{W\,m^{-2}}$ | $\sigma T^4$ / $\mathrm{W\,m^{-2}}$ | Integral relative error |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| $4000$ | $724.440$ | $724.443$ | $4.13\times10^{-6}$ | $1.451615853\times10^7$ | $1.451615851\times10^7$ | $1.08\times10^{-9}$ |
| $5000$ | $579.550$ | $579.554$ | $7.58\times10^{-6}$ | $3.543984016\times10^7$ | $3.543984012\times10^7$ | $1.08\times10^{-9}$ |
| $6000$ | $482.960$ | $482.962$ | $4.13\times10^{-6}$ | $7.348805255\times10^7$ | $7.348805247\times10^7$ | $1.08\times10^{-9}$ |

The small discrepancies are numerical-grid and floating-point errors. They are
far below the tolerances fixed before implementation: $10^{-3}$ for the peak
position and $2\times10^{-3}$ for the integrated power.

### Why the peak moves left

Wien's displacement law states

$$
\lambda_{\max}T=b.
$$

Therefore, $\lambda_{\max}$ is inversely proportional to temperature. Raising
$T$ from $4000$ to $6000\ \mathrm K$ multiplies the temperature by $1.5$, so
the peak wavelength must be divided by $1.5$: it moves from approximately
$724$ to $483\ \mathrm{nm}$. The numerical result follows this prediction.

On the graph, the $4000\ \mathrm K$ peak lies near the red edge of the visible
band, the $5000\ \mathrm K$ peak is near yellow-green wavelengths, and the
$6000\ \mathrm K$ peak is near blue-green wavelengths. This helps explain the
general connection between black-body temperature and apparent colour, but a
peak wavelength alone does not determine perceived colour; the complete
spectrum and the eye's response are also important.

### Why the curves rise so strongly

The Stefan--Boltzmann law gives the area beneath the complete exitance spectrum:

$$
M=\sigma T^4.
$$

Consequently, the $6000\ \mathrm K$ black body emits

$$
\left(\frac{6000}{4000}\right)^4=5.0625
$$

times as much total power per unit area as the $4000\ \mathrm K$ black body.
The spectral peak height grows even more rapidly: the wavelength-form Planck
law and Wien scaling imply a peak proportional to $T^5$. The displayed
$6000\ \mathrm K$ peak is therefore about $7.59$ times the $4000\ \mathrm K$
peak. This is why the hottest curve is both taller and shifted left.

The $T^4$ law applies to the area under the full curve, not to the value at one
chosen wavelength. Confusing total exitance with spectral exitance would give
an incorrect interpretation of the graph.

### Planck-model validation

The numerical spectra are finite and non-negative over every declared grid.
The conversion $M_{\lambda}=\pi B_{\lambda}$ is satisfied to the precision of
the stored arrays. The largest Wien relative error is
$7.58\times10^{-6}$, and the largest Stefan--Boltzmann relative error is
$1.082\times10^{-9}$. The independently calculated radiance integrals also
agree with $\sigma T^4/\pi$.

Agreement with both Wien's law and the Stefan--Boltzmann law tests two different
properties of the calculation: the location of each maximum and the area under
each spectrum. A plausible-looking curve could still fail either check, so
these tests provide stronger evidence than appearance alone.

## Part B: Einstein molar heat capacity

### What was calculated

For each official material, the supplied Debye temperature $T_D$ determines
one Einstein temperature and frequency:

$$
T_E=T_D\left(\frac{\pi}{6}\right)^{1/3},
\qquad
f_E=\frac{k_{\mathrm B}T_E}{h}.
$$

No values were fitted to the resulting curves. The model then predicts the
constant-volume molar heat capacity

$$
C_V=3R\frac{x^2e^x}{(e^x-1)^2},
\qquad
x=\frac{T_E}{T}.
$$

The calculated material scale and two representative heat capacities are:

| Material | $T_E$ / K | $f_E/10^{13}\ \mathrm{Hz}$ | $C_V(300\ \mathrm K)$ / $\mathrm{J\,mol^{-1}K^{-1}}$ | $C_V(800\ \mathrm K)$ / $\mathrm{J\,mol^{-1}K^{-1}}$ |
| --- | ---: | ---: | ---: | ---: |
| Au | $137.0$ | $0.2855$ | $24.51$ | $24.88$ |
| Cu | $276.9$ | $0.5769$ | $23.25$ | $24.70$ |
| Ti | $338.5$ | $0.7054$ | $22.46$ | $24.57$ |
| Al | $345.0$ | $0.7188$ | $22.37$ | $24.56$ |
| Fe | $378.8$ | $0.7893$ | $21.88$ | $24.48$ |
| Si | $519.9$ | $1.0832$ | $19.54$ | $24.08$ |
| C | $1797.4$ | $3.7451$ | $2.25$ | $16.65$ |

The classical Dulong--Petit limit is

$$
3R=24.9434\ \mathrm{J\,mol^{-1}K^{-1}}.
$$

### Why every curve starts at zero

At low temperature, $x=T_E/T$ is large. The energy spacing $hf_E$ is then
large compared with the thermal energy $k_{\mathrm B}T$, so very few
vibrational quanta can be excited. The model therefore predicts

$$
C_V\rightarrow0
\quad\text{as}\quad
T\rightarrow0.
$$

This is the quantum correction to the classical prediction. The implemented
$T=0$ value is exactly zero, and every curve increases monotonically from that
limit.

### Why materials rise at different temperatures

The curve depends on temperature through the ratio $T/T_E$. A low Einstein
temperature means that thermal energy becomes comparable with the vibrational
quantum at a lower physical temperature. Gold, with
$T_E\approx137\ \mathrm K$, therefore rises quickly and is already close to
$3R$ by room temperature. Carbon, with $T_E\approx1797\ \mathrm K$, remains
far below the classical limit even at $800\ \mathrm K$.

This difference does not mean carbon has fewer vibrational directions in the
model. All materials have the same factor of three. Their curves differ because
the single assumed oscillator frequency, and hence the energy quantum, is
different.

### Why every curve approaches $3R$

At high temperature, $k_{\mathrm B}T$ is much greater than $hf_E$, so the
oscillator energy becomes effectively classical. Each atom contributes three
vibrational directions, giving the molar limit $3R$. The graph shows the
low-$T_E$ materials approaching this value within the displayed range. Carbon
does not reach it by $800\ \mathrm K$ because $800\ \mathrm K$ is still only
about $0.45T_E$ for carbon; this is expected behaviour, not a failed limit.

The separate validation at $T=100T_E$ gives a relative difference from $3R$ of
$8.33\times10^{-6}$, below the pre-declared $10^{-5}$ tolerance.

### Meaning of the normalized collapse

When temperature is divided by $T_E$ and heat capacity by $3R$, all material
labels disappear from the Einstein equation:

$$
\frac{C_V}{3R}
=\frac{x^2e^x}{(e^x-1)^2},
\qquad
x=\frac{1}{T/T_E}.
$$

All seven curves consequently collapse onto one universal function. Their
largest numerical separation is only $8.88\times10^{-16}$, compared with the
$10^{-12}$ tolerance. This is both a physical scaling result and a strong
implementation check: any visible separation would indicate inconsistent
normalization or material conversion.

The collapse does not claim that real materials have identical heat capacities.
It says that, within the one-frequency Einstein model, the material affects
only the temperature scale $T_E$.

### Einstein-model validation

All calculated values are finite, lie between $0$ and $3R$, and are
non-decreasing over the declared grids. At $T=T_E$, the normalized heat
capacity agrees with the independent value

$$
\frac{e}{(e-1)^2}=0.9206735942
$$

to an absolute error of $2.22\times10^{-16}$. All seven calculated frequencies
also reproduce the four-decimal values printed in the official presentation.

## Assumptions and limitations

### Planck model

- The emitter is an ideal black body with emissivity equal to one.
- It is in thermal equilibrium at one uniform absolute temperature.
- The result is surface emission. Distance, geometric dilution, atmosphere,
  absorption lines, and detector response are not included.
- The wavelength is the vacuum wavelength.
- The curves are theoretical spectra, not fits to the Sun or another measured
  source.

A real object may have wavelength-dependent emissivity, spectral lines,
temperature gradients, or an intervening atmosphere. Its measured spectrum
can therefore differ from the ideal Planck curve even when a characteristic
temperature can be assigned.

### Einstein model

- A solid is represented by independent quantum harmonic oscillators.
- Every atom in one material is assigned the same oscillator frequency.
- Three vibrational directions per atom are included.
- The prediction is $C_V$, not the experimentally common $C_P$.
- Anharmonicity, thermal expansion, electronic heat capacity, defects, and
  phase changes are omitted.
- The Debye model's continuous distribution of vibrational frequencies is not
  included.

The most important physical limitation is the one-frequency assumption. It
correctly removes the classical non-zero heat capacity at $T=0$, but it predicts
an exponential low-temperature decrease. Real three-dimensional crystals have
low-frequency acoustic modes; the Debye model captures their approximate
$T^3$ low-temperature heat capacity more successfully. The Einstein model is
therefore valuable as a clear quantum model and qualitative comparison, not as
a complete precision description of real solids.

### Numerical limitations

- Every integral and maximum is evaluated on a finite declared grid.
- Double-precision floating-point arithmetic introduces rounding at roughly
  the $10^{-16}$ relative scale.
- The displayed Planck range is narrower than the integration range and must
  not be used alone to infer total emitted power.
- Curves between stored grid points are connected for visualization; they are
  not additional independent calculations.

The errors reported by validation are much smaller than the thresholds and do
not affect the physical trends discussed here.

## What the validation does and does not prove

The 27 checks establish that the implementation is internally consistent with
the declared equations, units, reference conversions, limiting cases, and
analytical laws. They make accidental unit errors, incorrect factors of $\pi$,
unstable exponential evaluation, and incorrect material scaling much less
likely.

They do not prove that the idealized equations contain every physical process,
nor do they compare the models with experimental uncertainty. Model validation
and experimental validation are different tasks. Our conclusion is therefore
that the code correctly implements the stated Planck and Einstein models over
the declared domains.

## Final scientific conclusion

The Planck calculation demonstrates that hotter ideal emitters radiate much
more total power and peak at shorter wavelengths, with numerical maxima and
integrals agreeing with Wien's and Stefan--Boltzmann laws. The Einstein
calculation demonstrates how quantum suppression drives molar heat capacity to
zero at low temperature and how all materials approach the common classical
limit $3R$ once temperature is high compared with their Einstein temperature.

Together, the results show how thermal behaviour can be organized by a
characteristic dimensionless ratio: $\lambda T$ for black-body peaks and
$T/T_E$ for Einstein solids. The agreement between equations, limiting cases,
reference values, generated figures, and automated validation supports the
claim that both required Task 3 models have been implemented correctly and
interpreted within their proper physical limits.

For the final presentation, the defensible one-sentence takeaway is:

> Increasing temperature shifts black-body emission towards shorter
> wavelengths, while a solid's Einstein temperature sets how quickly its heat
> capacity rises towards the universal classical limit $3R$.
