# Stage 7 acceptance — browser, accessibility and performance

## Outcome

Stage 7 is accepted. The app now has repeatable real-browser smoke and accessibility audits in `app/tests/`.

## Browser acceptance

- Exact default, zero-angle, backscatter and custom-energy outputs verified.
- All 17 default plotted curve paths are finite; the custom-energy case contains the expected 20 paths.
- Responsive layouts verified at 320, 390, 740, 1050 and 1440 px.
- No page-level horizontal overflow at any tested breakpoint.
- No browser-console errors, uncaught page errors or external network requests.
- Restrictive Content Security Policy delivered by the local server.
- Maximum measured full chart update: 21.90 ms, below the frozen 100 ms interaction budget.

## Accessibility acceptance

The ten evidence groups in `ACCESSIBILITY_AUDIT.md` all pass. The audit includes semantic exposure, focus order, keyboard input, live announcements, contrast, non-colour curve encoding, reflow, text resizing and display preferences.

## Reproduce

```bash
cd task09_compton_scattering/app
npm test
npm run test:ui
npm run test:a11y
```

## Stage boundary

Stage 7 validates the interactive product. Publication-ready static figures, a 4K summary and motion output belong to Stage 8.
