# Task 10 Stage 8 Acceptance — High-Quality Motion

Status: **PASS**

## Accepted motion package

The final motion artifact is *figures/task10/orbital_view_rotation.webp*.
It is a 3840×2160 animated WebP containing 80 opaque frames at 20 frames per
second. Its exact four-second loop follows a 360° azimuth path with a periodic
24°±5° elevation. The endpoint is excluded so the final frame advances by one
equal camera step into the first instead of creating a duplicated pause.

Every frame contains:

- hydrogen 3d, (m=0), state and energy;
- the 0.15 display threshold and (n^2a) coordinate scale;
- 17 semitransparent x-y density planes;
- fixed x-y and x-z slices with a shared relative-density scale;
- normalized radial probability and node counts;
- the 22/22 validation total; and
- an explicit statement that the motion is camera rotation, not electron
  motion or time evolution.

## Quality and integrity evidence

| Check | Result |
|---|---:|
| Dimensions | 3840×2160 |
| Frames | 80 |
| Exact frame duration | 50 ms |
| Total duration | 4000 ms |
| Loop | Continuous |
| WebP quality setting | 93 |
| File size | 9,594,614 bytes |
| Size budget | 104,857,600 bytes |
| Scientific gate | 22/22 passed |
| Sampled frame difference | 0.7917 minimum |
| Browser errors / external requests | 0 / 0 |

The animation SHA-256 is
`e101402323a2ba4d187c052b314ab4a8e80eae38095dc0ab190aa7838a46058c`.
All dimensions, timing, loop data, XMP title/description, file hashes and the
scientific-state digest are recorded in *figures/task10/motion_manifest.json*.

## Visual inspection and fallback

Frames 1, 21, 41, 61 and 80 were decoded from the final animation and inspected
at high resolution in
*reports/task10/orbital_view_rotation_contact_sheet.png*. The review found no
cropped headings, axis/colorbar collisions, black disposal frames or lost node
structure. The final colorbar uses a dedicated vertical region, and inspection
labels sit outside the decoded frames. Times New Roman is used throughout the
poster, animation and inspection sheet.

The offline viewer loads the 4K animation and the five-frame inspection sheet in
Chromium, reflows without page overflow at 320 px and makes no remote requests.
When `prefers-reduced-motion: reduce` is active it substitutes the accepted 4K,
240-DPI poster automatically.

## Reproduce

```bash
python3 -m task10_hydrogenic_orbitals.generate_task10_motion
python3 -m task10_hydrogenic_orbitals.validate_task10_motion
cd task10_hydrogenic_orbitals/app
npm run test:motion
```

Stage 8 is complete. Stage 9 may now document the accepted results and exact
reproduction sequence.
