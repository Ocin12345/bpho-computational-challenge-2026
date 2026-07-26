# Task 7 Mathematical Model

## Scope

The official Task 7 model is a non-relativistic particle of mass \(m\) in the
one-dimensional infinite potential well

$$
V(x)=\begin{cases}
0,&0<x<a,\\
\infty,&x\leq0\text{ or }x\geq a.
\end{cases}
$$

The baseline uses an electron and \(a=1.00\ \mathrm{nm}\). The analytical
implementation remains configurable in both mass and width.

## Eigenstates and energies

The boundary conditions \(\psi(0)=\psi(a)=0\) admit positive integer quantum
numbers \(n=1,2,\ldots\). The normalized stationary states are

$$
\psi_n(x,t)=\sqrt{\frac{2}{a}}
\sin\!\left(\frac{n\pi x}{a}\right)e^{-iE_nt/\hbar},
$$

with

$$
E_n=\frac{n^2\pi^2\hbar^2}{2ma^2}
=\frac{n^2h^2}{8ma^2}.
$$

The Born probability density is

$$
|\psi_n(x,t)|^2=\frac{2}{a}
\sin^2\!\left(\frac{n\pi x}{a}\right).
$$

The time-dependent factor has unit modulus, so a single energy eigenstate has
a stationary probability density.

## Position and momentum uncertainties

For every state,

$$
\langle x\rangle=\frac{a}{2},\qquad
\langle x^2\rangle=a^2\left(\frac13-\frac{1}{2n^2\pi^2}\right),
$$

and therefore

$$
\Delta x=a\sqrt{\frac{1}{12}-\frac{1}{2n^2\pi^2}}.
$$

Using \(\hat p=-i\hbar\,d/dx\),

$$
\langle p\rangle=0,\qquad
\langle p^2\rangle=\frac{n^2\pi^2\hbar^2}{a^2},\qquad
\Delta p=\frac{n\pi\hbar}{a}.
$$

The uncertainty product is

$$
\Delta x\Delta p
=\hbar\sqrt{\frac{n^2\pi^2}{12}-\frac12}
\geq\frac{\hbar}{2}.
$$

The ground-state value is approximately \(0.567862\hbar\), already above the
Heisenberg lower bound.

## Independent numerical model

The second derivative is discretized on \(N\) interior points:

$$
\frac{d^2\psi}{dx^2}\bigg|_j
\approx\frac{\psi_{j+1}-2\psi_j+\psi_{j-1}}{\Delta x^2}.
$$

This gives a symmetric tridiagonal Hamiltonian. Its eigenpairs are solved
without using the analytical energies. Grids of 100, 200, 400, 800 and 1600
interior points provide a convergence study; the expected energy error is
second order in \(\Delta x\).

## Plotting conventions

The primary probability axes are dimensionless:

$$
u=\frac{x}{a},\qquad a|\psi|^2.
$$

This preserves normalization and lets the shape be interpreted independently
of the selected physical width. Energies are also reported in electronvolts
for the configured electron example.

## Declared limitations

The model assumes an infinite one-dimensional well, a single non-interacting
particle, non-relativistic dynamics and stationary energy eigenstates. It does
not represent finite barriers, tunnelling, external fields, spin, particle
interactions, relativistic effects or measurement-induced state preparation.
