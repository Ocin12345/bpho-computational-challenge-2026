# Task 10 Stage 7 Acceptance — Browser, Accessibility and Performance

Status: **PASS**

## Browser acceptance

- All 25 official S–G presets render with valid live values.
- The wider validated endpoint (Z=20,n=8,l=7,m=+7) renders successfully.
- Impossible (l,m) options remain absent after every state transition.
- State, extent, plane count, cutoff, opacity, mouse camera and keyboard camera
  interactions all update the explorer.
- Responsive layouts pass at 320, 390, 740, 1050 and 1440 px.
- No page-level horizontal overflow occurs at any tested breakpoint.
- Unknown routes return HTTP 404 and keep the restrictive security headers.
- No browser-console errors, page errors or external network requests occur.

## Performance acceptance

The frozen full-state-update budget is 450 ms. Across three complete passes
through the official 25-state gallery:

| Metric | Result |
|---|---:|
| Full renders | 75 |
| Maximum | 67.60 ms |
| Mean | 66.02 ms |
| Budget margin | 85.0% |
| Post-GC heap change | 0.09 MB |

The measured maximum is comfortably inside the budget and repeated state
changes do not retain a growing history of numerical grids or Canvas textures.

## Accessibility acceptance

All thirteen groups in *ACCESSIBILITY_AUDIT.md* pass. The audit includes
semantics, figure alternatives, accessibility-tree exposure, focus order,
keyboard input, live announcements, contrast, 320 px reflow, 200% text,
reduced motion, forced colours and a meaningful non-Canvas fallback.

## Reproduce

```bash
cd task10_hydrogenic_orbitals/app
npm test
npm run test:ui
npm run test:a11y
```

## Stage boundary

Stage 7 accepts the interactive product. Stage 8 now produces and validates a
deterministic high-resolution motion artifact whose camera movement is stated
explicitly and cannot be mistaken for electron dynamics.
