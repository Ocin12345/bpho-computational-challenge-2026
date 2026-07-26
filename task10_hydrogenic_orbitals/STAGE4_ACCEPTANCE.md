# Task 10 Stage 4 Acceptance — Reproducible Data Package

Status: **PASS**

## Generated evidence

The deterministic package in *data/task10/* contains:

| File | Accepted content |
|---|---|
| orbital_state_catalog.csv | all 204 validated real basis states through \(n=8\) |
| official_gallery.csv | all 25 official 1s/2p/3d/4f/5g states |
| radial_profiles.csv | 6,005 samples for representative S–G radial profiles |
| radial_nodes.csv | all 84 positive radial nodes through \(n=8\) |
| reference_anchors.json | hydrogen, carbon, analytic-density and orientation anchors |
| validation_report.json | passing 22-check scientific report |
| manifest.json | schemas, sources, constants, domains, hashes and state digest |

## Containment and threshold contract

Every representative radial profile ends at the independently integrated
99.95% containment radius. The final trapezoidal cumulative values differ from
0.9995 by less than \(8\times10^{-9}\).

No three-dimensional volumetric grid is stored as opaque bulk data. The compact
state and radial evidence is sufficient to regenerate those grids exactly. The
official 0.15 relative-density threshold appears only in the visualization
contract and never changes the data or validation report.

## Acceptance evidence

- 22/22 scientific checks pass before generation.
- 34/34 Python tests pass.
- Two independent temporary builds are byte-for-byte identical.
- CSV schemas and exact row counts are checked before commit.
- All six evidence files are SHA-256 bound by the manifest.
- A failed scientific report prevents any file creation.
- An injected late replacement failure restores every pre-existing file.
- Python syntax and workspace diff hygiene pass.

Stage 4 is therefore complete. Publication figures may now consume only this
matching passing package.
