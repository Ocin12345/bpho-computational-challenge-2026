# Task 8 Stage 7 acceptance: publication figures and visual evidence

Status: **PASS**

Stage 7 is accepted only for the frozen Task 8 scientific model and the separately
labelled finite-photon extension. Every plotted value is generated from validated
code; no values are manually transcribed into the figures.

## Publication figure package

The generator `python3 -m task08_quantum_cryptography.generate_task08_figures`
produces four deterministic figure pairs in `figures/task08/`:

| Figure | Purpose | PNG size | Vector companions |
|---|---|---:|---|
| `probability_sweep` | Classical and quantum mismatch over the full detector-B sweep, plus their signed contrast | 2400 × 1500 | editable SVG and PDF |
| `mismatch_landscape` | Both exact mismatch surfaces and the quantum-minus-classical surface on the full angle grid | 2400 × 1500 | editable SVG and PDF |
| `finite_photon_sampling` | Official seeded sample and Wilson-interval contraction as photon count grows | 2400 × 1500 | editable SVG and PDF |
| `task08_summary` | Four-panel presentation summary with geometry, exact sweep, contrast map and finite sample | 3840 × 2160 | editable SVG and PDF |

All PNG files carry 300 DPI metadata. The SVG/PDF outputs preserve vector text, axes,
curves, markers and annotations. Heatmap cells remain raster-efficient inside the
otherwise editable vector container. The complete twelve-file package is below the
frozen 60 MiB limit. Every label and mathematical annotation uses Times New Roman;
generation fails if the font is unavailable, an SVG records a fallback family or a
PDF lacks an embedded Type 42 Times New Roman font.
`figures/task08/manifest.json` freezes the dimensions, DPI, editable-text status,
font family and SHA-256 digest of every PNG, SVG and PDF.

## Browser evidence package

`task08_quantum_cryptography/app/tests/capture-evidence.mjs` captures the validated
local application in `figures/task08/screenshots/`:

- `detector_workspace_4k.png` — 3840 × 2160;
- `probability_chart_4k.png` — 3840 × 2160;
- `finite_photon_extension_4k.png` — 3840 × 2160;
- `finite_photon_mobile_2x.png` — 860 × 1864;
- `manifest.json` — viewport, scale, pixel dimensions, Times New Roman runtime
  font contract and SHA-256 digest for every capture.

The capture run is offline and rejects console errors, uncaught page errors,
external network requests, incorrect dimensions and page-level horizontal overflow.

## Scientific and visual checks

- The plotting pipeline refuses a failed scientific report, a failed statistical
  report, or a report whose SHA-256 study digest does not match the plotted arrays.
- The full-angle probability panels use the same explicit 0–100% scale.
- Classical and quantum curves are distinguished by both colour and solid/dashed
  line style.
- The official setting is marked consistently at θ = −30° and φ = +30°.
- The exact official values are classical 37.5%, quantum 75.0%, and quantum minus
  classical +37.5 percentage points.
- The finite example is explicitly labelled as reproducible pseudo-random sampling,
  not cryptographic randomness. It keeps exact theory, observed counts and 95%
  Wilson intervals visually distinct.
- All four publication PNGs and all four browser PNGs were inspected at original
  resolution. Titles, captions, axes, colour bars, legends, annotations and panel
  boundaries are readable without clipping or overlap.

## Final audit evidence

- Python: **54/54 tests passed**, including five deterministic plotting tests and
  three end-to-end artifact-gate tests.
- Core science: **42/42 checks passed**.
- Statistical extension: **24/24 checks passed**.
- JavaScript: **10/10 tests passed**.
- Static application validation: **PASS**.
- Browser UI smoke: **PASS**, including desktop/mobile layouts, official/aligned/
  perpendicular cases, the 361-point chart, and a 100,000-pair sample below the
  100 ms budget.
- Accessibility: **11 evidence groups passed**, with no detected WCAG 2.2 AA
  violation, no 320 px page overflow and no 200% text clipping.
- Evidence capture: **PASS**, with no console, page or external-network errors.
- End-to-end artifact gate: **8/8 groups passed**.

Stage 7 therefore meets the requested high-resolution, publication-quality and
presentation-quality standard.
