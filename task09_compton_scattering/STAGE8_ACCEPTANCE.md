# Stage 8 acceptance — publication media and animation

## Outcome

Stage 8 is accepted. The validated media package is in `figures/task09/` and is indexed by `manifest.json` with SHA-256 hashes, byte sizes, dimensions and scientific-report digests.

## Static publication figures

Each scientific figure is supplied as a 300 DPI PNG plus editable SVG and PDF.

| Base name | Purpose | Raster size |
|---|---|---:|
| `required_kinematics` | The three official angular dependences for all five energies | 2400 × 1500 |
| `energy_transfer_geometry` | Energy partition plus exact momentum triangles | 2400 × 1500 |
| `klein_nishina_extension` | Clearly separated optional angular-weighting extension | 2400 × 1500 |
| `task09_summary` | 16:9 presentation and report summary plate | 3840 × 2160 |

All five incident energies use both a stable colour and a distinct line style. The recoil-speed axis is fixed to the full physical interval 0 ≤ v/c ≤ 1. The θ = 0° undefined-direction convention is stated on the required figure and summary.

Times New Roman is mandatory throughout the static figures and animation. The
generator rejects a missing font, any unexpected SVG font family, or a PDF that
does not embed Times New Roman as TrueType Type 42. Shared legends sit outside
the plotting regions so no data curve is obscured.

## Animation

`compton_angle_sweep.gif` is a deterministic 200 keV collision sweep:

- 1600 × 900 pixels, exact 16:9 aspect ratio.
- 73 inclusive frames from θ = 0° to θ = 180°.
- Configured at 18 frames per second and continuous loop.
- Fixed axes and one common arrow momentum scale.
- Simultaneous live markers for Δλ/λ, v/c and φ.
- Forward-limit disclosure and exact backscatter endpoint.
- Opaque full-frame RGB storage with GIF delta disposal disabled.
- Every stored frame is rejected if black-clearing artifacts exceed the frozen threshold.
- Mid-playback Chromium capture visually inspected after the writer fix.

## Acceptance evidence

| Check | Result |
|---|---:|
| Complete Python tests | 49/49 passed |
| JavaScript cross-language tests | 5/5 passed |
| Kinematic validation | 44/44 passed |
| Klein–Nishina validation | 30/30 passed |
| Static app contract | 21/21 passed |
| Browser UI smoke | Pass; 0 console/page/network errors |
| Accessibility groups | 10/10 passed |
| Media files in integrity manifest | 13 |
| Static figure representations | 4 PNG + 4 SVG + 4 PDF |
| Total manifested media size | 6,718,965 bytes |

## Reproduce

```bash
python3 -m task09_compton_scattering.generate_task09_figures
python3 -m task09_compton_scattering.animation
python3 -m task09_compton_scattering.generate_task09_media_manifest
```

## Stage boundary

Stage 8 freezes the visual outputs. Consolidated scientific interpretation, user instructions, dependency declaration and reproduction documentation belong to Stage 9.
