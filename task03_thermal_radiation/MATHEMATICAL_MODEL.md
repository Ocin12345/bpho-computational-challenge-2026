# Task 3 Mathematical and Numerical Specification

## Status and purpose

This document completes Stage 2. It freezes the mathematical definitions,
notation, units, constants, reference values, numerical domains, stable
evaluation rules, and validation tolerances for Task 3 before software design
or implementation begins.

The implementation must follow this specification unless a later change is
supported by evidence and documented explicitly. No numerical result produced
by the future code may be used to define its own expected validation value.

## Modelling conventions

The model has two independent parts:

1. the wavelength form of Planck's black-body radiation law; and
2. Einstein's model of the constant-volume molar heat capacity of a solid.

Both are deterministic equilibrium models. They contain no random variables,
time stepping, fitted parameters, or stochastic uncertainty.

All calculations will use IEEE 754 double precision and SI units internally.
Unit conversion and rounding are applied only when values are displayed or
written to presentation tables.

## Symbols and units

| Symbol | Meaning | SI unit |
| :---: | --- | :---: |
| $\lambda$ | Vacuum wavelength | $\mathrm m$ |
| $T$ | Absolute temperature | $\mathrm K$ |
| $h$ | Planck constant | $\mathrm{J\,s}$ |
| $c$ | Speed of light in vacuum | $\mathrm{m\,s^{-1}}$ |
| $k_{\mathrm B}$ | Boltzmann constant | $\mathrm{J\,K^{-1}}$ |
| $R$ | Molar gas constant | $\mathrm{J\,mol^{-1}K^{-1}}$ |
| $\sigma$ | Stefan--Boltzmann constant | $\mathrm{W\,m^{-2}K^{-4}}$ |
| $B_\lambda(\lambda,T)$ | Spectral radiance per unit wavelength | $\mathrm{W\,m^{-3}sr^{-1}}$ |
| $M_\lambda(\lambda,T)$ | Hemispherical spectral exitance per unit wavelength | $\mathrm{W\,m^{-3}}$ |
| $T_D$ | Debye temperature supplied for a solid | $\mathrm K$ |
| $T_E$ | Einstein temperature used by the model | $\mathrm K$ |
| $f_E$ | Einstein oscillator frequency | $\mathrm{Hz}$ |
| $x$ | Dimensionless thermal ratio $hf_E/(k_{\mathrm B}T)$ | dimensionless |
| $C_V(T)$ | Constant-volume molar heat capacity | $\mathrm{J\,mol^{-1}K^{-1}}$ |

The subscript $\lambda$ is retained because a spectral density depends on the
choice of wavelength rather than frequency as the independent variable.

## Physical constants

The baseline will use the exact defining SI values where available rather than
the rounded constants printed on the official slides.

| Constant | Value used |
| :---: | ---: |
| $h$ | $6.62607015\times10^{-34}\ \mathrm{J\,s}$ |
| $c$ | $299792458\ \mathrm{m\,s^{-1}}$ |
| $k_{\mathrm B}$ | $1.380649\times10^{-23}\ \mathrm{J\,K^{-1}}$ |
| $R$ | $8.31446261815324\ \mathrm{J\,mol^{-1}K^{-1}}$ |
| $\sigma$ | $5.670374419184\times10^{-8}\ \mathrm{W\,m^{-2}K^{-4}}$ |
| $b$ | $2.897771955185\times10^{-3}\ \mathrm{m\,K}$ |

Here $b$ is the Wien displacement constant for the wavelength form of
Planck's law. The Stefan--Boltzmann constant will also be calculated from

$$
\sigma=\frac{2\pi^5 k_{\mathrm B}^4}{15h^3c^2}
$$

as an internal consistency check.

## Part A: Planck black-body spectrum

### Dimensionless exponent

Define

$$
x_P=\frac{hc}{\lambda k_{\mathrm B}T}.
$$

The mathematical domain is

$$
\lambda>0,\qquad T>0.
$$

Zero or negative wavelength and zero or negative absolute temperature are
invalid inputs and must be rejected rather than silently replaced.

### Spectral radiance

The wavelength form of Planck's law supplied by the official presentation is

$$
B_\lambda(\lambda,T)
=\frac{2hc^2}{\lambda^5}
\frac{1}{\exp(x_P)-1}.
$$

This expression is a **spectral radiance**, with units

$$
\mathrm{W\,m^{-2}sr^{-1}\,m^{-1}}
=\mathrm{W\,m^{-3}sr^{-1}}.
$$

### Spectral exitance and the factor of pi

An ideal black body is a Lambertian emitter. Integrating its radiance over the
outward hemisphere gives

$$
M_\lambda(\lambda,T)=\pi B_\lambda(\lambda,T).
$$

Therefore,

$$
\int_0^\infty B_\lambda(\lambda,T)\,d\lambda
=\frac{\sigma T^4}{\pi},
$$

whereas

$$
\int_0^\infty M_\lambda(\lambda,T)\,d\lambda
=\sigma T^4.
$$

The official slides show the radiance formula without $\pi$, label the graph
in $\mathrm{W\,m^{-2}nm^{-1}}$, and equate its wavelength integral to
$\sigma T^4$. Those statements mix radiance and exitance conventions. Our
code will expose both quantities explicitly.

The principal presentation graph will use $M_\lambda$ per nanometre because
its area directly represents emitted power per square metre. It will be
labelled **spectral exitance**, while the documentation will still show the
official $B_\lambda$ equation.

### Conversion to a per-nanometre density

Since

$$
d\lambda_{\mathrm m}=10^{-9}d\lambda_{\mathrm{nm}},
$$

the plotted density is

$$
M_{\lambda,\mathrm{nm}}
=10^{-9}M_{\lambda,\mathrm m}.
$$

Its unit is

$$
\mathrm{W\,m^{-2}nm^{-1}}.
$$

The same factor applies when converting $B_\lambda$ from per metre to per
nanometre.

### Wien displacement law

Differentiating the wavelength spectrum with respect to $\lambda$ shows that
the peak exponent satisfies

$$
5\left(1-e^{-x_{\max}}\right)=x_{\max}.
$$

The positive non-zero solution is

$$
x_{\max}=4.965114231744277.
$$

Consequently,

$$
\lambda_{\max}T
=\frac{hc}{k_{\mathrm B}x_{\max}}
=b,
$$

or

$$
\lambda_{\max}=\frac{b}{T}.
$$

The exact-constant reference values for the three baseline temperatures are:

| $T$ / K | Expected $\lambda_{\max}$ / nm | Expected $\sigma T^4$ / $\mathrm{W\,m^{-2}}$ |
| ---: | ---: | ---: |
| $4000$ | $724.442989$ | $1.451615851\times10^7$ |
| $5000$ | $579.554391$ | $3.543984012\times10^7$ |
| $6000$ | $482.961993$ | $7.348805247\times10^7$ |

These are independent analytical targets for the future numerical model.

### Limiting behaviour

At short wavelengths, $x_P$ is large and

$$
B_\lambda\sim
\frac{2hc^2}{\lambda^5}e^{-x_P}\rightarrow0.
$$

At long wavelengths, $x_P$ is small and Planck's law approaches the
Rayleigh--Jeans form

$$
B_\lambda\sim\frac{2ck_{\mathrm B}T}{\lambda^4}.
$$

The numerical implementation must therefore tend to zero at both ends of a
sufficiently broad wavelength interval without producing non-finite values.

### Numerically stable occupation factor

Direct evaluation of $\exp(x_P)$ can overflow at very short wavelengths. The
implementation will evaluate

$$
n(x_P)=\frac{1}{e^{x_P}-1}
$$

using two branches:

$$
n(x_P)=
\begin{cases}
1/\mathrm{expm1}(x_P), & x_P\leq50,\\[4pt]
e^{-x_P}/(1-e^{-x_P}), & x_P>50.
\end{cases}
$$

`expm1` denotes the accurately evaluated quantity $e^x-1$. Underflow of the
second branch to zero is physically acceptable because it represents a
negligible short-wavelength contribution. Overflow, `NaN`, and negative
spectral values are not acceptable.

### Frozen numerical domains

The following grids are part of the baseline specification:

| Purpose | Domain | Resolution |
| --- | --- | --- |
| Principal Planck figure | $100$--$3000\ \mathrm{nm}$ | uniform $1\ \mathrm{nm}$ intervals |
| Numerical peak search | $100$--$3000\ \mathrm{nm}$ | uniform $0.01\ \mathrm{nm}$ intervals |
| Stefan--Boltzmann integration | $10^{-9}$--$10^{-2}\ \mathrm m$ | $200001$ logarithmically spaced points |

The required temperature set is

$$
T\in\{4000,5000,6000\}\ \mathrm K.
$$

The model may accept any finite $T>0$, but those three official demonstration
temperatures must appear in the principal comparison and validation report.

The display interval is intentionally wider than the official example so that
the $4000\ \mathrm K$ long-wavelength tail is visible. The much broader
integration interval prevents the graph's display limits from truncating the
Stefan--Boltzmann validation.

The integral will be evaluated over wavelength with a non-uniform-grid
trapezoidal rule. No SciPy dependency is required.

## Part B: Einstein molar heat capacity

### Einstein temperature and frequency

The official presentation supplies Debye temperatures and uses the conversion

$$
T_E=T_D\left(\frac{\pi}{6}\right)^{1/3}.
$$

Define the constant conversion factor

$$
\alpha_E=\left(\frac{\pi}{6}\right)^{1/3}
=0.805995977008235.
$$

The Einstein frequency is then

$$
f_E=\frac{k_{\mathrm B}T_E}{h}.
$$

No material parameters will be fitted. Each material's $T_D$ from the official
table uniquely determines $T_E$ and $f_E$.

### Einstein heat-capacity equation

For $T>0$, define

$$
x_E=\frac{hf_E}{k_{\mathrm B}T}
=\frac{T_E}{T}.
$$

The constant-volume molar heat capacity is

$$
C_V(T)=3R
\frac{x_E^2e^{x_E}}{\left(e^{x_E}-1\right)^2}.
$$

The factor of three represents three independent vibrational directions per
atom, and $R$ converts the per-particle result into a per-mole result.

The official slides label this quantity simply $C$. We will use $C_V$ because
Einstein's model predicts constant-volume heat capacity. It must not be
presented as a fitted constant-pressure heat capacity $C_P$.

### Stable dimensionless form

Define

$$
g(x)=\frac{x^2e^x}{(e^x-1)^2}.
$$

For ordinary and large $x$, evaluate the equivalent form

$$
g(x)=\frac{x^2e^{-x}}{(1-e^{-x})^2}
=\frac{x^2e^{-x}}{[-\mathrm{expm1}(-x)]^2}.
$$

For $x<10^{-3}$, use the high-temperature series

$$
g(x)=1-\frac{x^2}{12}+\frac{x^4}{240}+O(x^6)
$$

to avoid cancellation. At exactly $T=0$, the implementation will assign the
continuous limiting value

$$
C_V(0)=0
$$

without attempting to calculate $T_E/T$.

### Official-material reference conversion

Using the exact constants above gives:

| Material | $T_D$ / K | Calculated $T_E$ / K | Calculated $f_E/10^{13}\ \mathrm{Hz}$ | Official displayed value |
| --- | ---: | ---: | ---: | ---: |
| Au | $170$ | $137.019316$ | $0.285501930$ | $0.2855$ |
| Cu | $343.5$ | $276.859618$ | $0.576881841$ | $0.5769$ |
| Ti | $420$ | $338.518310$ | $0.705357710$ | $0.7054$ |
| Al | $428$ | $344.966278$ | $0.718793095$ | $0.7188$ |
| Fe | $470$ | $378.818109$ | $0.789328866$ | $0.7893$ |
| Si | $645$ | $519.867405$ | $1.083227912$ | $1.0832$ |
| C | $2230$ | $1797.371029$ | $3.745113555$ | $3.7451$ |

Every calculated frequency rounds to the value printed in the official
presentation. These conversions are independent reference targets for later
tests.

### Low-temperature limit

As $T\rightarrow0^+$, $x_E\rightarrow\infty$ and

$$
g(x_E)\sim x_E^2e^{-x_E}\rightarrow0.
$$

Therefore,

$$
\lim_{T\rightarrow0^+}C_V(T)=0.
$$

### High-temperature Dulong--Petit limit

As $T\rightarrow\infty$, $x_E\rightarrow0$ and $g(x_E)\rightarrow1$, so

$$
\lim_{T\rightarrow\infty}C_V(T)=3R.
$$

With the selected value of $R$,

$$
3R=24.943387854460\ \mathrm{J\,mol^{-1}K^{-1}}.
$$

At the useful dimensionless reference point $T=T_E$, where $x_E=1$,

$$
\frac{C_V}{3R}
=\frac{e}{(e-1)^2}
=0.920673594207792.
$$

### Frozen numerical domains

The principal material comparison will use

$$
0\leq T\leq800\ \mathrm K
$$

at uniform $1\ \mathrm K$ intervals. This reproduces the range shown in the
official presentation and includes $T=0$ through its limiting value.

The optional normalized supporting graph will use

$$
0\leq\frac{T}{T_E}\leq5
$$

with $1001$ uniformly spaced points and will plot

$$
\frac{C_V}{3R}
$$

against $T/T_E$. All materials must collapse onto the same dimensionless
Einstein curve; any separation would indicate a calculation or scaling error.

## Assumptions and interpretation boundary

### Planck model assumptions

- The emitter is an ideal black body with emissivity $\varepsilon=1$.
- The body is in thermal equilibrium at one uniform absolute temperature.
- The model gives emitted radiation at the surface; it does not model distance,
  geometric dilution, atmospheric absorption, or detector response.
- Vacuum wavelength is used.
- The plotted curves are theoretical spectra, not fits to solar observations.

### Einstein model assumptions

- The solid consists of independent quantum harmonic oscillators.
- Every oscillator in one material has the same frequency $f_E$.
- Three vibrational directions are included per atom.
- Anharmonicity, electronic heat capacity, defects, phase changes, and thermal
  expansion are omitted.
- The result is $C_V$, although experimental tables often report $C_P$.
- Debye's distribution of vibrational frequencies is outside the baseline.

The conclusions must therefore be described as behaviour of the declared
idealized models, not as exact predictions for every real sample.

## Validation requirements and tolerances

The future implementation must pass every baseline check below.

| Check | Required result | Tolerance |
| --- | --- | ---: |
| Planck domain validation | Reject non-positive $\lambda$ or $T$ | exact |
| Planck finiteness | No `NaN`, infinity, or negative value on declared grids | exact |
| Wien peak | Numerical $\lambda_{\max}$ agrees with $b/T$ | relative error $\leq10^{-3}$ |
| Stefan--Boltzmann integral | Numerical $\int M_\lambda d\lambda$ agrees with $\sigma T^4$ | relative error $\leq2\times10^{-3}$ |
| Radiance integral | Numerical $\int B_\lambda d\lambda$ agrees with $\sigma T^4/\pi$ | relative error $\leq2\times10^{-3}$ |
| Exitance conversion | $M_\lambda=\pi B_\lambda$ | relative error $\leq10^{-14}$ |
| Einstein domain validation | Reject $T<0$ and non-positive $T_D$, $T_E$, or $f_E$ | exact |
| Einstein zero limit | $C_V(0)=0$ | exact |
| Einstein physical bounds | $0\leq C_V\leq3R$ | relative slack $\leq10^{-12}$ |
| Einstein monotonicity | $C_V(T)$ is non-decreasing on each declared grid | absolute slack $\leq10^{-12}$ |
| Einstein anchor | $C_V(T_E)/(3R)=0.920673594207792$ | absolute error $\leq10^{-12}$ |
| High-temperature limit | At $T=100T_E$, $C_V$ agrees with $3R$ | relative error $\leq10^{-5}$ |
| Official frequency reproduction | Calculated values round to all seven displayed values | exact after four-decimal rounding |
| Normalized collapse | All normalized material curves coincide | maximum absolute difference $\leq10^{-12}$ |

Passing a check means meeting the declared threshold without changing it after
results are seen. Tighter observed errors may be reported, but they do not
retroactively alter these acceptance criteria.

## Output precision and reporting rules

- Internal arrays and calculations remain unrounded double-precision values.
- CSV files will retain enough significant figures to reproduce validation
  errors.
- Presentation tables may round wavelengths to $0.1\ \mathrm{nm}$,
  temperatures to $0.1\ \mathrm K$, heat capacities to
  $0.01\ \mathrm{J\,mol^{-1}K^{-1}}$, and relative errors to an appropriate
  scientific notation.
- Plot labels must state the quantity and unit, including `sr` for radiance or
  explicitly using spectral exitance when `sr` is absent.
- The labels "heat capacity" and "molar heat capacity" must not be used
  interchangeably without the molar unit.
- No graph may use degrees Celsius in place of absolute temperature.

## Stage 2 completion check

Stage 2 is complete when this specification is committed unchanged alongside
the Stage 1 scope and all of the following are true:

- both official equations have unambiguous definitions and domains;
- radiance and exitance are distinguished consistently;
- all constants and units are frozen;
- all seven material conversions have independent reference values;
- stable numerical forms and calculation grids are declared;
- physical assumptions and limitations are explicit; and
- validation thresholds are fixed before implementation.

The next stage is **Stage 3: software architecture and reproducibility design**.
