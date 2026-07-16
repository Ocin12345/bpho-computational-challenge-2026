# Task 4 Speaker Script

## Final competition version — approximately 17–18 seconds

Use this version in the final three-minute video:

> Task 4 models Einstein's photoelectric equation for nine metals. Every
> stopping-potential curve has gradient h over e; the work function sets the
> threshold. Sodium reaches visible light up to 517 nanometres. Below
> threshold, no photoelectrons exist, so stopping potential is undefined. All
> forty-three independent checks passed.

The equations, metal labels, and exact threshold markers remain visible and do
not need to be read aloud in the competition version.

### Visual cues

| Time | What to show or indicate | Words being spoken |
| --- | --- | --- |
| $0$--$7$ s | Indicate the parallel physical curves and threshold markers | “Task 4 models … sets the threshold.” |
| $7$--$12$ s | Indicate sodium and the $516.6\ \mathrm{nm}$ result | “Sodium reaches … nanometres.” |
| $12$--$18$ s | Indicate the animation status, then the validation badge | “Below threshold … checks passed.” |

Do not try to name all nine metals aloud. Their labels are already visible, and
the threshold ordering is more important than reciting the source table.

## Expanded version — approximately 35 seconds

Use this only if the final video plan gives Task 4 additional time:

> For Task 4, I used Einstein's photoelectric equation to calculate stopping
> potential against frequency and vacuum wavelength for all nine supplied
> metals. Every frequency curve has the same gradient, h over e, while a larger
> work function moves the threshold to higher frequency and shorter wavelength.
> Sodium has the lowest supplied work function, so it is the only material here
> that emits for part of the visible range, up to 516.6 nanometres. Below a
> threshold there are no photoelectrons, so stopping potential is undefined,
> not negative. The optional animation also shows that intensity changes the
> electron count rather than their maximum energy. All forty-three checks pass.

## Detailed rehearsal version — approximately 90 seconds

This version is for understanding and practice. It is too long for the final
three-minute video if all ten tasks must be included.

> Task 4 applies Einstein's photoelectric equation. One photon transfers energy
> $hf$ to one electron. The metal requires the work function $W$ to release the
> electron, leaving maximum kinetic energy $hf-W$. A reverse stopping potential
> removes that energy, so $eV_s=hf-W$.
>
> The required frequency plot is therefore a set of straight lines with common
> gradient $h/e$. Changing the metal changes the work function and shifts the
> threshold, but it does not change the gradient. Silver, aluminium, and lead
> coincide exactly because the official table gives each one the same displayed
> work function, 4.3 electronvolts. Gold has the highest supplied work function
> and therefore the highest threshold frequency. Sodium has the lowest value,
> 2.4 electronvolts, and its cut-off wavelength is 516.6 nanometres, so it emits
> for the shorter-wavelength part of visible light in this ideal model.
>
> Below threshold, the algebraic straight line becomes negative, but this is
> only an energy deficit. No electron is emitted, so there is no physical
> stopping potential to measure. The optional animation preserves this rule and
> also separates intensity from energy: more photons can produce more emitted
> electrons, while their maximum kinetic energy remains set by frequency and
> work function. At the stopping potential, even maximum-energy electrons fail
> to reach the collector.
>
> The forty-three independent checks test both Einstein identities, the common
> gradient, every metal's two analytical cut-offs, the physical masks,
> frequency-wavelength consistency, coincident materials, ordering, bounds, and
> scalar reference values. All checks pass. This remains an ideal one-photon,
> uniform-surface model rather than an experimental measurement of a real metal.

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| Einstein | “EYE-n-stine” |
| photoelectric | “foh-toh-ee-LEK-trik” |
| $h/e$ | “h over e” |
| $V_s$ | “stopping potential” or “V s” |
| $K_{\max}$ | “maximum kinetic energy” |
| electronvolt | “electron volt” |
| $516.6\ \mathrm{nm}$ | “five hundred and sixteen point six nanometres” |
| Ag, Al, Pb | “silver, aluminium, and lead” |

## Questions you should be ready to answer

**Why are all the frequency curves parallel?**

The equation is $V_s=(h/e)f-W/e$. Its gradient $h/e$ contains no material
property. A different work function changes the intercept and threshold only.

**Why do silver, aluminium, and lead appear as one curve?**

The official source rounds all three work functions to $4.3\ \mathrm{eV}$.
The ideal calculation therefore gives exactly coincident curves. More precise
real-surface work functions need not be identical.

**Why is stopping potential undefined below threshold rather than zero?**

Below threshold, one photon does not supply enough energy to release an
electron. With no emitted photoelectrons, there is no electron current to stop
and therefore no measurable stopping potential.

**What does a negative dashed line mean?**

It is the mathematical extrapolation $hf/e-W/e$. A negative value represents
an energy deficit, not a negative physical stopping-potential measurement.

**Why is sodium the only material shown emitting in visible light?**

Its supplied work function is the smallest, so its ideal cut-off wavelength is
$516.6\ \mathrm{nm}$. It emits only from the shorter-wavelength part of the
declared visible band, not from all visible wavelengths.

**Does increasing intensity increase stopping potential?**

Not in this one-photon model at fixed frequency. Greater intensity can increase
the number of emitted electrons and hence photocurrent, but $K_{\max}=hf-W$
and $V_s$ are unchanged.

**Is the GIF a quantitative trajectory simulation?**

No. Its counts, paths, speed, geometry, field arrow, and scale are schematic.
Its energy, threshold, and stopping-potential states come from the validated
study, but it does not model microscopic trajectories or a full circuit.

**How was the calculation validated?**

The 43 pre-declared checks compare the NumPy study with independent Decimal
references and analytical identities. They cover constants, grids, work
functions, both energy forms, gradient, all cut-offs, masks, domains, ordering,
coincident curves, cross-coordinate consistency, and frozen scalar anchors.

**What is the most important limitation?**

Each metal is represented by one uniform work function. Real values depend on
surface orientation, cleanliness, oxidation, temperature, and contact
potentials, and emitted electrons have an energy distribution below the
maximum.

**Why are repeated simulations or a GPU unnecessary?**

The model is deterministic and vectorized on fixed frequency and wavelength
grids. There is no randomness, particle time-stepping, fitting, or expensive
optimization, so the MacBook Air is already more than sufficient.
