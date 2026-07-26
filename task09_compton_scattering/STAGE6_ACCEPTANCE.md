# Stage 6 acceptance — offline interactive explorer

## Outcome

Stage 6 is accepted. The Task 9 explorer is a self-contained static application in `app/` and uses the same frozen equations as the validated Python study.

## Delivered interaction

- Incident-energy control from 1 to 5000 keV, with all five official presets.
- Photon-angle control from 0° to 180°, including both physical endpoints.
- Exact momentum-vector geometry for the selected collision.
- Live values for fractional wavelength shift, absolute shift, relativistic recoil speed, recoil direction, scattered-photon energy and electron kinetic energy.
- Three required five-energy charts with a shared colour mapping and selected-point guide.
- A visibly separate Klein–Nishina extension with differential strength, normalized polar-angle density and total cross-section.
- Offline-only assets, a local launcher and a restrictive local Content Security Policy.

## Acceptance evidence

| Check | Result |
|---|---:|
| Python test suite after app integration | 38/38 passed |
| JavaScript cross-language numerical tests | 5/5 passed |
| Static/offline/accessibility/typography contract | 21/21 passed |
| Browser console errors after desktop and 320 px renders | 0 |
| Desktop document overflow at 1440 px | 0 px |
| Mobile document overflow at 320 px | 0 px |
| 1000 keV, 180° fractional shift | 3.9139 |
| 1000 keV, 180° recoil speed | 0.92047 c |
| 1000 keV, 180° recoil angle | 0.00° |
| 1000 keV Klein–Nishina total cross-section | 0.2112 barn |

The mobile charts retain their publication-scale internal coordinate system and scroll inside explicitly labelled, keyboard-focusable regions. They do not force the page itself to overflow.

The root interface, controls, numerical cards, equations and all SVG chart text
use Times New Roman. The static validator and Chromium smoke test both reject a
font fallback.

## Run locally

From the repository root:

```bash
python3 -m task09_compton_scattering.serve_task09
```

Then open `http://127.0.0.1:4209/`.

## Stage boundary

Stage 6 establishes the complete explorer. Automated browser interaction, keyboard traversal, responsive breakpoint coverage and measured performance belong to Stage 7.
