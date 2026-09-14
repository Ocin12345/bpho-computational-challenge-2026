# Task 6 Optional-Extension Decision

## Post-baseline update — 2026-08-08

The required baseline has now passed its full acceptance gate, so the preferred
precision extension described below has been implemented as a separate,
secondary comparison.  The official non-relativistic model and its 39 checks
are unchanged.

The extension compares

$$
\lambda_{\mathrm{nr}}=\frac{h}{\sqrt{2m_{\mathrm e}eV}}
\quad\text{with}\quad
\lambda_{\mathrm{rel}}
=\frac{hc}{\sqrt{eV(eV+2m_{\mathrm e}c^2)}},
$$

then carries both wavelengths through the same exact Bragg and
$x=r\sin(2\phi)$ screen geometry.  It contains 401 records, passes 10 focused
checks, and reports the first-order inward ring shift for both graphite
spacings.  Automatic animation remains deferred because it would not add
validated physics.

Generate the extension evidence with:

```bash
python3 -m task06_electron_diffraction.generate_relativistic_extension
```

The original decision below is retained as the pre-extension scope record.

## Decision

Do not add an animation or relativistic correction to the authoritative Task
6 competition slide before the required baseline is accepted.

## Reason

The completed baseline already shows the voltage dependence in three
complementary ways: a 1, 3, and 5 kV ring comparison, continuous exact
radius-versus-voltage tracks, and a wavelength/order diagnostic. The mandatory
straight-line recovery of both graphite spacings remains the strongest
quantitative evidence for a short competition presentation.

A voltage-sweep animation could be visually attractive, but its ring
brightness would remain schematic and it would add file and narration cost
without another validated result. The static three-voltage comparison also
survives pausing, screenshots, PDF export, and a fast three-minute screencast
more reliably.

The relativistic wavelength is scientifically legitimate:

$$
\lambda_{\mathrm{rel}}
=\frac{hc}{\sqrt{eV(eV+2m_{\mathrm e}c^2)}}.
$$

It differs from the official non-relativistic value by approximately
$-0.049\%$ at 1 kV and $-0.244\%$ at 5 kV. That is useful in a longer
precision discussion, but placing both wavelength conventions on the main
slide would require extra explanation and weaken alignment with the official
derivation.

## Reconsider only if

An extension may be added later if Task 6 receives a longer standalone
presentation and the validated baseline remains unchanged. The preferred
extension would be a separate, clearly labelled non-relativistic versus
relativistic radius comparison before any decorative animation.

Any later extension must:

- preserve the non-relativistic results as the official baseline;
- use a separate configuration, validation, and output schema;
- avoid implying calibrated intensity or experimentally observed orders;
- keep the exact $x=r\sin(2\phi)$ geometry; and
- remain visually secondary to the required straight-line graph.
