# Task 8 Stage 9 acceptance: presentation package

Status: **PASS**

Stage 9 converts the accepted Task 8 evidence into a concise competition-ready
presentation without changing the scientific content or redrawing an already
validated figure.

## Deliverables accepted

- [`Task08_Quantum_Mismatch_Calculator.pptx`](Task08_Quantum_Mismatch_Calculator.pptx)
  is a one-slide, 16:9 PowerPoint presentation.
- [`preview/Task08_Quantum_Mismatch_Calculator_preview.png`](preview/Task08_Quantum_Mismatch_Calculator_preview.png)
  is a 4001 × 2250, 300-DPI full-slide render used for visual inspection.
- [`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md) contains the final 49-word narration,
  expanded explanation, timing cues and likely questions.
- [`SLIDE_CONTENT.md`](SLIDE_CONTENT.md) records the visible content and image
  alternative text.
- [`deck-style.md`](deck-style.md) records the shared competition deck style.
- [`images`](images/) contains eight byte-identical copies of the accepted
  publication and application assets.
- [`create_task08_presentation.js`](create_task08_presentation.js),
  [`render_preview.sh`](render_preview.sh) and
  [`validate_task08_presentation.py`](validate_task08_presentation.py) reproduce
  and validate the package.

## Scientific communication accepted

The slide displays the official detector geometry and the exact results

$$
P_{\mathrm C}=37.5\%,
\qquad
P_{\mathrm Q}=75.0\%
$$

at $\theta=-30^\circ$ and $\phi=+30^\circ$. The sweep, signed-contrast map and
finite-photon example remain visibly distinct. The narration calls the sample a
finite counting demonstration and does not present the calculator as a complete
QKD protocol or security proof.

## Design and accessibility accepted

- The previously validated 3840 × 2160 summary is embedded unchanged, preserving
  its exact curves, axes, labels, uncertainty intervals and validation statement.
- The editable PowerPoint theme and the validated embedded summary consistently
  use Times New Roman; presentation validation rejects an Arial fallback.
- The image is placed inside a narrow white safety margin without cropping or
  aspect-ratio distortion.
- Full-resolution visual inspection found no clipping, overlap, stretched
  content or illegible labels.
- Meaningful alternative text is attached to the embedded image.
- The final script is stored in the PowerPoint speaker notes.
- The one-slide format and approximately 18-second narration are appropriate for
  the three-minute, ten-task competition recording.

## Reproducibility audit

- Presentation validation: **PASS** — one slide, one embedded 4K visual,
  49-word final script, 4001 × 2250 300-DPI preview and eight byte-identical
  source assets.
- Two consecutive builds produced the same PowerPoint SHA-256 digest:
  `bf607a4dd99a3325a9ef15dd35d74a52b286684c5aa22568e5f5a0d7ddb06d66`.
- Preview rendering through LibreOffice and Poppler: **PASS**.
- Python validation-script compilation: **PASS**.

Stage 9 is therefore complete and ready for inclusion in the final competition
presentation.
