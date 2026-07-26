# Task 9 Final Acceptance

Status: **PASS — complete and presentation-ready**

This record closes the staged Task 9 implementation after a fresh end-to-end
regeneration and acceptance pass. It covers the exact relativistic calculation,
independent scientific validation, the optional Klein–Nishina extension, the
offline explorer, high-resolution static and animated media, technical
documentation and the final competition slide.

## Official requirement traceability

| Official requirement | Accepted evidence |
|---|---|
| Five incident photon energies | 50, 100, 200, 500 and 1000 keV are frozen in Python, JavaScript, figures and UI presets |
| Fractional wavelength shift against photon angle | Exact $\Delta\lambda/\lambda=E(1-\cos\theta)/(m_ec^2)$ curves over 0°–180° |
| Electron recoil speed against photon angle | Fully relativistic $v/c$ curves with a fixed 0–1 physical scale |
| Electron recoil angle against photon angle | Momentum-vector $\operatorname{atan2}$ result, with the undefined 0° direction disclosed and the 90° limit shown openly |
| Clear graphs for comparison | Five curves use stable colour plus distinct line style, common domains, direct labels and 90° reference guides |
| Demonstrable computational output | Offline interactive explorer, exact tables, publication figures, animation and PowerPoint are included |

## Accepted scientific result

For incident photon energy $E$,

$$
\frac{\Delta\lambda}{\lambda}
=\frac{E}{m_ec^2}(1-\cos\theta),
\qquad
E'=\frac{E}{1+\frac{E}{m_ec^2}(1-\cos\theta)},
$$

$$
\frac vc
=\sqrt{1-\left(1+\frac{E-E'}{m_ec^2}\right)^{-2}},
\qquad
\phi=\operatorname{atan2}\!\left(E'\sin\theta,E-E'\cos\theta\right).
$$

At the displayed 200 keV, 90° reference case,

| Quantity | Accepted value |
|---|---:|
| $\Delta\lambda/\lambda$ | 0.391390 |
| $v/c$ | 0.434186 |
| $\phi$ | 35.7050° |
| $E'$ | 143.7411 keV |
| Electron kinetic energy | 56.2589 keV |

Energy and both momentum components are conserved throughout all 3,605 official
states. The electron mass shell is independently checked, and every calculated
speed remains below $c$.

## Final acceptance matrix

| Layer | Final result |
|---|---:|
| Deterministic core-data regeneration | 5 files; PASS |
| Core scientific validation | 44/44 checks |
| Klein–Nishina data regeneration | 4 files; PASS |
| Extension validation | 30/30 checks |
| Static application validation | 21/21 checks, including strict typography |
| Documentation validation | 11/11 checks |
| Final artifact validation | 8/8 groups |
| Complete Python unit suite | 49/49 tests |
| JavaScript numerical suite | 5/5 tests; all 3,605 core and extension rows agree with Python |
| Browser UI smoke | PASS; exact default/forward/backscatter/custom states and five breakpoints |
| Browser performance evidence | 18.40 ms maximum measured update, below the 100 ms budget |
| Accessibility audit | 10 evidence groups; 0 detected WCAG 2.2 AA violations |
| Publication media | 4 PNG/SVG/PDF sets plus a 73-frame full-frame GIF |
| Media integrity manifest | 13 font-audited files; 6,718,965 bytes |
| Presentation validation | 1 slide, 1 embedded 4K visual, 48-word script and 5 byte-identical assets |
| Python and JavaScript syntax checks | PASS |
| `git diff --check` | PASS |

## Visual-quality acceptance

- The three analytical figures are 2400 × 1500 at 300 DPI and have editable SVG
  and PDF companions; the summary is 3840 × 2160 at 300 DPI with both vector
  companions. Every visual label and equation uses Times New Roman, and every
  PDF embeds the TrueType font.
- The 1600 × 900 animation contains 73 opaque full frames. Every frame is checked
  against black-clearing disposal artifacts, and a mid-playback Chromium frame
  was inspected after the full-frame writer correction.
- All five energies differ by line style as well as a restrained, synchronized
  colour palette. Shared legends occupy dedicated whitespace rather than the
  data region. The speed graph uses an honest fixed 0–1 scale, and endpoint
  conventions are stated on the figure.
- All four publication PNGs and the final 4001 × 2250 presentation render were
  inspected at original resolution. No clipping, overlap, distortion, misleading
  scaling or illegible annotation was found.
- Mobile reflow at 320 CSS pixels, 200% text resizing, keyboard navigation,
  reduced motion and forced-colour behaviour are included in acceptance. The
  browser smoke test also verifies the computed Times New Roman root font.

## Reproducibility and presentation handoff

- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) gives the frozen environment,
  deterministic build order and complete validation commands.
- [`figures/task09`](../figures/task09/) contains the accepted publication and
  animated evidence; its manifest records dimensions and SHA-256 digests.
- [`presentation/task09/Task09_Compton_Scattering.pptx`](../presentation/task09/Task09_Compton_Scattering.pptx)
  is the finished one-slide 16:9 competition deck.
- [`presentation/task09/preview/Task09_Compton_Scattering_preview.png`](../presentation/task09/preview/Task09_Compton_Scattering_preview.png)
  is the inspected 300-DPI render.
- Two consecutive deck builds produced SHA-256
  `5d0c6fca1ebc64cb1a1d34e33a7801dd3198f77e9d61417e01f80c5f5a91dec3`.

## Scope boundary retained

The required model is one photon scattering from one initially stationary, free
electron. It does not model atomic binding, material attenuation, multiple
scattering, beam polarisation, detector response, finite resolution or
experimental background. The separately labelled Klein–Nishina extension adds
ideal single-electron angular weighting only; it is not a bulk transport or
detector simulation.

Task 9 is therefore complete: every official graph is present and physically
correct, the numerical implementation is independently validated, the media meet
the requested highest-quality standard, the explorer is accessible and
responsive, and the competition presentation is ready to use.
