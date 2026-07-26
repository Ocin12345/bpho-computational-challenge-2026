# Task 8 Stage 6 acceptance: finite-photon extension

## Decision

Stage 6 is complete. The browser calculator now includes an optional, explicitly separated finite-photon sampling experiment while preserving the official ideal-probability result.

## Requirement evidence

| Requirement | Authoritative evidence | Result |
|---|---|---|
| Exact theory remains unchanged | Core 42/42 scientific validation and existing official reference fixtures | Pass |
| Integer finite-photon outcomes | Python and JavaScript Bernoulli counting; count-conservation tests | Pass |
| Reproducible samples | Displayed unsigned seed, frozen Mulberry32 vector and same-seed equality checks | Pass |
| Independent model streams | Distinct classical and quantum salted stream seeds | Pass |
| Correct sampling summaries | \(Np\), \(\sqrt{Np(1-p)}\), standardised residual and Wilson formulas tested independently | Pass |
| Boundary behaviour | \(p=0\) always gives zero; \(p=1\) always gives \(N\); residual labelled deterministic | Pass |
| Cross-language agreement | Six Python-generated experiment fixtures, including (N=100{,}000), matched exactly by JavaScript counts | Pass |
| Honest visual encoding | Observed sample, exact theory and 95% Wilson interval are separately labelled on a fixed 0–100% scale | Pass |
| Maximum approved workload | 100,000 pairs per model completed in 4.50 ms in the final browser run, below the 100 ms budget | Pass |
| Responsive and accessible operation | 11-group WCAG 2.2 AA audit, 320 px reflow, 200% text and full keyboard operation | Pass |
| Offline operation | Static validator confirms seven local runtime files and no external assets | Pass |

## Frozen default experiment

At the official angles \(\theta=-30^\circ\), \(\phi=30^\circ\), with \(N=1000\) and seed 2026:

| Model | Exact theory | Observed mismatches | Observed rate | 95% Wilson interval | Residual |
|---|---:|---:|---:|---:|---:|
| Classical | 37.5% | 363 / 1000 | 36.3% | 33.4–39.3% | −0.78σ |
| Quantum | 75.0% | 770 / 1000 | 77.0% | 74.3–79.5% | +1.46σ |

The observed quantum-minus-classical difference is +40.7 percentage points, compared with the exact theoretical +37.5 percentage points. The interface states that the difference is finite-sampling fluctuation.

## Final verification

- 54 Python unit tests passed.
- Baseline scientific validation passed 42/42 checks.
- Statistical validation passed 24/24 checks.
- Ten JavaScript tests passed, including all Python statistical fixtures.
- Desktop/mobile browser smoke testing passed with no console errors, page errors, external requests or overflow.
- Maximum measured angle update: 1.10 ms.
- Maximum measured 100,000-pair sample: 4.50 ms.
- Accessibility audit passed 11 evidence groups with zero detected WCAG 2.2 AA violations in the tested scope.
- Python compilation and `git diff --check` passed.

## Deliverables

- Statistical specification: `task08_quantum_cryptography/STATISTICAL_EXTENSION.md`
- Architecture decision: `task08_quantum_cryptography/architecture/ADR-002-reproducible-finite-photon-sampling.md`
- Python model: `task08_quantum_cryptography/statistics.py`
- Browser model: `task08_quantum_cryptography/app/statistics.js`
- Statistical validator: `task08_quantum_cryptography/validate_task08_statistics.py`
- Deterministic generator: `task08_quantum_cryptography/generate_task08_statistics.py`
- Reference fixtures and reports: `data/task08/finite_photon_reference.json`, `statistical_validation_report.json`, and `statistics_manifest.json`

The seeded generator is suitable for reproducible educational simulation only and is explicitly labelled as not cryptographically secure.
