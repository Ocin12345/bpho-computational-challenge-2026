# Task 9 Reproducibility Guide

## Reproduction boundary

The accepted Task 9 package has four layers:

1. **Required kinematics:** immutable Python arrays, an independent scalar
   reference, conservation tests and deterministic data exports.
2. **Optional angular weighting:** a separately labelled and validated
   Klein–Nishina study.
3. **Interactive explorer:** the same equations implemented in dependency-free
   browser JavaScript and checked against every Python row.
4. **Presentation media:** deterministic 300 DPI/vector figures, a 4K summary and
   a full-frame GIF animation.

Figures require matching passing core and extension reports. The animation
requires a matching passing core report. A mismatched or failed study therefore
cannot be silently presented.

## Accepted software environment

- Python 3.9.6;
- NumPy 2.0.2;
- Matplotlib 3.9.4;
- Pillow 11.3.0;
- Node.js 24.11.1 for tests only; and
- Playwright 1.61.1 with compatible Chromium for browser audits only.

Install the Python packages from the repository root:

```bash
python3 -m pip install -r task09_compton_scattering/requirements-task09.txt
```

The explorer itself has no Node dependency. In a standard environment, install
the optional browser-test tooling with:

```bash
cd task09_compton_scattering/app
npm install --no-save playwright@1.61.1
npx playwright install chromium
```

## Deterministic generation order

Run from the repository root:

```bash
python3 -m task09_compton_scattering.generate_task09
python3 -m task09_compton_scattering.generate_task09_cross_section
python3 -m task09_compton_scattering.generate_task09_figures
python3 -m task09_compton_scattering.animation
python3 -m task09_compton_scattering.generate_task09_media_manifest
```

The first command validates the 3605-state official study before atomically
replacing the five core files in `data/task09/`. The second produces the four
separate extension files. Each data manifest records a reproducible placeholder
timestamp, source links, configuration, study digest and content hashes.

The figure generator writes four PNG/SVG/PDF sets only after both reports pass,
match their studies and the required Times New Roman font is available. The
animation uses the same strict font contract and writes 73 opaque RGB frames
atomically. The final command hashes all 13 media files into
`figures/task09/manifest.json`.

## Independent validation

```bash
python3 -m task09_compton_scattering.validate_task09
python3 -m task09_compton_scattering.validate_task09_cross_section
python3 -m task09_compton_scattering.validate_task09_app
python3 -m task09_compton_scattering.validate_task09_documentation
python3 -m task09_compton_scattering.validate_task09_final
python3 -m unittest discover -s task09_compton_scattering -p 'test_*.py' -v
python3 -m py_compile task09_compton_scattering/*.py
```

Accepted Stage 8 baseline:

- 44/44 kinematic checks;
- 30/30 Klein–Nishina checks;
- 21/21 static/offline/typography app checks;
- 11/11 documentation checks;
- 8/8 final artifact groups;
- 49/49 Python tests; and
- deterministic figure and small-animation regeneration tests.

The suite includes deliberate scientific corruption, invalid inputs, wrong study
digests, failed reports, deterministic regeneration and transactional rollback.

## JavaScript and browser validation

From `task09_compton_scattering/app/` after Playwright is available:

```bash
npm test
npm run test:ui
npm run test:a11y
```

Expected results are five cross-language numerical tests, a passing UI smoke test
and ten passing accessibility evidence groups. The UI test checks exact default,
forward, backscatter and custom-energy states, five responsive breakpoints, no
external requests and a maximum update below 100 ms. The accessibility audit
covers the Chromium accessibility tree, keyboard order, focus, contrast,
colour-independent curve styles, 320 px reflow, 200% text size, reduced motion
and forced colours.

## Output inventory and integrity

Core data:

| File | Role |
|---|---|
| `compton_angle_study.csv` | 5 × 721 exact kinematic states |
| `energy_summary.csv` | official-energy endpoint summary |
| `reference_anchors.json` | independent forward, 90° and backscatter anchors |
| `validation_report.json` | machine-readable 44-check result |
| `manifest.json` | configuration, constants, provenance and hashes |

Extension data:

| File | Role |
|---|---|
| `klein_nishina_study.csv` | 5 × 721 differential and normalized values |
| `klein_nishina_summary.csv` | total cross-section anchors |
| `cross_section_validation_report.json` | machine-readable 30-check result |
| `cross_section_manifest.json` | extension provenance and hashes |

Media:

| Base name | PNG | SVG | PDF / motion |
|---|---:|---:|---:|
| `required_kinematics` | 2400 × 1500, 300 DPI | editable vector | embedded-font PDF |
| `energy_transfer_geometry` | 2400 × 1500, 300 DPI | editable vector | embedded-font PDF |
| `klein_nishina_extension` | 2400 × 1500, 300 DPI | editable vector | embedded-font PDF |
| `task09_summary` | 3840 × 2160, 300 DPI | editable vector | embedded-font PDF |
| `compton_angle_sweep` | — | — | 1600 × 900 GIF, 73 frames |

PNG dimensions and DPI metadata, SVG roots and exact font families, PDF embedded
font type, animation dimensions, frame count, continuous loop, black-disposal
artifact threshold and size budgets are checked during generation. The media
manifest records SHA-256 hashes for all 13 files.

## Determinism details

- Energies, angle grid, schemas, tolerances and output dimensions are frozen in
  `configuration.py`.
- Arrays become read-only after construction.
- Floating-point CSV values use 17 significant digits; JSON forbids non-finite
  values.
- Matplotlib uses a frozen Times New Roman style, custom matching mathematical
  text, Type 42 PDF embedding and SVG hash salt; SVG/PDF metadata omit the
  current date.
- The GIF stores full opaque RGB frames with disposal mode 1 and optimization
  disabled, avoiding browser-dependent delta-clearing artifacts.
- Local browser rendering can vary slightly with Chromium versions, but the app
  and browser audit require Times New Roman and every numerical assertion is
  platform-independent.

## Local application check

```bash
python3 -m task09_compton_scattering.serve_task09
```

Open [http://127.0.0.1:4209/](http://127.0.0.1:4209/) and confirm the default
200 keV, 90° state:

- fractional wavelength shift: 0.39139;
- electron recoil speed: 0.43419 c;
- electron recoil angle: 35.71°;
- scattered photon: 143.741 keV;
- electron kinetic energy: 56.259 keV; and
- Klein–Nishina total cross-section: 0.4065 barn.

Then select 0° and confirm that the electron direction is reported as undefined,
not as a physical 90° recoil.

## Presentation package

```bash
cd presentation/task09
npm ci
npm run build
npm run preview
npm run validate
```

The slide generator copies the accepted figures and animation, embeds the 4K
summary unchanged, adds image alternative text and the final speaker script, and
writes reproducible PowerPoint metadata. The preview command uses LibreOffice and
Poppler to create the inspected 300-DPI 16:9 render.

## Audit trail

- Official scope: [`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md)
- Frozen physics: [`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md)
- Extension decision: [`EXTENSION_DECISION.md`](EXTENSION_DECISION.md)
- Explorer acceptance: [`STAGE6_ACCEPTANCE.md`](STAGE6_ACCEPTANCE.md)
- Accessibility audit: [`ACCESSIBILITY_AUDIT.md`](ACCESSIBILITY_AUDIT.md)
- Browser acceptance: [`STAGE7_ACCEPTANCE.md`](STAGE7_ACCEPTANCE.md)
- Media acceptance: [`STAGE8_ACCEPTANCE.md`](STAGE8_ACCEPTANCE.md)
- Results narrative: [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md)
- Documentation acceptance: [`STAGE9_ACCEPTANCE.md`](STAGE9_ACCEPTANCE.md)
- Presentation acceptance: [`../presentation/task09/STAGE10_ACCEPTANCE.md`](../presentation/task09/STAGE10_ACCEPTANCE.md)
- Final acceptance: [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md)

No secret, account credential or external submission is used or stored.
