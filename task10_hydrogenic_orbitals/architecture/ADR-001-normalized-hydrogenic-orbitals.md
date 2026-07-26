# ADR-001 — Normalized Hydrogenic Orbital Core

Status: accepted

## Context

The official Task 10 slides provide a useful plotting recipe but mix angular
coordinate labels, present shape-only real-harmonic combinations without the
\(\sqrt2\) normalization factor, and use MATLAB special functions. A
competition-quality implementation needs reproducible normalization, explicit
orientation and an independent validation route.

## Decision

1. Use the official nuclear approximation \(M=A\,u\), with integer \(A\), so the
   default reproduces the displayed hydrogen energy.
2. Freeze standard polar colatitude \(\vartheta\) and azimuth \(\varphi\).
3. Use normalized real tesseral harmonics oriented as \(p_x,p_y,p_z\) for
   \(m=+1,-1,0\).
4. Implement associated Laguerre and sign-free Ferrers recurrences locally with
   NumPy; do not require SciPy for the scientific core.
5. Validate recurrence output against the official finite Laguerre sum and a
   separately coded scalar Ferrers reference.
6. Keep SI density, dimensionless scaled density and display-relative density as
   separate named outputs.
7. Use quadrature—not a finite Cartesian visualization grid—to certify
   normalization and orthogonality.
8. Retain the full field and apply the official 0.15 threshold only in the
   renderer.
9. Validate \(1\leq n\leq8\), including all official S–G states through \(n=5\).

## Consequences

- Every displayed orbital is a normalized physical state before visualization.
- The official shapes are reproduced while their omitted normalization is
  corrected transparently.
- Python and browser implementations can share small deterministic recurrences.
- Visual thresholds and camera choices cannot change validation results.
- A wider domain would require a new conditioning and performance review rather
  than an untested increase in control limits.
