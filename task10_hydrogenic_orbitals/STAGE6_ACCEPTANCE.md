# Task 10 Stage 6 Acceptance — Offline Interactive Explorer

Status: **PASS**

## Outcome

The Task 10 explorer is a self-contained static application in *app/*. It uses
the frozen hydrogenic equations, normalized real tesseral harmonics and the same
physical constants as the independently validated Python implementation.

## Delivered interaction

- Valid controls for atomic number (1\leq Z\leq20), (1\leq n\leq8),
  (0\leq l<n) and (-l\leq m\leq l); impossible (l,m) options never appear.
- Named presets for every one of the 25 official S–G gallery states.
- Semi-transparent density planes in an orbitable, zoomable Canvas 2D
  projection, with a stable physical scale and explicit axis triad.
- Physical-extent, plane-count, relative-cutoff and opacity controls.
- Three orthogonal slices with one shared colour scale and a visible threshold
  contour.
- A normalized radial-probability chart with radial-node markers.
- Live energy, effective Bohr length, physical extent, node, parity and
  degeneracy summaries.
- Explicit separation of normalized physics from relative display transforms,
  and of stationary density from camera rotation.
- Meaningful Canvas fallback text, a local launcher and a restrictive Content
  Security Policy; no remote libraries, fonts or assets are required.

## Acceptance evidence

| Check | Result |
|---|---:|
| Python suite after app integration | 42/42 passed |
| JavaScript scientific tests | 6/6 passed |
| Python/JavaScript state comparisons | 204/204 passed |
| Static/offline/accessibility contract | 23/23 passed |
| Official presets exercised in a browser | 25/25 passed |
| Responsive widths exercised | 320, 390, 740, 1050, 1440 px |
| Page-level overflow | 0 px at every width |
| External browser requests | 0 |
| Console and page errors | 0 |
| Slowest measured gallery update | 67.30 ms |
| Frozen update-performance budget | <450 ms |

The default and mobile screenshots are stored in *reports/task10/*. Both use
Times New Roman and were inspected at full resolution. The 3D density occupies a larger, clearer default
view without clipping the axis triad. At narrow widths, the publication-scale
radial chart scrolls only inside its named keyboard-focusable region; it never
forces the document to overflow.

## Run locally

From the repository root:

```bash
python3 -m task10_hydrogenic_orbitals.serve_task10
```

Then open `http://127.0.0.1:4210/`.

## Stage boundary

Stage 6 establishes the complete explorer and its deterministic scientific
contract. Stage 7 performs the deeper automated accessibility, focus, zoom,
media-preference, security and performance acceptance pass.
