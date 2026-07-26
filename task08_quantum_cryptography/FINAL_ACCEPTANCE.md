# Task 8 final acceptance

Status: **PASS — complete and presentation-ready**

This record closes the staged Task 8 implementation after a fresh end-to-end
regeneration and acceptance pass. It covers the official calculator, independent
scientific validation, the optional finite-photon extension, the high-resolution
figure and browser-evidence packages, the written explanation and the final
competition slide.

## Official requirement traceability

| Official requirement | Accepted evidence |
|---|---|
| Independently adjustable detector angles | Two synchronized controls for each angle, covering −90° to +90°, plus five named presets |
| Classical mismatch equation | Implemented in Python and JavaScript and checked against an algebraically independent double-angle reference |
| Quantum mismatch equation | Implemented in Python and JavaScript and checked independently over exact cases, a 361-point sweep and a two-dimensional grid |
| Immediate comparison on a common scale | Live classical-solid and quantum-dashed curves use the same fixed 0–100% axis |
| Visible detector orientations and angle difference | Two detector dials and the relative-angle annotation update with every control route |
| Probabilities and percentages | Accessible result cards expose both forms and the signed percentage-point difference |
| Official reference setting | $\theta=-30^\circ$, $\phi=+30^\circ$ gives exactly $P_{\mathrm C}=37.5\%$ and $P_{\mathrm Q}=75.0\%$ |
| Local, demonstrable output | Offline static app runs from the supplied Python server and has desktop, mobile and keyboard acceptance evidence |

## Accepted scientific result

For the official detector setting,

$$
P_{\mathrm C}=\frac38=37.5\%,
\qquad
P_{\mathrm Q}=\frac34=75.0\%,
$$

so the signed difference is **+37.5 percentage points**. The complete analytical
comparison is documented in [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md),
including

$$
P_{\mathrm Q}-P_{\mathrm C}
=-\frac12\sin(2\theta)\sin(2\phi).
$$

The optional finite-photon demonstration is deliberately separate from this
ideal answer. Its default seeded example produces 363 classical and 770 quantum
mismatches from 1,000 pairs; these are reproducible sample counts, not replacement
theory values.

## Final acceptance matrix

| Layer | Final result |
|---|---:|
| Deterministic core-data generation | 5 files; PASS |
| Core scientific validation | 42/42 checks |
| Statistical-data generation | 3 files; PASS |
| Statistical validation | 24/24 checks |
| Documentation validation | 10/10 checks |
| Final artifact validation | 8/8 groups |
| Complete Python unit suite | 54/54 tests |
| JavaScript numerical suite | 10/10 tests |
| Static application validation | PASS |
| Browser UI smoke | PASS; 361-point chart, desktop/mobile, official/aligned/perpendicular cases |
| Browser performance evidence | 1.10 ms maximum angle update; 4.50 ms for a 100,000-pair sample |
| Accessibility audit | 11 evidence groups; 0 detected WCAG 2.2 AA violations |
| Browser capture audit | 3 × 3840 × 2160 and 1 × 860 × 1864; no console, page or external-network errors |
| Publication figures | 4 PNG/SVG/PDF sets (12 files); embedded Times New Roman, correct dimensions, 300 DPI raster metadata, editable text, hashes and package budget |
| Presentation validation | 1 slide, Times New Roman theme, 1 embedded 4K visual, 49-word script, 4001 × 2250 preview and 8 byte-identical assets |
| Python and JavaScript syntax checks | PASS |
| `git diff --check` | PASS |

## Visual-quality acceptance

- The three analytical figures are 2400 × 1500 at 300 DPI and have editable SVG
  and PDF companions; the summary is 3840 × 2160 at 300 DPI with both vector
  companions. The generator, SVG audit, PDF embedded-font audit and integrity
  manifest all require Times New Roman without fallback.
- Classical and quantum predictions differ by both colour and line style, and
  every probability comparison uses an explicit common scale.
- The official setting, exact values, uncertainty intervals and optional-sample
  status are labelled directly rather than left to visual inference.
- All four publication PNGs, all four Times New Roman browser captures and the
  4001 × 2250 presentation render were inspected at original resolution. No
  clipping, overlap, distortion or illegible annotation was found.
- Mobile reflow at 320 CSS pixels, 200% text resizing, keyboard navigation,
  reduced motion and forced-colour behaviour are included in acceptance.

## Reproducibility and presentation handoff

- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) gives the frozen environment,
  deterministic build order and complete validation commands.
- [`figures/task08/manifest.json`](../figures/task08/manifest.json) binds every
  publication PNG/SVG/PDF to its dimensions, DPI, font and SHA-256 digest. The
  screenshot manifest similarly records browser dimensions, Times New Roman and
  SHA-256 digests.
- [`presentation/task08/Task08_Quantum_Mismatch_Calculator.pptx`](../presentation/task08/Task08_Quantum_Mismatch_Calculator.pptx)
  is the finished one-slide 16:9 competition deck.
- [`presentation/task08/preview/Task08_Quantum_Mismatch_Calculator_preview.png`](../presentation/task08/preview/Task08_Quantum_Mismatch_Calculator_preview.png)
  is the inspected 4001 × 2250, 300-DPI render.
- Two consecutive deck builds, including the final rebuild from freshly generated
  assets, produced SHA-256
  `bf607a4dd99a3325a9ef15dd35d74a52b286684c5aa22568e5f5a0d7ddb06d66`.

## Scope boundary retained

The package is a comparison calculator for the two equations supplied by the
official question. It is not a complete QKD protocol, Bell-test analysis or
security proof. It assumes ideal pairs and perfect two-outcome detectors and does
not model loss, dark counts, decoherence or eavesdropping. The pseudo-random
finite sampler is educational and must not be used for cryptographic key
generation.

Task 8 is therefore complete: the required calculator works, the official result
is reproduced exactly, the extension is clearly bounded, the figures meet the
requested high-quality standard, and the presentation package is ready to use.
