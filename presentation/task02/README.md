# Task 2 PowerPoint Pack

This folder contains the finished one-slide Task 2 presentation package. The
competition screencast is limited to three minutes for all ten tasks, so the
recommended version uses approximately **17–18 seconds of narration**.

## Ready-to-use slide

Open [`Task02_Brownian_Motion.pptx`](Task02_Brownian_Motion.pptx). It is an
editable 16:9 PowerPoint with:

- the 180-frame reference GIF embedded on the left;
- the 64-run MSD and endpoint evidence on the right;
- three concise result lines;
- meaningful image alternative text; and
- the final competition script embedded in the speaker-notes area.

A high-resolution rendering is available at
[`preview/Task02_Brownian_Motion_preview.png`](preview/Task02_Brownian_Motion_preview.png).
The preview shows the first GIF frame because PDF is static. In PowerPoint
slideshow mode, the embedded GIF should play automatically.

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

## Image folder

The [`images`](images/) folder is arranged so a replacement slide can be made
quickly in PowerPoint, Keynote, or another editor:

| File | Use |
| --- | --- |
| `01_reference_animation.gif` | Recommended model visual; 180 frames over the full 200 ps run |
| `02_baseline_statistics.png` | Main statistical evidence; use on the recommended slide |
| `03_reference_particle_scene.png` | Static fallback if GIF playback or video export is unreliable |
| `04_parameter_experiments.png` | Optional supporting slide if extra time is later available |
| `05_numerical_validation.png` | Optional numerical-method evidence or answer to a follow-up question |

Do not replace the baseline figure with the parameter-experiment figure on the
main slide. The baseline figure directly supports the central Brownian-motion
claim, whereas several parameter confidence intervals overlap and require more
careful explanation.

## Actual 16:9 layout

The generated slide uses a 13.333 by 7.5 inch canvas:

| Element | Position and size in inches |
| --- | --- |
| Title | x = 0.52, y = 0.22, width = 12.30, height = 0.48 |
| Claim | x = 0.54, y = 0.76, width = 12.10, height = 0.28 |
| Animation card | x = 0.46, y = 1.31, width = 4.38, height = 5.69 |
| Statistical card | x = 5.04, y = 1.31, width = 7.84, height = 3.58 |
| Result card | x = 5.04, y = 5.08, width = 7.84, height = 1.92 |

The design specification is saved in [`deck-style.md`](deck-style.md). Preserve
image aspect ratios and do not crop axes, legends, confidence intervals, or
units.

## GIF and static fallback

Test the PowerPoint in slideshow mode before recording. If the GIF does not
play reliably on the recording computer or becomes static during export:

1. replace the left GIF with `images/03_reference_particle_scene.png`;
2. keep the same position and size;
3. use the same final script—the phrase “producing an irregular path” remains
   accurate; and
4. if animation is still required, screen-record the GIF separately and place
   the clip over the left card during final video editing.

The slide does not depend on GIF playback for its statistical conclusion.

## Regenerating the PowerPoint

The deck is reproducible from the committed Step 9 figures:

```bash
cd presentation/task02
npm ci
npm run build
```

[`create_task02_presentation.js`](create_task02_presentation.js) copies the
current figure assets, reconstructs the editable layout, embeds the speaker
notes, and writes `Task02_Brownian_Motion.pptx`. Dependency versions are pinned
in `package-lock.json`.

## Final recording checklist

- Open the slide in PowerPoint and confirm the GIF plays from beginning to end.
- Record at 16:9 and check that the smaller labels in the MSD figure are still
  readable at final video size.
- Use the 17–18-second script unless the complete ten-task timing plan assigns
  Task 2 more time.
- Say “R squared zero point nine eight three” and “two point two five times ten
  to the minus three” clearly.
- Do not claim that one reference trajectory proves diffusion; the 64-run
  ensemble is the evidence.
- Do not claim that the parameter trends are universal physical laws.
- Keep the complete screencast below three minutes.

The full derivation, implementation, validation, statistical design, and model
limitations remain in the
[`Task 2 report`](../../task02_brownian_motion/README.md).
