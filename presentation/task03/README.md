# Task 3 PowerPoint Pack

This folder contains the finished one-slide Task 3 presentation package. The
competition screencast is limited to three minutes for all ten tasks, so the
recommended version uses approximately **17–18 seconds of narration**.

## Ready-to-use slide

Open [`Task03_Planck_Einstein.pptx`](Task03_Planck_Einstein.pptx). It is an
editable 16:9 PowerPoint with:

- the validated Planck-spectrum figure on the left;
- the validated Einstein heat-capacity figure on the right;
- one quantitative caption beneath each graph;
- a compact 27/27 validation band;
- meaningful image alternative text; and
- the final competition script embedded in the speaker-notes area.

A high-resolution rendering is available at
[`preview/Task03_Planck_Einstein_preview.png`](preview/Task03_Planck_Einstein_preview.png).

## What to say

Use the final 17–18-second version in
[`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md). It is also stored inside the
PowerPoint speaker notes.

The same file contains:

- a 35-second expanded version;
- a 90-second rehearsal explanation;
- timed visual cues;
- a pronunciation guide; and
- answers to likely physics and numerical-method questions.

The exact visible text and image alternative text are recorded in
[`SLIDE_CONTENT.md`](SLIDE_CONTENT.md).

## Why the main slide uses these two figures

The official task requires the Planck spectrum at several temperatures and the
Einstein heat capacity for several solids. The main slide therefore gives the
largest area to those two required outputs. It does not replace them with code,
a long equation derivation, or a supporting validation graph.

The short validation band shows that the two principal analytical laws and the
Einstein limits were tested. Detailed errors remain visible in the optional
supporting figures and in the full report.

## Image folder

The [`images`](images/) folder is arranged so the slide can be rebuilt or
adapted quickly in PowerPoint, Keynote, or another editor:

| File | Use |
| --- | --- |
| `01_planck_spectra.png` | Required Planck comparison; left side of the main slide |
| `02_einstein_heat_capacity.png` | Required Einstein comparison; right side of the main slide |
| `03_planck_validation.png` | Optional supporting slide for Wien and Stefan--Boltzmann errors |
| `04_einstein_normalized.png` | Optional supporting slide for universal scaling and collapse |
| `05_task03_summary.png` | Optional standalone overview when Task 3 is presented by itself |

The corresponding SVG files remain in `figures/task03/` if a vector replacement
is preferred. Preserve aspect ratios and do not crop axis labels, units,
legends, peak markers, or the $3R$ limit.

## Actual 16:9 layout

The generated slide uses a 13.333 by 7.5 inch canvas:

| Element | Position and size in inches |
| --- | --- |
| Title | x = 0.52, y = 0.22, width = 12.30, height = 0.48 |
| Claim | x = 0.54, y = 0.76, width = 12.10, height = 0.28 |
| Planck card | x = 0.46, y = 1.29, width = 6.12, height = 4.28 |
| Einstein card | x = 6.75, y = 1.29, width = 6.12, height = 4.28 |
| Validation card | x = 0.46, y = 5.75, width = 12.41, height = 1.17 |

The design specification is saved in [`deck-style.md`](deck-style.md). It
matches the Task 2 slide for visual continuity across the final video.

## Regenerating the PowerPoint

The deck is reproducible from the committed Stage 9 figures:

```bash
cd presentation/task03
npm ci
npm run build
npm run preview
npm run validate
```

[`create_task03_presentation.js`](create_task03_presentation.js) copies the
current figure assets, reconstructs the editable layout, embeds the speaker
notes, and writes `Task03_Planck_Einstein.pptx`. Dependency versions are pinned
in `package-lock.json`. Preview rendering requires LibreOffice and Poppler; the
PowerPoint build itself requires only Node.js and the pinned package.

## Supporting-slide guidance

Use only the main slide in the three-minute ten-task submission. If Task 3 is
later presented on its own:

1. follow the main slide with `03_planck_validation.png` to explain the two
   independent Planck checks;
2. then show `04_einstein_normalized.png` to explain why $T/T_E$ is the natural
   material-independent variable; and
3. finish with the model limitations from the full scientific report.

Do not add those supporting slides to the short competition video unless the
overall timing plan explicitly creates more space for Task 3.

## Final recording checklist

- Open the slide in PowerPoint and confirm all text and both figures are sharp.
- Record at 16:9 and inspect the smaller graph labels at final video size.
- Use the 17–18-second script unless the complete timing plan assigns Task 3
  more time.
- Say “Wien” as “veen,” “T to the fourth,” and “three R” clearly.
- Do not describe the curves as measured solar or experimental heat-capacity
  data.
- Do not say carbon fails to approach $3R$; $800\ \mathrm K$ is not its
  high-temperature regime.
- Keep the complete screencast below three minutes.

The full equations, evidence, validation, interpretation, and limitations are
available in the
[`Task 3 scientific report`](../../task03_thermal_radiation/RESULTS_AND_INTERPRETATION.md).
