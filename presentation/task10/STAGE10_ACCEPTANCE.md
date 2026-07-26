# Task 10 Stage 10 Acceptance — Competition Presentation

Status: **PASS**

Stage 10 packages the accepted Task 10 orbital evidence into the one-slide
competition format used by the preceding tasks. The slide is concise enough for
the three-minute ten-task screencast while retaining the required coloured-glass
view, systematic orbital structure, exact scaling and validation status.

## Accepted deliverables

| Deliverable | Accepted result |
|---|---|
| PowerPoint | [`Task10_Hydrogenic_Orbitals.pptx`](Task10_Hydrogenic_Orbitals.pptx), one 16:9 slide |
| Rendered preview | [`preview/Task10_Hydrogenic_Orbitals_preview.png`](preview/Task10_Hydrogenic_Orbitals_preview.png), 4001 × 2250 at 300 DPI |
| Primary visual | Byte-identical 3840 × 2160 Task 10 summary |
| Supporting assets | Five additional publication images copied byte-for-byte |
| Narration | 50 words, approximately 18 seconds |
| Speaker notes | Final script and four timed visual cues embedded in the PowerPoint |
| Accessibility | Meaningful alternative text covering the 3d example, family progression, radial graph, exact values and check totals |
| Reproducibility | Two consecutive builds produced the same SHA-256 digest |
| Typography | Times New Roman in the source visual and PowerPoint theme |

## Content acceptance

The slide visibly contains:

- the required 17-plane semi-transparent coloured-glass rendering of hydrogen
  3d, $m=0$;
- the numerical energy, 99.95% radius, radial-node and angular-node result
  cards;
- the official S-through-G progression 1s, 2p, 3d, 4f and 5g for $m=0$;
- scaled radial-probability curves with five distinguishable line styles;
- 22/22 scientific checks across 204 validated states; and
- explicit threshold, coordinate and camera-motion caveats.

The final narration states the 25-state scope, three-dimensional density and
nodes, exact $Z^2/n^2$ energy and $1/Z$ size scaling, and the camera-motion
caveat. It does not describe an electron trajectory or claim that thresholding
changes the probability density.

## Render and visual inspection

LibreOffice converted the generated PowerPoint to PDF and Poppler rasterised the
slide at 300 DPI. The resulting 4001 × 2250 preview was inspected at original
resolution. The inspection found:

- no cropped title, subtitle, result card, axis, legend, footer or validation
  total;
- no overlap among the coloured-glass view, family strip and radial graph;
- no stretched, blurred or recompressed source visual;
- readable state labels, numerical anchors, line-style legend and scaling
  equations;
- clean separation of orbital density from the white page background; and
- a uniform white safety margin around the slide.

## Structural and portability checks

The presentation validator confirms:

- one slide, one notes page and one embedded image;
- the embedded image is byte-identical to the validated 4K source summary;
- a 13.333 × 7.5 inch widescreen canvas;
- reproducible document timestamps;
- no machine-specific paths in the PowerPoint XML or documentation;
- all local documentation links resolve;
- all six copied media assets match their sources and declared dimensions; and
- the 0.58 MiB PowerPoint remains below the 10 MiB portability budget.

Two consecutive builds produced SHA-256
`71a7f923b2671f6b22d22e6c400affec5659d4a329240303b621924a039dc34e`.

Stage 10 is therefore complete. The slide is accurate, accessible,
reproducible, high-resolution and ready for the final repository-wide
acceptance audit.
