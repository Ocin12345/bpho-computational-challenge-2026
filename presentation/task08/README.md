# Task 8 PowerPoint Pack

This folder contains the finished one-slide Task 8 competition presentation. The
full ten-task screencast is limited to three minutes, so the recommended version
uses approximately **18 seconds of narration**.

## Ready-to-use slide

Open [`Task08_Quantum_Mismatch_Calculator.pptx`](Task08_Quantum_Mismatch_Calculator.pptx).
It is an editable 16:9 PowerPoint wrapper around the validated 4K Task 8 summary
and includes:

- the detector geometry and official angles;
- the exact classical/quantum sweep and official 37.5%/75.0% markers;
- the full signed-contrast heatmap;
- the separately labelled finite-photon example;
- a concise 42/42 scientific and 24/24 statistical validation statement;
- meaningful image alternative text; and
- the final competition script in the speaker-notes area.

The PowerPoint theme and every embedded source visual use Times New Roman. The
finished preview is 4001 × 2250 at 300 DPI for close inspection and clean export.

A high-resolution rendering is available at
[`preview/Task08_Quantum_Mismatch_Calculator_preview.png`](preview/Task08_Quantum_Mismatch_Calculator_preview.png).

## What to say

Use the final 49-word version in [`SPEAKER_SCRIPT.md`](SPEAKER_SCRIPT.md). The same
script is embedded in the PowerPoint notes. The file also contains an expanded
version, timed visual cues, pronunciation guidance and likely questions.

The exact visible content and image alternative text are recorded in
[`SLIDE_CONTENT.md`](SLIDE_CONTENT.md).

## Visual hierarchy

The slide embeds [`task08_summary.png`](../../figures/task08/task08_summary.png)
almost full-canvas. The geometry introduces the 60° official setting; the exact
sweep is the primary answer; the heatmap and finite sample provide supporting
interpretation; the validation statement finishes the evidence chain without
decorative status boxes.

## Image folder

The [`images`](images/) folder contains byte-identical copies of the accepted
publication PNGs and application captures. The PowerPoint embeds the 4K summary;
the other images remain available for a longer presentation or close-up edit.

| File | Dimensions | Use |
|---|---:|---|
| `01_probability_sweep.png` | 2400 × 1500 | Exact fixed-θ comparison |
| `02_mismatch_landscape.png` | 2400 × 1500 | Full two-angle surfaces |
| `03_finite_photon_sampling.png` | 2400 × 1500 | Sampling interpretation |
| `04_task08_summary.png` | 3840 × 2160 | Embedded competition overview |
| `05_detector_workspace_4k.png` | 3840 × 2160 | Interactive detector close-up |
| `06_probability_chart_4k.png` | 3840 × 2160 | Interactive graph close-up |
| `07_finite_photon_extension_4k.png` | 3840 × 2160 | Sampling UI close-up |
| `08_finite_photon_mobile_2x.png` | 860 × 1864 | Responsive-layout evidence |

The editable publication SVGs remain in `figures/task08/`. Preserve aspect ratios
and do not crop equations, axes, heatmap scales, finite-sample labels or the
validation statement.

## Actual 16:9 layout

The slide uses a 13.333 by 7.5 inch canvas. The 4K summary is placed at x = 0.12,
y = 0.08, width = 13.09 and height = 7.36 inches, leaving a narrow white safety
margin around the validated asset.

The shared visual specification is in [`deck-style.md`](deck-style.md).

## Regenerate the package

```bash
cd presentation/task08
npm ci
npm run build
npm run preview
npm run validate
```

The generator copies all current validated assets, embeds the summary unchanged,
adds accessible alternative text and speaker notes, and writes the PowerPoint with
reproducible metadata.

## Final recording checklist

- Say “thirty-seven point five percent” and “seventy-five percent” clearly.
- Describe orange as classical solid and teal as quantum dashed if colour is not
  visible to the audience.
- Keep both curves on the same 0–100% scale.
- Call the lower-right result a reproducible finite sample, not exact theory.
- Do not claim that the calculator is a complete QKD protocol or security proof.
- Finish on the validation statement and keep the ten-task screencast below three
  minutes.

The full explanation is in the
[`Task 8 results report`](../../task08_quantum_cryptography/RESULTS_AND_INTERPRETATION.md).
The completed presentation audit is recorded in
[`STAGE9_ACCEPTANCE.md`](STAGE9_ACCEPTANCE.md).
The end-to-end calculator handoff is recorded in
[`FINAL_ACCEPTANCE.md`](../../task08_quantum_cryptography/FINAL_ACCEPTANCE.md).
