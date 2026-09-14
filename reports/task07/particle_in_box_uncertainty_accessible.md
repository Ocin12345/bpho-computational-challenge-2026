# Particle in a One-Dimensional Box

## Energy quantisation, probability density and Heisenberg uncertainty

This semantic Markdown report is the accessible companion to the
[four-page PDF](particle_in_box_uncertainty.pdf) and
[editable LaTeX source](particle_in_box_uncertainty.tex). It contains the same
scientific argument in a heading, equation and table structure suitable for text
resizing and screen-reader navigation.

## Abstract

This report implements the exact stationary states of a non-relativistic
particle confined by an infinite one-dimensional potential well. The energy
spectrum and Born probability densities satisfy BPhO Task 7. The extension
evaluates the position and momentum moments and shows analytically and
computationally that every positive-integer state obeys

$$
\Delta x\,\Delta p\geq\frac{\hbar}{2}.
$$

An independent finite-difference eigensolver checks the analytical result.

## Physical model

The potential is zero inside a box of width (a) and infinite outside:

$$
V(x)=
\begin{cases}
0,&0<x<a,\\
\infty,&x\leq0\text{ or }x\geq a.
\end{cases}
$$

The wavefunction must vanish at both walls, (\psi(0)=\psi(a)=0). Within the
box, the time-independent Schrödinger equation is

$$
-\frac{\hbar^2}{2m}\frac{d^2\psi}{dx^2}=E\psi.
$$

The boundary conditions select positive integers (n=1,2,\ldots) and the
normalized eigenstates

$$
\psi_n(x,t)=\sqrt{\frac{2}{a}}
\sin\!\left(\frac{n\pi x}{a}\right)e^{-iE_nt/\hbar}.
$$

Their energies are

$$
E_n=\frac{n^2\pi^2\hbar^2}{2ma^2}
=\frac{n^2h^2}{8ma^2}.
$$

The computational baseline uses an electron and (a=1.00\ \mathrm{nm}). The
mass and width are configurable; the official brief does not require one unique
choice.

## Probability density

The Born probability density is

$$
|\psi_n(x,t)|^2=\frac{2}{a}
\sin^2\!\left(\frac{n\pi x}{a}\right).
$$

The factor (e^{-iE_nt/\hbar}) has unit modulus, so a single energy eigenstate
has a time-independent probability density. Normalization follows from

$$
\int_0^a|\psi_n|^2\,dx=1.
$$

State (n) has (n-1) interior nodes at (x=ka/n), where
(k=1,\ldots,n-1).

![Four panels show the scaled probability density a times absolute psi squared against normalized position x over a for n equals 1 through 4. Every curve begins and ends at zero, has area one, is symmetric about the box centre, and contains n minus 1 marked interior nodes.](../../figures/task07/probability_densities.png)

## Position uncertainty

The expectation value and second moment of position are

$$
\langle x\rangle=\int_0^a x|\psi_n|^2\,dx=\frac{a}{2},
$$

$$
\langle x^2\rangle
=a^2\left(\frac13-\frac{1}{2n^2\pi^2}\right).
$$

Therefore

$$
(\Delta x)^2
=\langle x^2\rangle-\langle x\rangle^2
=a^2\left(\frac1{12}-\frac{1}{2n^2\pi^2}\right),
$$

and

$$
\Delta x=a\sqrt{\frac1{12}-\frac{1}{2n^2\pi^2}}.
$$

## Momentum uncertainty

The momentum operator is

$$
\hat p=-i\hbar\frac{d}{dx}.
$$

Because each spatial eigenfunction is real and vanishes at the boundaries,

$$
\langle p\rangle
=\int_0^a\psi_n^*\left(-i\hbar\frac{d}{dx}\right)\psi_n\,dx
=-\frac{i\hbar}{2}\left[\psi_n^2\right]_0^a=0.
$$

Applying the operator twice gives

$$
\langle p^2\rangle
=\int_0^a\psi_n^*\left(-\hbar^2\frac{d^2}{dx^2}\right)\psi_n\,dx
=\frac{n^2\pi^2\hbar^2}{a^2}.
$$

Thus

$$
\Delta p=\sqrt{\langle p^2\rangle-\langle p\rangle^2}
=\frac{n\pi\hbar}{a}.
$$

## Verification of the uncertainty principle

Multiplying the two standard deviations gives

$$
\boxed{
\Delta x\,\Delta p
=\hbar\sqrt{\frac{n^2\pi^2}{12}-\frac12}
}.
$$

The expression increases with positive integer (n), so its minimum occurs at
(n=1):

$$
\frac{\Delta x\,\Delta p}{\hbar}
=\sqrt{\frac{\pi^2}{12}-\frac12}
=0.567861808\ldots>\frac12.
$$

Every stationary state therefore satisfies Heisenberg's relation. The ground
state is not a minimum-uncertainty Gaussian, so the inequality is strict.

![Three panels show position uncertainty, momentum uncertainty and their product for n equals 1 through 10. The product starts at 0.568 h-bar for n equals 1 and rises monotonically; every point lies above a dashed magenta line at the Heisenberg lower bound of 0.5 h-bar.](../../figures/task07/uncertainty_principle.png)

## Computational implementation and validation

The analytical model evaluates the preceding equations on a 2001-point position
grid. A separate numerical model approximates the second derivative by

$$
\left.\frac{d^2\psi}{dx^2}\right|_j
\approx\frac{\psi_{j+1}-2\psi_j+\psi_{j-1}}{(\Delta x)^2},
$$

creating a symmetric tridiagonal Hamiltonian. SciPy's tridiagonal eigensolver
calculates its eigenvalues without inserting the analytical spectrum.

| Interior points | Maximum relative energy error over the first ten states |
|---:|---:|
| 100 | (8.04\times10^{-3}) |
| 200 | (2.03\times10^{-3}) |
| 400 | (5.11\times10^{-4}) |
| 800 | (1.28\times10^{-4}) |
| 1600 | (3.21\times10^{-5}) |

The observed convergence orders lie between 1.99896 and 1.99996, consistent
with second-order discretization error. On the finest grid, the absolute overlap
between every numerical eigenvector and its analytical counterpart exceeds
0.999999. Position and momentum moments are also computed directly from every
normalized eigenvector. At 1600 points, the maximum relative errors in both
momentum uncertainty and the uncertainty product are below
\(1.605\times10^{-5}\), with measured convergence orders between 1.99961 and
2.00038. All 50 grid-state pairs satisfy the Heisenberg bound. The 50-check
acceptance suite also checks normalization,
orthogonality, node counts, boundary values, energy scaling, expectation values
and the uncertainty inequality.

## Interpretation and limitations

The infinite well is idealized. Real confining potentials are finite and may
allow tunnelling. This model is one-dimensional and non-relativistic, contains
one non-interacting particle, and omits external fields and spin dynamics. These
assumptions do not affect the internal verification of Task 7, but they limit
direct quantitative comparison with a particular laboratory system.

The stationary density does not move. A physically meaningful time-dependent
animation would require a separately declared superposition or wave packet.

## Reproducibility and provenance

The source interpretation is recorded in
[`OFFICIAL_REQUIREMENTS.md`](../../task07_particle_in_box/OFFICIAL_REQUIREMENTS.md).
The complete environment, build order, integrity checks and artifact inventory
are recorded in
[`REPRODUCIBILITY.md`](../../task07_particle_in_box/REPRODUCIBILITY.md).
The deterministic manifest binds the accepted data and figures to the passing
50-check study.
