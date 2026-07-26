# Task 9 PowerPoint Pack

This folder contains the finished one-slide Task 9 competition presentation. The
full ten-task screencast is limited to three minutes, so the recommended version
uses approximately **18 seconds of narration**.

## Ready-to-use slide

Open [`Task09_Compton_Scattering.pptx`](Task09_Compton_Scattering.pptx). It is an
editable 16:9 PowerPoint wrapper around the validated 4K Task 9 summary and
includes:

- the exact 200 keV momentum geometry;
- all three official five-energy curve families;
- the required wavelength shift, relativistic speed and recoil angle;
- the exact 200 keV, 90° reference values;
- 44/44 core and 30/30 extension validation totals;
- meaningful image alternative text; and
- the final competition script in the speaker-notes area.

A 300-DPI rendering is available at
[`preview/Task09_Compton_Scattering_preview.png`](preview/Task09_Compton_Scattering_preview.png).

## What to say

Use the final 48-word version in [`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md). The same
script is embedded in the PowerPoint notes. The file also contains an expanded
version, timed visual cues, pronunciation guidance and likely questions.

The exact visible content and image alternative text are recorded in
[`SLIDE_CONTENT.md`](SLIDE_CONTENT.md).

## Visual hierarchy

The slide embeds [`task09_summary.png`](../../figures/task09/task09_summary.png)
almost full-canvas. The 200 keV momentum triangle establishes the physical
geometry; the wavelength, speed and recoil-angle curves give the complete
official answer; the validation totals finish the evidence chain. Times New
Roman is used throughout the source visual and PowerPoint theme.

## Image folder

The [`images`](images/) folder contains byte-identical copies of the accepted
publication PNGs and animation. The PowerPoint embeds the 4K summary; the other
files remain available for a longer presentation or close-up edit.

| File | Dimensions | Use |
|---|---:|---|
| `01_required_kinematics.png` | 2400 × 1500 | Direct official answer |
| `02_energy_transfer_geometry.png` | 2400 × 1500 | Conservation explanation |
| `03_klein_nishina_extension.png` | 2400 × 1500 | Separate angular weighting |
| `04_task09_summary.png` | 3840 × 2160 | Embedded competition overview |
| `05_compton_angle_sweep.gif` | 1600 × 900, 73 frames | Animated 200 keV sweep |

The editable publication SVGs and PDFs remain in `figures/task09/`. Preserve
aspect ratios and do not crop equations, axes, endpoint notes, numerical
anchors, momentum arrows or validation totals.

## Actual 16:9 layout

The slide uses a 13.333 by 7.5 inch canvas. The 4K summary is placed at x = 0.12,
y = 0.08, width = 13.09 and height = 7.36 inches, leaving a narrow white safety
margin around the validated asset.

The shared visual specification is in [`deck-style.md`](deck-style.md).

## Regenerate the package

```bash
cd presentation/task09
npm ci
npm run build
npm run preview
npm run validate
```

The generator copies all current validated assets, embeds the summary unchanged,
adds accessible alternative text and speaker notes, enforces a Times New Roman
theme, and writes the PowerPoint with reproducible metadata.

## Final recording checklist

- Say “fractional shift” and “electron speed” while following the top two graph
  families.
- Describe the line styles as well as colour if the audience cannot distinguish
  the five hues.
- Say that the recoil direction is undefined at exactly 0°, despite its 90°
  continuous limit.
- Call the Klein–Nishina calculation a separately labelled optional extension.
- Do not claim that the ideal free-electron model is a detector or material
  simulation.
- Finish on the validation totals and keep the ten-task screencast below three
  minutes.

The full explanation is in the
[`Task 9 results report`](../../task09_compton_scattering/RESULTS_AND_INTERPRETATION.md).
The completed presentation audit is recorded in
[`STAGE10_ACCEPTANCE.md`](STAGE10_ACCEPTANCE.md).
The end-to-end handoff is recorded in
[`FINAL_ACCEPTANCE.md`](../../task09_compton_scattering/FINAL_ACCEPTANCE.md).
