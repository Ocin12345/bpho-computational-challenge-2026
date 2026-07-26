# ADR-001: Static Browser Calculator with a Python Reference Model

## Status

Accepted

## Context

Task 8 requires a visual calculator whose two detector angles can be varied
interactively. The result must be clear in a short screencast, work on the
project computers and retain the repository's existing standard of tested,
reproducible scientific evidence.

This is a small, single-user educational application. It has two numerical
inputs, no persistent user data, no authentication, no database, no external
integration and no independent scaling requirement. Updates should feel
immediate, but no multi-user real-time synchronization is needed.

## Options considered

| Option | Advantages | Limitations | Complexity |
| --- | --- | --- | --- |
| Spreadsheet | Explicitly allowed and quick to construct | Weaker visual control and less suitable for a polished screencast | Low |
| Tkinter desktop GUI | Python-only calculation path and works offline | Platform-dependent appearance and harder responsive layout | Medium |
| Streamlit app | Fast Python development and convenient widgets | Adds a framework/runtime and server lifecycle for two equations | Medium |
| Static browser app plus Python reference | Polished interaction, portable, offline-capable and independently testable | Formula exists in both Python and JavaScript | Low |

## Decision

Build a small static browser application using semantic HTML, CSS and plain
JavaScript, served locally by a minimal static file server. Keep the browser
calculation in a pure JavaScript module so it can be tested without the visual
layer. Implement the same stated physics independently in Python as the
authoritative evidence-generation and validation path.

Use a modular-monolith layout rather than a framework, backend API, database or
distributed architecture:

```text
task08_quantum_cryptography/
  app/                 Static calculator interface
  architecture/        Accepted design decisions
  configuration.py     Frozen scientific and output conventions
  constants.py         Mathematical and official reference constants
  models.py            Python reference model (Stage 2)
  validation.py        Scientific validation (Stage 3)
```

Generated evidence will remain in the repository's existing top-level
`data/task08`, `figures/task08` and `presentation/task08` locations.

## Rationale

1. A browser gives the clearest slider-driven demonstration and responsive
   visual layout for the screencast.
2. The app can run locally without accounts, network calls or proprietary
   software.
3. Plain browser technologies avoid a build framework for a calculation with
   only two inputs and a few derived values.
4. The separate Python implementation prevents the displayed JavaScript result
   from being its own only source of validation.
5. Shared reference fixtures will expose cross-language drift.

## Trade-offs

- The formulas are implemented twice. This is accepted to obtain an
  independently checked browser experience; dense-grid fixtures and official
  anchor cases will compare the two implementations.
- ES modules generally need a local HTTP server rather than direct `file://`
  opening. A documented one-command launcher will mitigate this.
- Gesture controls are not included in the baseline because accessible sliders
  and numeric inputs already satisfy the brief more reliably.
- A complete quantum-key-distribution protocol is deferred because it is beyond
  the official mismatch-calculator requirement.

## Consequences

- The scientific model, user interface and generated evidence have explicit
  boundaries while remaining in one small repository module.
- The app must have no external runtime requests and must remain usable offline.
- Browser integration tests and visual inspection are required in addition to
  Python unit tests.
- Every displayed result must identify its angle convention and probability
  scale.

## Revisit trigger

Reconsider this decision only if the competition requires deployment to a
public URL, mandates gesture controls, or expands Task 8 into a multi-step
quantum-key-distribution simulation.
