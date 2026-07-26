# Task 8 Results and Interpretation

## Direct answer to the official comparison

For the official detector settings

$$
\theta=-30^\circ,
\qquad
\phi=+30^\circ,
$$

the squared trigonometric values are

$$
\cos^2(\pm30^\circ)=\frac34,
\qquad
\sin^2(\pm30^\circ)=\frac14.
$$

The classical mismatch probability supplied by the task is therefore

$$
\begin{aligned}
P_{\mathrm C}
&=1-\cos^2\theta\cos^2\phi-\sin^2\theta\sin^2\phi\\
&=1-\frac{9}{16}-\frac{1}{16}\\
&=\frac38=0.375=37.5\%.
\end{aligned}
$$

The relative angle is \(\phi-\theta=60^\circ\), so the quantum result is

$$
P_{\mathrm Q}=\sin^2(60^\circ)=\frac34=0.750=75.0\%.
$$

Thus

$$
P_{\mathrm Q}-P_{\mathrm C}=\frac38=37.5\text{ percentage points}.
$$

At this particular setting, the quantum mismatch probability is twice the
classical value. The calculator reports the percentage-point difference rather
than a ratio because a ratio is undefined wherever the classical probability is
zero.

## Algebra that explains the full result

Using \(\cos^2x=(1+\cos2x)/2\), the classical expression becomes

$$
P_{\mathrm C}=\frac{1-\cos(2\theta)\cos(2\phi)}{2}.
$$

The quantum expression can be written

$$
P_{\mathrm Q}
=\frac{1-\cos\!\left(2\phi-2\theta\right)}{2}
=\frac{1-\cos(2\theta)\cos(2\phi)-\sin(2\theta)\sin(2\phi)}{2}.
$$

Subtracting gives the compact contrast equation

$$
\boxed{\Delta P=P_{\mathrm Q}-P_{\mathrm C}
=-\frac12\sin(2\theta)\sin(2\phi)}.
$$

This form explains all four lobes in the contrast heatmap:

- \(\Delta P>0\) when \(\sin(2\theta)\) and \(\sin(2\phi)\) have opposite signs;
- \(\Delta P<0\) when they have the same sign;
- \(\Delta P=0\) when either doubled-angle sine is zero; and
- \(-0.5\leq\Delta P\leq+0.5\).

Maximum positive contrast occurs, for example, at
\(\theta=-45^\circ,\phi=+45^\circ\): the classical model gives 50% and the
quantum model gives 100%. Maximum negative contrast occurs at equal 45° settings:
the classical model gives 50% while the quantum model gives 0%.

## What the fixed-θ sweep shows

The primary sweep fixes \(\theta=-30^\circ\) and varies \(\phi\) from −90° to
+90°. The equations reduce to

$$
P_{\mathrm C}=\frac12-\frac14\cos(2\phi),
$$

$$
P_{\mathrm Q}=\sin^2(\phi+30^\circ),
$$

$$
\Delta P=\frac{\sqrt3}{4}\sin(2\phi).
$$

The classical sweep therefore stays between 25% and 75%. The quantum sweep
reaches 0% at \(\phi=-30^\circ\), where both detectors are aligned, and 100% at
\(\phi=+60^\circ\), where their relative angle is 90°. The official point at
\(\phi=+30^\circ\) lies between those extrema and gives 37.5% versus 75.0%.

The two curves must be read on the same 0–100% axis. Autoscaling each curve
separately would exaggerate or hide their difference, so the calculator and all
figures keep the physical probability scale fixed.

## What the two-dimensional landscape shows

The classical surface depends on the product
\(\cos(2\theta)\cos(2\phi)\). It is symmetric when the detector labels are
exchanged, but it retains both absolute orientations relative to the chosen
reference axis.

The quantum surface is \(\sin^2(\phi-\theta)\). It depends only on relative
orientation, which produces diagonal bands:

- the main diagonal \(\phi=\theta\) is exactly zero mismatch;
- parallel diagonal lines repeat because polarisation axes have a 180° period;
- a 90° relative angle gives unit mismatch.

Equal detector settings are especially instructive. Quantum mismatch is always
zero because the measurement bases coincide. The supplied classical comparison
instead gives

$$
P_{\mathrm C}(\theta,\theta)=\frac12\sin^2(2\theta),
$$

which reaches 50% at \(\theta=\pm45^\circ\). This difference is a property of
the two mathematical models defined by the task. The calculator demonstrates
that contrast; it does not by itself constitute a laboratory Bell test or a
general proof against every classical theory.

## Optional finite-photon demonstration

Exact theory gives probabilities, whereas a finite experiment gives integer
counts. For \(N\) detected pairs the extension samples

$$
K_{\mathrm C}\sim\operatorname{Binomial}(N,P_{\mathrm C}),
\qquad
K_{\mathrm Q}\sim\operatorname{Binomial}(N,P_{\mathrm Q})
$$

on independent deterministic pseudo-random streams. At the official angles with
\(N=1000\) and seed 2026, the accepted sample is:

| Model | Exact theory | Expected count | Observed count | Observed fraction | 95% Wilson interval | Residual |
|---|---:|---:|---:|---:|---:|---:|
| Classical | 37.5% | 375.0 | 363 | 36.3% | 33.4–39.3% | −0.78σ |
| Quantum | 75.0% | 750.0 | 770 | 77.0% | 74.3–79.5% | +1.46σ |

The observed difference is +40.7 percentage points, rather than the exact
+37.5 percentage points, because finite counts fluctuate. Both observed rates
remain statistically ordinary for their generating probabilities. The Wilson
interval estimates a binomial proportion from one observed sample; it is not an
uncertainty interval for the exact equations.

The typical sampling scale decreases approximately as \(1/\sqrt N\). Individual
seeded points need not move monotonically toward theory, but their interval widths
contract as \(N\) grows. One pseudo-random realization is an illustration, not
independent evidence that either physical model is correct.

## Figure-by-figure reading guide

1. [`probability_sweep`](../figures/task08/probability_sweep.png) is the clearest
   answer to the interactive-calculator question. The upper panel compares exact
   probabilities; the lower panel shows their signed difference.
2. [`mismatch_landscape`](../figures/task08/mismatch_landscape.png) shows that the
   quantum prediction forms relative-angle bands while the classical prediction
   retains the two absolute detector directions.
3. [`finite_photon_sampling`](../figures/task08/finite_photon_sampling.png) keeps
   theory, one observed sample and its Wilson interval separate, then shows the
   shrinking sampling scale as \(N\) increases.
4. [`task08_summary`](../figures/task08/task08_summary.png) combines the geometry,
   exact comparison, full contrast map and reproducible sample for a 16:9
   competition presentation.

All four PNGs were inspected at original resolution. Each has editable SVG and PDF
companions; the accepted output dimensions and visual checks are recorded in
[`STAGE7_ACCEPTANCE.md`](STAGE7_ACCEPTANCE.md).

## Physical and statistical limitations

The ideal model omits loss, detector inefficiency, dark counts, dead time,
decoherence, imperfect entanglement, angular calibration uncertainty and finite
timing resolution. The optional sampler conditions directly on the ideal
probabilities and therefore does not add those effects.

The implementation also stops before quantum-key-distribution protocol steps:
there is no random basis choice, eavesdropper, basis sifting, quantum-bit error
rate threshold, error correction, privacy amplification or composable security
claim. The reproducible Mulberry32 generator is deliberately unsuitable for real
cryptography.

Within those declared assumptions, the result is not a numerical approximation:
the browser evaluates the exact supplied equations, and the Python study confirms
them against independent double-angle forms on the complete approved grids.
