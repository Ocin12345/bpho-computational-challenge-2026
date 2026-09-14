# Task 7 PowerPoint Pack

This folder contains the finished one-slide Task 7 competition presentation.
The full ten-task screencast is limited to three minutes, so the recommended
version uses approximately **18 seconds of narration**.

## Ready-to-use slide

Open [`Task07_Particle_In_A_Box.pptx`](Task07_Particle_In_A_Box.pptx). It is an
editable 16:9 PowerPoint wrapper around the validated 4K summary and includes:

- the official probability-density and energy results;
- the completed uncertainty-principle extension;
- analytical equations and numerical anchors;
- a 50/50 validation badge;
- meaningful alternative text; and
- the final competition script in the speaker-notes area.

A 300-DPI rendering is available at
[`preview/Task07_Particle_In_A_Box_preview.png`](preview/Task07_Particle_In_A_Box_preview.png).
All visible typography and the PowerPoint theme use Times New Roman.

## What to say

Use the final 18-second version in [`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md).
The same script is embedded in the PowerPoint notes. The file also contains a
longer explanation, timed cues, pronunciation guidance and likely questions.

The exact visible content and image alternative text are recorded in
[`SLIDE_CONTENT.md`](SLIDE_CONTENT.md).

## Visual hierarchy

The slide embeds [`task07_summary.png`](../../figures/task07/task07_summary.png)
at almost the full 16:9 canvas. This preserves the deliberately balanced
hierarchy: probability densities are the largest visual, energy and
uncertainty receive equal supporting panels, and equations plus validation
remain readable on the right.

## Image folder

The [`images`](images/) folder contains byte-identical copies of all six
validated Task 7 PNGs. The slide embeds the 4K summary; the other five remain
available for a longer presentation.

| File | Dimensions | Use |
| --- | ---: | --- |
| `01_energy_spectrum.png` | $2400\times1500$ | Official discrete energy result |
| `02_probability_densities.png` | $2400\times1500$ | Official Born distributions |
| `03_wavefunctions_and_density.png` | $2400\times1500$ | Amplitude/probability distinction |
| `04_energy_level_wavefunctions.png` | $2400\times1500$ | Standing-wave level diagram |
| `05_uncertainty_principle.png` | $2400\times1500$ | Official extension evidence |
| `06_task07_summary.png` | $3840\times2160$ | Embedded competition overview |

The editable SVG versions remain in `figures/task07/`. Preserve aspect ratios
and do not crop axes, equations, result cards or the validation badge.

## Actual 16:9 layout

The slide uses a 13.333 by 7.5 inch canvas. The 4K summary is placed at
x = 0.12, y = 0.08, width = 13.09 and height = 7.36 inches, leaving a narrow
white safety margin around the validated asset.

The shared visual specification is in [`deck-style.md`](deck-style.md).

## Regenerating the package

```bash
cd presentation/task07
npm ci
npm run build
npm run preview
npm run validate
```

The generator copies all current validated assets, embeds the summary without
alteration, adds accessible alternative text and speaker notes, and writes the
PowerPoint with reproducible metadata.

## Final recording checklist

- Keep the probability curves, energy stems and uncertainty bound legible.
- Say “n squared,” “h-bar” and “half h-bar” clearly.
- Do not describe the energy values between integer quantum numbers as allowed.
- Do not imply that a stationary-state density moves with time.
- State that \(0.568\hbar\) is above, not equal to, the lower bound.
- Keep the complete ten-task screencast below three minutes.

The full explanation is in the
[`Task 7 scientific report`](../../task07_particle_in_box/RESULTS_AND_INTERPRETATION.md).
The exact final-package evidence and deterministic deck hash are recorded in
[`STAGE10_ACCEPTANCE.md`](STAGE10_ACCEPTANCE.md).
