# ADR-001: deterministic relativistic Compton core

Status: accepted for Stage 2

## Context

Task 9 requires three smooth angle-dependent curves at five photon energies. The
500 and 1000 keV cases are relativistic, and the forward endpoint has an undefined
electron direction despite a finite plotted angular limit. A compact plotting
script alone would make it difficult to prove that these details are correct.

## Decision

Use a pure, vectorised Python core with:

- exact SI defining constants and the frozen 2022 CODATA electron mass;
- an immutable validated configuration;
- a wavelength-first production path following the official equations;
- a separate scalar energy–momentum reference path;
- read-only broadcast arrays for scalar, vector and energy-by-angle studies;
- a direction-validity flag independent of the recoil-angle plotting value; and
- explicit intermediate state variables so energy, momentum and mass-shell
  conservation can be audited point by point.

## Consequences

The official curves remain inexpensive to generate, but every plotted point has a
complete physical state and an independent validation route. The later browser
implementation can be tested against frozen data rather than becoming a second
unverified calculator.

The cost is a larger data model than the three visible outputs alone require. This
is accepted because the intermediate quantities make relativistic correctness and
endpoint handling observable.
