# Task 8 finite-photon statistical extension

## Purpose and separation from the official calculator

The official Task 8 equations give exact ideal mismatch probabilities. A real finite run produces integer counts that fluctuate around those probabilities. This optional extension demonstrates that sampling variation without changing or replacing the official result.

For fixed detector angles, write

$$
p_{\mathrm C}=P_{\mathrm C}(\text{mismatch}),
\qquad
p_{\mathrm Q}=P_{\mathrm Q}(\text{mismatch}).
$$

For \(N\) detected photon pairs, the simulated mismatch counts are independent binomial random variables,

$$
K_{\mathrm C}\sim\operatorname{Binomial}(N,p_{\mathrm C}),
\qquad
K_{\mathrm Q}\sim\operatorname{Binomial}(N,p_{\mathrm Q}).
$$

The observed mismatch fraction for either model is

$$
\hat p=\frac{K}{N}.
$$

Its exact binomial expectation and standard deviation are

$$
E[K]=Np,
\qquad
\sigma_K=\sqrt{Np(1-p)}.
$$

When \(\sigma_K>0\), the calculator also reports the standardised residual

$$
z_{\mathrm{sample}}=\frac{K-Np}{\sqrt{Np(1-p)}}.
$$

At \(p=0\) or \(p=1\), the count is deterministic and the residual is labelled accordingly rather than dividing by zero.

## 95% Wilson interval

The displayed interval estimates an unknown binomial mismatch probability from the observed count. With (z=1.959963984540054),

$$
\text{centre}
=\frac{\hat p+z^2/(2N)}{1+z^2/N},
$$

$$
\text{half-width}
=\frac{z}{1+z^2/N}
\sqrt{\frac{\hat p(1-\hat p)}{N}+\frac{z^2}{4N^2}}.
$$

The interval is the centre plus or minus the half-width, clipped only to the probability range \([0,1]\). It is labelled a **95% Wilson interval**, not an error bar on the exact theoretical equation. Wilson intervals are used instead of the simple normal interval because they remain finite and informative when the observed count is zero or \(N\).

## Reproducible pseudo-random sampling

The extension uses a 32-bit Mulberry32 pseudo-random generator because it is small, deterministic and exactly reproducible in both Python and JavaScript. The displayed unsigned seed lies in

$$
0\leq s\leq2^{32}-1.
$$

Classical and quantum samples use independently salted streams derived from the displayed seed. The same angles, photon count and seed therefore reproduce the same counts across both implementations.

Mulberry32 is **not cryptographically secure**. It is used only to make an educational Monte Carlo result reproducible; it must never generate a real cryptographic key or security token.

## Frozen interaction conventions

- Photon-pair count: integer from 10 to 100,000.
- Default photon-pair count: 1,000.
- Default seed: 2,026.
- Changing an angle, count or seed immediately recomputes the deterministic sample.
- “Next sample” advances the unsigned seed by one, wrapping after \(2^{32}-1\).
- Both models use the same \(N\) but separate pseudo-random streams.
- The observed and theoretical probabilities remain on a fixed 0–100% visual scale.

## Acceptance criteria

- Counts are integers and satisfy \(K+(N-K)=N\).
- \(p=0\) always produces zero mismatches and \(p=1\) always produces \(N\).
- Expected counts, standard deviations, residuals and Wilson bounds match independent formulas.
- Every Wilson interval is ordered and lies in \([0,1]\).
- Fixed Python fixtures agree exactly with JavaScript counts and within numerical tolerance for derived values.
- Repeating a seed is deterministic; advancing the seed selects a new sample.
- The maximum approved sample of 100,000 pairs per model remains within the interaction budget.
- The interface explicitly distinguishes theoretical probability from one finite observed sample.

## Limitations

This extension models only ideal binomial sampling conditional on the official mismatch probabilities. It does not add photon loss, detector inefficiency, dark counts, dead time, basis sifting, eavesdropping, error correction, privacy amplification or a full quantum-key-distribution protocol.
