# Reproducibility and Release Handoff

This folder contains the commands for checking the models, rebuilding their
outputs and packaging a copy of the project. Verification reports state what was
run; a saved result is not a substitute for rerunning a calculation after editing it.

The competition's external deliverable is the maximum three-minute unlisted
YouTube screencast. The ZIP built here is an internal evidence and backup copy,
not an additional upload requirement.

## Accepted environment

- Python 3.9.6;
- NumPy 2.0.2, SciPy 1.13.1, Matplotlib 3.9.4 and Pillow 11.3.0;
- Node.js 24.11.1 for JavaScript validation and npm 11.6.2 for rebuilding PowerPoints; and
- Times New Roman for final scientific figures.

Install the accepted Python set with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r submission/requirements-lock.txt
```

Run all commands from the repository root with this environment active. Use
`python` after activation (on Windows, activate with `.venv\Scripts\Activate.ps1`).
Verification calls this same Python interpreter for the presentation checks.
It does not require npm packages or LibreOffice unless you regenerate outputs.

Times New Roman must be installed and visible to Matplotlib. To check:

```bash
python -c "from matplotlib import font_manager; print(font_manager.findfont('Times New Roman', fallback_to_default=False))"
node --version
```

The font is normally available on Windows and macOS; it is not bundled here.
On a machine without it, install a licensed copy and refresh Matplotlib's font
cache before running figure tests. The static website has its own bundled fonts
and does not require this desktop font.

## One-command verification

From the repository root:

```bash
python -m submission.verify_project
```

This runs all ten task test suites (738 tests in the accepted snapshot), the
four Task 7–10 final artifact gates, the 35-check advanced-extension gate, the
ten-pair advanced-figure gate, all ten website gates, the Advanced Lab static gate, the presentation
and typography gates, the master timing check, the saved Task 2 convergence
check, local website dependency checks, document-link checks and PowerPoint
portability checks. It checks the saved full Task 2 refinement by default; it does
not rerun that expensive simulation unless requested.

For a fast website-only file check:

```bash
python -m submission.validate_site
```

This catches missing local HTML/CSS/module dependencies. Browser interaction and
rendering still need a browser check; it does not test external websites.

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

This is intentionally much slower. It also regenerates the cross-task advanced
JSON and all ten extension figures. It can install the locked PowerPoint
dependencies with `npm ci` when their local `node_modules` folders are absent.
The generator never uploads or submits anything.

Full regeneration also needs LibreOffice's `soffice`, Poppler's `pdftoppm`, and
`bash` on PATH to render slide previews. The render scripts accept `SOFFICE` and
`PDFTOPPM` environment variables for installations outside PATH. Check those
tools before starting a long rebuild. Regeneration overwrites generated project
files; use a clean checkout so you can review the resulting diff.

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
