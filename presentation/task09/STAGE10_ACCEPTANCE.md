# Task 9 Stage 10 Acceptance — Competition Presentation

Status: **PASS**

Stage 10 packages the accepted Task 9 evidence into the one-slide competition
format used by the preceding tasks. The slide is concise enough for the
three-minute ten-task screencast while retaining the full official answer,
numerical anchor and validation status.

## Accepted deliverables

| Deliverable | Accepted result |
|---|---|
| PowerPoint | [`Task09_Compton_Scattering.pptx`](Task09_Compton_Scattering.pptx), one 16:9 slide |
| Rendered preview | [`preview/Task09_Compton_Scattering_preview.png`](preview/Task09_Compton_Scattering_preview.png), 4001 × 2250 |
| Primary visual | Byte-identical 3840 × 2160 Task 9 summary |
| Supporting assets | Four publication images plus the 73-frame animation copied byte-for-byte |
| Narration | 48 words, approximately 18 seconds |
| Speaker notes | Final script and four timed visual cues embedded in the PowerPoint |
| Accessibility | Meaningful alternative text covering the geometry, all three curve families, five energies, reference values and check totals |
| Typography | Times New Roman source visual and PowerPoint theme; Arial fallback rejected |
| Reproducibility | Two consecutive builds produced the same SHA-256 digest |

## Content acceptance

The slide visibly contains:

- the 200 keV, 90° momentum-vector construction;
- the required fractional wavelength-shift, electron-speed and recoil-angle
  graphs over 0° to 180°;
- all five official energies with both colour and line-style encoding;
- the 200 keV reference values 0.391390, 0.434186 c and 35.7050°;
- the forward-limit and backscatter endpoint note; and
- 44/44 core and 30/30 separately labelled extension checks.

The final narration states the three required trends and the validated reference
case. It does not claim that the optional cross-section extension changes the
official kinematics or that the free-electron calculation is a detector model.

## Render and visual inspection

LibreOffice converted the generated PowerPoint to PDF and Poppler rasterised the
slide at 300 DPI. The resulting 4001 × 2250 preview was inspected at original
resolution. The inspection found:

- no cropped title, equation, axis, legend, endpoint note or validation total;
- no overlap among the collision geometry, result cards and graph region;
- no stretched or blurred source visual;
- clear separation of all five energy curves by line style as well as colour;
- readable 90° reference guides and numerical callouts; and
- a clean white safety margin around the slide.

## Structural and portability checks

The presentation validator confirms:

- one slide, one notes page and one embedded image;
- the embedded image is byte-identical to the validated 4K source summary;
- a 13.333 × 7.5 inch widescreen canvas;
- reproducible document timestamps;
- a Times New Roman theme with no residual Arial typeface;
- no machine-specific paths in the PowerPoint XML or documentation;
- all local documentation links resolve;
- all five copied media assets match their sources and declared dimensions; and
- the 0.53 MiB PowerPoint remains below the 10 MiB portability budget.

Two consecutive builds produced SHA-256
`5d0c6fca1ebc64cb1a1d34e33a7801dd3198f77e9d61417e01f80c5f5a91dec3`.

Stage 10 is therefore complete. The slide is accurate, accessible, reproducible,
high-resolution and ready for the final repository-wide acceptance audit.
