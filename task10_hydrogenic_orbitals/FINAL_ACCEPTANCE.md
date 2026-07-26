# Task 10 Final Acceptance

Status: **PASS — complete and presentation-ready**

This record closes the staged Task 10 implementation after a presentation-layer
polish and full regression pass. The accepted scientific data and equations were
preserved. It covers normalized hydrogenic physics, the
complete official S-through-G gallery, the required coloured-glass construction,
the offline explorer, publication-grade static and animated media, technical
documentation and the final competition slide.

## Official requirement traceability

| Official requirement | Accepted evidence |
|---|---|
| Probability density for selected valid $n,l,m$ | Normalized real hydrogenic states are implemented for all 204 basis states through $n=8$ |
| Complete S, P, D, F and G examples | The direct gallery contains all 25 real states: 1s, 2p, 3d, 4f and 5g with every allowed $m$ |
| Radial and angular wavefunction structure | Independent radial profiles, radial roots, nodal counts and real spherical-harmonic references |
| Genuine three-dimensional result | Required 17-plane semi-transparent coloured-glass density, orthogonal slices, comparison figure and interactive camera |
| Clear physical coordinates and scale | Standard polar-colatitude convention, $n^2a$ coordinates and ångström/effective-Bohr values are explicit |
| Display threshold used correctly | The official 0.15 cutoff changes opacity only and never changes the full field or normalization |
| Screencast-readable computational output | 4K summary, 4K animation, offline explorer and accessible one-slide PowerPoint |

## Accepted scientific result

The normalized state is

$$
\psi_{nlm}(r,\vartheta,\varphi)
=R_{nl}(r)\mathcal Y_{lm}(\vartheta,\varphi),
\qquad
\int |\psi_{nlm}|^2\,d^3r=1,
$$

where $\mathcal Y_{lm}$ is the frozen real tesseral basis. The one-electron
point-Coulomb energy and length scales obey

$$
E_n=-\frac12E_h\frac{\mu}{m_e}\frac{Z^2}{n^2},
\qquad
a=\frac{m_e}{\mu}\frac{a_0}{Z}.
$$

For the displayed hydrogen-1 3d, $m=0$ reference state:

| Quantity | Accepted value |
|---|---:|
| Energy | −1.510914822816 eV |
| Effective Bohr length | 0.529467506530 Å |
| 99.95% radial extent | 15.13 Å |
| Radial nodes | 0 |
| Angular nodes | 2 |
| Parity | even |
| $m$ degeneracy | 5 |

All 22 independent science groups pass across the full 204-state acceptance
domain. The frozen state digest is
`d298695290395956560641493fc603e5970a4ea01609eca677b3b4b683fa085e`.

## Final acceptance matrix

| Layer | Final result |
|---|---:|
| Deterministic core-data regeneration | 7 files; PASS |
| Independent scientific validation | 22/22 checks |
| Data-manifest integrity | 6/6 content digests |
| Publication static media | 5 PNG figures, 4 editable SVGs and 4 embedded-font PDFs |
| Static-media manifest integrity | 13/13 files; 4,243,300 bytes |
| Motion package | 4K, 80 frames, 20 fps, exact 4-second loop |
| Motion-manifest integrity | 4/4 media items; 11,110,603 bytes |
| Static application validation | 23/23 checks |
| Documentation validation | 13/13 checks |
| Final artifact validation | 8/8 groups |
| Complete Python unit suite | 52/52 tests |
| JavaScript numerical suite | 6/6 tests; all 204 state summaries agree with Python |
| Browser UI smoke | PASS; 25 presets, 5 breakpoints, 67.30 ms maximum update |
| Accessibility and performance audit | 13 evidence groups; 0 detected violations; 67.60 ms maximum and 66.02 ms mean over 75 renders |
| Retained-memory evidence | 0.09 MB post-GC heap change |
| Motion browser audit | PASS; 4K WebP, five decoded views, 320 px reflow and reduced-motion poster |
| Presentation validation | 1 slide, 1 embedded 4K visual, 50-word script and 6 byte-identical assets |
| Presentation reproducibility | SHA-256 `71a7f923b2671f6b22d22e6c400affec5659d4a329240303b621924a039dc34e` twice |
| Python and JavaScript syntax checks | PASS |
| `git diff --check` | PASS |

## Visual-quality acceptance

- The complete gallery is 3840×2400; the summary and motion are 3840×2160.
  Every static PNG is stored at 300 DPI, with a 240-DPI motion poster.
- Four static figures have editable hybrid SVG companions and embedded-font PDF
  companions. The layered 3D transparency remains raster by design so its
  accepted opacity is preserved.
- Times New Roman is enforced across the static figures, motion, explorer and
  PowerPoint; the PDFs embed the font and the SVGs retain editable text.
- Every static PNG, the five-view motion contact sheet and the final 4001×2250
  presentation preview were inspected at original resolution.
- No cropped title, state label, result card, axis, legend, colour scale, footer,
  node, equation or validation total was found.
- Density, phase, visual threshold and camera rotation remain explicitly
  distinguished. The rotating view is not electron motion or time evolution.
- Colour is backed by labels or line styles where comparison is required, and
  the explorer reflows at 320 CSS pixels with keyboard, reduced-motion,
  forced-colour and 200% text support.

## Reproducibility and presentation handoff

- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) gives the frozen environment,
  deterministic generation order and complete validation commands.
- [`figures/task10`](../figures/task10/) contains the accepted static and motion
  evidence; both manifests record current dimensions and SHA-256 digests.
- [`presentation/task10/Task10_Hydrogenic_Orbitals.pptx`](../presentation/task10/Task10_Hydrogenic_Orbitals.pptx)
  is the finished one-slide 16:9 competition deck.
- [`presentation/task10/preview/Task10_Hydrogenic_Orbitals_preview.png`](../presentation/task10/preview/Task10_Hydrogenic_Orbitals_preview.png)
  is the inspected 300-DPI render.
- [`presentation/task10/SPEAKER_SCRIPT.md`](../presentation/task10/SPEAKER_SCRIPT.md)
  contains the final 50-word narration, timed visual cues and an expanded
  explanation.

## Scope boundary retained

The required model is one non-relativistic electron in an ideal point-Coulomb
field with reduced nuclear mass. It does not model electron-electron interaction,
screening, spin, fine or hyperfine structure, radiative effects, external fields,
finite nuclear size, chemical bonding, measurement dynamics or detector
response. The stationary density and its camera rotation are not an electron
trajectory.

Task 10 is therefore complete: every official S-through-G probability-density
requirement has direct passing evidence, the numerical implementation is
independently validated, the media meet the requested highest-quality standard,
the explorer is accessible and responsive, and the competition presentation is
ready to use.
