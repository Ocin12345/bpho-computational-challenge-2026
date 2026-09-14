# Submission Evidence Manifest

The competition's external deliverable is the maximum three-minute unlisted
YouTube screencast. This repository package is the clean, reproducible evidence
and backup copy supporting that video.

| Location | Purpose |
| --- | --- |
| `task01_random_walk` through `task10_hydrogenic_orbitals` | Simulation, analytical model, generators, validators, tests and task-specific documentation |
| `data/taskXX` and Task 2's local analysis folders | Machine-readable numerical evidence and integrity manifests |
| `data/advanced_extensions.json` | Deterministic 35-check evidence bundle for the complete optional extension programme |
| `figures/taskXX` and Task 2's local figure folder | Publication figures, animations and visual manifests |
| `figures/advanced` | Ten publication PNG/SVG extension figure pairs and their manifest |
| `reports` | Extended scientific reports and accessible companions |
| `presentation/task01` through `presentation/task10` | Individual competition slides, notes and rendered previews |
| `presentation/master` | Final ten-slide PowerPoint, PDF, narration, contact sheet and acceptance record |
| `site` | Integrated offline Tasks 1–10 website, Advanced Lab, packaged Task 4 app, pinned runtime assets and browser audit scripts |
| `submission` | Environment lock, assumptions register, verification tool, archive builder and release checklist |
| `VIDEO_FILMING_CHECKLIST.md` | Exact three-minute live-site recording sequence and spoken result cues |

The generated ZIP also contains `SUBMISSION_MANIFEST.sha256`. It records the
SHA-256 digest and byte size of every archived file. The archive itself has a
sidecar `.sha256` file.

## Deliberately excluded

- Git history and local editor state;
- virtual environments, `node_modules`, caches and compiled Python files;
- downloaded official source archives;
- temporary files and earlier release ZIPs; and
- credentials, tokens or external-account information.

Generated scientific data, figures, static applications, animations,
PowerPoints and reports remain included because they are observable evidence,
not disposable build caches.
