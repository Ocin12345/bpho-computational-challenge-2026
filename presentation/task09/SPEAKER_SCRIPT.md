# Task 9 Speaker Script

## Final competition version

> Task 9 models exact Compton scattering at five energies. Fractional shift and
> electron speed rise with angle, while recoil angle falls to zero at
> backscatter. At 200 keV and 90 degrees we obtain 0.391, 0.434 c and 35.7
> degrees. Energy-momentum conservation passed all 44 checks.

### Visual cues

- **0–4 seconds:** show the exact 200 keV momentum triangle.
- **4–10 seconds:** follow the wavelength-shift and relativistic-speed curves.
- **10–15 seconds:** point to the recoil-angle curves and reference markers.
- **15–18 seconds:** finish on the core and extension validation totals.

## Expanded 35-second version

> Task 9 uses exact relativistic energy and momentum conservation to model a
> photon scattering from a free electron initially at rest. Across the five
> required incident energies, fractional wavelength shift and recoil speed rise
> with scattering angle, while the electron direction rotates toward the
> incident axis. At 200 keV and 90 degrees, the fractional shift is 0.391390,
> electron speed is 0.434186 c, and recoil angle is 35.705 degrees. The official
> kinematics pass all 44 independent checks; the separately labelled
> Klein–Nishina extension passes 30 more.

## Rehearsal explanation

For incident photon energy $E$, define

$$
\alpha=\frac{E}{m_ec^2}.
$$

The three required quantities are

$$
\frac{\Delta\lambda}{\lambda}=\alpha(1-\cos\theta),
$$

$$
\frac vc=\sqrt{1-\left(1+\frac{E-E'}{m_ec^2}\right)^{-2}},
$$

$$
\phi=\operatorname{atan2}\!\left(E'\sin\theta,
E-E'\cos\theta\right),
\qquad
E'=\frac{E}{1+\alpha(1-\cos\theta)}.
$$

The speed is calculated relativistically. At exactly $\theta=0^\circ$, the
electron momentum is zero, so its direction is undefined; the curve shows the
continuous 90° limit as an open point. At $180^\circ$, the electron recoils
along the incident direction and $\phi=0^\circ$.

## Pronunciation guide

| Term | Say it as |
|---|---|
| Compton | “COMP-ton” |
| keV | “kilo-electron-volts” |
| Klein–Nishina | “Kline NISH-ee-na” |
| $\theta$ | “theta” |
| $\phi$ | “fie” |

## Questions you should be ready to answer

**Why does the fractional shift increase with energy?**

The absolute Compton shift depends only on angle, but the incident wavelength is
shorter at higher energy, so the same absolute shift is a larger fraction of it.

**Why is the electron speed not calculated with $K=\tfrac12m_ev^2$?**

Several required cases are strongly relativistic. The model instead obtains the
Lorentz factor from the transferred kinetic energy and guarantees $v<c$.

**Why is the recoil angle undefined at 0°?**

Forward scattering transfers no momentum to the electron. A zero vector has no
direction, although the limiting recoil angle as $\theta\to0^+$ is 90°.

**What does the Klein–Nishina extension add?**

It weights how likely different photon angles are for an ideal free electron. It
does not alter the official wavelength, speed or recoil-angle kinematics.

**Does the model predict a real detector spectrum?**

No. It omits atomic binding, material attenuation, multiple scattering,
polarisation, detector efficiency, finite resolution and background.
