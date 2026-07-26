# Task 10 Reproducibility Guide

## Reproduction boundary

The accepted Task 10 package has four linked layers:

1. **Scientific core:** normalized radial and real-angular functions, independent
   references, 204 supported states and deterministic data exports.
2. **Static evidence:** a complete 25-state gallery, radial diagnostics, required
   coloured glass, renderer comparison and 4K summary.
3. **Interactive explorer:** the same frozen equations in dependency-free browser
   JavaScript with cross-language and real-browser acceptance.
4. **Motion evidence:** an 80-frame 4K animated WebP, reduced-motion poster,
   decoded-frame inspection sheet and integrity manifest.

Figures and motion require a passing report whose state digest matches the
current scientific implementation. Failed or mismatched physics cannot be
silently presented.

## Accepted software environment

- Python 3.9.6;
- NumPy 2.0.2;
- Matplotlib 3.9.4;
- Pillow 11.3.0 with animated-WebP support;
- Node.js 24.14.0 for tests only; and
- Playwright 1.61.1 with compatible Chromium for browser audits only.

Install Python packages from the repository root:

```bash
python3 -m pip install -r task10_hydrogenic_orbitals/requirements-task10.txt
```

The explorer itself has no Node dependency. For optional browser testing in a
standard environment:

```bash
cd task10_hydrogenic_orbitals/app
npm install --no-save playwright@1.61.1
npx playwright install chromium
```

## Deterministic generation order

Run from the repository root:

```bash
python3 -m task10_hydrogenic_orbitals.generate_task10
python3 -m task10_hydrogenic_orbitals.generate_task10_figures
python3 -m task10_hydrogenic_orbitals.generate_task10_motion
```

The data generator runs all 22 science groups before atomically replacing the
seven files in `data/task10/`. CSV floats use 17 significant digits and JSON
forbids non-finite values. The manifest records configuration, constants,
source provenance, the scientific-state digest and content hashes.

The figure generator refuses to run unless the stored data report and manifest
match the current passing state. It writes five PNG graphics plus four editable
SVG and four embedded-font PDF companions, then records all thirteen hashes in
`figures/task10/manifest.json`.

The motion generator validates science again, streams one 4K RGB frame at a time
to avoid retaining the complete sequence in memory, then atomically commits the
WebP and poster. It decodes every frame to verify dimensions and exact timing,
samples five views for integrity, creates the offline/reduced-motion viewer and
writes `figures/task10/motion_manifest.json`.

## Independent validation

```bash
python3 -m task10_hydrogenic_orbitals.validate_task10
python3 -m task10_hydrogenic_orbitals.validate_task10_app
python3 -m task10_hydrogenic_orbitals.validate_task10_motion
python3 -m task10_hydrogenic_orbitals.validate_task10_documentation
python3 -m task10_hydrogenic_orbitals.validate_task10_final
python3 -m unittest discover -s task10_hydrogenic_orbitals -p 'test_*.py' -v
python3 -m py_compile task10_hydrogenic_orbitals/*.py
```

Accepted Stage 8 baseline:

- 22/22 independent science checks;
- 42/42 Python tests before motion/documentation integration;
- 6/6 JavaScript scientific tests;
- 23/23 static/offline app checks;
- all 25 official presets and five responsive widths in Chromium;
- 13/13 accessibility/performance evidence groups;
- 3840×2160, 80-frame motion validation; and
- deterministic small-WebP regeneration tests.

The scientific suite deliberately tests invalid quantum numbers, corrupted
digests, failed reports, non-finite inputs, immutable results, deterministic
regeneration and transactional rollback.

## JavaScript and browser validation

From `task10_hydrogenic_orbitals/app/` after Playwright is available:

```bash
npm test
npm run test:ui
npm run test:a11y
npm run test:motion
```

The numerical suite compares all 204 Python state summaries with JavaScript and
checks every distinct radial normalization. The UI suite exercises all 25
official presets, renderer controls, mouse and keyboard camera operation and
320, 390, 740, 1050 and 1440 px layouts. The accessibility audit covers semantic
exposure, Canvas fallbacks, focus order, contrast, live status, 320 px reflow,
200% text, forced colours, reduced motion, the full validated endpoint and
retained heap. The motion browser test loads the 4K WebP, decoded inspection
frames and reduced-motion poster with no remote requests.

## Output inventory and integrity

Data:

| File | Role |
|---|---|
| `orbital_state_catalog.csv` | all 204 real states through \(n=8\) |
| `official_gallery.csv` | exact 25-state S–G gallery |
| `radial_profiles.csv` | five normalized family profiles |
| `radial_nodes.csv` | independently derived positive radial roots |
| `reference_anchors.json` | analytic values and coordinate convention |
| `validation_report.json` | machine-readable 22-check report |
| `manifest.json` | provenance, configuration, schema and hashes |

Static media:

| Base name | PNG | Companion |
|---|---:|---|
| `required_orbital_gallery` | 3840×2400, 300 DPI | editable SVG + embedded-font PDF |
| `radial_and_nodal_structure` | 2400×1500, 300 DPI | editable SVG + embedded-font PDF |
| `coloured_glass_density` | 3000×1875, 300 DPI | raster only |
| `rendering_comparison` | 3000×1800, 300 DPI | editable SVG + embedded-font PDF |
| `task10_summary` | 3840×2160, 300 DPI | editable SVG + embedded-font PDF |

Motion media:

| File | Accepted property |
|---|---|
| `orbital_view_rotation.webp` | 3840×2160, 80 frames, 20 fps, 4 s loop |
| `orbital_view_rotation_poster.png` | 3840×2160, 240 DPI |
| `orbital_view_rotation_viewer.html` | offline and reduced-motion aware |
| `orbital_view_rotation_contact_sheet.png` | five decoded viewpoints |

Both media manifests store SHA-256 hashes. The accepted scientific-state digest
is `d298695290395956560641493fc603e5970a4ea01609eca677b3b4b683fa085e`.

## Determinism details

- Quantum domains, CODATA constants, tolerances, sampling grids and rendering
  dimensions are frozen in source.
- Production arrays become read-only before leaving their constructors.
- CSV uses stable ordering and 17 significant digits; JSON is key-sorted and
  rejects NaN/Infinity.
- Matplotlib requires Times New Roman, uses a frozen style and fixed SVG hash
  salt, and refuses silent font fallback. SVG and PDF metadata omit the current
  date; PDFs embed the TrueType font and SVG text stays editable.
- The explorer, motion viewer and PowerPoint theme also use Times New Roman;
  browser and PowerPoint validators confirm the effective family.
- PNG dimensions and DPI are checked after generation.
- The animated WebP uses opaque full RGB frames, an exact 50 ms duration, a
  continuous-loop flag and deterministic XMP title/interpretation metadata.
- The camera path excludes its endpoint, preventing a duplicated pause frame.
- Local Canvas rasterization can differ slightly across browser versions, but
  numerical assertions and generated publication media are browser-independent.

## Local application check

```bash
python3 -m task10_hydrogenic_orbitals.serve_task10
```

Open [http://127.0.0.1:4210/](http://127.0.0.1:4210/) and confirm the default
hydrogen 3d, \(m=0\) state:

- energy: −1.510915 eV;
- effective Bohr length: 0.529468 Å;
- nodes: 0 radial and 2 angular;
- parity: even;
- \(m\) degeneracy: fivefold; and
- renderer: 17 planes, cutoff 0.15, maximum opacity 72%.

Orbit the camera and confirm the state values do not change. Then choose C-12
and confirm −54.420285 eV and 0.088200 Å.

## Audit trail

- Official scope: [OFFICIAL_REQUIREMENTS.md](OFFICIAL_REQUIREMENTS.md)
- Frozen physics: [MATHEMATICAL_MODEL.md](MATHEMATICAL_MODEL.md)
- Scientific stages: [STAGE1_ACCEPTANCE.md](STAGE1_ACCEPTANCE.md),
  [STAGE2_ACCEPTANCE.md](STAGE2_ACCEPTANCE.md) and
  [STAGE3_ACCEPTANCE.md](STAGE3_ACCEPTANCE.md)
- Data acceptance: [STAGE4_ACCEPTANCE.md](STAGE4_ACCEPTANCE.md)
- Figure acceptance: [STAGE5_ACCEPTANCE.md](STAGE5_ACCEPTANCE.md)
- Explorer acceptance: [STAGE6_ACCEPTANCE.md](STAGE6_ACCEPTANCE.md)
- Accessibility audit: [ACCESSIBILITY_AUDIT.md](ACCESSIBILITY_AUDIT.md)
- Browser acceptance: [STAGE7_ACCEPTANCE.md](STAGE7_ACCEPTANCE.md)
- Motion acceptance: [STAGE8_ACCEPTANCE.md](STAGE8_ACCEPTANCE.md)
- Results narrative: [RESULTS_AND_INTERPRETATION.md](RESULTS_AND_INTERPRETATION.md)
- Final repository audit: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md)

No secret, account credential or external submission is used or stored.
