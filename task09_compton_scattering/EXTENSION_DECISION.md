# Task 9 extension decision: Klein–Nishina angular weighting

Status: **APPROVED — separately labelled extension**

## Decision

Add the unpolarized Klein–Nishina differential cross-section as an extension to
the required Compton kinematics. The official curves answer what wavelength
shift, electron speed and recoil direction follow from a chosen scattering angle.
The extension answers a different question: how strongly a free electron scatters
the photon into each solid angle.

The extension is scientifically useful because it explains why the complete
$0^\circ$–$180^\circ$ kinematic range is not sampled uniformly in a real free-
electron scattering model. It will never weight, hide or replace any of the three
required plots.

## Model

For an unpolarized incident photon,

$$
\frac{\mathrm d\sigma}{\mathrm d\Omega}
=\frac{r_e^2}{2}
\left(\frac{E'}{E}\right)^2
\left(
\frac{E'}{E}+\frac{E}{E'}-\sin^2\theta
\right),
$$

where $r_e$ is the classical electron radius and

$$
\frac{E'}{E}=\frac{1}{1+\alpha(1-\cos\theta)}.
$$

After integrating over azimuth, the angular density in polar angle is

$$
\frac{\mathrm d\sigma}{\mathrm d\theta}
=2\pi\sin\theta\frac{\mathrm d\sigma}{\mathrm d\Omega}.
$$

Dividing this density by the total Klein–Nishina cross-section gives a normalized
probability density in $\theta$. This density is zero at both polar endpoints
because their solid-angle rings have zero area, even though
$\mathrm d\sigma/\mathrm d\Omega$ is finite there.

## Validation boundary

- The analytical total cross-section will be compared with independent
  Gauss–Legendre integration over solid angle.
- The normalized polar-angle density will integrate to one on the plotted grid.
- The forward differential cross-section must equal $r_e^2$ for every energy.
- The total cross-section must be positive, below the Thomson value for nonzero
  photon energy and decrease over the official energy set.
- Values will be reported in both square metres and barns, with the conversion
  $1\ \mathrm{barn}=10^{-28}\ \mathrm{m^2}$.

NIST describes incoherent Compton-scattering data as being based on the
[Klein–Nishina free-electron formula](https://physics.nist.gov/PhysRefData/Xcom/Text/chap2.html).
The original result is O. Klein and Y. Nishina,
[doi:10.1007/BF01366453](https://doi.org/10.1007/BF01366453).

## Scope and limitations

The formula assumes one unpolarized photon and one free electron initially at
rest. It does not include electron binding, atomic incoherent scattering
functions, polarization selection, detector efficiency, multiple scattering or
material attenuation. Those omissions will be stated beside any extension plot.

No Monte Carlo sample is required to establish the extension. A later animation
may visualize selected exact events, but deterministic curves and normalized
densities remain the authoritative evidence.
