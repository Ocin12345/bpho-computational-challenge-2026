# Task 6 Final Acceptance

## Decision

The Task 6 electron-diffraction baseline is accepted as complete for local
competition use.

The official model, complete numerical evidence, independent validation,
high-resolution figure package, scientific interpretation, optional-extension
decision, and one-slide presentation are all present and reproducible. Git
commit and remote synchronization remain a separate user-controlled hand-off;
they were not performed as part of this acceptance run.

## Official-scope acceptance

- [x] Voltage spans the complete 1--5 kV interval.
- [x] Both nominal graphite spacings, 0.123 and 0.213 nm, are modelled.
- [x] The tube radius is 65 mm.
- [x] The non-relativistic de Broglie wavelength matches the official slides.
- [x] Bragg's law and $\phi=2\theta$ are implemented directly.
- [x] The photographic geometry is $x=r\sin(2\phi)$.
- [x] The separate caliper relation $y=2r\sin\phi$ is not substituted for
  $x$.
- [x] Maximum possible Bragg orders are calculated.
- [x] Forward-screen orders are separately classified and explained.
- [x] The required $1/\sqrt V$ versus $\sin(\phi/2)$ graph is generated.
- [x] Both fitted gradients recover their nominal atomic spacings.

## Numerical acceptance

The authoritative study contains:

- 401 voltage values in exact 10 V increments;
- 11,386 Bragg-allowed order records;
- 7,927 forward-screen order records;
- 4,113 normalized $d_1$ fit records;
- 7,273 normalized $d_2$ fit records; and
- 39 passing independent validation checks.

The frozen endpoint results include:

| Quantity | 1 kV | 5 kV |
| --- | ---: | ---: |
| Electron wavelength | 38.782994320 pm | 17.344282334 pm |
| $d_1$ first-order radius | 38.465414872 mm | 18.103939862 mm |
| $d_2$ first-order radius | 23.181331826 mm | 10.541869105 mm |
| $d_1$ Bragg / screen maximum | 6 / 4 | 14 / 10 |
| $d_2$ Bragg / screen maximum | 10 / 7 | 24 / 17 |

The constrained first-order gradients are
$0.200582837411736\ \mathrm{V^{-1/2}}$ and
$0.347350767225202\ \mathrm{V^{-1/2}}$. They recover 0.123000000 nm and
0.213000000 nm with $R^2=1$ to displayed precision.

## Evidence acceptance

The transactionally generated data package contains:

- `voltage_sweep.csv`;
- `diffraction_orders.csv`;
- `validation_fits.csv`;
- `reference_anchors.json`;
- `validation_report.json`; and
- `manifest.json` with SHA-256 hashes for every other data and figure file.

All CSV row counts, column order, JSON finiteness, manifest hashes, and output
size budgets are checked before destination files are replaced. A forced late
replacement failure restores every pre-existing file.

## Figure acceptance

Six figure families are accepted in matched PNG and SVG forms:

1. forward-screen rings at 1, 3, and 5 kV;
2. exact projected ring radius versus voltage;
3. the official first-order straight-line validation;
4. normalized all-order collapse;
5. wavelength and maximum-order diagnostics; and
6. a 4K 16:9 Task 6 summary.

The first five PNGs are 2400 by 1500 pixels. The summary is 3840 by 2160
pixels. The review checked titles, axes, units, legends, fit labels, ring-family
encoding, caption accuracy, clipping, collision, and thumbnail/slide clarity.

The first visual pass found clipped or colliding headings in three figures.
Those layouts were corrected, regenerated, and reinspected. The accepted
figures clearly state that ring brightness and width are schematic rather than
predicted intensity.

## Presentation acceptance

The final presentation package contains:

- one editable 16:9 PowerPoint slide;
- the official validation graph as the dominant visual;
- the three-voltage ring model as supporting evidence;
- equations, recovered spacings, and a 39/39 badge;
- meaningful alternative text for both embedded images;
- a 50-word approximately 18-second script in both Markdown and speaker
  notes; and
- a 2401 by 1350 rendered preview.

The structural validator confirms one slide, one notes page, two byte-identical
validated images, reproducible creation/modification metadata, portable XML,
working local links, and 16:9 preview geometry. The rendered preview was then
visually inspected at original resolution.

## Commands and final observed results

```bash
python3 -m task06_electron_diffraction.generate_task06
```

Observed: 6 data files and 12 figure files generated; 39/39 validation checks
passed.

```bash
python3 -m task06_electron_diffraction.validate_task06
```

Observed: 39/39 independent checks passed.

```bash
python3 -m unittest discover -s task06_electron_diffraction -p 'test_*.py' -q
```

Observed: 29 tests passed, including invalid inputs, corruption detection,
byte reproducibility, figure shape checks, and transaction rollback.

```bash
python3 presentation/task06/validate_task06_presentation.py
```

Observed: presentation validation passed with one slide, two embedded visuals,
a 50-word script, and a 2401 by 1350 preview.

## Scientific boundary

The accepted model predicts ideal geometric ring positions and order domains.
It does not claim quantitative intensity, experimental visibility, graphite
structure factors, broadening, beam imperfections, detector response, or
relativistic precision. Those exclusions are explicit in the slide pack and
scientific report.

The optional animation and relativistic comparison are deferred. This keeps
the required graph, exact geometry, and recovered spacings central to the
three-minute competition submission.
