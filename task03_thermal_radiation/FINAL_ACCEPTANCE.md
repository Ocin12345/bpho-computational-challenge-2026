# Task 3 Final Acceptance Report

**Status:** Accepted

**Acceptance date:** 16 July 2026

**Scope:** Official Task 3 baseline only

This report closes the acceptance boundary declared before implementation. It
reviews the complete Planck-radiation and Einstein-heat-capacity package as a
single deliverable rather than treating the completion of an individual stage
as proof that the whole task is ready.

## Acceptance matrix

| Requirement | Evidence | Result |
| --- | --- | :---: |
| Generate both official curve families from our own code | `planck_spectra` and `einstein_heat_capacity` are generated directly from the tested model APIs | Pass |
| Include all official reference cases | $4000$, $5000$, and $6000\ \mathrm K$ plus Au, Cu, Ti, Al, Fe, Si, and C are present | Pass |
| Use explicit, consistent notation and units | The mathematical specification, code API, CSV schemas, plots, and scientific report agree | Pass |
| Pass pre-declared analytical and numerical checks | 27/27 checks pass without changing a tolerance | Pass |
| Regenerate numerical and visual evidence cleanly | An isolated run reproduced all 17 committed data and figure files byte for byte | Pass |
| Inspect every final visual | Five figures and the final slide preview were inspected at original resolution | Pass |
| Explain physical meaning and limitations | [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md) distinguishes validation from experiment and states both models' assumptions | Pass |
| Complete the competition presentation package | One editable slide, embedded notes, timed narration, source assets, and a high-resolution preview are present | Pass |
| Leave a clean, synchronized private repository | Local `main` and fetched `origin/main` agree after the Stage 12 push; GitHub reports the repository as private | Pass |

## Fresh acceptance evidence

### 1. Isolated scientific regeneration

The complete generator was run into a new `work/task03-stage12` directory:

```bash
python3 -m task03_thermal_radiation.generate_task03 \
  --data-dir work/task03-stage12/data \
  --figure-dir work/task03-stage12/figures
```

The run completed in **2.21 seconds**, passed all **27 validation checks**, and
created exactly **7 data files** and **10 figure files**. A file-set and binary
comparison confirmed that all 17 files were byte-identical to the committed
evidence. The separate validation command also passed, and the focused
data-only subprocess test confirmed that data generation does not import
Matplotlib.

### 2. Complete automated test suite

```bash
python3 -m unittest discover -q
```

Result: **224 tests passed** in the final repository state. This comprises all
107 Task 3 tests and the 117 regression tests from Tasks 1 and 2.

### 3. PowerPoint reconstruction

From `presentation/task03/`, the pinned dependencies were installed and the
deck was rebuilt, rendered, and validated:

```bash
npm ci
npm run build
npm run preview
npm run validate
```

The dependency audit reported zero vulnerabilities. Two consecutive deck
builds were byte-identical with SHA-256
`f83e7035fe605e15e14509843d57f0a8d4ee04a29a67fe6a2c38ab9ed8a0be8d`.
The package validator confirmed one slide, one notes page, two embedded main
figures, source-image integrity, accessible descriptions, a 47-word final
script, deterministic core metadata, and a $2401\times1350$ 16:9 preview.

### 4. Visual inspection

The following PNGs were inspected at original resolution:

- `planck_spectra.png`;
- `planck_validation.png`;
- `einstein_heat_capacity.png`;
- `einstein_normalized.png`;
- `task03_summary.png`; and
- `Task03_Planck_Einstein_preview.png`.

Titles, axes, units, legends, curve identities, peak markers, tolerance lines,
the $3R$ limit, and all slide elements were readable. No clipping, overlap,
incorrect scaling, or visual scientific contradiction was found.

### 5. Repository quality and synchronization

The final audit also passed:

- Python compilation and JavaScript and shell syntax checks;
- tracked Task 3 Markdown-link resolution;
- a 10 MiB per-file limit for every tracked file;
- checks for sensitive tracked filenames and this machine's absolute home
  path;
- `git diff --check` and `git fsck --full`; and
- a fetched comparison of local `HEAD` with `origin/main`.

Git reported some unreachable historical objects during `git fsck`; this is
normal local object-store housekeeping and not repository corruption. The
command exited successfully.

## Open risks and operational check

There is no open scientific or software defect blocking Task 3. The package
was rendered through LibreOffice and structurally inspected as a PowerPoint
archive. Before recording, open the slide once in Microsoft PowerPoint on the
actual recording computer and confirm local font rendering, graph-label size,
and the 16:9 canvas. This is an operational compatibility check, not a missing
Task 3 deliverable.

The same clean run was not repeated on the separate RTX 4090 laptop. That is
not required by the official task: the calculation is deterministic,
CPU-light, dependency-pinned, and fully reproducible on the everyday MacBook
Air. GitHub remains the transfer mechanism if a second-machine confirmation is
later desired.

## Final decision

Task 3 satisfies the declared definition of done and is **accepted**. Further
work should begin only as an explicitly optional extension or as Task 4.
