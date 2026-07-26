# Task 8 Mathematical Model

## Scope and detector convention

An ideal source sends an entangled photon pair to detectors A and B. Detector A
has orthogonal outcomes \(X_A\) and \(Y_A\); detector B has orthogonal outcomes
\(X_B\) and \(Y_B\). Their \(X\)-axes are oriented at angles \(\theta\) and
\(\phi\) relative to one fixed reference axis.

Polarisation axes are unoriented lines, so adding \(180^\circ\) describes the
same physical setting. The user-facing interval is therefore
\(-90^\circ\leq\theta,\phi\leq90^\circ\), with the two endpoints physically
equivalent. Angles are displayed in degrees and converted to radians before
trigonometric evaluation.

## Classical comparison model

Malus' law assigns the marginal probabilities

$$
P(X_A)=\cos^2\theta,\quad P(Y_A)=\sin^2\theta,
$$

$$
P(X_B)=\cos^2\phi,\quad P(Y_B)=\sin^2\phi.
$$

In the classical comparison supplied by the task, the two detector outcomes
are combined independently. Matching outcomes therefore have probability

$$
P_{\mathrm C}(\mathrm{match})
=\cos^2\theta\cos^2\phi+\sin^2\theta\sin^2\phi,
$$

and

$$
P_{\mathrm C}(\mathrm{mismatch})
=1-\cos^2\theta\cos^2\phi-\sin^2\theta\sin^2\phi.
$$

An algebraically independent validation form is

$$
P_{\mathrm C}(\mathrm{mismatch})
=\frac{1-\cos(2\theta)\cos(2\phi)}{2}.
$$

## Quantum model

Measurement at detector A collapses the photon pair into the measured basis.
Detector B is then separated from that basis by

$$
\delta=\phi-\theta.
$$

The quantum matching and mismatch probabilities are

$$
P_{\mathrm Q}(\mathrm{match})=\cos^2\delta,
\qquad
P_{\mathrm Q}(\mathrm{mismatch})=\sin^2\delta.
$$

An independent validation form is

$$
P_{\mathrm Q}(\mathrm{mismatch})
=\frac{1-\cos(2\delta)}{2}.
$$

## Comparison quantity

The calculator reports the signed difference

$$
\Delta P=P_{\mathrm Q}(\mathrm{mismatch})
-P_{\mathrm C}(\mathrm{mismatch}).
$$

A positive value means the quantum model predicts more mismatches; a negative
value means it predicts fewer. This definition avoids an unstable probability
ratio when the classical prediction is zero.

## Reference cases

| \(\theta\) | \(\phi\) | Classical mismatch | Quantum mismatch | \(\Delta P\) | Purpose |
| ---: | ---: | ---: | ---: | ---: | --- |
| \(-30^\circ\) | \(30^\circ\) | \(3/8\) | \(3/4\) | \(3/8\) | Official example |
| \(0^\circ\) | \(0^\circ\) | \(0\) | \(0\) | \(0\) | Common reference axis |
| \(45^\circ\) | \(45^\circ\) | \(1/2\) | \(0\) | \(-1/2\) | Maximum negative contrast |
| \(-45^\circ\) | \(45^\circ\) | \(1/2\) | \(1\) | \(1/2\) | Maximum positive contrast |
| \(0^\circ\) | \(90^\circ\) | \(1\) | \(1\) | \(0\) | Perpendicular axes |

## Optional finite-photon extension

The official equations above remain exact ideal probabilities. Stage 6 adds an
explicitly separate finite-sample demonstration in which the classical and
quantum mismatch counts are independent binomial draws with the same selected
photon-pair count. Expected counts, binomial standard deviations, standardised
residuals and 95% Wilson intervals are defined in
[`STATISTICAL_EXTENSION.md`](STATISTICAL_EXTENSION.md).

## Numerical and plotting conventions

- All probabilities are dimensionless and plotted on the fixed interval
  \([0,1]\).
- Percentages are probabilities multiplied by 100; they are not a separate
  calculation.
- Angle sweeps include both endpoints and zero degrees.
- Difference plots use a diverging scale centred on \(\Delta P=0\).
- Values slightly outside \([0,1]\) by round-off may be clipped only after the
  unclipped value passes the configured numerical tolerance.
- The browser and Python implementations must agree on shared reference cases
  within the configured cross-language tolerance.

## Declared limitations

The baseline assumes ideal entangled pairs, perfect two-outcome detectors,
perfect alignment, no photon loss, no background counts and no decoherence. It
does not model a complete BB84 exchange, key sifting, error correction,
privacy amplification, detector loopholes or every possible classical hidden-
variable theory. The classical expression is specifically the comparison model
defined by the official Task 8 presentation.
