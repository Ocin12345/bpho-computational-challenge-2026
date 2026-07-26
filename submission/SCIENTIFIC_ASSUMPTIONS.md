# Scientific Assumptions and Judge-Facing Scope

This register gives the shortest defensible answer to four questions for every
task: what was modelled, how it was checked, what the result establishes and
what it deliberately does not claim.

## Task 1 — Two-dimensional random walk

- **Model:** independent fixed-length steps in an unbounded plane, with each
  direction uniformly sampled from $[0,2\pi)$ and no drift or interaction.
- **Validation:** exact step-length and seed-reproducibility tests, isotropy and
  containment checks, and the ensemble law $\langle r^2\rangle=Ns^2$.
- **Result:** the fitted MSD slope is $0.9992\pm0.0031$, consistent with theory.
- **Boundary:** this is a discrete ideal walk, not a model of forces, obstacles,
  correlated steps or a finite physical container.

## Task 2 — Collision-driven Brownian motion

- **Model:** a two-dimensional hard-contact tracer surrounded by small
  particles of one prescribed speed; periodic direction resets represent an
  unresolved thermal bath and small-small collisions are omitted.
- **Validation:** collision identities, walls, penetration and displacement
  bounds, controlled first-order convergence, complete baseline/half-step/
  quarter-step refinement, equal-seed reproducibility and multi-seed ensemble
  statistics.
- **Result:** ensemble MSD is diffusive over the declared fitting interval and
  the mean displacement is statistically consistent with zero drift.
- **Boundary:** the visible mass and radius ratios are pedagogical; the model
  omits a Maxwell speed distribution, fluid drag, hydrodynamics, rotation,
  three-dimensional motion and a quantitatively realistic pollen grain.

## Task 3 — Planck radiation and Einstein heat capacity

- **Model:** an ideal black body with emissivity one and a one-frequency
  Einstein solid containing three independent oscillator directions per atom.
- **Validation:** numerical peaks and integrated exitance are checked against
  Wien's and Stefan--Boltzmann laws; heat capacities are checked against bounds,
  limits and the universal $T/T_E$ curve.
- **Result:** hotter black bodies peak at shorter wavelengths, while a larger
  Einstein temperature delays the rise toward $3R$.
- **Boundary:** the calculation omits emissivity spectra, atmosphere and
  detector response; the Einstein solid omits acoustic-mode dispersion,
  anharmonicity, electronic heat capacity and phase changes.

## Task 4 — Photoelectric effect

- **Model:** Einstein's ideal one-photon equation with one uniform supplied work
  function per metal, vacuum wavelength and a stopping potential balancing the
  maximum photoelectron kinetic energy.
- **Validation:** independent threshold, unit, slope, monotonicity and duplicate-
  curve checks across the full frequency and wavelength grids.
- **Result:** every physical frequency curve has gradient $h/e$ and the work
  function shifts its threshold; intensity does not change maximum energy.
- **Boundary:** the model does not predict photocurrent, energy distributions,
  surface-condition changes, contact potentials, space charge or apparatus
  response. The optional trajectories are explicitly schematic.

## Task 5 — Hydrogen spectrum

- **Model:** ideal stationary-proton, non-relativistic Bohr levels through
  $n=10$, with photon energy equal to the positive atomic energy loss.
- **Validation:** all 45 declared downward transitions are checked through
  independent energy, frequency, wavelength, named-line and series-limit
  identities.
- **Result:** discrete levels produce discrete photon wavelengths, including
  ideal H-alpha at 656.112 nm.
- **Boundary:** reduced mass, selection rules, line strengths and widths, fine
  and hyperfine structure, Lamb, Zeeman and Stark shifts are not modelled.

## Task 6 — Electron diffraction

- **Model:** the official non-relativistic de Broglie wavelength, elastic Bragg
  scattering from ideal graphite plane families and exact screen geometry.
- **Validation:** independent equation and order-domain checks plus the required
  straight-line recovery of 0.123 nm and 0.213 nm spacings.
- **Result:** higher accelerating voltage shortens the wavelength and contracts
  the geometrically allowed diffraction rings.
- **Boundary:** ring brightness and width are schematic. Structure factors,
  crystallite broadening, beam spread, multiple scattering, detector response
  and relativistic corrections are outside the baseline.

## Task 7 — Particle in a one-dimensional box

- **Model:** one non-relativistic electron in a 1.00 nm infinite square well,
  using normalized stationary eigenstates.
- **Validation:** high-precision analytical references and an independent
  finite-difference Hamiltonian verify energies, states, normalization,
  orthogonality, nodes and approximately second-order grid convergence.
- **Result:** the energy scales as $n^2$ and every stationary state satisfies
  $\Delta x\Delta p\geq\hbar/2$.
- **Boundary:** finite barriers, tunnelling, interactions, spin, fields,
  time-dependent superpositions and relativity are not included.

## Task 8 — Quantum mismatch calculator

- **Model:** the two ideal classical and quantum mismatch expressions supplied
  by the task for perfect two-outcome polarisation detectors.
- **Validation:** algebraically independent references, full sweep and grid
  identities, exact anchor cases, cross-language agreement, seeded statistical
  fixtures and offline browser acceptance.
- **Result:** at $-30^\circ,+30^\circ$, the supplied models predict 37.5% and
  75.0% mismatch respectively.
- **Boundary:** this is not a full quantum-key-distribution protocol or a
  security proof; it omits loss, dark counts, decoherence, eavesdropping, key
  sifting, error correction and privacy amplification.

## Task 9 — Compton scattering

- **Model:** exact relativistic kinematics for one photon scattering from one
  initially stationary free electron; Klein--Nishina weighting is a separate
  ideal extension.
- **Validation:** independent scalar references over 3,605 states, energy and
  two-component momentum conservation, the electron mass shell and independent
  quadrature of the extension.
- **Result:** wavelength shift and recoil speed rise with angle and incident
  energy while the electron remains subluminal.
- **Boundary:** atomic binding, attenuation, multiple scattering, polarisation,
  bulk transport, detector resolution and experimental backgrounds are omitted.

## Task 10 — Hydrogenic orbitals

- **Model:** normalized stationary one-electron Coulomb eigenstates with reduced
  nuclear mass and real tesseral harmonics; the displayed quantity is
  $|\psi|^2$, not an electron trajectory.
- **Validation:** independent radial and angular formulations verify
  normalization, orthogonality, analytic anchors, nodes, parity, scaling and all
  25 official S--G gallery states.
- **Result:** the orbital families are normalized three-dimensional probability
  densities; rotating the view changes only the camera.
- **Boundary:** screening, correlation, spin-orbit coupling, fine and hyperfine
  structure, Lamb shifts, finite nuclear size, external fields, ionization,
  measurement and detector response are excluded.

## Cross-project interpretation rule

Passing numerical checks establishes that the implemented equations, declared
domains and generated evidence agree. It does not experimentally validate every
idealisation or turn a schematic visual encoding into a measured observable.
