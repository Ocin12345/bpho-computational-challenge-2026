# Task 7 Speaker Script

## Final competition version

> Task 7 solves an electron in a one-nanometre infinite box. Boundary
> conditions create standing waves and discrete energies growing as n squared.
> The probability densities remain normalised, while the uncertainty
> calculation gives 0.568 h-bar in the ground state, above Heisenberg's
> half-h-bar limit. Fifty independent checks pass.

### Visual cues

- **0--6 seconds:** follow the first four probability-density curves.
- **6--11 seconds:** point to the discrete energy spectrum and \(n^2\) law.
- **11--16 seconds:** show the uncertainty line above the magenta bound.
- **16--18 seconds:** finish on the validation badge.

## Expanded 35-second version

> Task 7 solves Schrödinger's equation for an electron confined to a
> one-nanometre infinite box. Zero wavefunction at both walls selects standing
> waves, so the energies grow as n squared. Squaring each normalized
> wavefunction gives the position probability density. Calculating the
> position and momentum spreads gives 0.568 h-bar in the ground state, safely
> above Heisenberg's half-h-bar limit. A separate finite-difference eigensolver
> converges to the analytical spectrum, and all fifty scientific checks
> pass.

## Rehearsal explanation

The infinite walls enforce \(\psi(0)=\psi(a)=0\), so only an integer number of
half-wavelengths fits inside the box. This produces

$$
\psi_n=\sqrt{\frac{2}{a}}\sin\left(\frac{n\pi x}{a}\right)
$$

and

$$
E_n=\frac{n^2\pi^2\hbar^2}{2ma^2}.
$$

The probability density is \(|\psi_n|^2\). A stationary state's time factor
is a phase, so its density does not change with time.

For the uncertainty extension,

$$
\Delta x\Delta p
=\hbar\sqrt{\frac{n^2\pi^2}{12}-\frac12}.
$$

The minimum over the positive integer states occurs at \(n=1\) and equals
\(0.567862\hbar\), which is greater than \(\hbar/2\).

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| Schrödinger | “SHROE-ding-er” |
| \(\psi\) | “sigh” |
| \(\hbar\) | “h-bar” |
| eigenstate | “EYE-gen-state” |
| \(0.568\hbar\) | “zero point five six eight h-bar” |

## Questions you should be ready to answer

**Why are the energies discrete?**

The infinite walls force the wavefunction to vanish at both boundaries. Only
standing waves with an integer number of half-wavelengths satisfy both
conditions.

**Why is the probability density stationary?**

An energy eigenstate acquires only the phase \(e^{-iE_nt/\hbar}\). Its modulus
is one, so \(|\psi_n(x,t)|^2\) is time independent.

**Does the ground state reach the minimum uncertainty \(\hbar/2\)?**

No. Its product is \(0.567862\hbar\). Equality is associated with a Gaussian
minimum-uncertainty state, not the sine-shaped infinite-well ground state.

**How was the analytical solution checked?**

A separate tridiagonal finite-difference Hamiltonian was solved on increasingly
fine grids. Its energies converge at second order, and its eigenvectors have
near-unity overlap with the analytical states.
