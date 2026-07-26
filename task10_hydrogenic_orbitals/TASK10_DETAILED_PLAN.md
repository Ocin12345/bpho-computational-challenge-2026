# Task 10 Detailed Staged Plan

## Goal

Build a research-grade, competition-ready hydrogenic-orbital package that
computes normalized \(|\psi_{nlm}|^2\), proves the physics independently, shows
the official S–G state families clearly, and delivers the requested
semi-transparent 3D “coloured glass” visualization at the same visual and
validation standard as Tasks 5–9.

## Current progress

- Stages 0–6: complete with direct acceptance evidence.
- Stages 7–8: complete with direct browser, accessibility and media evidence.
- Stage 9: complete with corruption-tested documentation evidence.
- Stage 10: complete with deterministic PowerPoint and 300-DPI render evidence.
- Stage 11: complete with repository-wide final acceptance evidence.

## Stage 0 — Official scope and visual contract

### Work

- Read PDF pages 62–76 and record file hashes and page evidence.
- Freeze the valid \(n,l,m\) domain, the \(Z\)-dependent hydrogenic model, S–G
  gallery and 0.15 example display threshold.
- Resolve the source slides' \(\theta/\phi\) coordinate-label inconsistency by
  adopting explicit polar-colatitude and azimuth symbols.
- Separate mandatory density mapping from optional phase, isosurface or
  superposition views.

### Acceptance gate

- Every official requirement is traceable to a source page.
- No example threshold, plotting convention or unnormalized angular combination
  is mistaken for underlying physics.
- The scope document contains explicit inclusion and exclusion boundaries.

## Stage 1 — Mathematical specification and independent anchors

### Work

- Derive the normalized associated-Laguerre radial function.
- Derive normalized real tesseral harmonics from complex \(Y_l^m\).
- Define reduced mass, effective Bohr length, energy and Cartesian conversion.
- Freeze factorial/recurrence algorithms and overflow-safe numerical domains.
- Establish analytic anchors for 1s, 2s and 2p; numerical anchors for D/F/G.
- Define validation tolerances for normalization, orthogonality, nodes,
  expectation values and scaling laws.

### Acceptance gate

- Radial, angular and total normalization are separately testable.
- Independent formulations exist for every production equation.
- Endpoint conventions at \(r=0\), the polar axis and nodal surfaces are explicit.

## Stage 2 — Deterministic scientific core

### Work

- Implement immutable constants and configuration.
- Implement associated Laguerre and Legendre recurrences without hidden external
  state.
- Implement normalized radial functions, real harmonics, full wavefunctions and
  densities.
- Support the official range through G orbitals, with a conservative wider
  validated range only if conditioning remains sound.
- Return both dimensional density and display-normalized density.
- Reject non-integer or invalid quantum-number triples.

### Acceptance gate

- Pure functions are deterministic, finite and immutable.
- Vectorized grids and scalar reference calculations agree.
- All arrays have declared shapes, units and coordinate conventions.

## Stage 3 — Independent scientific validation

### Work

- Integrate \(|R|^2r^2\), \(|\mathcal Y|^2\) and \(|\psi|^2\) independently.
- Check radial orthogonality for equal \(l\), angular orthogonality for all
  official \(l,m\), and complete-state normalization.
- Check analytic 1s/2s/2p values and known radial-node locations.
- Check radial node count \(n-l-1\), angular nodal count/orientation and parity
  \((-1)^l\).
- Check \(\langle r\rangle\), \(\langle r^2\rangle\), \(Z^2/n^2\) energy scaling
  and \(1/Z\) length scaling.
- Include deliberate-corruption and invalid-input tests.

### Acceptance gate

- All acceptance states pass the frozen numerical tolerances.
- A machine-readable validation report links every check to the state digest.
- Transactional generation refuses or rolls back failed science.

## Stage 4 — Reproducible state gallery and data

### Work

- Generate a compact official gallery for 1s, 2p, 3d, 4f and 5g, including every
  allowed \(m\) for each family.
- Export radial profiles, node tables, energy/length summaries and validation
  anchors.
- Record configuration, constants, units, formulas, hashes and source
  provenance in manifests.
- Keep large volumetric grids regenerated on demand; store compact evidence
  rather than opaque bulk arrays.

### Acceptance gate

- Repeated generation is byte-for-byte deterministic where the format permits.
- Every data file is schema-checked and hash-bound to its validation report.
- The official gallery is complete and no state is duplicated or omitted.

## Stage 5 — Publication-quality static figures

Status: **complete** — see *STAGE5_ACCEPTANCE.md*.

### Work

- Create a 300-DPI required gallery covering S–G orbital families.
- Create radial-density and node diagnostics with physical axes.
- Create the required semitransparent coloured-glass slice construction.
- Create an orthogonal-slice/isosurface comparison that explains what each
  rendering preserves and hides.
- Create a 3840×2160 competition summary.
- Export editable SVG wherever the visual representation is truly vector-safe.

### Visual standards

- Colour maps are perceptually ordered and colour-blind safe.
- Phase, if shown, uses a diverging scale and never masquerades as density.
- Density comparisons disclose whether colour is absolute or normalized per
  state.
- Camera, lighting, opacity, threshold and physical scale remain stable in
  comparisons.
- Labels remain readable at presentation and report sizes.

### Acceptance gate

- Dimensions, DPI, transparency, labels, colorbars and hashes are automated.
- All figures are inspected at original resolution for clipping, occlusion,
  aliasing, misleading opacity and lost internal nodes.

## Stage 6 — Offline interactive 3D explorer

Status: **complete** — see *STAGE6_ACCEPTANCE.md*.

### Work

- Provide controls for \(Z,n,l,m\), physical extent, slice count, opacity and
  display threshold.
- Keep invalid \(l,m\) choices impossible and announce state changes.
- Render the coloured-glass slice stack with orbit, zoom and reset controls.
- Add orthogonal slices and a radial-profile panel for interpretation.
- Show energy, effective radius, node counts, normalization and the distinction
  between absolute and display-normalized density.
- Run entirely offline with no account or remote asset dependency.

### Acceptance gate

- Python and JavaScript agree on all frozen anchors.
- The exact official gallery is reachable through named presets.
- Desktop and mobile layouts expose every control and result without page-level
  overflow.

## Stage 7 — Browser, performance and accessibility acceptance

Status: **complete** — see *STAGE7_ACCEPTANCE.md* and
*ACCESSIBILITY_AUDIT.md*.

### Work

- Test default, endpoint, invalid-route and representative S–G states.
- Test keyboard-only operation, focus visibility, live announcements and skip
  navigation.
- Test 320 px reflow, 200% text, reduced motion, forced colours and graph
  descriptions.
- Verify colour-independent state/phase encodings.
- Measure full 3D state update latency and memory use on the official gallery.
- Reject external requests, console errors and WebGL fallback failures.

### Acceptance gate

- Frozen performance budgets are met on the supplied browser runtime.
- Accessibility evidence is recorded by criterion group.
- A meaningful non-WebGL fallback preserves the scientific result.

## Stage 8 — High-quality motion output

Status: **complete** — see *STAGE8_ACCEPTANCE.md*.

### Work

- Produce a deterministic 4K or high-resolution orbital animation using a fixed
  camera path and stable density threshold.
- Prefer a slow rotation of the coloured-glass/isosurface view or a clearly
  labelled S–G state sequence; do not imply time evolution of a stationary state.
- Include state, energy, threshold and scale in every frame.
- Store opaque full frames or a codec/container that avoids disposal artifacts.

### Acceptance gate

- Frame count, dimensions, timing, loop, metadata and file budget are checked.
- Beginning, middle, transition and final frames are inspected in a real browser.
- The caption explicitly says “view rotation” or “state gallery,” not electron
  motion.

## Stage 9 — Results, interpretation and reproducibility

Status: **complete** — see *STAGE9_ACCEPTANCE.md*.

### Work

- Explain radial versus angular structure, nodes, degeneracy, scaling with \(Z\)
  and the meaning of probability density.
- Explain why orbitals are not classical electron paths.
- Document threshold/opacity effects and the limitations of 2D slices,
  coloured-glass stacks and isosurfaces.
- Freeze environment versions, deterministic build order and every validation
  command.
- Validate local links, equations, anchors, scope statements and evidence files.

### Acceptance gate

- A new reader can reproduce data, figures, animation and explorer checks.
- Claims remain inside the one-electron non-relativistic scope.
- Documentation corruption tests detect missing endpoints, anchors and caveats.

## Stage 10 — Competition presentation

Status: **complete** — see
[`presentation/task10/STAGE10_ACCEPTANCE.md`](../presentation/task10/STAGE10_ACCEPTANCE.md).

### Work

- Build one accessible 16:9 slide around the validated 4K Task 10 summary.
- Use a concise approximately 18-second script for the ten-task screencast.
- Embed meaningful alternative text and the final script in speaker notes.
- Render the PowerPoint through LibreOffice to a 300-DPI preview.

### Acceptance gate

- The deck is deterministic, portable and below the file-size budget.
- The rendered slide is inspected at original resolution.
- No equation, node, state label, colorbar or validation total is cropped.

## Stage 11 — Final repository-wide acceptance

Status: **complete** — see [`FINAL_ACCEPTANCE.md`](FINAL_ACCEPTANCE.md).

### Work

- Regenerate every Task 10 artifact from the frozen inputs.
- Run Python, JavaScript, browser, accessibility, documentation, media and
  presentation suites.
- Confirm manifests and copied presentation assets against current sources.
- Run syntax, whitespace and `git diff --check` hygiene.
- Record a requirement-by-requirement final acceptance matrix.

### Completion gate

Task 10 is complete only when the official S–G probability-density requirement,
normalized physics, coloured-glass 3D visualization, figures, explorer, motion,
documentation and competition slide all have direct passing evidence.
