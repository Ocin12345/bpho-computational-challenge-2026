# Task 10 Stage 5 Acceptance — Publication Figures

Status: **PASS**

## Accepted figure inventory

The final package in *figures/task10/* contains thirteen graphics plus a deterministic
quality manifest.

| Figure | Accepted PNG | Companion |
|---|---:|---|
| Complete official S–G gallery | 3840×2400, 300 DPI | editable SVG + embedded-font PDF |
| Radial structure and nodes | 2400×1500, 300 DPI | editable SVG + embedded-font PDF |
| Semi-transparent coloured glass | 3000×1875, 300 DPI | PNG only by design |
| Slice/isosurface comparison | 3000×1800, 300 DPI | editable SVG + embedded-font PDF |
| Competition summary | 3840×2160, 300 DPI | editable SVG + embedded-font PDF |

The gallery contains all 25 required real states: 1s, every 2p state, every 3d
state, every 4f state and every 5g state. Family labels sit outside the data
panels, so the 5g, (m=-4) state is not covered or omitted.

## Scientific display contract

- Every density comes from the passing normalized scientific core.
- The 0.15 cutoff controls opacity or the selected isosurface only; it never
  modifies the field, normalization or exported scientific data.
- Gallery density is normalized separately per state and says so on the figure.
- The slice/isosurface comparison states exactly what each representation
  preserves and hides.
- The coloured-glass and summary figures state that view rotation is not
  electron motion.
- Family colour is redundant with labels and line styles where line comparison
  is required.

## Visual inspection

Every PNG was inspected at original resolution. The acceptance pass explicitly
checked and corrected:

- heading and validation-total collisions;
- family-label overlap with the complete G row;
- bottom-margin, colourbar and axis-label collisions;
- semitransparent plane occlusion and visible-slice selection;
- isosurface topology, nodal separation and slice contour consistency;
- text clipping on the 4K summary; and
- readability of the smallest state and node labels.

The coloured-glass graphic intentionally has no SVG companion because layered
3D transparency is rasterized; presenting it as fully editable vector geometry
would be misleading. Other SVGs preserve editable Times New Roman text and
linework while embedding the density layers as deterministic raster images.
Their PDF companions embed the TrueType font for reliable print and submission
rendering.

## Automated acceptance evidence

- 39/39 Python tests pass.
- 22/22 independent scientific checks pass.
- Two full thirteen-graphic builds are byte-for-byte identical.
- Exact PNG dimensions and 300-DPI metadata are tested.
- SVG/PDF fonts, output inventory, hashes and canvas-bound figure text are tested.
- Non-finite, mutable and invalid projection inputs are rejected.
- A deliberately corrupted scientific-state digest blocks figure generation.
- `git diff --check` passes.

The accepted scientific-state digest is
**d298695290395956560641493fc603e5970a4ea01609eca677b3b4b683fa085e**.
All artifact hashes and the matching data-manifest hash are recorded in
*figures/task10/manifest.json*.

Stage 5 is complete. The offline explorer may now consume only this matching
passing scientific state.
