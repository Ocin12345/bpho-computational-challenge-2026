# ADR-001: Fixed-Step NumPy Array Architecture

- **Status:** Accepted
- **Date:** 16 July 2026
- **Scope:** Task 2 baseline simulation

## Context

Task 2 needs to simulate approximately 1,000 small particles and one large
tracer for 200 ps. The implementation must be understandable to a Year 12
student, reproducible on a MacBook Air, testable in small pieces, and able to
produce both statistical data and an animation.

The official challenge suggests a fixed-time-step loop. The mathematical
specification also requires a controlled time-step convergence study, so the
numerical resolution must be explicit rather than hidden inside a library.

The model does not need a database, web service, distributed process, or GPU.
Its main architectural risks are:

- mixing configuration, mutable state, and recorded results;
- consuming random numbers in an order that makes runs difficult to reproduce;
- storing every coordinate of every particle at every step; and
- adding collision code before the geometry and data contracts are testable.

## Options considered

| Option | Strengths | Weaknesses | Decision |
| --- | --- | --- | --- |
| One Python object per particle | Visually intuitive and easy to introduce | Repeated Python loops are slower; bulk geometry is harder to inspect and test | Rejected |
| NumPy arrays with a fixed-step loop | Efficient vector operations; compact state; matches the official method; easy convergence tests | Array shapes need strict validation; collision timing remains a finite-step approximation | **Selected** |
| Event-driven hard-disc simulation | Resolves exact collision times between events | Much more complex; periodic direction resets and wall events require a priority queue; unnecessary for the challenge baseline | Rejected |

## Decision

The baseline will use one focused Python implementation module built around
NumPy arrays and a fixed time grid.

### 1. Immutable configuration

**BrownianParameters** owns all physical and numerical inputs. It is frozen
after construction and validates values immediately. Derived quantities such
as the thermal speed, randomization interval, and maximum initial time step are
computed from the configuration, avoiding duplicated constants.

### 2. Explicit fixed time grid

**FixedTimeGrid** stores a constant step size and read-only array of times. An
explicitly requested time step acts as an upper bound. Without one, the builder
uses a measured 40% safety factor below the nominal initial ceiling. It then
slightly reduces the candidate when necessary so that the final point is
exactly the requested maximum time.

This makes the run length deterministic and allows direct comparisons between
the baseline and refined time steps.

### 3. Mutable structure-of-arrays state

**SimulationState** owns contiguous arrays for:

- all small-particle positions;
- all small-particle velocities;
- each particle's next direction-reset time;
- the large-particle position and velocity; and
- the current time and step index.

The state is intentionally mutable because every physics step will update it.
Each array has a validated shape, and copying a state makes independent arrays.

### 4. Independent random streams

A single user-visible seed creates four child streams:

1. initial positions;
2. initial directions;
3. initial reset phases; and
4. future direction resets.

This prevents a change in one initialization procedure from silently shifting
all later random choices. Runs with the same parameters and seed are therefore
reproducible.

### 5. Validated simulation context

**SimulationContext** binds the immutable parameters, time grid, display-frame
schedule, mutable state, future reset stream, and initialization report. It is
the object that each complete simulation step receives.

Initialization places the large particle at the centre and exactly at rest.
Small particles are sampled within radius-aware walls and outside the large
particle. Small-particle overlaps with one another are allowed because the
baseline deliberately omits explicit small-small collisions.

### 6. Memory-aware immutable results

**BrownianSimulationResult** will keep:

- large-particle position and velocity at every physics step; and
- small-particle positions only at selected animation frames; and
- immutable per-step counts and aggregate numerical diagnostics.

The integrated reference run uses 17,706 physics steps after applying the
measured time-step safety factor. A full small-particle position history would
therefore require about 283 MB. Keeping 240 display frames requires about
3.8 MB instead. Result arrays are copied and made read-only so later plotting
cannot accidentally alter the evidence.

Complete steps snapshot both mutable arrays and the future random stream. A
failed transport, collision, convergence, or validation operation restores the
snapshot, preventing a partially advanced trajectory.

## Consequences

### Positive

- The architecture follows the official fixed-step method.
- Configuration errors and malformed arrays fail early.
- Initialization can be verified before any physics update exists.
- NumPy operations should be comfortable on either of the user's computers.
- Statistical histories and animation frames have separate storage policies.
- Random runs can be repeated exactly by recording parameters and seed.

### Costs and limitations

- Fixed-step collision detection is an approximation and can miss a crossing
  if the step is too large.
- NumPy arrays are less visually object-oriented than one object per particle.
- The mutable state must not be mistaken for an immutable result.
- Explicit small-small collisions would require a different performance design
  because testing every pair scales quadratically.

The specification's displacement limit, overlap correction, collision
diagnostics, and time-step convergence experiment mitigate the first risk.

## Revisit triggers

Reconsider this decision only if evidence shows one of the following:

- results fail to converge as the time step is reduced;
- the explicit small-small-collision extension becomes part of the baseline;
- the model grows to roughly 100,000 particles or needs GPU acceleration;
- three-dimensional simulation becomes a requirement; or
- memory measurements show that the selected frame strategy is inadequate.

Until one of those conditions occurs, additional frameworks or architectural
layers would not improve the scientific result.
