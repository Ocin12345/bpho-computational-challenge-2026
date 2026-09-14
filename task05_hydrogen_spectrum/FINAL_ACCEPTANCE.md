# Task 5 Final Acceptance Record

Date: 16 July 2026

## Outcome

The Task 5 implementation, numerical evidence, figure package, scientific
report, and one-slide PowerPoint pack satisfy the approved ideal Bohr-model
scope. The release artifacts pass all local scientific, structural,
reproducibility, presentation, and repository-wide checks listed below.

## Scientific validation

Command:

```bash
python3 -m task05_hydrogen_spectrum.validate_task05
```

Result: **PASS, 30/30 checks**.

The checks cover source constants, exact level and pair enumeration, energy
ordering, independent Decimal energies, positive emission energies, joule
conversions, $E_\gamma\lambda=hc$, $f\lambda=c$, independent Rydberg
wavelengths, frequencies, six named lines, five analytical limits, convergence,
labels, and spectral-region classification.

## Automated tests

Focused command:

```bash
python3 -m unittest discover -s task05_hydrogen_spectrum -p 'test_*.py' -q
```

Result: **PASS, 42 tests**.

Repository command:

```bash
python3 -m unittest discover -v
```

Result: **PASS, 415 tests in 120.954 seconds**.

## Reproducibility

A clean out-of-tree generation was compared byte for byte with every committed
Task 5 evidence artifact:

- 5 CSV/JSON data files: byte-identical;
- 12 PNG/SVG figure files: byte-identical; and
- 2 consecutive PowerPoint builds: byte-identical, SHA-256
  `3a41906ab545f8f21deaad24254ea2fca60f318a923e5a330ff20c26a361d1ca`.

Generation is transactional. Focused tests also inject late replacement
failures and confirm that every pre-existing data or figure destination is
restored.

## Visual acceptance

All six final PNGs were inspected after generation:

- the mandatory energy--wavelength graph is legible across its logarithmic
  axis, distinguishes all series, shows the declared visible band, and labels
  analytical limits honestly;
- the closely spaced $n=3$--6 energy-level labels use separated callouts;
- the Balmer line labels and ultraviolet limit remain readable;
- the convergence explanation does not obscure data;
- the validation graphic clearly separates numerical ratios from structural
  checks; and
- the four-panel summary has no clipped titles or overlapping evidence text.

The rendered slide preview was inspected at $2401\times1350$ pixels. The
required graph remains dominant and uncropped; the Balmer spectrum is visibly
secondary; equations, the ideal H-$\alpha$ result, and the 30/30 badge are
clear at final video resolution.

## Final publication-quality audit

A second original-resolution audit confirmed that the complete figure package
meets the intended publication and presentation standard:

| Figure group | PNG export | Editable export | Audit result |
| --- | ---: | :---: | --- |
| Required energy--wavelength graph | $3840\times2160$, 300 DPI | SVG | Pass |
| Bohr energy-level diagram | $3200\times1800$, 300 DPI | SVG | Pass |
| Balmer visible-spectrum figure | $3200\times1800$, 300 DPI | SVG | Pass |
| Series-convergence figure | $3200\times1800$, 300 DPI | SVG | Pass |
| Validation figure | $3840\times1920$, 300 DPI | SVG | Pass |
| Four-panel summary | $3840\times2160$, 300 DPI | SVG | Pass |

The audit checked axes and units, logarithmic-scale labelling, marker and legend
consistency, series-limit conventions, title and annotation clipping, compact
panel readability, slide-scale readability, and visual hierarchy. The series
palette is supported by distinct marker shapes, so interpretation does not rely
on colour alone. Text remains live vector content in SVG, while the PNGs are
large enough for 4K slides, reports, and video export without upscaling.

No further visual correction was required after this audit.

## Presentation validation

Command:

```bash
cd presentation/task05
npm run validate
```

Result: **PASS** with one slide, two embedded validated visuals, one notes
page, a 47-word final script, a 16:9 high-resolution preview, exact copied
assets, reproducible metadata, portable links, and no machine-specific paths
inside the PowerPoint.

## Repository hygiene

- Python compilation: pass;
- local Markdown link check: pass;
- `git diff --check`: pass;
- private-key and common token-pattern scan over Task 5 artifacts: pass;
- no generated cache or dependency folder is tracked; and
- the optional reduced-mass work is stored and validated separately rather
  than mixed into the official ideal-model result; orbital animation remains
  excluded.

## Handoff boundary

The Task 5 files are deliberately left as local working-tree changes for review.
No commit or push was performed as part of this acceptance run. Repository
synchronization therefore remains a separate user-directed release action; it
does not affect the scientific or artifact checks above.

## Optional-extension acceptance addendum

Date: 8 August 2026

The Task 5 scope was reopened after baseline acceptance to implement the
preferred finite-proton-mass extension. The accepted baseline remains frozen.

- `reduced_mass_extension.py` applies
  $\mu/m_e=1/(1+m_e/m_p)$ using the NIST 2022 CODATA electron-proton mass
  ratio;
- `reduced_mass_validation.json` and `reduced_mass_transitions.csv` contain a
  separate 45-transition result set;
- 12/12 extension validation checks and all 9 focused extension tests pass;
- the complete Task 5 focused suite now contains 51 passing tests;
- the static website validator passes 16/16 checks; and
- desktop and mobile browser audits confirm the selector, H-$\alpha$ anchor,
  five-line table, high-DPI canvas, fail-closed evidence state, semantic
  labels, and absence of horizontal page overflow or runtime errors.

The H-$\alpha$ vacuum wavelength changes from $656.112276$ nm in the accepted
infinite-mass baseline to $656.469606$ nm in the reduced-mass-only model, a
$357.330$ pm shift. This is not presented as a precision measured wavelength:
fine structure, hyperfine structure, the Lamb shift, line strengths, and
broadening remain excluded.
