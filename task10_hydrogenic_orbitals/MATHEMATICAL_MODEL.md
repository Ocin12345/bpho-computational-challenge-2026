# Task 10 Mathematical Model

## 1. Physical system and constants

The model is the stationary non-relativistic Schrödinger equation for one
electron in the Coulomb field of a point nucleus with charge \(+Ze\):

$$
\left[-\frac{\hbar^2}{2\mu}\nabla^2
-\frac{Ze^2}{4\pi\epsilon_0r}\right]\psi
=E\psi.
$$

The official recipe approximates the nuclear mass by

$$
M=A\,u,
$$

where \(A\) is the integer mass number and \(u\) is the atomic mass constant.
This convention is retained because it reproduces the official hydrogen value
\(-13.5982\) eV while including the requested reduced-mass correction:

$$
\mu=\frac{m_eM}{m_e+M}.
$$

The implementation freezes the [2022 CODATA recommended
values](https://physics.nist.gov/cuu/pdf/wall_2022.pdf):

| Quantity | Symbol | Value |
|---|---:|---:|
| Electron mass | \(m_e\) | \(9.1093837139\times10^{-31}\) kg |
| Atomic mass constant | \(u\) | \(1.66053906892\times10^{-27}\) kg |
| Bohr radius | \(a_0\) | \(5.29177210544\times10^{-11}\) m |
| Hartree energy | \(E_h\) | \(4.3597447222060\times10^{-18}\) J |
| Hartree energy | \(E_h/e\) | \(27.211386245981\) eV |
| Elementary charge | \(e\) | \(1.602176634\times10^{-19}\) C, exact |

Using the tabulated \(a_0\) and \(E_h\) avoids inventing extra precision by
recombining correlated measured constants.

## 2. Effective length and energy

Define

$$
a=\frac{m_e}{\mu}\frac{a_0}{Z}.
$$

All spatial structure scales with \(a\), and the energy is

$$
E_n
=-\frac12E_h\,\frac{\mu}{m_e}\frac{Z^2}{n^2}.
$$

For the official hydrogen-1 approximation \(Z=A=1\):

$$
\frac{\mu}{m_e}=0.999451720865875,
\qquad
a=0.529467506530\ {\rm \mathring A},
$$

$$
E_1=-13.5982334053\ {\rm eV},
\qquad
E_3=-1.51091482282\ {\rm eV}.
$$

The energy is independent of \(l,m\) in this model. That degeneracy must be
stated rather than interpreted as a numerical coincidence.

## 3. Coordinate convention

The project uses

$$
x=r\sin\vartheta\cos\varphi,\qquad
y=r\sin\vartheta\sin\varphi,\qquad
z=r\cos\vartheta,
$$

with

$$
r\geq0,\qquad
\vartheta\in[0,\pi],\qquad
\varphi\in(-\pi,\pi].
$$

At \(r=0\), \(\vartheta\) and \(\varphi\) are undefined. Numerically they are set
to zero only to evaluate the limiting formula. Every \(l>0\) radial function
vanishes there, while an S state is angularly constant, so the density remains
well-defined and orientation-independent.

## 4. Radial wavefunction

Let

$$
q=n-l-1,\qquad
\alpha=2l+1,\qquad
\rho=\frac{2r}{na}.
$$

The normalized radial function is

$$
R_{nl}(r)
=
\sqrt{\frac{q!}{2n(n+l)!}}
\left(\frac{2}{na}\right)^{3/2}
e^{-\rho/2}\rho^lL_q^\alpha(\rho).
$$

Production evaluation uses the stable three-term associated-Laguerre recurrence

$$
L_0^\alpha(x)=1,
\qquad
L_1^\alpha(x)=1+\alpha-x,
$$

$$
L_k^\alpha(x)
=\frac{(2k-1+\alpha-x)L_{k-1}^\alpha(x)
-(k-1+\alpha)L_{k-2}^\alpha(x)}{k}.
$$

The independent scalar reference uses the finite factorial sum printed in the
official brief. Agreement between a recurrence and a direct sum is stronger than
testing a formula against itself.

The radial normalization is

$$
\int_0^\infty |R_{nl}(r)|^2r^2\,dr=1.
$$

The number of positive finite radial nodes is

$$
N_{\rm radial}=n-l-1.
$$

## 5. Angular wavefunction

To keep the sign convention explicit, define the associated Ferrers function
without a Condon–Shortley sign:

$$
\overline P_m^m(x)
=(2m-1)!!(1-x^2)^{m/2},
$$

$$
\overline P_{m+1}^m(x)
=(2m+1)x\overline P_m^m(x),
$$

$$
\overline P_l^m(x)
=
\frac{(2l-1)x\overline P_{l-1}^m(x)
-(l+m-1)\overline P_{l-2}^m(x)}
{l-m}.
$$

For \(m\geq0\),

$$
Y_l^m(\vartheta,\varphi)
=(-1)^mN_{lm}\,
\overline P_l^m(\cos\vartheta)e^{im\varphi},
$$

$$
N_{lm}
=\sqrt{\frac{2l+1}{4\pi}\frac{(l-m)!}{(l+m)!}}.
$$

The normalized real basis is evaluated directly as

$$
\mathcal Y_{lm}(\vartheta,\varphi)=
\begin{cases}
\sqrt2N_{l|m|}\overline P_l^{|m|}(\cos\vartheta)
\sin(|m|\varphi), & m<0,\\[2mm]
N_{l0}\overline P_l^0(\cos\vartheta), & m=0,\\[2mm]
\sqrt2N_{lm}\overline P_l^m(\cos\vartheta)
\cos(m\varphi), & m>0.
\end{cases}
$$

This convention gives the intuitive orientations:

- \(m=+1\) P state proportional to \(x/r\);
- \(m=-1\) P state proportional to \(y/r\);
- \(m=0\) P state proportional to \(z/r\);
- \(m=+2\) D state proportional to \((x^2-y^2)/r^2\); and
- \(m=-2\) D state proportional to \(2xy/r^2\).

The angular normalization and orthogonality are

$$
\int_{4\pi}\mathcal Y_{lm}\mathcal Y_{l'm'}\,d\Omega
=\delta_{ll'}\delta_{mm'}.
$$

The parity relation is

$$
\mathcal Y_{lm}(\pi-\vartheta,\varphi+\pi)
=(-1)^l\mathcal Y_{lm}(\vartheta,\varphi).
$$

## 6. Full wavefunction and density

The real stationary orbital is

$$
\psi_{nlm}(r,\vartheta,\varphi)
=R_{nl}(r)\mathcal Y_{lm}(\vartheta,\varphi),
$$

and the required probability density is

$$
\rho_{nlm}=|\psi_{nlm}|^2.
$$

Its SI unit is \({\rm m}^{-3}\). For numerically and visually convenient values,
the dimensionless scaled density is

$$
\widetilde\rho=a^3\rho.
$$

The display-relative density is a third, distinct quantity:

$$
\rho_{\rm rel}
=\frac{\rho}{\max_{\rm displayed\ domain}\rho}.
$$

Only \(\rho\) is physical dimensional density. \(\widetilde\rho\) changes units
without changing shape, while \(\rho_{\rm rel}\) is a per-view contrast control
and must never be used for normalization or comparisons of absolute magnitude.

## 7. Analytic anchors

The first radial functions are

$$
R_{10}=2a^{-3/2}e^{-r/a},
$$

$$
R_{20}
=\frac{1}{2\sqrt2}a^{-3/2}
\left(2-\frac ra\right)e^{-r/(2a)},
$$

$$
R_{21}
=\frac{1}{2\sqrt6}a^{-3/2}
\frac rae^{-r/(2a)}.
$$

Therefore

$$
\rho_{100}
=\frac{e^{-2r/a}}{\pi a^3},
$$

$$
\rho_{200}
=\frac{(2-r/a)^2e^{-r/a}}{32\pi a^3},
$$

$$
\rho_{210}
=\frac{(r/a)^2e^{-r/a}\cos^2\vartheta}{32\pi a^3}.
$$

The 2s radial node is exactly \(r=2a\). The 2p density has a nodal \(x\)-\(y\)
plane for \(m=0\) and no positive radial node.

## 8. Expectation-value anchors

For every valid hydrogenic state,

$$
\langle r\rangle
=\frac a2\left[3n^2-l(l+1)\right],
$$

$$
\langle r^2\rangle
=\frac{a^2n^2}{2}
\left[5n^2+1-3l(l+1)\right].
$$

These tests probe the complete radial distribution and are more discriminating
than a few point values.

## 9. Numerical domain and tolerances

The production core supports and validates

$$
1\leq n\leq8,\qquad
0\leq l<n,\qquad
-l\leq m\leq l,
$$

$$
1\leq Z\leq20,\qquad
Z\leq A\leq3Z,
$$

with integer quantum and nuclear numbers.

Independent validation uses:

- Gauss–Laguerre or mapped Gauss–Legendre radial quadrature;
- Gauss–Legendre integration in \(\cos\vartheta\);
- a Fourier-complete uniform azimuth grid;
- direct-factorial scalar references at non-symmetric points; and
- analytic low-state formulas.

Frozen acceptance tolerances are:

| Check | Maximum error |
|---|---:|
| Production versus independent scalar value | \(5\times10^{-13}\) absolute plus relative |
| Radial normalization | \(2\times10^{-12}\) |
| Angular normalization/orthogonality | \(2\times10^{-12}\) |
| Same-\(l\) radial orthogonality | \(2\times10^{-11}\) |
| Analytic expectation values | \(5\times10^{-11}\) relative |
| Energy and length scaling | \(5\times10^{-14}\) relative |
| Parity | \(5\times10^{-13}\) absolute |

The visualization extent is chosen from the radial cumulative probability so
that at least 99.95% of the state probability lies within the enclosing sphere.
The official 0.15 display cutoff is then applied only to opacity.

## 10. Interpretation boundary

An orbital is a stationary probability amplitude, not a path followed by an
electron. Rotating a view changes the camera, not the quantum state. Changing
\(m\) selects another normalized basis state inside an energy-degenerate
subspace; it is not an animation of a transition.

The model omits spin, relativity, fine structure, Lamb shift, fields,
electron–electron interactions and time-dependent superpositions.
