# Task 4 PowerPoint Pack

This folder contains the finished one-slide Task 4 presentation package. The
competition screencast is limited to three minutes for all ten tasks, so the
recommended version uses approximately **17–18 seconds of narration**.

## Ready-to-use slide

Open [`Task04_Photoelectric_Effect.pptx`](Task04_Photoelectric_Effect.pptx). It
is an editable 16:9 PowerPoint with:

- the required validated nine-metal frequency graph as the dominant visual;
- the optional validated sodium GIF as a smaller explanatory extension;
- both governing equation forms;
- the $516.6\ \mathrm{nm}$ sodium visible-light cut-off;
- a compact 43/43 validation badge;
- meaningful alternative text for both embedded visuals; and
- the final competition script embedded in the speaker-notes area.

A high-resolution static rendering is available at
[`preview/Task04_Photoelectric_Effect_preview.png`](preview/Task04_Photoelectric_Effect_preview.png).
The preview shows the GIF's first frame; the GIF animates in PowerPoint slide
show mode. The embedded animation is a six-second, 60-frame,
$1920\times1080$ GIF rendered at 10 frames per second.

## What to say

Use the final 17–18-second version in
[`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md). It is also stored inside the
PowerPoint speaker notes.

The same file contains:

- a 35-second expanded version;
- a 90-second rehearsal explanation;
- timed visual cues;
- a pronunciation guide; and
- answers to likely physics, modelling, and validation questions.

The exact visible text and image alternative text are recorded in
[`SLIDE_CONTENT.md`](SLIDE_CONTENT.md).

## Why the slide uses these two visuals

The official requirement is a stopping-potential comparison against frequency
or vacuum wavelength for various metals. The frequency graph therefore receives
the largest area. It includes all nine source records, analytical cut-offs, and
the honest Ag/Al/Pb overlap.

The smaller GIF adds threshold, intensity, and stopping-potential intuition
that the static graph cannot show. It remains visibly secondary and does not
replace the quantitative result.

## Image folder

The [`images`](images/) folder is arranged so the slide can be rebuilt or
adapted quickly in PowerPoint, Keynote, or another editor:

| File | Dimensions | Use |
| --- | ---: | --- |
| `01_stopping_voltage_frequency.png` | $3840\times2160$ | Required comparison; main competition visual |
| `02_photoelectric_demo.gif` | $1920\times1080$ | Optional threshold/intensity/stopping extension |
| `03_stopping_voltage_wavelength.png` | $3840\times2160$ | Optional wavelength and visible-band support |
| `04_copper_threshold_explanation.png` | $3200\times1800$ | Optional physical-domain explanation |
| `05_photoelectric_validation.png` | $3840\times1920$ | Optional detailed validation evidence |
| `06_task04_summary.png` | $3840\times2160$ | Optional standalone four-panel overview |
| `07_photoelectric_demo_storyboard.png` | $2400\times1350$ | Static fallback when GIF playback is unavailable |

The corresponding SVG files remain in `figures/task04/` where available.
Preserve aspect ratios and do not crop axes, units, legends, threshold markers,
status labels, or explanatory notes.

## Actual 16:9 layout

The generated slide uses a 13.333 by 7.5 inch canvas:

| Element | Position and size in inches |
| --- | --- |
| Title | x = 0.52, y = 0.22, width = 12.30, height = 0.48 |
| Claim | x = 0.54, y = 0.76, width = 12.10, height = 0.28 |
| Required-graph card | x = 0.46, y = 1.29, width = 8.02, height = 5.63 |
| Animation card | x = 8.68, y = 1.29, width = 4.19, height = 2.94 |
| Equation/evidence card | x = 8.68, y = 4.42, width = 4.19, height = 2.50 |

The design specification is saved in [`deck-style.md`](deck-style.md). It
matches the Task 2 and Task 3 slides for visual continuity across the final
video.

## Regenerating the PowerPoint

The deck is reproducible from the committed Stage 10 figures:

```bash
cd presentation/task04
npm ci
npm run build
npm run preview
npm run validate
```

[`create_task04_presentation.js`](create_task04_presentation.js) copies the
current validated visual assets, reconstructs the editable layout, embeds the
speaker notes, and writes `Task04_Photoelectric_Effect.pptx`. Dependency
versions are pinned in `package-lock.json`. Preview rendering requires
LibreOffice and Poppler; the PowerPoint build itself requires only Node.js and
the pinned package.

The exporter freezes the PowerPoint creation and modification metadata to
`2026-01-01T00:00:00Z` as a reproducibility marker; it is not the real build
time. This prevents the current clock from changing an otherwise identical
file.

## Supporting-slide guidance

Use only the main slide in the three-minute ten-task submission. If Task 4 is
later presented on its own:

1. follow the main slide with `03_stopping_voltage_wavelength.png` to explain
   sodium's visible-light range;
2. use `04_copper_threshold_explanation.png` to distinguish the physical curve
   from negative mathematical extrapolation;
3. show `05_photoelectric_validation.png` to explain analytical and numerical
   agreement; and
4. use `07_photoelectric_demo_storyboard.png` if the GIF cannot play.

Do not add those supporting slides to the short competition video unless the
overall timing plan explicitly creates more space for Task 4.

## Final recording checklist

- Open the slide in PowerPoint and confirm the graph labels remain sharp.
- Start slide-show mode and confirm that the GIF cycles through all four scenes.
- Record at 16:9 and inspect labels at final video size.
- Use the 17–18-second script unless the complete timing plan assigns Task 4
  more time.
- Say “h over e,” “five hundred and seventeen nanometres,” and “forty-three”
  clearly.
- Do not call the negative extrapolation a measured negative stopping voltage.
- Do not imply that all visible wavelengths eject electrons from sodium.
- Do not describe schematic GIF trajectories or counts as quantitative.
- Keep the complete screencast below three minutes.

The full equations, evidence, validation, interpretation, and limitations are
available in the
[`Task 4 scientific report`](../../task04_photoelectric_effect/RESULTS_AND_INTERPRETATION.md).
