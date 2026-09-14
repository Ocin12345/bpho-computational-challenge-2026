# Task 7 Final Acceptance

**Status: PASS**

The accepted package is traceable to the official BPhO Computational Physics
Challenge Task 7 wording and has passed the scientific, documentation, report,
figure, presentation and final-package validators described below.

## Official traceability

- [x] Official detailed Task 7 source identified on pages 48--49.
- [x] Official source URL, page range and SHA-256 digests recorded.
- [x] Concise competition specification cross-checked against the detailed brief.
- [x] Required outputs and the uncertainty-principle extension are mapped in
  [`OFFICIAL_REQUIREMENTS.md`](OFFICIAL_REQUIREMENTS.md).

## Required model

- [x] Infinite one-dimensional potential well defined on \(0<x<a\).
- [x] Normalized stationary wavefunctions implemented.
- [x] Energy plotted against discrete quantum number.
- [x] Probability densities plotted against displacement.
- [x] Electron and \(1.00\ \mathrm{nm}\) baseline documented.

## Uncertainty extension

- [x] Position moments derived.
- [x] Momentum moments derived with the momentum operator.
- [x] \(\Delta x\Delta p\geq\hbar/2\) proven for every positive integer state.
- [x] Ground-state value independently anchored.
- [x] LaTeX source compiled into a visually inspected four-page PDF.
- [x] A semantic Markdown companion supplies headings, equations, tables and
  descriptive figure text for accessible reading.
- [x] Report-source, PDF and accessible-companion hashes are frozen in the
  report manifest.

The accepted PDF is not structurally tagged. The semantic Markdown companion
is therefore a required part of the report package rather than an optional
duplicate.

## Numerical validation

- [x] Independent tridiagonal finite-difference Hamiltonian implemented.
- [x] Real-space central-difference (p_h=-i\hbar D_1) and
  (p_h^2=-\hbar^2D_2) operators applied directly to normalized eigenvectors.
- [x] Five grid refinements evaluated.
- [x] First ten numerical energies converge monotonically.
- [x] Observed convergence order is approximately two.
- [x] Finest-grid eigenfunctions match analytical states.
- [x] Normalisation, orthogonality and node counts pass.
- [x] Numerical Δp, ΔxΔp and Heisenberg checks pass for all 50 grid-state pairs.
- [x] Numerical moments, uncertainty convergence and downloads are visible on the
  judge-facing Task 7 page.
- [x] Numerical position and momentum moments are computed from eigenvectors.
- [x] All 50 grid-state uncertainty products obey the Heisenberg bound.
- [x] Numerical uncertainty errors decrease at measured second order.

## Reproducibility and evidence

- [x] Nine ordered data artifacts generated.
- [x] Manifest contains configuration, constants, schemas and SHA-256 hashes.
- [x] Regeneration produces identical hashes.
- [x] Forced late replacement failure restores prior outputs.
- [x] All non-finite JSON values are rejected.

## Figures

- [x] Six PNG/SVG figure pairs produced.
- [x] All visible figure typography and mathematical text use Times New Roman.
- [x] Analytical PNGs are 2400 by 1500 pixels.
- [x] Summary PNG is 3840 by 2160 pixels.
- [x] Energy states are shown as discrete markers.
- [x] Probability axes are dimensionless and normalized.
- [x] Wavefunction and probability density are not conflated.
- [x] Heisenberg lower bound is explicitly marked.
- [x] Two visual-inspection passes completed and detected defects corrected.

## Software quality

- [x] 50 independent scientific checks pass.
- [x] 13 documentation checks pass.
- [x] 8 final artifact groups pass.
- [x] 47 focused software tests pass, including direct finite-difference momentum tests.
- [x] Invalid inputs and deliberately corrupted studies are rejected.
- [x] Python sources compile successfully.
- [x] Exact numerical Python dependencies are pinned.
- [x] End-to-end regeneration and validation commands are documented.

## Presentation

- [x] One-slide PowerPoint generated from validated Task 7 assets.
- [x] Final 47-word speaker script held near the approved 18-second length.
- [x] Rendered 16:9 preview inspected at 4001 by 2250 pixels and 300 DPI.
- [x] Meaningful image alternative text embedded.
- [x] Deterministic PowerPoint SHA-256 recorded in the presentation acceptance
  record.
- [x] Presentation structure, assets and portability validated.

## Final evidence

Run the following commands from the repository root to reproduce the accepted
checks:

```bash
python3 -m unittest discover -s task07_particle_in_box -p 'test_*.py' -v
python3 -m task07_particle_in_box.validate_task07
python3 -m task07_particle_in_box.validate_task07_documentation
python3 -m task07_particle_in_box.validate_task07_final
python3 presentation/task07/validate_task07_presentation.py
```

All Task 7 scientific, computational, report, accessibility-companion, figure
and presentation requirements are accepted. Cross-task timing for the eventual
ten-task video remains a separate final-production check.

## Optional superposition addendum

**Acceptance date:** 8 August 2026

After the official uncertainty extension was accepted, Task 7 was reopened for
one additional lab that compares a stationary eigenstate with a coherent
equal-weight $n=1$ and $n=2$ superposition. The official baseline, figures,
report, and presentation remain unchanged.

- 14/14 separate superposition checks pass over 17 phase anchors;
- all 8 focused extension tests pass within the current 47-test Task 7 suite;
- the extension evidence regenerates byte-for-byte as JSON and CSV;
- the website validator passes 20/20 checks, while the official page now keeps
  the superposition UI out of the stationary-state judging path; and
- desktop and mobile browser audits pass phase presets, analytical readouts,
  high-DPI canvas rendering, accessible descriptions, page overflow, runtime
  errors, and external-request checks.

For the accepted $1.00$ nm electron box, the probability-density period is
$3.666078$ fs. At phase $0$, $\langle x\rangle=0.319873a$ and the left-half
probability is $92.441\%$; at phase $\pi$, these become $0.680127a$ and
$7.559\%$. The mean energy remains $0.940075$ eV throughout. These values
describe a quantum probability distribution, not a particle trajectory.
