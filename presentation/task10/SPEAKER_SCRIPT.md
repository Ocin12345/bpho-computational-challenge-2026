# Task 10 Speaker Script

## Final competition version

> Task 10 constructs normalized hydrogenic orbitals from S through G. The
> gallery contains twenty-five real states, while coloured-glass slices reveal
> three-dimensional density and nodes. Energy scales as Z squared over n
> squared, and size as one over Z. View rotation is camera motion, not electron
> motion; all twenty-two checks pass.

### Visual cues

- **0–5 seconds:** show the coloured-glass density and node result cards.
- **5–10 seconds:** follow the S-through-G progression and 25-state gallery.
- **10–15 seconds:** point to radial structure and the $Z$-scaling statements.
- **15–18 seconds:** finish on the validation totals and camera-motion caveat.

## Expanded 35-second version

> Task 10 evaluates normalized hydrogenic radial functions and spherical
> harmonics to construct real S-through-G orbitals. The 25-state gallery makes
> the angular families visible, while the coloured-glass slices expose the
> three-dimensional probability density and nodal surfaces without changing
> the density threshold. Energies scale exactly as minus $Z^2/n^2$, while
> orbital size scales as $1/Z$. Across the accepted domain, normalization,
> nodes, energy, size and reference values pass all 22 checks covering 204
> states.

## Rehearsal explanation

The separated hydrogenic wavefunction is

$$
\psi_{nlm}(r,\theta,\phi)=R_{nl}(r)Y_l^m(\theta,\phi),
$$

with probability density $|\psi_{nlm}|^2$. The energy depends only on $n$ and
$Z$,

$$
E_n=-13.5984346\ \mathrm{eV}\,\frac{Z^2}{n^2}.
$$

The displayed S, P, D, F and G families correspond to $l=0,1,2,3,4$. A state
has $n-l-1$ radial nodes and $l$ angular nodes. The coloured-glass view samples
the same normalized density on parallel planes; its threshold controls visual
opacity and does not alter the computed probability.

## Pronunciation guide

| Term | Say it as |
|---|---|
| hydrogenic | “high-dro-JEN-ick” |
| orbital | “OR-bit-al” |
| angstrom | “ANG-strum” |
| spherical harmonic | “SFEH-ri-cal har-MON-ic” |
| $\psi$ | “sigh” |

## Questions you should be ready to answer

**Why are there 25 displayed states?**

The five families include all real display orientations for $l=0$ through
$l=4$: 1, 3, 5, 7 and 9 states, which total 25.

**What does the transparency threshold do?**

It changes only how strongly low-density samples are drawn. It neither removes
probability from the calculation nor renormalizes the wavefunction.

**Is the rotating orbital showing electron motion?**

No. It rotates the camera around a stationary probability distribution. A
hydrogenic energy eigenstate changes only by a global phase in time, leaving
$|\psi|^2$ unchanged.

**Why does increasing $Z$ shrink the orbital?**

The stronger Coulomb attraction rescales the characteristic radial length as
$a_0/Z$, while the binding energy magnitude grows as $Z^2$.

**What is outside this model?**

It is a one-electron Coulomb model. Electron-electron interactions, screening,
fine structure, external fields and measurement dynamics are not included.
