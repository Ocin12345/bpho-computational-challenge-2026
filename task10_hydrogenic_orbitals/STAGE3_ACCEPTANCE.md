# Task 10 Stage 3 Acceptance — Independent Scientific Validation

Status: **PASS**

## Scope

The validator covers all 204 real basis states with \(1\leq n\leq8\), all 36
distinct radial functions and all 64 angular functions through \(l=7\).

## Validation result

All **22/22 scientific checks** pass.

| Check family | Worst accepted error | Tolerance |
|---|---:|---:|
| Laguerre recurrence vs direct factorial sum | \(3.737\times10^{-12}\) | \(5\times10^{-12}\) |
| Ferrers recurrence vs differentiated Legendre form | \(3.015\times10^{-15}\) | \(5\times10^{-13}\) |
| Full radial function vs independent reference | \(2.220\times10^{-16}\) | \(5\times10^{-13}\) |
| Real harmonic vs independent reference | \(2.109\times10^{-15}\) | \(5\times10^{-13}\) |
| Full Cartesian wavefunction vs independent reference | \(5.551\times10^{-17}\) | \(5\times10^{-13}\) |
| Radial normalization | \(7.261\times10^{-14}\) | \(2\times10^{-12}\) |
| Angular normalization and orthogonality | \(2.788\times10^{-14}\) | \(2\times10^{-12}\) |
| Same-\(l\) radial orthogonality | \(6.322\times10^{-13}\) | \(2\times10^{-11}\) |
| Mean radius | \(7.385\times10^{-14}\) relative | \(5\times10^{-11}\) |
| Mean-square radius | \(7.464\times10^{-14}\) relative | \(5\times10^{-11}\) |
| Radial value at independently solved nodes | \(5.577\times10^{-16}\) | \(2\times10^{-12}\) |
| Angular parity | \(7.772\times10^{-16}\) | \(5\times10^{-13}\) |
| Analytic low-state densities | \(1.110\times10^{-16}\) | \(5\times10^{-13}\) |
| Energy scaling | 0 | \(5\times10^{-14}\) |
| Length scaling | \(1.221\times10^{-16}\) relative | \(5\times10^{-14}\) |

Exact gates also confirm:

- 204 supported states;
- 25 unique official gallery states;
- the radial-node count \(n-l-1\) for all 36 radial functions;
- finite non-negative density;
- separation of physical and display-relative density; and
- the official hydrogen energy and radius anchors.

## Corruption evidence

The unit suite now passes 26/26 tests, including deliberate perturbations:

- scaling every radial function by 1.001 is detected by the independent
  reference, normalization and expectation-value gates; and
- scaling every angular function by 0.999 is detected by reference and
  orthogonality gates.

The accepted scientific-state SHA-256 digest is
**d298695290395956560641493fc603e5970a4ea01609eca677b3b4b683fa085e**.

Stage 3 is therefore complete. Data and figures may be generated only from a
matching passing report.
