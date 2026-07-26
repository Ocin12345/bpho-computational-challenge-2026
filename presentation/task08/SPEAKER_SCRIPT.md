# Task 8 Speaker Script

## Final competition version

> Task 8 compares classical Malus probabilities with the entangled quantum
> prediction. At minus thirty and plus thirty degrees, classical mismatch is
> thirty-seven point five percent, while quantum mismatch is seventy-five
> percent. The sweep exposes their different angle dependence; a finite sample
> shows counting fluctuations. All sixty-six validation checks pass.

### Visual cues

- **0–5 seconds:** show the detector geometry and 60° separation.
- **5–11 seconds:** follow the solid/dashed sweep to the official markers.
- **11–15 seconds:** point to the contrast heatmap and the finite sample.
- **15–18 seconds:** finish on the 42/42 and 24/24 validation statement.

## Expanded 35-second version

> Task 8 compares the detector-mismatch probabilities supplied for classical
> independent Malus outcomes and an entangled quantum pair. At detector angles
> minus thirty and plus thirty degrees, the classical result is thirty-seven
> point five percent, but the quantum result is seventy-five percent. The sweep
> shows that the quantum model follows only the relative detector angle, while
> the classical comparison keeps both absolute orientations. The lower panels
> map that contrast and show one reproducible finite-photon sample. All
> forty-two scientific and twenty-four statistical checks pass.

## Rehearsal explanation

The exact equations are

$$
P_{\mathrm C}
=1-\cos^2\theta\cos^2\phi-\sin^2\theta\sin^2\phi,
$$

$$
P_{\mathrm Q}=\sin^2(\phi-\theta).
$$

At \(-30^\circ,+30^\circ\), these give \(3/8\) and \(3/4\). The signed
contrast simplifies to

$$
P_{\mathrm Q}-P_{\mathrm C}
=-\frac12\sin(2\theta)\sin(2\phi),
$$

so its full range is −50 to +50 percentage points. The finite-photon panel does
not change the official answer; it demonstrates how integer counts fluctuate
around exact probabilities.

## Pronunciation guide

| Term | Say it as |
|---|---|
| \(\theta\) | “theta” |
| \(\phi\) | “fie” |
| Malus | “MAL-us” |
| Wilson interval | “WILL-sun interval” |
| percentage point | the direct difference between two percentages |

## Questions you should be ready to answer

**Why is the quantum value 75% in the official case?**

The detector separation is 60°, so \(P_{\mathrm Q}=\sin^2 60^\circ=3/4\).

**Why can the two models disagree even at equal detector settings?**

Quantum mismatch is zero whenever \(\phi=\theta\). The supplied classical
comparison combines independent Malus-law outcomes and gives
\(\tfrac12\sin^2(2\theta)\), which can be non-zero.

**Why report percentage points instead of saying “twice as large”?**

The factor of two is true only at the official setting. A ratio becomes undefined
when the classical probability is zero, while the signed percentage-point
difference is defined everywhere.

**What do 363 and 770 represent?**

They are one reproducible pair of binomial mismatch counts from 1,000 simulated
photon pairs at seed 2026. They illustrate sampling variation and are not extra
exact predictions.

**Does this demonstrate secure quantum cryptography?**

No. The official task asks for a probability comparison. The calculator does not
implement basis sifting, an eavesdropper, error correction, privacy amplification
or a security proof, and its pseudo-random sampler is not cryptographically secure.
