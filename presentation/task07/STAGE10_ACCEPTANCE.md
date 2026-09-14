# Task 7 Stage 10 Acceptance — Competition Presentation

Status: **PASS**

The Task 7 presentation packages the accepted infinite-well and uncertainty
evidence into one accessible 16:9 competition slide.

## Accepted package

| Item | Accepted evidence |
|---|---|
| PowerPoint | [`Task07_Particle_In_A_Box.pptx`](Task07_Particle_In_A_Box.pptx), one slide with one notes page |
| Primary visual | Byte-identical 3840 × 2160 validated Task 7 summary |
| Supporting assets | Six source PNGs copied byte-for-byte into [`images/`](images/) |
| Preview | [`preview/Task07_Particle_In_A_Box_preview.png`](preview/Task07_Particle_In_A_Box_preview.png), 4001 × 2250 at 300 DPI |
| Narration | 47 words with an approximately 18-second cue sequence |
| Accessibility | Meaningful image alternative text, speaker notes and portable local assets |
| Typography | Times New Roman for the complete visible visual and PowerPoint theme |

## Acceptance checks

- The slide canvas is the standard 13.333 × 7.5 inch widescreen format.
- The embedded media is the current validated 4K Task 7 summary, not a
  recompressed or manually edited copy.
- The final script states the (n^2) energy law, normalized probability density,
  strict (0.568\hbar>0.5\hbar) ground-state result and 50-check validation.
- PowerPoint XML contains no machine-specific path and uses frozen created and
  modified timestamps.
- Both major and minor PowerPoint theme fonts are Times New Roman, with no
  residual Arial fallback in the generated theme.
- The 300-DPI preview was inspected at its original 4001 × 2250 resolution.
- Two consecutive deck builds produced the identical SHA-256 digest
  `7ef063c83114247375ee1ad73cfdc17c61ead78db1bf09eff1c2b98444ee0acc`.
- The accepted preview SHA-256 digest is
  `9dd03951fefdb795cc4c068cada0f3c0a8b5520ac74e884e76d18682cb2a89ac`.

## Reproduction

```bash
cd presentation/task07
npm ci
npm run build
npm run preview
npm run validate
```

Task 7 Stage 10 is accepted for integration into the final three-minute
competition screencast. Final cross-task timing remains a separate submission
integration gate.
