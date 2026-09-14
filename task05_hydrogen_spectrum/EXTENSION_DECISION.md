# Task 5 Optional-Extension Decision

## Decision

Accept a separate ideal-versus-reduced-mass wavelength comparison. Do not add
a classical electron-orbit animation.

The accepted stationary-nucleus calculation remains the authoritative Task 5
competition baseline. The extension is an optional precision lab after the
baseline evidence and uses its own schema, validation report, CSV, interface,
and interpretation boundary.

## Physical refinement

For a nucleus of mass $M$, the electron mass is replaced by the reduced mass

$$
\mu=\frac{m_eM}{m_e+M}.
$$

For protium, using the 2022 CODATA electron-proton mass ratio,

$$
\frac{\mu}{m_e}=\frac{1}{1+m_e/m_p},
\qquad
\lambda_H=\lambda_\infty\left(1+\frac{m_e}{m_p}\right).
$$

The extension therefore lowers every ideal transition energy and frequency by
$\mu/m_e$ and lengthens every wavelength by the same relative fraction,
$m_e/m_p=5.446170214889\times10^{-4}$. The constant comes from the
[NIST 2022 CODATA recommended values](https://physics.nist.gov/cuu/pdf/wall_2022.pdf).

## Accepted evidence

- all 45 baseline transitions are corrected without changing the baseline;
- 12/12 independent structural, scaling, identity, and Decimal-anchor checks
  pass;
- H-$\alpha$ changes from $656.112276$ nm to $656.469606$ nm in this model;
- CSV and JSON evidence regenerate byte-for-byte; and
- the browser lab passes desktop and mobile interaction, overflow, console,
  label, caption, and accessible-description checks.

Regenerate and test with:

```bash
python3 -m task05_hydrogen_spectrum.generate_reduced_mass_extension
python3 -m unittest task05_hydrogen_spectrum.test_reduced_mass_extension -v
node site/validate-task-05.mjs
```

## Interpretation boundary

The reduced-mass extension is not a precision fit to measured hydrogen. It
does not model intensity, transition probability, linewidth, fine or hyperfine
structure, Lamb shifts, fields, or broadening. Equal-height markers show
wavelength position only.

An electron energy eigenstate is also not a small planet following a resolved
trajectory. A decorative orbital animation would make the model less honest,
so it remains excluded.
