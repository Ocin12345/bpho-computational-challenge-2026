# Task 6 Presentation — Electron Diffraction

This folder contains the finished one-slide Task 6 competition package,
standardized for the final Tasks 1–10 presentation.

## Final deliverables

- [PowerPoint](Task06_Electron_Diffraction.pptx) — one 16:9 slide with speaker notes and meaningful
  image alternative text.
- [300-DPI preview](preview/Task06_Electron_Diffraction_preview.png) — 4001 × 2250 pixels.
- [Embedded 4K summary](images/06_task06_summary.png) — byte-identical to the
  [validated source](../../figures/task06/task06_summary.png).
- [Final task narration](SPEAKER_SCRIPT.md) and [visible-content
  record](SLIDE_CONTENT.md).
- [Presentation validator](validate_task06_presentation.py).

The slide uses Times New Roman throughout. Its 3840 × 2160 master visual follows
model → quantitative validation → result, with axes, units, uncertainty
information and aspect ratios preserved. Supporting figures in the `images`
folder remain available for extended explanations but are not crowded onto the
three-minute competition slide.

## Rebuild and validation

Run from the `presentation` directory:

```bash
npm ci
node build_task_presentations.js 6
bash render_task_previews.sh
python3 task06/validate_task06_presentation.py
```

The current scientific regression suite contains 29 passing Task 6
tests. The presentation validator separately checks the slide, notes, embedded
4K summary, Times New Roman theme, reproducible timestamps, portability and
300-DPI preview.

The complete ten-slide deliverable is in the
[master presentation](../master/BPhO_Computational_Challenge_Tasks_1_to_10.pptx).
