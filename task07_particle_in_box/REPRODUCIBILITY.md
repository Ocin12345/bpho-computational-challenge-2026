# Task 7 Reproducibility Guide

## Reproduction boundary

The accepted Task 7 package has four linked layers:

1. **Analytical model:** normalized infinite-well eigenstates, discrete energies,
   moments and uncertainty products.
2. **Independent numerical check:** a tridiagonal finite-difference Hamiltonian
   evaluated on five grid refinements without inserting the analytical spectrum.
3. **Evidence package:** deterministic CSV/JSON data and six high-resolution
   PNG/SVG figure pairs bound by SHA-256 hashes.
4. **Report and presentation:** an editable LaTeX report, an accessible Markdown
   companion, a four-page PDF and a reproducible one-slide PowerPoint.

Figures are rendered only from a study with a matching passing 50-check report.
Generation validates the complete temporary package before replacing accepted
outputs, and a failed late replacement restores the previous files.

## Accepted software environment

- Python 3.9.6;
- NumPy 2.0.2;
- SciPy 1.13.1;
- Matplotlib 3.9.4;
- Pillow 11.3.0;
- Times New Roman regular, bold, italic and bold-italic fonts;
- Node.js 24.11.1 and npm 11.6.2 for PowerPoint generation only;
- PptxGenJS 4.0.1; and
- LibreOffice plus Poppler for the 300-DPI slide preview.

Install the frozen Python environment from the repository root:

```bash
python3 -m pip install -r task07_particle_in_box/requirements-task07.txt
```

The scientific core has no network, account or browser dependency.

## Deterministic scientific generation

Run from the repository root:

```bash
python3 -m task07_particle_in_box.generate_task07
```

The command constructs the analytical and numerical studies, requires all 50
scientific checks to pass, writes nine data files and twelve figure files into a
temporary directory, verifies schemas, dimensions, finite JSON values, size
budgets and SHA-256 hashes, and then replaces the accepted package atomically.

The manifest records a fixed build timestamp, the official source URL and pages,
source-document hashes, configuration, constants, equations, study digest and
content hashes. CSV floating-point values use 17 significant digits; JSON rejects
NaN and infinity; SVG hashing uses deterministic Matplotlib settings. The
generator requires Times New Roman and refuses to substitute a fallback font;
the manifest records the accepted figure font family.

## Independent validation

For each finite-difference eigenvector, the code first normalizes with the
discrete SI inner product Σ|ψ_i|^2Δx. It then applies the central operators

$$
p_h=-i\hbar D_1, \qquad p_h^2=-\hbar^2D_2,
$$

with zero Dirichlet ghost values at both walls. The stored numerical
\(\langle p\rangle\), \(\langle p^2\rangle\), \(\Delta p\) and
\(\Delta x\Delta p\) values are generated before comparison with the
analytical reference columns. The route is covered by the focused momentum
tests, including a guard that fails if the analytical \(\Delta p\) function is
called by the operator calculation.

```bash
python3 -m task07_particle_in_box.validate_task07
python3 -m task07_particle_in_box.validate_task07_documentation
python3 -m task07_particle_in_box.validate_task07_final
python3 -m unittest discover -s task07_particle_in_box -p 'test_*.py' -v
python3 -m py_compile task07_particle_in_box/*.py
```

The suite covers:

- exact integer-state and grid enumeration;
- high-precision scalar energy, moment and uncertainty anchors;
- boundary conditions, normalization, orthogonality and node counts;
- (E_n/E_1=n^2) scaling and monotonic energy gaps;
- the strict Heisenberg lower bound for every accepted state;
- five finite-difference refinements, second-order convergence and eigenvector
  overlap;
- numerical position and momentum moments computed from all 50 grid-state
  eigenvectors, with refinement and Heisenberg checks;
- invalid inputs, corrupted immutable studies and mismatched reports;
- deterministic data/figure regeneration; and
- rollback after a forced late replacement failure.

## Output inventory

Data:

| File | Role |
|---|---|
| `energy_levels.csv` | (n=1\ldots10), energies, ratios and gaps |
| `stationary_states.csv` | signed amplitudes and densities for (n=1\ldots4) |
| `expectation_values.csv` | position/momentum moments and uncertainty products |
| `numerical_eigenvalues.csv` | five-grid convergence and finest-grid overlaps |
| `numerical_moments.csv` | direct position/momentum moments for 50 grid-state pairs |
| `uncertainty_convergence.csv` | five-grid maximum errors and measured orders |
| `reference_anchors.json` | independent 60-digit scalar anchors |
| `validation_report.json` | machine-readable 50-check result |
| `manifest.json` | provenance, schemas, configuration and 20 content hashes |

Figures:

| Base name | Raster | Companion |
|---|---:|---:|
| `energy_spectrum` | 2400 × 1500, 300 DPI | editable SVG |
| `probability_densities` | 2400 × 1500, 300 DPI | editable SVG |
| `wavefunctions_and_density` | 2400 × 1500, 300 DPI | editable SVG |
| `energy_level_wavefunctions` | 2400 × 1500, 300 DPI | editable SVG |
| `uncertainty_principle` | 2400 × 1500, 300 DPI | editable SVG |
| `task07_summary` | 3840 × 2160, 300 DPI | editable SVG |

## Report package

The report is supplied in three forms:

- [`particle_in_box_uncertainty.tex`](../reports/task07/particle_in_box_uncertainty.tex)
  is the editable publication source;
- [`particle_in_box_uncertainty.pdf`](../reports/task07/particle_in_box_uncertainty.pdf)
  is the visually accepted four-page A4 rendering; and
- [`particle_in_box_uncertainty_accessible.md`](../reports/task07/particle_in_box_uncertainty_accessible.md)
  is the semantic, screen-reader-friendly companion with descriptive figure
  alternatives.

The supplied PDF was produced by a LaTeX installation that is not bundled with
the repository. On a TeX Live installation containing `amsmath`, `amssymb`,
`booktabs`, `graphicx`, `float`, `xcolor`, `hyperref` and `microtype`, rebuild it
from the repository root with:

```bash
cd reports/task07
pdflatex -interaction=nonstopmode -halt-on-error particle_in_box_uncertainty.tex
pdflatex -interaction=nonstopmode -halt-on-error particle_in_box_uncertainty.tex
cd ../..
python3 -m task07_particle_in_box.generate_task07_report_manifest
```

The accepted PDF is not structurally tagged by that original compiler. The
accessible Markdown report is therefore part of the required handoff, not an
optional note. The report manifest records that distinction explicitly and
hashes all three report representations.

## Presentation package

```bash
cd presentation/task07
npm ci
npm run build
npm run preview
npm run validate
```

The generator copies all six accepted PNGs byte-for-byte, embeds the 4K summary,
adds meaningful alternative text and speaker notes, and writes deterministic
PowerPoint metadata. The preview step uses LibreOffice and Poppler at 300 DPI;
the validator requires a 16:9 render of at least 3900 × 2100 pixels.

## Manual acceptance anchors

Before recording, verify that:

- energy appears only at discrete positive integers and follows (n^2);
- every plotted density vanishes at both walls and integrates to one in (x/a);
- signed (\psi_n) and non-negative (a|\psi_n|^2) are not conflated;
- the ground-state uncertainty product reads approximately (0.568\hbar), above
  the (0.5\hbar) line; and
- no narration or animation implies that a stationary probability density moves.

## Audit trail

- Official scope: [`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md)
- Frozen model: [`MATHEMATICAL_MODEL.md`](MATHEMATICAL_MODEL.md)
- Extension decision: [`EXTENSION_DECISION.md`](EXTENSION_DECISION.md)
- Results: [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md)
- Presentation: [`../presentation/task07/README.md`](../presentation/task07/README.md)
- Final acceptance: [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md)

No secret, credential, external account or external submission is required or
stored.
