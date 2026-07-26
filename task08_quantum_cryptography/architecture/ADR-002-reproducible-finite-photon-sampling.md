# ADR-002: Reproducible finite-photon sampling

## Status

Accepted

## Context

The official calculator reports ideal probabilities, whereas a finite sequence of detected photon pairs produces fluctuating integer counts. The extension must illustrate this distinction, remain fast in the static browser app, work offline and be independently reproducible in Python.

## Options considered

| Option | Advantages | Limitations |
|---|---|---|
| Browser `Math.random()` | Minimal code | Cannot reproduce a sample or compare it exactly with Python |
| Cryptographic browser randomness | Strong entropy | Deliberately non-reproducible and unnecessary for an educational simulation |
| Normal approximation only | Fast closed form | Does not generate integer binomial outcomes and performs poorly near 0 or 1 |
| Seeded Bernoulli sampling with Wilson intervals | Integer outcomes, reproducible cross-language fixtures and robust displayed intervals | Requires a small PRNG implementation in both languages |

## Decision

Use exact Bernoulli counting with a displayed 32-bit seed and independent salted Mulberry32 streams for the two models. Compute uncertainty summaries from the exact binomial mean and variance. Display a 95% Wilson interval for the observed fraction.

Keep the implementation in a separate Python `statistics.py` module and browser `statistics.js` module. The official probability functions remain unchanged. A separate statistical validation report and manifest preserve the distinction between the 42 baseline physics checks and the extension checks.

## Rationale

1. Integer Bernoulli counting is the direct simulation of a binomial experiment.
2. A visible seed makes screenshots, tests and demonstrations reproducible.
3. Separate salted streams avoid presenting the two conceptual models as the same physical event sequence.
4. Wilson intervals behave sensibly for zero and full counts without external numerical libraries.
5. A separate module and report keep the optional extension from obscuring the official answer.

## Consequences

- The generator is suitable for reproducible simulation but explicitly unsuitable for real cryptography.
- A 100,000-pair limit bounds browser work to 200,000 Bernoulli draws per update.
- Python-generated reference fixtures must test exact cross-language counts.
- Accessibility and responsive checks must cover the added controls, status updates and interval graphics.
