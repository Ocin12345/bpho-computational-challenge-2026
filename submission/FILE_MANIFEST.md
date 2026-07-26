# Submission Evidence Manifest

The competition's external deliverable is the maximum three-minute unlisted
YouTube screencast. This repository package is the clean, reproducible evidence
and backup copy supporting that video.

| Location | Purpose |
| --- | --- |
| `task01_random_walk` through `task10_hydrogenic_orbitals` | Simulation, analytical model, generators, validators, tests and task-specific documentation |
| `data/taskXX` and Task 2's local analysis folders | Machine-readable numerical evidence and integrity manifests |
| `figures/taskXX` and Task 2's local figure folder | Publication figures, animations and visual manifests |
| `reports` | Extended scientific reports and accessible companions |
| `presentation/task01` through `presentation/task10` | Individual competition slides, notes and rendered previews |
| `presentation/master` | Final ten-slide PowerPoint, PDF, narration, contact sheet and acceptance record |
| `submission` | Environment lock, assumptions register, verification tool, archive builder and release checklist |

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
