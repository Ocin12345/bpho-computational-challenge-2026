# Task 4 Final Acceptance Report

## Verdict

**ACCEPTED — Task 4 is complete to the declared high-standard boundary.**

The mandatory stopping-potential comparison, supporting wavelength study,
independent validation, deterministic evidence, original-resolution figures,
scientific interpretation, optional animation extension, editable presentation
slide, and timed narration are complete. No required Task 4 work remains.

Audit date: **16 July 2026**.

## Official objective and source boundary

The accepted solution answers Task 4 from page 2 of the written 2026 challenge
brief and slides 25--28 of the official Quantum presentation. It plots the
photoelectron stopping potential against incident-light frequency and vacuum
wavelength for all nine supplied metals.

The solution uses the exact work-function values displayed in the official
table. The animation is treated as the official optional extension and never as
a replacement for the required graph.

## Acceptance evidence

| Requirement | Accepted evidence |
| --- | --- |
| Own computational model | Vectorized Python/NumPy implementation in [`models.py`](models.py) and immutable study assembly in [`analysis.py`](analysis.py) |
| All nine supplied metals | Immutable official table in [`materials.py`](materials.py) and nine-row [`material_cutoffs.csv`](../data/task04/material_cutoffs.csv) |
| Required stopping-potential graph | [`stopping_voltage_frequency.png`](../figures/task04/stopping_voltage_frequency.png) and SVG equivalent |
| Supporting wavelength comparison | [`stopping_voltage_wavelength.png`](../figures/task04/stopping_voltage_wavelength.png) and SVG equivalent |
| Correct threshold physics | Physical emission masks, analytical cut-off markers, undefined below-threshold voltage, and the [`copper threshold explanation`](../figures/task04/copper_threshold_explanation.png) |
| Independent validation | Decimal references and the complete [`43-check report`](../data/task04/validation_report.json) |
| Reproducible numerical evidence | Five deterministic files in [`data/task04`](../data/task04/) plus the complete manifest |
| Scientific interpretation | [`RESULTS_AND_INTERPRETATION.md`](RESULTS_AND_INTERPRETATION.md) |
| Optional extension | Validated [`60-frame GIF`](../figures/task04/photoelectric_demo.gif), static [`storyboard`](../figures/task04/photoelectric_demo_storyboard.png), and [`ANIMATION_DECISION.md`](ANIMATION_DECISION.md) |
| Competition presentation | Editable [`Task04_Photoelectric_Effect.pptx`](../presentation/task04/Task04_Photoelectric_Effect.pptx), [`preview`](../presentation/task04/preview/Task04_Photoelectric_Effect_preview.png), and [`speaker script`](../presentation/task04/SPEAKER_SCRIPT.md) |

## Physics acceptance

The accepted model implements

$$
eV_s=hf-W,
$$

with the equivalent frequency and vacuum-wavelength forms

$$
V_s=\frac{h}{e}f-\frac{W}{e},
\qquad
V_s=\frac{hc}{e\lambda}-\frac{W}{e}.
$$

It also implements the analytical cut-offs

$$
f_0=\frac{W}{h},
\qquad
\lambda_0=\frac{hc}{W}.
$$

The accepted domain convention is explicit: below threshold, no photoelectron
is emitted and a physical stopping potential is undefined. A negative dashed
line is permitted only when labelled as non-physical mathematical
extrapolation.

The frequency curves have the common gradient $h/e$. Ag, Al, and Pb coincide
because the official table displays the same $4.3\ \mathrm{eV}$ work function
for all three. Sodium has the longest ideal cut-off wavelength,
$516.601\ \mathrm{nm}$, so it alone reaches the shorter-wavelength part of the
declared visible band in this supplied comparison.

## Validation acceptance

The independent report passes all **43/43** pre-declared checks. These cover:

- exact constants, source records, conversions, grids, and finite values;
- both energy identities and the common frequency gradient;
- all 18 metal-specific analytical cut-offs;
- frequency and wavelength threshold behaviour and physical masks;
- non-negative physical voltage and undefined inactive values;
- work-function ordering, coincident materials, and cut-off ordering;
- frequency--wavelength consistency; and
- both frozen scalar reference anchors.

Deliberately changing a work function, curve value, cut-off, or emission-mask
entry causes validation to fail. The validator does not repair a failed study
or derive its reference targets from the production arrays.

## Clean regeneration acceptance

The complete out-of-tree command

```bash
python3 -m task04_photoelectric_effect.generate_task04 \
  --with-animation \
  --data-dir TEMP/data \
  --figure-dir TEMP/figures
```

produced the exact declared file sets. All **17** generated artifacts matched
the committed bytes: five data files, ten static PNG/SVG files, one animated
GIF, and one storyboard PNG. Their combined size was **5,607,430 bytes**. The
ordered aggregate comparison digest was:

```text
67c0492bd606e978def3f3d03f608d86704bbead2f7d27ab2661f2213c8f32a2
```

This SHA-256 digest uses the declared artifact order and, for each artifact,
hashes its UTF-8 filename, a null separator, its complete bytes, and another
null separator.

Transactional tests also confirm that writer, verification, or later install
failures preserve pre-existing outputs and leave no temporary siblings.

## Visual and animation acceptance

All five principal static PNGs were regenerated at 300 dpi, with the main
comparison and summary outputs at $3840\times2160$. They were inspected at
original resolution. A
wavelength-legend overlap was corrected and the affected outputs re-inspected.

The optional animation was also inspected through its complete four-panel
storyboard and extracted full-resolution frames. It is a deterministic,
six-second, $1920\times1080$, 60-frame looping GIF. One right-edge status-label
defect was corrected before acceptance. The display explicitly marks maximum
kinetic energy and stopping potential as undefined below threshold.

The animation's counts, trajectories, speeds, geometry, and scale remain
labelled schematic. Its energy and threshold states come directly from the
validated immutable study.

## Presentation acceptance

The final package contains one editable 16:9 PowerPoint slide. The required
nine-metal frequency graph is the dominant visual; the optional GIF is smaller
and secondary. The deck includes editable equations and captions, meaningful
alternative text, embedded speaker notes, and a **46-word** final script timed
for approximately 17--18 seconds.

The presentation validator confirms exactly one slide, one notes page, and two
embedded visuals. The embedded graph and animated GIF are byte-identical to
their validated source assets, and the GIF remains a complete 60-frame loop.
The static preview is $2401\times1350$ and was inspected at original
resolution.

Two consecutive clean builds and renders were byte-identical. Their accepted
SHA-256 digests are:

```text
c9450623d5188262d7f12297a67128c4d511fef131f654ae42057a54c4b06829  Task04_Photoelectric_Effect.pptx
0738bc249aaf2956b99205198617ee386d23a263a7b2b228fe9973aabc97d726  Task04_Photoelectric_Effect_preview.png
```

## Test, hygiene, and synchronization acceptance

- All **149** focused Task 4 tests pass.
- All **373** repository tests pass.
- The presentation package validator passes.
- Python compilation, JavaScript syntax, shell syntax, and `git diff --check`
  pass.
- Tracked-text scans found no credentials, private keys, machine-specific home
  directories, or temporary operating-system paths.
- No `.DS_Store`, backup, editor-temporary, or hidden generated artifact is
  present in the accepted Task 4 output folders.
- The repository is verified live as GitHub visibility **PRIVATE**.
- The accepted branch is `main`; local and `origin/main` were verified equal
  immediately before this report was added, and the final handoff verifies the
  final acceptance commit after synchronization.

## Explicit limitations retained

These are model boundaries rather than unfinished work:

- one photon transfers energy to one electron;
- each ideal metal has one uniform work function;
- wavelength means in-vacuum wavelength;
- only maximum electron kinetic energy is modelled;
- intensity is not used to infer stopping potential;
- no full current--voltage characteristic or microscopic trajectory model is
  claimed;
- surface orientation, contamination, oxidation, temperature, contact
  potential, experimental uncertainty, and electron-energy distributions are
  omitted; and
- the results validate the numerical implementation internally, not against a
  new laboratory experiment.

## Ready-to-use handoff

For the competition slide, open the
[`PowerPoint`](../presentation/task04/Task04_Photoelectric_Effect.pptx) and use
the final 17--18-second section of
[`SPEAKER_SCRIPT.md`](../presentation/task04/SPEAKER_SCRIPT.md). Confirm GIF
playback in slide-show mode before recording. The static storyboard is the
approved fallback if the recording software does not preserve GIF playback.

Task 4 is now closed. Work may proceed to Task 5 without carrying any unfinished
Task 4 implementation, evidence, presentation, or documentation step.
