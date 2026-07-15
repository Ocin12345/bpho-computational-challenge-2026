# Task 2 Speaker Script

## Final competition version — approximately 17–18 seconds

Use this version in the final three-minute video:

> Task 2 models one thousand small particles colliding with a larger particle
> initially at rest, producing an irregular path. Across sixty-four runs,
> displacement was unbiased and mean-squared displacement was linear: R
> squared 0.983, with a diffusion coefficient of 2.25 times ten to the minus
> three.

The unit, `nm² ps⁻¹`, remains visible on the slide and does not need to be read
aloud in the competition version.

### Visual cues

| Time | What to show or indicate | Words being spoken |
| --- | --- | --- |
| 0–6 s | Let the reference GIF play; indicate the tracer and its trail | “Task 2 models … irregular path.” |
| 6–12 s | Move attention to the endpoint cloud and first result line | “Across sixty-four runs, displacement was unbiased …” |
| 12–18 s | Indicate the linear-fit segment and diffusion result | “… mean-squared displacement … minus three.” |

Say the final number steadily: “two point two five times ten to the minus
three.” Do not attempt to describe the parameter-experiment figure in this
short version.

## Expanded version — approximately 35 seconds

Use this only if the final video plan gives Task 2 additional time:

> For Task 2, I modelled one thousand small particles moving at a prescribed
> thermal speed around a larger particle that starts from rest. Momentum and a
> coefficient of restitution determine every small–large collision, while
> periodic random direction changes represent unresolved molecular scattering.
> The collision impulses produce the irregular tracer path shown. Across
> sixty-four independent runs, both mean-displacement confidence intervals
> included zero. The mean-squared displacement was approximately linear from
> 20 to 100 picoseconds, with R squared 0.983 and effective diffusion
> coefficient 2.25 times ten to the minus three nanometres squared per
> picosecond. Halving the time step changed this estimate by only 5.7 percent.

## Detailed rehearsal version — approximately 90 seconds

This version is for understanding and practice. It is too long for the final
three-minute video if all ten tasks must be included.

> Task 2 asks how random molecular impacts can produce Brownian motion. I used
> a two-dimensional square containing one thousand identical small particles
> and one larger tracer. The tracer begins at rest in the centre. Small
> particles move at the thermal speed specified by the challenge and their
> directions are periodically randomized. This replaces unresolved molecular
> scattering, so I do not also include explicit small–small collisions.
>
> At every small–large contact, I calculate the collision normal and apply an
> impulse only when the pair is approaching. The impulse conserves vector
> momentum and satisfies the chosen coefficient of restitution. The reference
> model is elastic, with coefficient one. Radius-aware wall reflections keep
> all particle centres inside the container.
>
> The reference animation uses one thousand small particles for 200
> picoseconds. It records 3,721 applied collision impulses, which make the
> initially stationary tracer follow an irregular path. One trajectory cannot
> establish Brownian behaviour, so I analysed 64 independent baseline runs.
> The 95-percent confidence intervals for mean horizontal and vertical
> displacement both include zero, and the endpoint cloud has no preferred
> direction.
>
> In the pre-declared 20-to-100-picosecond interval, mean-squared displacement
> is approximately linear, with R squared 0.983. Using the two-dimensional
> relation mean-squared displacement equals four D t gives an effective
> diffusion coefficient of 2.25 times ten to the minus three nanometres squared
> per picosecond. A matched half-time-step ensemble differed by 5.7 percent and
> had an overlapping confidence interval. All 224 statistical runs also passed
> the deterministic collision and geometry checks. This supports unbiased,
> collision-driven diffusion within the declared simplified model.

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| MSD | “mean squared displacement” |
| $R^2$ | “R squared” |
| $D$ | “D” or “diffusion coefficient” |
| $2.25\times10^{-3}$ | “two point two five times ten to the minus three” |
| $mathrm{nm^2\,ps^{-1}}$ | “nanometres squared per picosecond” |
| coefficient of restitution | “coefficient of restitution” |
| isotropic | “eye-so-TROP-ik” |
| Knudsen | “NUD-sen” |

## Questions you should be ready to answer

**Why does the large particle begin at rest?**

That is the explicit Task 2 condition. Its later velocity therefore comes only
from the simulated collision impulses.

**Why randomize small-particle directions?**

The official example uses direction changes to represent unresolved molecular
scattering while preserving the small particles' prescribed speed. Explicit
small–small collisions are omitted so the same scattering is not counted
twice.

**How is a small–large collision calculated?**

The code resolves the relative velocity along the contact normal, applies an
impulse only to approaching particles, conserves vector momentum, and enforces
the coefficient-of-restitution equation. Tangential relative velocity is
unchanged.

**Why are 64 runs needed?**

One stochastic trajectory can drift in any direction by chance. An ensemble
is needed to estimate mean displacement, directional spread, mean-squared
displacement, and confidence intervals. The final sample size was fixed before
the reported analysis and was large enough for all declared statistical checks
to pass.

**How is the diffusion coefficient obtained?**

For two-dimensional diffusion, intermediate-time mean-squared displacement is
approximately $4Dt$. A straight line is fitted only over the pre-declared
20-to-100-picosecond window, and the fitted slope is divided by four.

**Why not fit all the way to 200 ps?**

The reflecting container eventually confines the tracer, so late-time motion
is not expected to follow unrestricted linear diffusion. The intermediate
window avoids both the earliest inertial transient and much of the later
confinement.

**How do you know the result is not caused by an unsafe time step?**

The baseline maximum one-step movement is below 40 percent of the declared
limit. Controlled collision tests converge at first order, and a 64-run matched
half-step ensemble changes $D$ by 5.7 percent with overlapping confidence
intervals.

**What is the most important limitation?**

This is a two-dimensional pedagogical heat-bath model. Small particles have one
speed, direction resets replace explicit molecular collisions, and the tracer
mass and size are scaled for visible computation. Its conclusions apply to the
simulation, not as a complete quantitative model of pollen in a real fluid.

**Does increasing particle count always reduce real Brownian diffusion?**

No. That trend appears in this finite simplified model and should not be stated
as a universal density law. The other parameter comparisons also have broadly
overlapping intervals, so they are supporting explorations rather than strong
monotonic conclusions.
