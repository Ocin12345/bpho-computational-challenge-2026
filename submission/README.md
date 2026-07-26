# Reproducibility and Release Handoff

The simulation and programming work is complete. This folder hardens the final
evidence so that it can be checked, rebuilt and archived without mixing in local
development files.

The competition's external deliverable is the maximum three-minute unlisted
YouTube screencast. The ZIP built here is an internal evidence and backup copy,
not an additional upload requirement.

## Accepted environment

- Python 3.9.6;
- NumPy 2.0.2, SciPy 1.13.1, Matplotlib 3.9.4 and Pillow 11.3.0;
- Node.js 24.11.1 and npm 11.6.2 for rebuilding PowerPoints; and
- Times New Roman for final scientific figures.

Install the accepted Python set with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r submission/requirements-lock.txt
```

## One-command verification

From the repository root:

```bash
python3 -m submission.verify_project
```

This runs the six Task 1–6 test suites, the four Task 7–10 final artifact gates,
the presentation and typography gates, the master timing check, the saved Task 2
convergence check, document-link checks and PowerPoint portability checks.

To rerun the expensive full Task 2 baseline/half-step/quarter-step convergence
instead of only validating its saved evidence:

```bash
python3 -m submission.verify_project --full-task2
```

## One-command regeneration

The following regenerates the numerical evidence, figures, animations,
applications and presentation package in their documented order, then runs the
complete verification suite:

```bash
python3 -m submission.verify_project --regenerate --workers 4
```

This is intentionally much slower. It can install the locked PowerPoint
dependencies with `npm ci` when their local `node_modules` folders are absent.
The generator never uploads or submits anything.

## Build the clean evidence archive

```bash
python3 -m submission.build_release_archive
```

The builder excludes Git history, dependencies, caches, downloads and secrets;
adds a per-file SHA-256 manifest; checks the ZIP; and writes an external archive
digest. See [`FILE_MANIFEST.md`](FILE_MANIFEST.md) for the inclusion policy and
[`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) for the final handoff sequence.

Scientific assumptions and judge-facing limitations are consolidated in
[`SCIENTIFIC_ASSUMPTIONS.md`](SCIENTIFIC_ASSUMPTIONS.md). Task 2's refreshed
high-cost refinement evidence is summarized separately in
[`TASK2_CONVERGENCE_CLOSEOUT.md`](TASK2_CONVERGENCE_CLOSEOUT.md).
