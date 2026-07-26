# Task 3 Presentation — Planck Radiation and Einstein Heat Capacity

This folder contains the finished one-slide Task 3 competition package,
standardized for the final Tasks 1–10 presentation.

## Final deliverables

- [PowerPoint](Task03_Planck_Einstein.pptx) — one 16:9 slide with speaker notes and meaningful
  image alternative text.
- [300-DPI preview](preview/Task03_Planck_Einstein_preview.png) — 4001 × 2250 pixels.
- [Embedded 4K summary](images/05_task03_summary.png) — byte-identical to the
  [validated source](../../figures/task03/task03_summary.png).
- [Final task narration](SPEAKER_SCRIPT.md) and [visible-content
  record](SLIDE_CONTENT.md).
- [Presentation validator](validate_task03_presentation.py).

The slide uses Times New Roman throughout. Its 3840 × 2160 master visual follows
model → quantitative validation → result, with axes, units, uncertainty
information and aspect ratios preserved. Supporting figures in the `images`
folder remain available for extended explanations but are not crowded onto the
three-minute competition slide.

## Rebuild and validation

Run from the `presentation` directory:

```bash
npm ci
node build_task_presentations.js 3
bash render_task_previews.sh
python3 task03/validate_task03_presentation.py
```

The current scientific regression suite contains 107 passing Task 3
tests. The presentation validator separately checks the slide, notes, embedded
4K summary, Times New Roman theme, reproducible timestamps, portability and
300-DPI preview.

The complete ten-slide deliverable is in the
[master presentation](../master/BPhO_Computational_Challenge_Tasks_1_to_10.pptx).
