# Task 8 publication-figure contract

## Core conclusion

At the official detector settings, the supplied quantum model predicts a 75.0%
mismatch probability, twice the supplied classical value of 37.5%; the difference
is an exact model result, while finite observed counts fluctuate around the two
ideal probabilities.

## Figure architecture

- **Archetype:** asymmetric quantitative composite.
- **Backend:** Python with Matplotlib, exclusively for drawing, export and visual
  quality assurance.
- **Hero evidence:** the fixed-θ probability sweep, which displays both exact
  predictions on one 0–100% scale and marks the +37.5 percentage-point official
  contrast directly.
- **Generalization evidence:** the two-angle landscape, which distinguishes the
  quantum model's relative-angle bands from the classical model's dependence on
  both absolute detector settings.
- **Robustness evidence:** the finite-photon panel, which separates exact theory,
  one seeded observation and its 95% Wilson interval.
- **Summary evidence:** one asymmetric four-panel composite for presentation use;
  the sweep remains dominant while geometry, landscape and sampling are quieter.

Every panel has a distinct role. The finite-photon simulation is not presented as
additional evidence for the official ideal probabilities and is not cryptographic
randomness.

## Journal and export contract

- Primary editable formats: SVG and PDF with text retained as text.
- Preview format: RGB PNG at 300 DPI.
- Analytical figures: 2400 × 1500 pixels; summary: 3840 × 2160 pixels.
- Typography: Times New Roman throughout, retained at the user's explicit request.
  This is a deliberate house-style exception: a strict Nature submission would
  normally replace it with Arial or Helvetica before production.
- Panel labels: lowercase, bold and ordered from the top left.
- Axes: labelled quantities and units, outward ticks, no background gridlines.
- Colour: colour-blind-safe vermillion and blue, reinforced by solid and dashed
  line styles; diverging maps are centred at zero and rainbow maps are excluded.
- Integrity: the figure manifest records file size, digest, raster resolution,
  vector editability, font family and PDF font type for every representation.

## Statistics and source data

- The exact curves and angle landscapes are analytical evaluations, not fitted
  data; no p-value or inferential test applies.
- The finite-count intervals are 95% Wilson intervals for binomial proportions.
- The left sampling panel uses one reproducible experiment with 1,000 detected
  pairs and seed 2,026. The right panel uses the same seed across the displayed
  sample sizes and independent deterministic streams for the two models.
- Source data are `data/task08/angle_sweep.csv`,
  `data/task08/mismatch_grid.csv`, and
  `data/task08/finite_photon_reference.json`; their accepted digests are recorded
  in the core and statistical manifests.

## Image-integrity notes

The analytical curves and heatmaps are rendered directly from validated arrays.
There is no crop, local contrast adjustment, interpolation-based smoothing or
manual transcription of plotted values. Heatmap cells are rasterized only inside
otherwise editable SVG/PDF containers. The official markers are derived from the
same validated arrays as the curves and surfaces.

## Reviewer-risk checks

- The two probability curves always share a full 0–100% axis.
- Percentage-point differences are not described as percentage increases.
- The supplied classical equation is not generalized to every possible classical
  or hidden-variable theory.
- Exact model output and finite-sampling uncertainty remain visually separate.
- The official point is located at θ = −30°, φ = +30° in every figure.
- The pseudo-random sampler is labelled as educational and not cryptographically
  secure.
