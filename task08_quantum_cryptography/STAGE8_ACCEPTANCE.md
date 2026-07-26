# Task 8 Stage 8 acceptance: explanation and reproducibility

Status: **PASS**

Stage 8 converts the validated calculator, study and figures into a complete
question-focused explanation and a reproducible handoff. It does not introduce a
new physical model or alter any accepted numerical output.

## Documentation delivered

- [`README.md`](README.md) gives the objective, exact equations, official answer,
  calculator instructions, quick-start command, evidence inventory, validation
  strategy and scope boundary.
- [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md) derives the
  official 37.5% and 75.0% results, derives the full signed-contrast equation,
  explains the fixed-angle sweep and two-dimensional landscape, interprets the
  finite sample, guides the reader through every publication figure and states the
  physical limitations.
- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) freezes the accepted software
  environment, generation order, validation commands, output inventory,
  determinism guarantees, browser-audit route and manual official-case check.
- [`requirements-task08.txt`](requirements-task08.txt) exactly pins NumPy,
  Matplotlib and Pillow to the accepted versions.
- [`documentation_validation.py`](documentation_validation.py) and
  [`validate_task08_documentation.py`](validate_task08_documentation.py) provide
  a machine-readable integrity gate for required files, local links, scientific
  anchors, interpretation, scope statements, commands, evidence and package pins.

## Scientific interpretation accepted

The narrative directly derives

$$
P_{\mathrm C}=\frac38=37.5\%,
\qquad
P_{\mathrm Q}=\frac34=75.0\%
$$

at \(\theta=-30^\circ\), \(\phi=+30^\circ\), and explains the complete contrast
surface through

$$
\Delta P=P_{\mathrm Q}-P_{\mathrm C}
=-\frac12\sin(2\theta)\sin(2\phi).
$$

The explanation distinguishes percentage-point difference from a potentially
undefined ratio, identifies the ±50 percentage-point extrema, explains the
relative-angle diagonal structure, and avoids treating the supplied classical
expression as every possible classical theory.

## Statistical interpretation accepted

The documentation keeps the official ideal result authoritative. The seeded
finite-photon extension is labelled optional and is interpreted as one pair of
binomial samples conditional on the exact model probabilities. Wilson intervals
are described as proportion intervals, not uncertainty in the ideal equations.
The deterministic generator is explicitly rejected for real cryptographic use.

## Reproducibility accepted

- Core, statistical and figure generation commands are complete and ordered.
- Python, JavaScript, UI, accessibility and 4K evidence commands are documented.
- Every linked local document, data file, figure and directory resolves.
- The difference between numerically deterministic outputs and platform-sensitive
  browser pixels is declared.
- No credential, secret or real cryptographic key is required or stored.

## Final Stage 8 audit

- Documentation validation: **10/10 checks passed**.
- Documentation unit tests: **3/3 passed**.
- Complete Task 8 Python suite: **54/54 tests passed**.
- End-to-end artifact validation: **8/8 groups passed**.
- Python compilation: **PASS**.
- `git diff --check`: **PASS**.
- Stage 7 scientific, statistical, browser, accessibility and figure acceptance
  remains unchanged and passing.

Stage 8 is therefore complete and suitable as the written foundation for the
final presentation package.
