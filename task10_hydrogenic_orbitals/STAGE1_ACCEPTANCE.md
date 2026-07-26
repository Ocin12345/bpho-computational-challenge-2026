# Task 10 Stage 1 Acceptance — Mathematical Model

Status: **PASS**

## Model acceptance

The normalized hydrogenic specification is frozen in
[MATHEMATICAL_MODEL.md](MATHEMATICAL_MODEL.md). It includes:

- reduced mass with the official \(M=A\,u\) approximation;
- CODATA 2022 Bohr, Hartree, electron-mass and atomic-mass constants;
- the \(Z^2/n^2\) energy and \(1/Z\) length laws;
- normalized associated-Laguerre radial functions;
- normalized real tesseral harmonics with explicit orientation;
- unambiguous Cartesian/spherical conversion;
- separate dimensional, scaled and display-relative densities;
- origin and node conventions;
- analytic 1s, 2s and 2p anchors;
- expectation-value, parity, orthogonality and normalization identities; and
- frozen numerical domains and tolerances.

## Independent validation design

The production route and reference route do not reuse the same polynomial
algorithm:

| Quantity | Production | Independent reference |
|---|---|---|
| Associated Laguerre | three-term recurrence | official finite factorial sum |
| Associated Ferrers | vector recurrence | scalar derivative/finite-polynomial route |
| Low states | general \(n,l,m\) formula | closed-form 1s, 2s and 2p expressions |
| Normalization | model evaluation | independent quadrature weights |
| Energy and length | reduced-mass formula | ratio identities and hand anchors |
| Nodes | polynomial roots/sign structure | exact count and analytic low-state locations |

## Frozen numerical anchors

For \(Z=A=1\):

| Quantity | Accepted value |
|---|---:|
| \(\mu/m_e\) | 0.999451720865875 |
| \(a\) | 0.529467506530 Å |
| \(E_1\) | −13.5982334053 eV |
| \(E_3\) | −1.51091482282 eV |
| 2s radial node | \(2a\) |

These reproduce the official \(-13.5982\) eV hydrogen ground-state label at its
displayed precision.

## Architecture decision

[ADR-001](architecture/ADR-001-normalized-hydrogenic-orbitals.md) records why the
core uses local recurrences, normalized real harmonics, quadrature certification
and a renderer-only threshold.

Stage 1 is therefore complete. Stage 2 may implement the deterministic
scientific core against these equations and tolerances.
