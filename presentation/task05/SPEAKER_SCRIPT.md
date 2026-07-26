# Task 5 Speaker Script

## Final competition version

> Task 5 uses ten ideal Bohr energy levels to calculate all forty-five
> downward level pairs. Each emitted photon follows E equals h c over lambda,
> but only discrete wavelengths occur. The Balmer series crosses visible
> light, including ideal H-alpha at 656 nanometres. All thirty independent
> checks pass.

### Visual cues

- **0--7 seconds:** follow the Lyman-to-infrared points across the main graph.
- **7--13 seconds:** point to the Balmer line spectrum and H-$\alpha$ result.
- **13--18 seconds:** finish on the equations and 30/30 badge.

## Expanded 35-second version

> Task 5 uses the stationary-nucleus Bohr equation for the first ten hydrogen
> levels. Every downward level pair gives a positive photon energy, producing
> forty-five discrete points. All points obey E equals h c over lambda, but the
> integer energy levels mean hydrogen does not emit a continuous spectrum.
> The Balmer series crosses visible light, with ideal H-alpha at 656.1
> nanometres, while its higher lines crowd toward a 364.5-nanometre ultraviolet
> limit. Independent energy, Rydberg-wavelength, frequency, named-line, and
> convergence checks all pass.

## Rehearsal explanation

The level energy is negative because a bound electron needs energy to reach
the zero-energy ionization limit. During emission the atom moves to a more
negative level, so the photon receives the positive energy lost by the atom.

The graph uses all level pairs $1\leq n_f<n_i\leq10$. Its 45 markers are
complete for that declared finite catalogue. They lie on the inverse photon
relation $E_\gamma=hc/\lambda$, but only at wavelengths selected by integer
level differences. The hollow diamonds show analytical
$n_i\rightarrow\infty$ limits and are not finite lines.

Seven declared pairs fall in the chosen 380--750 nanometre visible band. They
are Balmer transitions from $n_i=3$ through 9 to $n_f=2$. The $10\rightarrow2$
line is about 379.7 nanometres, just outside the declared boundary.

The spectrum uses equal line heights only to show positions. This model does
not calculate transition probability, intensity, degeneracy, selection rules,
or linewidth. It also uses the infinite-nuclear-mass Rydberg constant, so
precision measured hydrogen wavelengths differ slightly.

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| Bohr | “bore” |
| Balmer | “BALL-mer” |
| Lyman | “LIE-man” |
| Paschen | “PASH-en” |
| H-$\alpha$ | “H alpha” |
| $E_\gamma$ | “photon energy” or “E gamma” |
| $hc/\lambda$ | “h c over lambda” |
| $656\ \mathrm{nm}$ | “six hundred and fifty-six nanometres” |

## Questions you should be ready to answer

**Why is the electron energy negative?**

Zero is the ionization limit. A bound state has less energy than a separated
electron and proton, so its energy is negative relative to that reference.

**Why is emitted photon energy positive?**

For $n_i>n_f$, the final atomic energy is more negative. The positive energy
lost by the atom is $E_{n_i}-E_{n_f}$ and is carried by the photon.

**Why use a logarithmic wavelength axis?**

The finite catalogue spans roughly 92 nanometres to 38.8 micrometres. A linear
axis would compress most ultraviolet and visible points into a tiny area.

**Do all 45 level pairs produce equally strong measured lines?**

No. The finite catalogue enumerates energy differences only. Line strength and
observability require transition probabilities, degeneracies, selection rules,
populations, and experimental conditions, none of which are modelled.

**What are the hollow diamonds?**

They are analytical series limits for $n_i\rightarrow\infty$. They show where
the lines converge and are not additional finite transitions.

**Why is ideal H-alpha 656.1 nanometres rather than a slightly different
measured value?**

The official model uses the stationary-nucleus Bohr equation with $R_\infty$.
Real hydrogen has finite proton mass and further corrections. The slide labels
the number as ideal to keep that convention explicit.

**How was the calculation checked?**

Thirty pre-declared checks compare the immutable NumPy result with independent
Decimal and Rydberg calculations. They cover constants, all levels and pairs,
energy differences, photon identities, wavelengths, frequencies, named lines,
series limits, ordering, labels, regions, and convergence.
