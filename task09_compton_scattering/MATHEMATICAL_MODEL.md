# Task 9 mathematical model

## Physical system and conventions

An incident photon of energy $E$ travels along $+x$ and scatters through an angle
$\theta\in[0,\pi]$ from a free electron initially at rest. The scattered photon is
drawn above the incident axis. Momentum conservation therefore places the recoil
electron below that axis; $\phi\in[0,\pi/2]$ is reported as the positive magnitude
of that downward recoil angle.

The required study uses

$$
E\in\{50,100,200,500,1000\}\ \mathrm{keV}.
$$

The core calculation assumes a single two-body collision in vacuum. The electron
is unbound and initially stationary, and the calculation is fully relativistic.

## Constants and dimensionless energy

The implementation will freeze the exact SI defining values

$$
c=299\,792\,458\ \mathrm{m\,s^{-1}},
\qquad
h=6.626\,070\,15\times10^{-34}\ \mathrm{J\,s},
\qquad
e=1.602\,176\,634\times10^{-19}\ \mathrm C,
$$

from the [BIPM SI defining constants](https://www.bipm.org/en/measurement-units/si-defining-constants),
and the 2022 CODATA electron mass

$$
m_e=9.109\,383\,7139\times10^{-31}\ \mathrm{kg}
$$

from the [NIST CODATA table](https://physics.nist.gov/cuu/pdf/wall_2022.pdf).
These give

$$
m_e c^2=510.998\,950\,692\ \mathrm{keV},
\qquad
\lambda_C=\frac{h}{m_e c}
=2.426\,310\,23538\times10^{-12}\ \mathrm m.
$$

Define the dimensionless incident energy

$$
\alpha=\frac{E}{m_e c^2}
$$

and the angular factor $u=1-\cos\theta$. These two quantities expose most of the
kinematics without mixing units.

## Photon wavelength and energy

The incident wavelength is

$$
\lambda=\frac{hc}{E}.
$$

The Compton shift and scattered wavelength are

$$
\Delta\lambda=\lambda_C u,
\qquad
\lambda'=\lambda+\Delta\lambda.
$$

Therefore the first required output is

$$
\boxed{
\frac{\Delta\lambda}{\lambda}
=\alpha(1-\cos\theta)
}
$$

and the scattered photon energy has two equivalent forms:

$$
\boxed{
E'=\frac{hc}{\lambda'}
=\frac{E}{1+\alpha(1-\cos\theta)}
}.
$$

The wavelength-based expression will be one production route and the
dimensionless energy-ratio expression will be an independent reference route.

## Electron kinetic energy and speed

Energy conservation gives the electron kinetic energy

$$
K=E-E'.
$$

Its total energy and Lorentz factor are

$$
E_e=m_e c^2+K,
\qquad
\gamma=\frac{E_e}{m_e c^2}
=1+\frac{K}{m_e c^2}.
$$

The second required output is then

$$
\boxed{
\beta\equiv\frac{v}{c}
=\sqrt{1-\gamma^{-2}},
\qquad
v=\beta c
}.
$$

Substitution gives the formula shown in the official material:

$$
v=c\sqrt{1-
\left(
\frac{m_e c^2}
{E-E'+m_e c^2}
\right)^2}.
$$

For an independent momentum-based check, photon momentum has magnitude $p=E/c$
and $p'=E'/c$, so

$$
(p_e c)^2=E^2+E'^2-2EE'\cos\theta
$$

and

$$
\beta=\frac{p_e c}{E_e}.
$$

The energy- and momentum-based speed calculations must agree over the complete
grid.

## Electron recoil angle

Momentum conservation gives electron components

$$
p_{e,x}=\frac{E-E'\cos\theta}{c},
\qquad
|p_{e,y}|=\frac{E'\sin\theta}{c}.
$$

The third required output is evaluated with a quadrant-safe two-argument
arctangent:

$$
\boxed{
\phi=\operatorname{atan2}
\left(E'\sin\theta,\ E-E'\cos\theta\right)
}.
$$

Dividing by $E'$ recovers the official relation:

$$
\tan\phi
=\frac{\sin\theta}
{1+\alpha(1-\cos\theta)-\cos\theta}
=\frac{\cot(\theta/2)}{1+\alpha}.
$$

The `atan2` form is the numerical definition because it avoids division by a
small denominator and preserves the correct quadrant.

## Endpoint and limiting behaviour

### Forward scattering: $\theta=0$

At exactly $0^\circ$,

$$
\Delta\lambda=0,
\qquad
E'=E,
\qquad
K=0,
\qquad
v=0.
$$

The recoil electron has zero momentum, so its direction is physically undefined.
However,

$$
\lim_{\theta\to0^+}\phi=90^\circ.
$$

The data schema must therefore include both an angle-validity flag and the
continuous plotting limit. A graph may start at $90^\circ$ only if its annotation
states that the exact endpoint is undefined.

### Backscattering: $\theta=\pi$

At $180^\circ$,

$$
\frac{\Delta\lambda}{\lambda}=2\alpha,
\qquad
\frac{E'}{E}=\frac{1}{1+2\alpha},
\qquad
\phi=0^\circ.
$$

This is the maximum wavelength shift, maximum recoil kinetic energy and maximum
recoil speed for a fixed incident energy.

### Low-energy limit

For $\alpha\ll1$,

$$
\frac{\Delta\lambda}{\lambda}\approx\alpha(1-\cos\theta),
\qquad
\beta\approx2\alpha\sin\frac{\theta}{2},
\qquad
\phi\approx90^\circ-\frac{\theta}{2}.
$$

This provides a controlled non-relativistic comparison, but not a replacement for
the relativistic production model.

## Conservation identities

Every generated point must satisfy all of the following within a frozen numerical
tolerance:

$$
E+m_e c^2=E'+E_e,
$$

$$
\frac{E}{c}=\frac{E'}{c}\cos\theta+p_e\cos\phi,
$$

$$
0=\frac{E'}{c}\sin\theta-p_e\sin\phi,
$$

and the electron mass shell

$$
E_e^2-(p_e c)^2=(m_e c^2)^2.
$$

These residuals are more informative than checking the three requested formulas
alone because they test the complete collision state.

## Frozen numerical anchors

Using the constants above:

| $E$ (keV) | $\alpha$ | $\Delta\lambda/\lambda$ at 180° | $v/c$ at 180° | $\phi$ at 90° |
|---:|---:|---:|---:|---:|
| 50 | 0.097847559 | 0.195695118 | 0.176848643 | 42.329552° |
| 100 | 0.195695118 | 0.391390236 | 0.318793384 | 39.906872° |
| 200 | 0.391390236 | 0.782780472 | 0.521337140 | 35.705015° |
| 500 | 0.978475590 | 1.956951181 | 0.794736222 | 26.813843° |
| 1000 | 1.956951181 | 3.913902362 | 0.920465868 | 18.684826° |

These anchors will be frozen in independent tests. They are not manually inserted
into plots.

## Validation design

The future implementation must compare:

1. wavelength-shift and energy-ratio formulations of $E'$;
2. Lorentz-factor and momentum-magnitude formulations of $v/c$;
3. momentum-component and official tangent formulations of $\phi$;
4. analytical endpoints and low-energy asymptotics against computed values;
5. pointwise energy, two-component momentum and mass-shell residuals;
6. scalar outputs against broadcast vector and two-dimensional energy–angle
   arrays; and
7. Python outputs against the later browser implementation.

No validation route may call the same production function it is meant to check.

## Scope retained

This model produces exact ideal kinematics, not event probabilities. The
Klein–Nishina differential cross-section may later be considered as a separately
labelled extension, but it must not alter or weight the three official curves.
