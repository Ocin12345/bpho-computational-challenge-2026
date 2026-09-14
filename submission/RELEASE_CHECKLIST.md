# Final Release Checklist

## Evidence

- [x] Run `python3 -m submission.verify_project` from the repository root.
- [x] Confirm all ten task suites report 738 passing tests in total (52, 94,
  125, 154, 58, 42, 40, 61, 54 and 58 respectively).
- [x] Confirm Tasks 7–10 each pass all 8 final artifact groups.
- [x] Confirm the advanced bundle reports 35/35 checks, ten complete tasks,
  ten illustrated reports and ten publication PNG/SVG figure pairs.
- [x] Confirm the Advanced Lab static gate passes and its desktop/mobile browser
  audit exercises Task 3 and the Task 10 state-morph control.
- [x] Confirm the presentation bundle reports ten slides, ten 4K summaries and
  a narration estimate below 180 seconds.
- [x] Confirm the refreshed Task 2 convergence closeout is marked PASS.
- [x] Confirm all ten website data validators pass.
- [x] Confirm all ten task pages pass the rendered desktop/mobile audit with
  no runtime errors, external requests or horizontal overflow.
- [x] Confirm the landing page, task index and Advanced Lab load Three.js,
  animation code, fonts and data locally with no runtime CDN request.

## Portability

- [ ] Open the master PowerPoint and PDF on a second computer.
- [ ] Open the Task 8–10 offline applications and the Advanced Lab through their
  documented local servers on a second computer.
- [x] Confirm Times New Roman is installed before regenerating figures.
- [x] Keep downloaded official ZIPs, virtual environments and `node_modules`
  outside the release archive.

## Archive

- [x] Build the archive with `python3 -m submission.build_release_archive`.
- [x] Confirm the tool reports ZIP integrity and per-file SHA-256 verification.
- [x] Extract the archive into a new temporary folder and rerun
  `python3 -m submission.verify_project` there.
- [ ] Retain both the ZIP and its `.sha256` sidecar in two separate locations.

## External submission

- [ ] Upload only the finished maximum three-minute screencast required by the
  competition, using the required unlisted visibility setting.
- [ ] Watch the uploaded version from start to finish before submitting its link.
- [ ] Verify the final URL, title, permissions and submission confirmation.

No upload, account change or external submission is performed by the local
verification and archive tools.
