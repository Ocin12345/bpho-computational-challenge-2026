# Task 8 Reproducibility Guide

## Reproduction boundary

The accepted Task 8 package has three layers:

1. **Exact theory:** immutable Python study arrays, independent references,
   validation reports and the offline browser calculator.
2. **Optional sampling:** deterministic finite-photon fixtures and a separately
   validated Python/JavaScript statistical model.
3. **Presentation evidence:** deterministic Matplotlib PNG/SVG/PDF figures and
   browser captures produced from the accepted local app.

The exact-theory result does not depend on the optional sampler. Figure generation
requires both validation reports to pass so a failed or mismatched study cannot be
silently presented.

## Accepted software environment

- Python 3.9.6;
- NumPy 2.0.2;
- Matplotlib 3.9.4;
- Pillow 11.3.0;
- Node.js 24.11.1 for tests only;
- Playwright 1.61.1 with its compatible Chromium for browser audits only.
- Times New Roman regular, bold and italic faces for every generated visual.

Install the Python packages from the repository root:

```bash
python3 -m pip install -r task08_quantum_cryptography/requirements-task08.txt
```

The calculator itself has no Node dependency. To run the optional browser test
suite in a standard environment:

```bash
cd task08_quantum_cryptography/app
npm install --no-save playwright@1.61.1
npx playwright install chromium
```

## Deterministic generation order

Run these commands from the repository root:

```bash
python3 -m task08_quantum_cryptography.generate_task08
python3 -m task08_quantum_cryptography.generate_task08_statistics
python3 -m task08_quantum_cryptography.generate_task08_figures
```

The first command validates the complete analytical study before atomically
replacing five core files in `data/task08/`. Its manifest binds the data to the
configuration, equations, source documents, study SHA-256 digest and four content
hashes.

The second command writes the finite-photon reference fixtures, statistical
validation report and statistical manifest. The third writes four PNG/SVG/PDF
figure sets only after receiving a passing core report with the correct study digest and
a passing statistical report. It also writes `figures/task08/manifest.json`, which
records the dimensions, DPI, editable-vector status, exact font family and SHA-256
digest of all eight publication files. Figure generation stops if Times New Roman
is unavailable or if any SVG resolves to another font family.

## Independent validation

```bash
python3 -m task08_quantum_cryptography.validate_task08
python3 -m task08_quantum_cryptography.validate_task08_statistics
python3 -m task08_quantum_cryptography.validate_task08_app
python3 -m task08_quantum_cryptography.validate_task08_documentation
python3 -m task08_quantum_cryptography.validate_task08_final
python3 -m unittest discover -s task08_quantum_cryptography -p 'test_*.py' -v
python3 -m py_compile task08_quantum_cryptography/*.py
```

Accepted final baseline:

- 42/42 core scientific checks;
- 24/24 statistical checks;
- 10/10 documentation checks;
- 8/8 final artifact groups;
- 54/54 Python tests;
- static application and presentation validation pass.

The test suite includes deliberate data corruption, invalid inputs, wrong report
digests, failed reports, deterministic regeneration and forced late-transaction
rollback. A green result therefore checks rejection paths as well as nominal
calculations.

## JavaScript and browser validation

From `task08_quantum_cryptography/app/` after Playwright is available:

```bash
npm test
npm run test:ui
npm run test:a11y
npm run evidence
```

Expected results are ten JavaScript unit tests, a passing desktop/mobile UI smoke
test, eleven passing accessibility evidence groups and four browser captures.
The browser scripts reject console errors, uncaught page errors and external
network requests.

The evidence command writes:

- three 3840 × 2160 desktop captures;
- one 860 × 1864 responsive-mobile capture; and
- `figures/task08/screenshots/manifest.json`, containing the CSS viewport,
  device scale, final pixel dimensions, Times New Roman runtime-font contract
  and SHA-256 digest of every PNG.

## Output inventory and integrity

Core data:

| File | Role |
|---|---|
| `angle_sweep.csv` | 361-point fixed-θ sweep |
| `mismatch_grid.csv` | 181 × 181 two-angle study |
| `reference_cases.json` | exact named anchors |
| `validation_report.json` | machine-readable 42-check result |
| `manifest.json` | configuration, provenance and hashes |

Statistical data:

| File | Role |
|---|---|
| `finite_photon_reference.json` | fixed cross-language simulation fixtures |
| `statistical_validation_report.json` | machine-readable 24-check result |
| `statistics_manifest.json` | statistical provenance and hashes |

Figures:

| Base name | PNG | SVG | PDF |
|---|---:|---:|---:|
| `probability_sweep` | 2400 × 1500, 300 DPI | editable vector | editable, embedded Type 42 font |
| `mismatch_landscape` | 2400 × 1500, 300 DPI | vector labels with embedded heatmaps | editable, embedded Type 42 font |
| `finite_photon_sampling` | 2400 × 1500, 300 DPI | editable vector | editable, embedded Type 42 font |
| `task08_summary` | 3840 × 2160, 300 DPI | editable vector | editable, embedded Type 42 font |

PNG dimensions, DPI metadata, SVG roots, filename order and the 60 MiB package
budget are checked during generation and by `test_plotting.py`. All figure text,
including mathematical labels, is rendered in Times New Roman. The generated
`figures/task08/manifest.json` binds every PNG/SVG/PDF representation to its
accepted digest, records that SVG and PDF text remain editable, and verifies that
each PDF embeds Times New Roman as TrueType Type 42 rather than outlining glyphs.

## Determinism details

- Study grids, ordering, schemas, tolerances and output dimensions are frozen in
  `configuration.py`.
- Floating-point CSV values use 17 significant digits.
- JSON forbids non-finite values.
- Arrays become read-only after construction.
- Matplotlib uses a frozen style and SVG hash salt; generated SVG metadata omits
  the current date. The generator and manifest independently reject font fallback
  from Times New Roman.
- The finite sampler uses a frozen 32-bit Mulberry32 sequence and two fixed stream
  salts. Identical angles, \(N\) and seed reproduce identical Python and JavaScript
  counts.
- Browser capture pixels can vary across operating systems, fonts or Chromium
  versions. The accepted browser app explicitly uses Times New Roman, and the live
  UI and evidence scripts verify the computed font before accepting a capture. The
  manifest identifies the accepted capture; the underlying numerical assertions
  are platform-independent.

## Local application check

```bash
python3 -m task08_quantum_cryptography.serve_task08
```

Open [http://127.0.0.1:4178/](http://127.0.0.1:4178/), select the official preset
and confirm:

- detector A: −30°;
- detector B: +30°;
- classical mismatch: 37.5%;
- quantum mismatch: 75.0%;
- signed difference: +37.5 percentage points;
- default finite sample: 363 and 770 mismatches from 1,000 pairs at seed 2026.

The final line is a reproducible demonstration, not an additional official answer.

## Audit trail

- Official scope: [`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md)
- Frozen physics: [`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md)
- Sampling specification: [`STATISTICAL_EXTENSION.md`](STATISTICAL_EXTENSION.md)
- Figure acceptance: [`STAGE7_ACCEPTANCE.md`](STAGE7_ACCEPTANCE.md)
- Results narrative: [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md)
- Presentation acceptance: [`presentation/task08/STAGE9_ACCEPTANCE.md`](../presentation/task08/STAGE9_ACCEPTANCE.md)
- Final acceptance: [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md)

No secret, credential or real cryptographic key is used or stored anywhere in the
Task 8 package.
