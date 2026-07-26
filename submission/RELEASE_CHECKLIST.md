# Final Release Checklist

## Evidence

- [x] Run `python3 -m submission.verify_project` from the repository root.
- [x] Confirm Tasks 1–6 report 444 passing tests in total.
- [x] Confirm Tasks 7–10 each pass all 8 final artifact groups.
- [x] Confirm the presentation bundle reports ten slides, ten 4K summaries and
  a narration estimate below 180 seconds.
- [x] Confirm the refreshed Task 2 convergence closeout is marked PASS.

## Portability

- [ ] Open the master PowerPoint and PDF on a second computer.
- [ ] Open the Task 8–10 offline applications through their documented local
  servers and confirm that no external network request is needed.
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
