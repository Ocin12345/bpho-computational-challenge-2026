# Master Presentation Audit — Tasks 1–10

## Purpose

This audit defines the current presentation state and the acceptance contract
for the final three-minute BPhO Computational Challenge presentation. It keeps
scientific validation, visual quality, narration timing, and deliverable
completeness separate so that a polished slide cannot substitute for a tested
simulation.

Audit date: 19 July 2026

## Verified current state

| Task | Scientific evidence checked in this audit | Presentation state | Required action |
| --- | --- | --- | --- |
| 1 | 37 unit and figure tests pass | Slide content, narration, and images exist; no PowerPoint, rendered preview, or presentation validator exists | Build the missing one-slide presentation and validator; regenerate selected figures in Times New Roman |
| 2 | 80 tests pass | One-slide PowerPoint exists; older Arial design and 2401 × 1350 preview | Restyle to the common Times New Roman system, render at the final preview standard, and add a presentation validator |
| 3 | 107 tests pass; current presentation validator passes | One-slide PowerPoint exists; older Arial design and 2401 × 1350 preview | Restyle and upgrade the preview while preserving the validated science and notes |
| 4 | 149 tests pass; current presentation validator passes | One-slide PowerPoint exists; older Arial design and 2401 × 1350 preview | Restyle and upgrade the preview while preserving the validated science, animation, and notes |
| 5 | 42 tests pass; current presentation validator passes | One-slide PowerPoint exists; older Arial design and 2401 × 1350 preview | Restyle and upgrade the preview while preserving the validated science and notes |
| 6 | 29 tests pass; current presentation validator passes | One-slide PowerPoint exists; older Arial design and 2401 × 1350 preview | Restyle and upgrade the preview while preserving the validated science and notes |
| 7 | Final validator passes 8/8; presentation validator passes | Times New Roman, 4001 × 2250 preview, embedded high-resolution visual and speaker notes | Preserve unless the master-deck viewport check exposes a concrete defect |
| 8 | Final validator passes 8/8; app and presentation validators pass | Times New Roman, 4001 × 2250 preview, validated presentation assets and speaker notes | Preserve unless the master-deck viewport check exposes a concrete defect |
| 9 | Final validator passes 8/8; presentation validator passes | Times New Roman, 4001 × 2250 preview, validated presentation assets and speaker notes | Preserve unless the master-deck viewport check exposes a concrete defect |
| 10 | Final validator passes 8/8; presentation validator passes | Times New Roman, 4001 × 2250 preview, validated presentation assets and speaker notes | Preserve unless the master-deck viewport check exposes a concrete defect |

The Task 1–6 scientific audit totals 444 passing tests. Tasks 7–10 were also
rechecked through their final and presentation gates. The expensive Task 2
full time-step refinement was not rerun to completion during this audit; the
80-test Task 2 suite passed, and existing committed validation evidence remains
available separately. It was subsequently rerun during release hardening on
22 July 2026, passed all 9/9 checks and refreshed the saved evidence; see
`submission/TASK2_CONVERGENCE_CLOSEOUT.md`.

## Consistency findings

1. There is no combined Tasks 1–10 PowerPoint in the current presentation
   tree.
2. Task 1 has no finished PowerPoint or rendered preview.
3. Tasks 2–6 use the earlier Arial slide system. Their 2401 × 1350 previews are
   clear, but they do not meet the Times New Roman and 4001 × 2250 standard now
   established by Tasks 7–10.
4. Tasks 7–10 are already presentation-ready at the current standard. Their
   small compositional differences are intentional and are not defects.
5. The Task 1 source figures contain DejaVu Sans text and therefore require
   typography regeneration before final slide assembly.

## Narration timing audit

| Task | Current final-script word count |
| --- | ---: |
| 1 | 43 |
| 2 | 47 |
| 3 | 47 |
| 4 | 46 |
| 5 | 47 |
| 6 | 50 |
| 7 | 47 |
| 8 | 49 |
| 9 | 48 |
| 10 | 50 |
| **Total** | **474** |

The present narration lasts approximately 189.6 seconds at 150 words per
minute, 183.5 seconds at 155 words per minute, and 177.8 seconds at 160 words
per minute. Even the fastest case leaves effectively no allowance for slide
changes, emphasis, or a short opening and closing. The master narration should
therefore target approximately 410–420 spoken words, with a timed rehearsal
demonstrating a total duration no longer than 180 seconds.

## Final acceptance contract

The master presentation is complete only when all of the following are true:

- one 16:9 slide exists for every task from 1 through 10;
- the final master PowerPoint contains all ten slides in task order;
- all visible slide text uses Times New Roman, with mathematical symbols
  rendered legibly and without fallback-font defects;
- each final static slide preview is 4001 × 2250 pixels or better and remains
  readable at a 1920 × 1080 viewing viewport;
- plots preserve axes, units, legends, uncertainty information, and aspect
  ratios without cropping or distortion;
- every included figure is copied from or regenerated from validated task
  outputs, with byte-level or manifest-level checks where appropriate;
- speaker notes are embedded for every task and agree with the final narration
  source files;
- a master validator checks slide count, order, dimensions, embedded media,
  fonts, notes, and required task titles;
- the PowerPoint renders without overflow, missing glyphs, clipped text, or
  broken media;
- the timed narration, including transitions, does not exceed three minutes;
- Tasks 7–10 continue to pass their existing scientific and presentation gates
  after assembly; and
- the final deliverable is reproducible from documented commands and uses
  relative or packaged assets rather than machine-specific links.

## Rebuild boundary

The presentation repair must not change a validated numerical claim merely to
fit a layout. Tasks 1–6 may be visually regenerated and their competition
narration may be shortened without changing meaning. Tasks 7–10 should be
carried into the master deck unchanged unless a rendered master-deck inspection
identifies a specific readability, typography, or media defect.
