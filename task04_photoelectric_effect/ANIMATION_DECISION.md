# Task 4 Optional Animation Decision

## Decision

Implement a short, deterministic, schematic animation after the mandatory
Task 4 calculation, validation, evidence, figures, and interpretation have
already passed.

The extension is worthwhile because motion communicates three relationships
that the required static graph does not show directly:

1. emission switches off when one photon's energy is below the work function;
2. increasing intensity increases the illustrative electron count without
   changing the maximum electron energy or stopping potential; and
3. a reverse voltage equal to the stopping potential prevents even the
   maximum-energy emitted electrons from reaching the collector.

The extension remains optional evidence. It does not replace the required
stopping-potential graph or any numerical validation.

## Frozen four-scene story

The animation uses sodium with the official $W=2.4\ \mathrm{eV}$ value so one
below-threshold and one above-threshold example can both use visible light.

| Scene | Frozen controls | Intended observation |
| ---: | --- | --- |
| 1 | $\lambda=550\ \mathrm{nm}$; medium intensity; $V=0$ | $E_\gamma<W$, so no photoelectron is emitted and $V_s$ is undefined |
| 2 | $\lambda=450\ \mathrm{nm}$; low intensity; $V=0$ | photoelectrons are emitted and reach the collector |
| 3 | $\lambda=450\ \mathrm{nm}$; high intensity; $V=0$ | more illustrative electrons appear, while $K_{\max}$ and $V_s$ stay unchanged |
| 4 | $\lambda=450\ \mathrm{nm}$; high intensity; $V=V_s$ | even maximum-energy electrons fail to reach the collector, so the photocurrent is zero |

At $450\ \mathrm{nm}$ the validated model gives
$E_\gamma=2.755\ \mathrm{eV}$ and
$K_{\max}=eV_s=0.355\ \mathrm{eV}$. At $550\ \mathrm{nm}$ it gives
$E_\gamma=2.254\ \mathrm{eV}<W$, so there is no emitted electron for which a
maximum kinetic energy or stopping potential could be measured.

## Scientific safeguards

- Scene values are read from the immutable, validated wavelength study; the
  animation does not contain an independent plotting-only physics model.
- The below-threshold scene says “not defined” and “undefined,” not zero or a
  negative physical stopping potential.
- The displayed electrons represent the maximum-energy boundary used by
  Einstein's equation, not the full experimental electron-energy distribution.
- Photon and electron positions, counts, speed, spacing, trajectories, plate
  geometry, and electric-field arrow are schematic and not to scale.
- Intensity level is a qualitative visual control, not a calibrated optical
  power or quantum-efficiency calculation.
- “Photocurrent” means that illustrative emitted electrons reach the collector;
  no complete current-voltage characteristic or circuit model is claimed.
- The extension remains separate from the mandatory quantitative evidence.

## Outputs and rendering contract

[`animation.py`](animation.py) writes exactly:

- [`photoelectric_demo.gif`](../figures/task04/photoelectric_demo.gif): 60
  deterministic frames, $1920\times1080$, 10 frames per second, 6 seconds,
  continuous loop; and
- [`photoelectric_demo_storyboard.png`](../figures/task04/photoelectric_demo_storyboard.png):
  a $2400\times1350$ four-panel static preview suitable for documents or slides
  that cannot play GIF files.

Both files are installed in one rollback-safe transaction only after the core
43-check report passes. Repeated clean generation must be byte-identical.

Generate only the extension with:

```bash
python3 -m task04_photoelectric_effect.animation
```

Generate the complete data, static figures, and extension with:

```bash
python3 -m task04_photoelectric_effect.generate_task04 --with-animation
```

## Acceptance result

The extension is accepted because its two artifacts regenerate
deterministically, satisfy their declared dimensions and frame contract, fit
within the existing portability budget, survive transaction-failure tests, and
make the threshold, intensity, and stopping-potential distinctions visible
without weakening the core solution's scientific claims.
