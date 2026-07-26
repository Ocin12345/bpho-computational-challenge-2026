# Final BPhO Presentation — Tasks 1–10

## Ready-to-use deliverables

- [Master PowerPoint](BPhO_Computational_Challenge_Tasks_1_to_10.pptx) — ten
  ordered 16:9 slides with one 4K visual and one speaker-notes page per task.
- [Master PDF](BPhO_Computational_Challenge_Tasks_1_to_10.pdf) — static export
  for portability and printing.
- [Narration and visual cues](MASTER_NARRATION.md) — 410 spoken words, estimated
  at 164 seconds at 150 words per minute.
- [Contact sheet](preview/BPhO_Master_Contact_Sheet.png) — overview of all ten
  rendered slides.
- [300-DPI previews](preview/) — ten 4001 × 2250 slide renders for original-size
  inspection.
- [Final acceptance record](FINAL_PRESENTATION_ACCEPTANCE.md).

## Narrative

The presentation is written for BPhO judges and physics-literate viewers. Each
slide follows model → quantitative validation → result. The sequence moves from
classical random motion and collisions through thermal and early quantum
phenomena, then wave mechanics, entanglement, relativistic scattering and
hydrogenic orbitals.

The ten current scripts total 410 words. The recommended pace is approximately
150 words per minute, leaving about 16 seconds within the three-minute limit
for slide changes, emphasis and a final pause. The deck deliberately has no
separate title or closing slide because either would take time from the ten
required tasks.

## Visual standard

- Times New Roman is used throughout the scientific figures and PowerPoint
  themes; STIX supplies only specialist mathematical glyphs.
- Every master visual is exactly 3840 × 2160 pixels and is embedded without
  cropping or distortion.
- Every rendered slide is 4001 × 2250 pixels at 300 DPI.
- Figures retain axes, units, legends, uncertainty information, validation
  badges and scientific limitations.
- Tasks 7–10 are carried into the master deck byte for byte from their already
  accepted summary figures.
- Tasks 1–6 were regenerated at source level before assembly; the typography
  change is not a text overlay.

## Rebuild

From the `presentation` directory:

```bash
npm ci
python3 build_task01_task02_summaries.py
npm run build
bash render_task_previews.sh
bash master/render_master_preview.sh
python3 master/create_contact_sheet.py
npm run validate
```

The build fixes PowerPoint timestamps to 1 January 2026, copies only repository
assets, and writes no machine-specific links into the presentation files.

## Recording checklist

1. Open the master PowerPoint in slideshow mode at 16:9.
2. Use the speaker notes from `MASTER_NARRATION.md` without adding improvised
   technical detail.
3. Rehearse once at approximately 150 words per minute and confirm the complete
   recording is below three minutes.
4. Preserve slide aspect ratio when exporting or screen-recording.
5. Check the final recording at 1920 × 1080 or better, especially the smallest
   legends on Tasks 3–5 and the footer limitations on Tasks 6, 9 and 10.
6. Do not describe a camera rotation as electron motion in Task 10 or ring
   brightness as physically modelled in Task 6.
