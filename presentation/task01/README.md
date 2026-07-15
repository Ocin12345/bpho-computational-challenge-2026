# Task 1 PowerPoint Pack

This folder contains everything needed to make the Task 1 section of the final
presentation. The competition video is limited to three minutes for all ten
tasks, so the recommended version uses **one slide** and approximately
**16–17 seconds of narration**.

## Recommended slide

Use a blank **16:9 widescreen** slide.

1. Add the title **Task 1 — Two-Dimensional Random Walk** across the top.
2. Insert [`images/01_fifty_walks.png`](images/01_fifty_walks.png) on the left.
3. Insert [`images/02_endpoint_distribution.png`](images/02_endpoint_distribution.png)
   on the right.
4. Add the three short result lines from [`SLIDE_CONTENT.md`](SLIDE_CONTENT.md)
   beneath the right-hand image.
5. Paste the final script from [`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md) into the
   PowerPoint speaker-notes area.

### Suggested 16:9 layout

For a standard 13.33 by 7.50 inch PowerPoint slide:

| Element | Approximate position and size |
| --- | --- |
| Title | x = 0.55, y = 0.25, width = 12.2, height = 0.55 |
| 50-walk image | x = 0.55, y = 1.05, width = 5.75, height = 5.35 |
| Endpoint image | x = 6.60, y = 1.05, width = 5.75, height = 4.75 |
| Result text box | x = 6.60, y = 5.95, width = 5.75, height = 1.05 |

Keep each image's aspect ratio locked. Do not stretch it to fill the suggested
box exactly.

## Image choices

| File | Use |
| --- | --- |
| `01_fifty_walks.png` | Recommended main visual: 50 independent paths |
| `02_endpoint_distribution.png` | Recommended evidence of isotropy and radial spread |
| `03_statistical_validation.png` | Optional replacement if the validation graphs remain readable |
| `04_single_walk.png` | Optional simple visual when explaining how one path is constructed |
| `05_random_walk_animation.gif` | Optional animated replacement for the left image |

The static 50-walk image is the safest choice for the final video. PowerPoint
usually plays the GIF during a slideshow, but animation behaviour can change
when a presentation is exported or screen-recorded. Test the GIF before relying
on it.

## Presentation rule

The slide should show the model and its strongest evidence, not the entire
report. Avoid adding code screenshots or paragraphs of text. The detailed
derivation, testing, and limitations remain available in the full
[`Task 1 report`](../../task01_random_walk/README.md).

## Final checklist

- Use a 16:9 slide and preserve image aspect ratios.
- Keep the result text at least 24 pt and the title at least 30 pt.
- Use the 16–17-second script unless the final video plan gives Task 1 more
  time.
- Say “theta,” “two pi,” and “mean squared displacement” clearly.
- Record one practice attempt and check that the figures are readable at full
  video size.
- Do not exceed the overall three-minute competition limit.
