# Task 7 Extension Decision

## Numerical momentum upgrade

The official uncertainty result is now accompanied by a separate real-space
finite-difference momentum calculation. Normalized eigenvectors from the
100, 200, 400, 800 and 1600-point grids are acted on by central first- and
second-derivative operators to obtain ⟨p⟩, ⟨p²⟩, Δp and ΔxΔp directly. The
analytical values are comparison references only. The route is covered by
regression tests, 50 scientific checks and the visible numerical-moments and
convergence evidence on the Task 7 page.

## Decision

Keep the official Heisenberg uncertainty-principle extension unchanged and
accept one separate coherent-superposition lab after the full stationary-state
baseline is secure.

The new lab combines the accepted $n=1$ and $n=2$ infinite-well eigenstates
with equal probabilities. It is optional, appears after the official proof,
and uses its own model module, evidence schema, tests, browser controls, and
interpretation boundary.

## Why this extension

A single eigenstate has

$$
\psi_n(x,t)=\phi_n(x)e^{-iE_nt/\hbar},
$$

so its global phase changes while $|\psi_n|^2$ remains stationary. Motion in a
density plot would therefore be misleading. A coherent superposition has a
relative phase and a genuinely time-dependent density:

$$
\Psi(x,t)=\frac{1}{\sqrt2}\left(\psi_1+\psi_2\right),
\qquad
\theta=\frac{(E_2-E_1)t}{\hbar},
$$

$$
a|\Psi|^2
=\sin^2(\pi u)+\sin^2(2\pi u)
+2\cos\theta\sin(\pi u)\sin(2\pi u),
\qquad u=\frac{x}{a}.
$$

This directly explains the difference between an unobservable global phase
and observable interference.

## Accepted implementation

- equal $n=1$ and $n=2$ probabilities, each $1/2$;
- manual relative-phase control from $0$ to $2\pi$ with five exact presets;
- a normalized density chart and expectation-position marker;
- live $t/T$, $\langle x\rangle/a$, left-half probability, and mean-energy
  readouts;
- the $1.00$ nm electron-box beat period, $T=3.666078$ fs;
- 17 frozen phase anchors and 14/14 independent extension checks;
- deterministic JSON and CSV evidence plus a PNG chart export; and
- desktop and mobile interaction, overflow, console, semantics, and high-DPI
  canvas audits.

There is no autoplay. Time is controlled manually so the visual change remains
a deliberate physics comparison rather than decorative motion.

## Interpretation boundary

The density is a probability distribution, not a classical particle path. The
extension does not simulate measurement collapse, decoherence, finite walls,
tunnelling, environmental noise, or particle interactions.

Finite wells, higher-dimensional boxes, perturbing fields, and interacting
particles remain deferred.

## Reproduction

```bash
python3 -m task07_particle_in_box.generate_superposition_extension
python3 -m unittest task07_particle_in_box.test_superposition_extension -v
node site/validate-task-07.mjs
```
