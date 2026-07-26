# Task 9 accessibility audit

## Scope

The audit exercises the locally served Task 9 explorer in Chromium. It is an automated engineering audit against the relevant WCAG 2.2 AA behaviours; it is not a substitute for a formal third-party conformance assessment.

## Result

All ten evidence groups passed with zero detected violations in the tested behaviours.

| Evidence group | WCAG criteria | Result |
|---|---|---:|
| Semantic structure, names and dynamic descriptions | 1.1.1, 1.3.1, 3.3.2, 4.1.2, 4.1.3 | Pass |
| Chromium accessibility-tree exposure | 1.3.1, 4.1.2 | Pass |
| Text and essential non-text contrast | 1.4.3, 1.4.11 | Pass |
| Colour-independent curve encoding and honest speed scale | 1.4.1 | Pass |
| Complete keyboard route and visible focus | 2.1.1, 2.4.3, 2.4.7 | Pass |
| Working skip link | 2.4.1 | Pass |
| Keyboard operation and announced live update | 2.1.1, 4.1.3 | Pass |
| 320 px reflow | 1.4.10 | Pass |
| 200% text resize | 1.4.4 | Pass |
| Reduced-motion and forced-colour preferences | 1.4.11, 2.3.3 | Pass |

## Measured evidence

- 11 ordered, non-empty headings.
- 16 named controls.
- Six SVG figures with programmatic titles and dynamically updated descriptions.
- Five named, keyboard-focusable chart scroll regions.
- 614 nodes exposed in the Chromium accessibility tree; all principal controls, the energy-retention progress element and all required figures were named.
- 21 focusable elements reached exactly once in DOM order.
- Every tested focus indicator was at least 3 px.
- Minimum tested text contrast: 4.71:1.
- Minimum tested graph/component contrast: 3.15:1.
- Five visibly written line-style descriptions and five distinct SVG dash patterns prevent energy curves from relying on colour alone.
- No page-level horizontal overflow at 320 px.
- No clipping of principal text regions at 200% root text size.

## Reproduce

With Playwright and Chromium available to Node:

```bash
cd task09_compton_scattering/app
npm run test:a11y
```

The executable can be selected with `TASK09_CHROMIUM_EXECUTABLE`; the audit port can be changed with `TASK09_A11Y_PORT`.
