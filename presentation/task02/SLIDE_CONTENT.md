# Text to Put on the Task 2 Slide

## Title

**Task 2 — Collision-Driven Brownian Motion**

## One-line claim

**Random molecular impacts produce unbiased diffusive tracer motion.**

## Reference-run caption

```text
Reference simulation
N = 1,000  •  200 ps  •  3,721 collision impulses
```

## Result box

Use only these three lines on the visible slide:

```text
64-run ensemble: ⟨Δx⟩ and ⟨Δy⟩ 95% CIs include 0
MSD ∝ t: R² = 0.983; D = 2.25 × 10⁻³ nm² ps⁻¹
Time-step halving: ΔD = 5.7%; all 224 runs numerically valid
```

The first line establishes that there is no statistically significant drift.
The second provides the main Brownian-motion result. The third shows that the
result is not an obvious time-step artefact and that every ensemble run passed
the numerical checks.

## Image alternative text

**Reference animation:** One thousand blue small particles move inside a square
container. A large translucent yellow tracer begins at the centre, while an
orange trail accumulates as collisions make its centre follow an irregular
path.

**Baseline statistics:** The left panel shows mean-squared displacement from 64
simulations with a 95% confidence band and a linear fit between 20 and 100
picoseconds. The right panel shows a roughly circular cloud of final horizontal
and vertical displacements centred close to the origin.

## Content rule

Do not add the collision derivation, parameter table, code screenshots, or all
four parameter experiments to this slide. They are useful supporting evidence,
but they would weaken the single main claim at competition-video size.
