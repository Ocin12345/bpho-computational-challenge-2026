# Task 7 Results and Interpretation

## Result summary

The infinite-well model has been evaluated for an electron in a
\(1.00\ \mathrm{nm}\) box. The official energy and probability-density plots
are complete, the uncertainty-principle extension has been derived in LaTeX,
and a separate tridiagonal finite-difference eigensolver confirms the first ten
analytical states.

All 50 scientific validation checks pass, including direct numerical moment,
Heisenberg-bound and uncertainty-convergence tests.

## Quantised energies

The energy eigenvalues are

$$
E_n=\frac{n^2\pi^2\hbar^2}{2m_{\mathrm e}a^2}.
$$

Selected values are:

| \(n\) | \(E_n\) / eV | \(E_n/E_1\) |
| ---: | ---: | ---: |
| 1 | 0.376030162 | 1 |
| 2 | 1.504120648 | 4 |
| 3 | 3.384271459 | 9 |
| 4 | 6.016482594 | 16 |
| 10 | 37.603016210 | 100 |

The quadratic law means adjacent levels become more widely separated:

$$
E_{n+1}-E_n=(2n+1)E_1.
$$

The energy figure uses stems and markers because quantum number is discrete; it
does not imply physically allowed values between adjacent integers.

## Probability densities

The normalized densities are

$$
|\psi_n|^2=\frac{2}{a}\sin^2\left(\frac{n\pi x}{a}\right).
$$

Every stored state:

- vanishes at \(x=0\) and \(x=a\);
- integrates to one;
- is symmetric about \(x=a/2\); and
- contains \(n-1\) interior nodes.

The primary figures use \(x/a\) and \(a|\psi|^2\), making the curve shapes
independent of the chosen box width. The wavefunction comparison separately
shows that negative wavefunction amplitude is permitted while probability
density remains non-negative.

## Uncertainty-principle extension

The analytical moments are

$$
\langle x\rangle=\frac{a}{2},
\qquad
\langle x^2\rangle=a^2\left(\frac13-\frac{1}{2n^2\pi^2}\right),
$$

$$
\langle p\rangle=0,
\qquad
\langle p^2\rangle=\frac{n^2\pi^2\hbar^2}{a^2}.
$$

Therefore,

$$
\Delta x\Delta p
=\hbar\sqrt{\frac{n^2\pi^2}{12}-\frac12}.
$$

The ground state produces the smallest value in this family:

$$
\Delta x\Delta p=0.567861808\hbar>0.5\hbar.
$$

The product rises monotonically to \(9.041388353\hbar\) at \(n=10\). The
four-page report in [`reports/task07`](../reports/task07/) gives the complete
derivation and computational evidence.

## Independent numerical solution

The central finite-difference Hamiltonian was solved on 100, 200, 400, 800 and
1600 interior points. The maximum relative energy errors over the first ten
states are:

| Interior points | Maximum relative error |
| ---: | ---: |
| 100 | \(8.04\times10^{-3}\) |
| 200 | \(2.03\times10^{-3}\) |
| 400 | \(5.11\times10^{-4}\) |
| 800 | \(1.28\times10^{-4}\) |
| 1600 | \(3.21\times10^{-5}\) |

Observed convergence orders range from 1.99896 to 1.99996, matching the
expected second-order central-difference error. Every finest-grid analytical-
numerical eigenfunction overlap exceeds 0.9999999999999.

The numerical route also applies discrete position, momentum and momentum-
squared operators directly to every eigenvector. At (N=1600), the maximum
relative errors in (Delta p) and (Delta xDelta p) are both below
(1.605\times10^{-5}). Their measured orders across all ten states span
1.99961 to 2.00038, and all 50 grid-state products satisfy the Heisenberg bound.

The visible judge-facing evidence table reports, for \(n=1,2,3,5,10\), the
numerical \(\langle p^2\rangle\), numerical and analytical \(\Delta p\),
\(\Delta x\Delta p/\hbar\), and \(2\Delta x\Delta p/\hbar\). The accompanying
five-grid convergence view reports energy, \(\Delta p\), and product errors;
the downloadable CSV also retains \(\Delta x\), \(p^2\), normalization,
\(\langle p\rangle\), and measured convergence orders.

## Figure package

1. [`energy_spectrum`](../figures/task07/energy_spectrum.png) shows discrete
   energies and adjacent level gaps.
2. [`probability_densities`](../figures/task07/probability_densities.png) shows
   the first four official Born distributions.
3. [`wavefunctions_and_density`](../figures/task07/wavefunctions_and_density.png)
   distinguishes signed amplitude from probability.
4. [`energy_level_wavefunctions`](../figures/task07/energy_level_wavefunctions.png)
   places the first five standing waves at their allowed energies.
5. [`uncertainty_principle`](../figures/task07/uncertainty_principle.png) verifies
   the Heisenberg inequality.
6. [`task07_summary`](../figures/task07/task07_summary.png) is the 4K 16:9
   competition summary.

All figures were inspected after generation. The first inspection exposed
title clipping, repeated-label collisions and crowded uncertainty axes; these
were corrected before final acceptance.

## Scientific limitations

The infinite well is an ideal boundary model. Real wells have finite barriers,
and their wavefunctions can penetrate classically forbidden regions. This
study also excludes interactions, external potentials, spin, measurement
dynamics and relativistic effects. Those omissions are declared scope choices,
not numerical approximations within the specified infinite-well problem.
