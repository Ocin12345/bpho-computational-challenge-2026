# Task 10 Accessibility Audit

## Scope

The audit exercises the locally served Task 10 explorer in Chromium. It is an
automated engineering audit against relevant WCAG 2.2 AA behaviours, not a
substitute for a formal third-party conformance assessment.

## Result

All thirteen evidence groups passed with zero detected violations in the tested
behaviours.

| Evidence group | Criteria or quality area | Result |
|---|---|---:|
| Invalid route and security headers | Robustness and local security | Pass |
| Semantic structure, names, fallbacks and live descriptions | 1.1.1, 1.3.1, 3.3.2, 4.1.2, 4.1.3 | Pass |
| Chromium accessibility-tree exposure | 1.3.1, 4.1.2 | Pass |
| Text and essential non-text contrast | 1.4.3, 1.4.11 | Pass |
| Complete keyboard route and visible focus | 2.1.1, 2.4.3, 2.4.7 | Pass |
| Working skip link | 2.4.1 | Pass |
| Keyboard operation and announced update | 2.1.1, 4.1.3 | Pass |
| Validated domain endpoint | Scientific input robustness | Pass |
| 320 px reflow | 1.4.10 | Pass |
| 200% text resize | 1.4.4 | Pass |
| Reduced-motion and forced-colour preferences | 1.4.11, 2.3.3 | Pass |
| Gallery performance and retained memory | Interaction quality | Pass |
| Offline runtime integrity | Privacy and robustness | Pass |

## Measured evidence

- Nine ordered, non-empty headings.
- Fifteen named form/button controls.
- Five programmatically named scientific figures: four canvases and one SVG.
- Meaningful fallback text in all four Canvas elements.
- 396 nodes exposed in Chromium's accessibility tree; the main state controls
  and every scientific figure are exposed by name.
- Eighteen focusable elements reached exactly once in DOM order.
- Every tested focus indicator is at least 3 px.
- Minimum tested normal-text contrast: 5.50:1.
- Minimum tested component/graph contrast: 3.68:1.
- No page-level horizontal overflow at 320 px.
- No clipping of principal text regions at 200% root text size.
- The full validated endpoint (Z=20,n=8,l=7,m=+7) renders finite results.
- Seventy-five full official-gallery renders have a maximum time of 67.60 ms
  and a mean time of 66.02 ms.
- Post-garbage-collection heap change after that stress cycle is 0.09 MB.
- Zero browser-console errors, uncaught page errors or external requests.

The scalar density map does not encode unrelated categories by colour. Its
numeric endpoints are written beside the colour ramp, density contours are
visible in white, every state is named, and the radial profile is independently
identified by axes and description.

## Non-Canvas fallback

Canvas fallback text states which view is unavailable and directs the reader to
the still-available numerical results and interpretation. The normalized state,
energy, effective length, nodes, parity, degeneracy and model scope remain plain
HTML. Therefore loss of graphical Canvas support does not erase the scientific
result.

## Reproduce

With Playwright and Chromium available to Node:

```bash
cd task10_hydrogenic_orbitals/app
npm run test:a11y
```

The executable can be selected with `TASK10_CHROMIUM_EXECUTABLE`; the audit port
can be changed with `TASK10_A11Y_PORT`.
