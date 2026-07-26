# Task 10 PowerPoint Pack

This folder contains the finished one-slide Task 10 competition presentation.
The full ten-task screencast is limited to three minutes, so the recommended
version uses approximately **18 seconds of narration**.

## Ready-to-use slide

Open [`Task10_Hydrogenic_Orbitals.pptx`](Task10_Hydrogenic_Orbitals.pptx). It is
an editable 16:9 PowerPoint wrapper around the validated 4K Task 10 summary and
includes:

- the S-through-G orbital family and 25 real display states;
- the required coloured-glass three-dimensional density construction;
- radial and angular node evidence;
- exact hydrogenic energy and size scaling;
- 22/22 scientific checks across 204 validated states;
- meaningful image alternative text; and
- the final competition script in the speaker-notes area.

A 300-DPI rendering is available at
[`preview/Task10_Hydrogenic_Orbitals_preview.png`](preview/Task10_Hydrogenic_Orbitals_preview.png).

## What to say

Use the final 50-word version in [`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md). The
same script is embedded in the PowerPoint notes. The file also contains an
expanded version, timed visual cues, pronunciation guidance and likely
questions.

The exact visible content and image alternative text are recorded in
[`SLIDE_CONTENT.md`](SLIDE_CONTENT.md).

## Visual hierarchy

The slide embeds [`task10_summary.png`](../../figures/task10/task10_summary.png)
almost full-canvas. The coloured-glass 3d example establishes the main physical
result; the S-through-G strip and radial curves show the systematic structure;
the validation totals complete the evidence chain.

## Image folder

The [`images`](images/) folder contains byte-identical copies of the accepted
publication PNGs and motion poster. The PowerPoint embeds the 4K summary; the
other files remain available for a longer presentation or close-up edit.

| File | Dimensions | Use |
|---|---:|---|
| `01_required_orbital_gallery.png` | 3840 × 2400 | Complete 25-state gallery |
| `02_radial_and_nodal_structure.png` | 2400 × 1500 | Radial and node evidence |
| `03_coloured_glass_density.png` | 3000 × 1875 | Three-dimensional density method |
| `04_rendering_comparison.png` | 3000 × 1800 | Rendering-method comparison |
| `05_task10_summary.png` | 3840 × 2160 | Embedded competition overview |
| `06_orbital_view_rotation_poster.png` | 3840 × 2160 | Accessible motion fallback |

The editable publication SVGs and embedded-font PDFs remain in
`figures/task10/`. Preserve aspect ratios and do not crop orbital planes,
result cards, axes, scale relationships, caveats or validation totals.

## Actual 16:9 layout

The slide uses a 13.333 by 7.5 inch canvas. The 4K summary is placed at x = 0.12,
y = 0.08, width = 13.09 and height = 7.36 inches, leaving a narrow white safety
margin around the validated asset.

The shared visual specification is in [`deck-style.md`](deck-style.md).

## Regenerate the package

```bash
cd presentation/task10
npm ci
npm run build
npm run preview
npm run validate
```

The generator copies all current validated assets, embeds the summary unchanged,
adds accessible alternative text and speaker notes, and writes the PowerPoint
with reproducible metadata.

## Final recording checklist

- Say “probability density” rather than describing an electron trajectory.
- State that there are 25 real display states from S through G.
- Use the exact $Z^2/n^2$ energy and $1/Z$ size scaling.
- Say that opacity thresholding does not modify or renormalize the density.
- Say that view rotation is camera motion, not electron motion.
- Finish on the 22/22 validation total and keep the ten-task screencast below
  three minutes.

The full explanation is in the
[`Task 10 results report`](../../task10_hydrogenic_orbitals/RESULTS_AND_INTERPRETATION.md).
The completed presentation audit is recorded in
[`STAGE10_ACCEPTANCE.md`](STAGE10_ACCEPTANCE.md).
The end-to-end handoff is recorded in
[`FINAL_ACCEPTANCE.md`](../../task10_hydrogenic_orbitals/FINAL_ACCEPTANCE.md).
