# Task 9 Results and Interpretation

## Direct answer to the official task

The requested five-energy curves are collected in
[`required_kinematics`](../figures/task09/required_kinematics.png). They use one
common angle domain, 0° ≤ \(\theta\) ≤ 180°, with 721 samples at 0.25° spacing.

For a photon of incident energy \(E\), define

$$
\alpha=\frac{E}{m_ec^2},
\qquad m_ec^2=510.998950692\ \mathrm{keV}.
$$

Then

$$
\boxed{\frac{\Delta\lambda}{\lambda}=\alpha(1-\cos\theta)}.
$$

The scattered photon and electron kinetic energies are

$$
E'=\frac{E}{1+\alpha(1-\cos\theta)},
\qquad K=E-E'.
$$

The electron Lorentz factor and speed are

$$
\gamma=1+\frac{K}{m_ec^2},
\qquad
\boxed{\frac vc=\sqrt{1-\gamma^{-2}}}.
$$

Resolving momentum parallel and perpendicular to the incoming photon gives

$$
p_{e,x}c=E-E'\cos\theta,
\qquad
|p_{e,y}|c=E'\sin\theta,
$$

and therefore

$$
\boxed{\phi=\operatorname{atan2}\!\left(E'\sin\theta,E-E'\cos\theta\right)}.
$$

## Numerical anchors at 90°

| \(E\) / keV | \(\Delta\lambda/\lambda\) | \(v/c\) | \(\phi\) / degree | \(E'\) / keV | \(K\) / keV |
|---:|---:|---:|---:|---:|---:|
| 50 | 0.097848 | 0.131210 | 42.3296 | 45.5437 | 4.4563 |
| 100 | 0.195695 | 0.247197 | 39.9069 | 83.6334 | 16.3666 |
| 200 | 0.391390 | 0.434186 | 35.7050 | 143.7411 | 56.2589 |
| 500 | 0.978476 | 0.738829 | 26.8138 | 252.7198 | 247.2802 |
| 1000 | 1.956951 | 0.900090 | 18.6848 | 338.1862 | 661.8138 |

Every row satisfies \(E=E'+K\) to the frozen conservation tolerance. At 90°,
the recoil-angle equation also simplifies to

$$
\tan\phi=\frac{E'}{E}=\frac{1}{1+\alpha},
$$

which makes the fall of \(\phi\) with incident energy especially transparent.

## Endpoint behaviour

Forward scattering gives

$$
\theta=0^\circ:
\quad \Delta\lambda=0,\quad E'=E,\quad K=0,\quad v=0.
$$

The electron has zero momentum, so no recoil direction exists. A formal limit
from positive angles gives \(\phi\to90^\circ\), which is why the graphs show an
open 90° limiting point rather than claiming a defined direction.

At backscatter,

$$
\theta=180^\circ:
\quad \frac{\Delta\lambda}{\lambda}=2\alpha,
\quad \phi=0^\circ.
$$

| \(E\) / keV | backscatter \(\Delta\lambda/\lambda\) | backscatter \(v/c\) |
|---:|---:|---:|
| 50 | 0.195695 | 0.176849 |
| 100 | 0.391390 | 0.318793 |
| 200 | 0.782780 | 0.521337 |
| 500 | 1.956951 | 0.794736 |
| 1000 | 3.913902 | 0.920466 |

The absolute wavelength shift is independent of incident energy:

$$
\Delta\lambda=\lambda_C(1-\cos\theta),
$$

so its maximum is \(2\lambda_C=4.85262047\) pm. The plotted *fractional* shift
still grows linearly with \(E\) because the incident wavelength is shorter at
higher energy.

## What the three curve families show

### Fractional wavelength shift

Since \(1-\cos\theta=2\sin^2(\theta/2)\), every curve begins horizontally at
zero, increases monotonically and reaches its maximum at 180°. The five curves
have identical angular shape and amplitudes proportional to 50:100:200:500:1000.

### Electron speed

Energy transfer \(K\) increases with both \(E\) and \(\theta\), so \(v/c\) is
monotonic in both. The calculation is explicitly relativistic. Even the most
energetic official backscatter case gives \(v/c=0.920466\), safely below one;
using \(K=\tfrac12m_ev^2\) would be inappropriate for much of this domain.

### Electron recoil angle

For every non-zero photon angle, the electron is on the opposite side of the
incident axis from the scattered photon so transverse momenta cancel. As
\(\theta\) rises, the electron direction rotates toward the incident axis and
\(\phi\) decreases to zero. Higher-energy curves lie lower because the changed
photon energy ratio changes the momentum triangle.

## Energy and momentum interpretation

[`energy_transfer_geometry`](../figures/task09/energy_transfer_geometry.png)
plots both \(E'/E\) and \(K/E\). They are exact complements at every point. The
three 200 keV momentum triangles use a single momentum scale within each panel:

$$
\vec p_e=\vec p_\gamma-\vec p_{\gamma'}.
$$

This vector relation is stronger evidence than energy balance alone. The
validation suite independently checks the parallel component, transverse
component, momentum magnitude and relativistic mass shell

$$
(E_e)^2=(p_ec)^2+(m_ec^2)^2.
$$

## Optional Klein–Nishina extension

The official three plots answer what happens *if* a photon scatters through a
chosen angle. They do not say how frequently each angle occurs. The separate
extension applies the unpolarized free-electron Klein–Nishina formula

$$
\frac{d\sigma}{d\Omega}
=\frac{r_e^2}{2}\left(\frac{E'}E\right)^2
\left(\frac{E'}E+\frac E{E'}-\sin^2\theta\right).
$$

The angular density in polar angle includes the azimuthal solid-angle factor:

$$
p(\theta)=\frac{2\pi\sin\theta}{\sigma}
\frac{d\sigma}{d\Omega}.
$$

This density is zero at both 0° and 180° because an infinitesimally thin polar
ring has zero solid-angle area, even though \(d\sigma/d\Omega\) is finite there.

| \(E\) / keV | total Klein–Nishina cross-section / barn |
|---:|---:|
| 50 | 0.561507 |
| 100 | 0.492748 |
| 200 | 0.406482 |
| 500 | 0.289166 |
| 1000 | 0.211208 |

The total cross-section falls with energy and the angular distribution becomes
more forward weighted. These statements apply only to the declared ideal
single-electron model; the extension does not model a bulk target or detector.

## Figure-by-figure reading guide

1. [`required_kinematics`](../figures/task09/required_kinematics.png) is the
   direct official answer and should be the first figure shown.
2. [`energy_transfer_geometry`](../figures/task09/energy_transfer_geometry.png)
   explains conservation through complementary energies and momentum triangles.
3. [`klein_nishina_extension`](../figures/task09/klein_nishina_extension.png)
   adds angular likelihood while remaining visibly separate from the required
   kinematics.
4. [`task09_summary`](../figures/task09/task09_summary.png) combines the 200 keV,
   90° collision with all three curve families in a 16:9 competition plate.
5. [`compton_angle_sweep.gif`](../figures/task09/compton_angle_sweep.gif) animates
   one 200 keV photon continuously from forward scattering to backscatter on
   fixed axes.

All four static PNGs were inspected at original resolution. Each has an editable
SVG companion. Animation frames were checked for GIF-disposal artifacts and a
mid-sweep frame was inspected in Chromium.

## Physical limitations

The electron is assumed free and initially at rest. The calculation omits atomic
binding and momentum distributions, material composition, attenuation, multiple
scattering, beam polarisation, detector efficiency, energy resolution, angular
resolution, background and uncertainty in measured constants.

Consequently, the Klein–Nishina extension is a differential cross-section model,
not a full Monte Carlo experiment. Within the declared ideal assumptions, the
kinematics are exact analytical relations rather than a timestep approximation.
