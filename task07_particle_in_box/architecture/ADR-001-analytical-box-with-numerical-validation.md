# ADR-001: Analytical Infinite-Well Model with Numerical Validation

## Status

Accepted

## Context

Task 7 requires energy against quantum number and probability densities for a
particle in an infinite box. The extension requires a defensible uncertainty-
principle calculation. The repository already uses deterministic Python
packages, saved evidence and validation-first figure generation.

## Options considered

| Option | Advantages | Limitations |
| --- | --- | --- |
| Analytical equations only | Exact, compact and directly matches the brief | A coding error could reproduce itself across every output |
| Numerical eigensolver only | Demonstrates a general computational method | Adds discretization error to a problem with a known exact solution |
| Analytical model plus independent numerical eigensolver | Exact official results and a separate convergence check | Slightly larger implementation and evidence package |

## Decision

Use the analytical infinite-well solution as the authoritative model and a
central finite-difference tridiagonal eigensolver as an independent validation
path. Use normalized axes \(x/a\) and \(a|\psi|^2\) for primary shape plots,
while retaining physical SI and electronvolt values in the data files.

## Rationale

1. The analytical solution directly answers the official task.
2. The numerical solver verifies energies, eigenfunctions, orthogonality and
   expected second-order convergence without reusing the analytical formula.
3. Dimensionless visual axes make the probability plots general and readable.
4. A modular package matches Tasks 5 and 6 and supports transactional output.

## Trade-offs

- The baseline does not include a graphical user interface.
- A stationary-state animation is excluded because \(|\psi_n|^2\) is time
  independent; a global phase animation would not add observable information.
- Finite wells, wave packets and tunnelling remain separate optional extensions.

## Consequences

- Every displayed result has an analytical definition and an independent
  numerical or high-precision reference check.
- The output package is larger than an equation-only solution but remains small
  enough for the repository and screencast workflow.
- Model assumptions and the distinction between wavefunction and probability
  density must remain explicit in every relevant figure and explanation.

## Revisit trigger

Reconsider the scope only if the official brief changes, or after the complete
Task 7 acceptance suite passes and an additional extension is requested.
