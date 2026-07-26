# Final Reproducibility and Release Acceptance

Acceptance date: 22 July 2026

## Scientific evidence

- PASS — Tasks 1–6 complete 444 unit and regression tests.
- PASS — Tasks 3–6 also pass their independent numerical science gates.
- PASS — Tasks 7–10 each pass all 8 final artifact groups.
- PASS — the Task 2 official-scale baseline, half-step and quarter-step study
  was rerun; all 9 convergence, geometry, identity, stability and
  reproducibility checks pass.
- PASS — the Task 2 caveat recorded during presentation polishing is closed.

## Presentation and application evidence

- PASS — all ten individual PowerPoints and the ten-slide master deck pass.
- PASS — all ten summary visuals are 3840 × 2160 and all rendered previews are
  4001 × 2250.
- PASS — Times New Roman is enforced in the scientific SVGs and PowerPoint
  themes.
- PASS — the master narration contains 410 words and is estimated at 164
  seconds at 150 words per minute.
- PASS — offline application checks for the interactive tasks pass.
- PASS — all 11 PowerPoints contain no machine-specific local-file links.

## Reproducibility handoff

- PASS — `python3 -m submission.verify_project` succeeds from the working
  repository and writes a structured JSON report.
- PASS — the accepted Python environment is locked separately from the broader
  development constraints.
- PASS — model assumptions and limitations are consolidated for all ten tasks.
- PASS — the full regeneration order is encoded in the same verifier under the
  explicit `--regenerate` option.
- PASS — all project Markdown links resolve outside deliberately excluded
  third-party dependency documentation.

## Archive evidence

- PASS — the dated ZIP excludes Git history, dependencies, caches, downloads,
  temporary files and credentials.
- PASS — every archived file has a size and SHA-256 entry in the internal
  `SUBMISSION_MANIFEST.sha256`.
- PASS — the ZIP integrity test and every internal file digest pass.
- PASS — the whole archive has an external `.sha256` sidecar.
- PASS — the archive was extracted into a new temporary directory containing no
  local dependency folders, and the complete one-command verifier passed again.

## Remaining human actions

The programming and local release work is complete. The remaining actions
require the entrant: copy the ZIP and sidecar to a second storage location,
open the main deliverables on a second computer, record the screencast, watch
the uploaded unlisted YouTube version and submit its confirmed URL. No local
tool uploads files or changes an external account.
