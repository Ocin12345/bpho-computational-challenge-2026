# Task 2: Brownian Motion from Particle Collisions

## Status

Steps 2 through 10 are complete. The mathematical model, validated architecture,
reproducible initialization, transport physics, collision physics, complete
simulation loop, diagnostics, and memory-aware recording are implemented and
tested. Controlled convergence and full-reference time-step refinement also
pass their declared validation thresholds. The statistical ensembles and
controlled parameter experiments pass all eight pre-declared checks. Their
saved evidence has now been converted into inspected, presentation-ready
static figures and a reproducible animation. A one-slide PowerPoint, embedded
speaker notes, timed scripts, optional supporting images, and a rendered
preview complete the presentation package.

Task 2 is complete and ready to integrate into the final ten-task screencast.

## Official objective

The official Challenge Presentation asks us to consider $N$ small particles
of mass $m$ and radius $r$, moving randomly around one large particle of
mass $M$ and radius $R$. The large particle begins from rest. Its subsequent
motion must be calculated from two-body collisions and should ideally be
animated.

The official example also recommends:

- a fixed-time-step loop for time, position, and velocity;
- picoseconds for time, nanometres for position, and nanometres per picosecond
  for velocity;
- conservation of momentum and a coefficient of restitution for collisions;
- constant-speed small particles whose directions are periodically randomized;
- initially using $C=1$, then reducing $C$ to investigate inelastic
  collisions; and
- ignoring gravity on the short time and length scales of the model.

Source: pages 12–16 of the
[official 2026 Challenge Presentation pack](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip).

## Physical interpretation

The small particles represent unresolved gas molecules. The large particle
represents a visible grain, such as pollen or soot. Although the molecular
motion has no preferred direction, the impacts are not perfectly balanced at
every instant. Their fluctuating impulses make the large particle follow an
irregular path: Brownian motion.

The simulation is therefore a stochastic heat-bath model rather than a complete
molecular-dynamics calculation.

## Baseline model

The baseline implementation will contain:

1. $N$ independent small circular particles;
2. one large circular tracer particle;
3. free motion between instantaneous collisions;
4. exact small–large collision impulses;
5. elastic, radius-aware reflections at the walls of a square container;
6. periodic randomization of each small particle's direction;
7. no explicit small–small collisions; and
8. a large particle that begins exactly at rest in the centre.

Ignoring small–small collisions follows the official example. Their omitted
interactions are represented by the random direction changes. Simulating
small–small collisions while also randomizing directions would count the same
molecular scattering twice.

The implemented extension in
[`small_particle_extension.py`](small_particle_extension.py) replaces direction
randomization with explicit small–small hard-disc collisions. The two modes
remain separate: enabling both would count the same molecular scattering twice.

The extension uses equal-mass normal impulses, symmetric overlap correction and
non-overlapping initialization. Its deterministic website evidence is generated
with `python3 -m task02_brownian_motion.generate_extension_evidence`; focused
tests verify pair momentum, elastic kinetic energy, geometry and the absence of
direction resets in hard-disc mode.

## Step 3 software architecture

The architecture is deliberately small: one NumPy-based implementation module,
focused test modules, and one decision record. This is enough for a transparent
scientific simulation without introducing application frameworks.

| Component | Responsibility |
| --- | --- |
| **BrownianParameters** | Immutable, validated physical and numerical inputs plus derived quantities |
| **FixedTimeGrid** | Read-only, uniformly spaced times that end exactly at $t_{\max}$ |
| **SimulationState** | Mutable current positions, velocities, reset times, time, and step index |
| **SimulationContext** | Parameters, grid, frame schedule, initial state, random stream, and validation report |
| **SimulationDiagnostics** | Read-only per-step event histories and numerical error evidence |
| **BrownianSimulationResult** | Read-only tracer history, sampled display frames, and diagnostics |

Initialization uses four independent random-number streams derived from one
recorded seed: positions, initial directions, initial reset phases, and future
resets. The same parameters and seed therefore reproduce the same state without
coupling unrelated random choices.

The large particle's position and velocity will be retained at every physics
step for analysis. Small-particle positions will be saved only at up to 240
selected display frames. For the reference grid this reduces small-position
storage from about $567\ \mathrm{MB}$ to about $3.8\ \mathrm{MB}$.

Files:

- [simulation implementation](brownian_motion.py);
- [command-line runner](run_task02.py);
- [architecture tests](test_brownian_motion.py);
- [transport tests](test_transport.py);
- [collision tests](test_collisions.py);
- [integrated simulation tests](test_simulation.py); and
- [numerical validation program](validation.py);
- [validation command-line runner](validate_task02.py);
- [saved validation evidence](validation/reference_validation.json); and
- [ensemble-analysis program](analysis.py);
- [analysis command-line runner](analyze_task02.py);
- [saved statistical report](analysis/analysis_report.json); and
- [ADR-001: fixed-step NumPy array model](architecture/ADR-001-fixed-step-array-model.md).

Run the Task 2 tests from the repository root with:

    python3 -m unittest discover -s task02_brownian_motion -p 'test_*.py' -v

Run the complete official-scale baseline with:

    python3 -m task02_brownian_motion.run_task02

For a short terminal check, use:

    python3 -m task02_brownian_motion.run_task02 --particles 100 --time-ps 5

Reproduce the complete Step 7 validation with:

    python3 -m task02_brownian_motion.validate_task02

Reproduce all Step 8 ensembles and statistics with:

    python3 -m task02_brownian_motion.analyze_task02 --workers 4

The architecture, initialization, transport, collision, and integration
contracts were implemented and tested as separate sequential stages before
being combined.

## Variables and units

| Symbol | Meaning | Unit |
| :---: | --- | :---: |
| $N$ | Number of small particles | dimensionless |
| $m$ | Mass of one small particle | kg |
| $r$ | Radius of one small particle | nm |
| $M$ | Mass of the large particle | kg |
| $R$ | Radius of the large particle | nm |
| $L$ | Side length of the square simulation region | nm |
| $T_{\mathrm{gas}}$ | Gas temperature | K |
| $k_{\mathrm B}$ | Boltzmann constant | J K$^{-1}$ |
| $v_s$ | Reference speed of a small particle | nm ps$^{-1}$ |
| $K_n$ | Reduced Knudsen parameter used by the model | dimensionless |
| $\tau_{\mathrm r}$ | Direction-randomization interval | ps |
| $C$ | Coefficient of restitution | dimensionless |
| $\Delta t$ | Physics time step | ps |
| $t_{\max}$ | Total simulation time | ps |
| $\mathbf x_i$ | Position of particle $i$ | nm |
| $\mathbf v_i$ | Velocity of particle $i$ | nm ps$^{-1}$ |

The large-particle position will be written $\mathbf X(t)$, with velocity
$\mathbf V(t)$.

## Reference parameter set

The official MATLAB example provides the following illustrative values:

| Parameter | Reference value |
| --- | ---: |
| $N$ | $1000$ |
| $T_{\mathrm{gas}}$ | $373\ \mathrm K$ ($100^\circ\mathrm C$) |
| $m$ | $28.96\times10^{-3}/(6.02\times10^{23}) = 4.81\times10^{-26}\ \mathrm{kg}$ |
| $M$ | $10m = 4.81\times10^{-25}\ \mathrm{kg}$ |
| $r$ | $0.16\ \mathrm{nm}$ |
| $R$ | $10r = 1.60\ \mathrm{nm}$ |
| $L$ | $7R = 11.2\ \mathrm{nm}$ |
| $K_n$ | $15$ |
| $C$ | $1$ |
| $t_{\max}$ | $200\ \mathrm{ps}$ |

These are pedagogical scaling values, not a claim that the represented large
particle has the true mass and size of a pollen grain. The final defaults may
be adjusted only when numerical stability, collision frequency, and visual
clarity have been measured.

The official sample assigns a thermal speed to the large particle, but the Task
2 wording says that it starts from rest. We will follow the task wording:

$$
\mathbf V(0)=(0,0).
$$

## Thermal speed and random direction changes

Following the official example, the small particles use the three-dimensional
root-mean-square thermal speed

$$
v_s=\sqrt{\frac{3k_{\mathrm B}T_{\mathrm{gas}}}{m}}.
$$

For the reference parameters,

$$
v_s\approx566.57\ \mathrm{m\,s^{-1}}
=0.56657\ \mathrm{nm\,ps^{-1}}.
$$

The conversion is

$$
1\ \mathrm{m\,s^{-1}}=10^{-3}\ \mathrm{nm\,ps^{-1}}.
$$

The characteristic direction-randomization interval is

$$
\tau_{\mathrm r}=\frac{K_n r}{v_s}.
$$

For $K_n=15$,

$$
\tau_{\mathrm r}\approx4.236\ \mathrm{ps}.
$$

Each small particle will have an independent randomization phase so that all
particles do not turn simultaneously. Its first reset time is sampled from

$$
t_{\mathrm r,i}^{(0)}
\sim\mathrm{Uniform}(0,\tau_{\mathrm r}),
$$

and subsequent reset times are separated by $\tau_{\mathrm r}$. When a reset
time is reached, the particle receives a new independent angle

$$
\theta_i\sim\mathrm{Uniform}(0,2\pi)
$$

and its velocity is reset to

$$
\mathbf v_i=v_s(\cos\theta_i,\sin\theta_i).
$$

The reset restores the prescribed molecular speed while representing
unresolved collisions with the surrounding gas. If the pre-reset speed is
already $v_s$, only direction and momentum change. A small–large collision
can alter that speed, however, so a later reset may add or remove kinetic
energy. The randomization mechanism therefore acts as an implicit thermal
reservoir.

The formula uses a three-dimensional thermal speed inside a two-dimensional
visual model because that is the convention supplied in the Challenge
Presentation. A strictly two-dimensional equilibrium gas would instead have
$v_{\mathrm{RMS}}=\sqrt{2k_{\mathrm B}T/m}$; this distinction will be stated
as a limitation.

## Initial conditions

At $t=0$, the large particle is placed in the centre:

$$
\mathbf X(0)=\left(\frac{L}{2},\frac{L}{2}\right),
\qquad
\mathbf V(0)=(0,0).
$$

Each small-particle centre is sampled uniformly inside the radius-aware region

$$
r\leq x_i\leq L-r,
\qquad
r\leq y_i\leq L-r,
$$

subject to

$$
\left\lVert\mathbf x_i-\mathbf X(0)\right\rVert>r+R.
$$

Small particles are independent in the baseline model, so they are permitted
to overlap one another mathematically. We will nevertheless use a visually
reasonable density and avoid initial small–small overlaps when practical.
Strict non-overlap becomes mandatory only in the explicit hard-disc extension.

Initial small-particle directions are independent and uniform:

$$
\theta_i(0)\sim\mathrm{Uniform}(0,2\pi).
$$

A non-negative seed will reproduce the complete initialization and all later
randomizations.

## Free motion

Between collision events, velocity is constant. A fixed physics step updates
each position:

$$
\mathbf x_i(t+\Delta t)
=\mathbf x_i(t)+\mathbf v_i(t)\Delta t,
$$

$$
\mathbf X(t+\Delta t)
=\mathbf X(t)+\mathbf V(t)\Delta t.
$$

The animation frame rate is separate from the physics step. Several physics
steps may occur between displayed frames.

## Reflective boundaries

The official sample draws a square scene but does not treat it as a wall. Our
baseline uses an elastic reflecting container to keep the particle population
and collision rate stable throughout a run. This is a documented modelling
choice, not an official requirement.

For a particle of radius $a_i$, a collision with a vertical wall reverses the
horizontal component:

$$
v_{x,i}\longrightarrow-v_{x,i},
$$

while a horizontal-wall collision reverses the vertical component:

$$
v_{y,i}\longrightarrow-v_{y,i}.
$$

The particle centre is returned to the valid interval

$$
a_i\leq x_i,y_i\leq L-a_i.
$$

Wall reflections conserve the particle's speed. The main reference run should
be chosen so that the large particle rarely reaches a wall; otherwise
confinement would dominate the Brownian trajectory.

## Step 4 transport implementation

Transport is split into four independently testable operations:

1. **randomize_expired_directions** resets only particles whose timers are due,
   restores the prescribed speed, and advances each deadline by exactly
   $\tau_{\mathrm r}$;
2. **advance_free_motion** applies the constant-velocity position equations
   without changing the simulation clock;
3. **reflect_square_walls** folds every coordinate back into its radius-aware
   interval and reverses the required velocity components; and
4. **advance_transport_step** enforces the required reset, motion, wall order
   and commits the exact next time from the fixed grid.

The wall algorithm uses an unfolded coordinate with period
$2(L-2a_i)$. It therefore handles corner impacts, arrival exactly at a wall,
and even multiple wall crossings in one call. Velocity components reverse
according to the parity of the impact count, so speed is conserved.

Before consuming a random number or changing the state, each ordered step
calculates the greatest proposed displacement. If it exceeds $0.10r$, the
operation fails without partially updating positions, timers, the random
stream, time, or step index.

The regression suite includes:

- isolated free-motion equations;
- deterministic reset scheduling and speed restoration;
- exact, corner, radius-specific, and multiple wall impacts;
- transactional failure of an unsafe time step;
- repeated-seed trajectory reproduction; and
- all 35,411 transport steps of the 200 ps reference configuration.

This check deliberately isolates transport. The collision engine also retains
its own independent tests even though Step 6 now combines both operations.

## Two-body collision geometry

Consider particles 1 and 2 with masses $m_1,m_2$, radii $a_1,a_2$,
positions $\mathbf x_1,\mathbf x_2$, and pre-collision velocities
$\mathbf u_1,\mathbf u_2$.

Define the centre displacement, distance, and contact normal:

$$
\mathbf d=\mathbf x_2-\mathbf x_1,
\qquad
d=\lVert\mathbf d\rVert,
\qquad
\widehat{\mathbf n}=\frac{\mathbf d}{d}.
$$

The particles are touching or overlapping when

$$
d\leq a_1+a_2.
$$

Using a normal that points from particle 1 to particle 2, define the relative
normal speed

$$
g=(\mathbf u_2-\mathbf u_1)\mathbin{\cdot}\widehat{\mathbf n}.
$$

The particles are approaching only when

$$
g<0.
$$

No impulse is applied when $g\geq0$, because the particles are already
stationary relative to one another or separating.

## Collision impulse and coefficient of restitution

The coefficient of restitution is defined along the contact normal:

$$
(\mathbf v_2-\mathbf v_1)\mathbin{\cdot}\widehat{\mathbf n}
=-C g,
\qquad
0\leq C\leq1.
$$

The scalar impulse is

$$
J=
\frac{-(1+C)g}
{\dfrac{1}{m_1}+\dfrac{1}{m_2}}.
$$

Because $g<0$, the impulse magnitude $J$ is positive. The post-collision
velocities are

$$
\boxed{
\mathbf v_1
=\mathbf u_1-\frac{J}{m_1}\widehat{\mathbf n}
}
$$

and

$$
\boxed{
\mathbf v_2
=\mathbf u_2+\frac{J}{m_2}\widehat{\mathbf n}.
}
$$

This is the physically correct two-dimensional extension of the
zero-momentum-frame argument in the Challenge Presentation. Only the normal
velocity components change; tangential components remain unchanged for smooth,
frictionless particles.

The centre-of-mass velocity,

$$
\mathbf V_{\mathrm{CM}}
=\frac{m_1\mathbf u_1+m_2\mathbf u_2}{m_1+m_2},
$$

is unchanged by the collision.

## Conservation laws

Every isolated collision must conserve vector momentum:

$$
m_1\mathbf u_1+m_2\mathbf u_2
=m_1\mathbf v_1+m_2\mathbf v_2.
$$

For $C=1$, kinetic energy is also conserved:

$$
\frac12m_1\lVert\mathbf u_1\rVert^2
+\frac12m_2\lVert\mathbf u_2\rVert^2
=
\frac12m_1\lVert\mathbf v_1\rVert^2
+\frac12m_2\lVert\mathbf v_2\rVert^2.
$$

For $C<1$, the kinetic-energy change is

$$
\Delta K
=-\frac12\mu(1-C^2)g^2,
$$

where the reduced mass is

$$
\mu=\frac{m_1m_2}{m_1+m_2}.
$$

Momentum remains conserved while kinetic energy decreases.

Global momentum is not expected to remain constant in the complete baseline
simulation because wall impulses and randomized molecular directions exchange
momentum with the modelled environment. Global kinetic energy can also change
when the thermal reservoir restores a post-collision small particle to
$v_s$, or when $C<1$. Momentum and energy identities are therefore tested
separately for every isolated particle collision.

## Overlap correction

A finite time step can place two particles slightly inside one another before a
collision is detected. Let

$$
\delta=a_1+a_2-d
$$

be the penetration depth. Before applying the impulse, the positions will be
separated along the contact normal:

$$
\mathbf x_1
\longrightarrow
\mathbf x_1-
\frac{m_2}{m_1+m_2}(\delta+\varepsilon)
\widehat{\mathbf n},
$$

$$
\mathbf x_2
\longrightarrow
\mathbf x_2+
\frac{m_1}{m_1+m_2}(\delta+\varepsilon)
\widehat{\mathbf n}.
$$

The more massive particle therefore moves less. The small numerical clearance
$\varepsilon$ prevents immediate re-detection caused by floating-point
rounding. This positional correction changes neither velocity nor momentum.

Exact coincident centres, $d=0$, are forbidden by initialization. The
collision routine will still detect this case and fail clearly rather than
divide by zero.

## Step 5 collision implementation

The function **resolve_small_large_collisions** performs one deterministic
contact pass. It tests only small–large pairs and processes candidate small
particles in ascending index order. Explicit small–small collisions remain
outside the baseline model.

For every touching or overlapping pair, the implementation:

1. constructs the normal from the small particle toward the large particle;
2. records the penetration and pre-collision relative normal speed;
3. applies the mass-weighted positional correction plus a floating-point
   clearance;
4. applies an impulse only when $g<0$;
5. leaves the relative tangential speed unchanged;
6. measures the post-collision restitution residual;
7. measures normalized vector-momentum and analytical energy errors; and
8. records the residual penetration.

The complete pass is transactional. Position and velocity changes are prepared
on copies and committed only after every candidate succeeds. If any pair has
exactly coincident centres, the function raises a clear error without leaving
earlier particles partially changed.

Each event is preserved in an immutable **CollisionEventReport**. A
**CollisionBatchReport** supplies contact counts, applied-impulse counts,
maximum normalized errors, maximum residual penetration, and total measured
kinetic-energy change.

The tests cover:

- exact one-dimensional elastic results;
- oblique impacts and unchanged tangential motion;
- $C=0$, $C=0.5$, $C=0.7$, and $C=1$;
- the reduced-mass inelastic energy-loss identity;
- separating overlaps with correction but no impulse;
- weighted correction and centre-of-mass preservation;
- coincident-centre failure without partial mutation;
- deterministic multiple-contact passes; and
- 2,000 randomized approaching collisions using the official mass scale.

An additional 20,000-collision stress run with the official masses found
maximum normalized errors of $3.76\times10^{-16}$ for momentum,
$5.01\times10^{-14}$ for restitution, and $8.73\times10^{-16}$ for the energy
identity. All are below the declared $10^{-12}$ threshold, and no residual
penetration remained.

## Time-step requirement

A fixed-step collision method can miss a collision if a particle crosses too
far in one update. The physics step must satisfy

$$
v_{\max}\Delta t
\leq\eta r,
\qquad
\eta=0.10,
$$

and

$$
\Delta t\leq0.01\tau_{\mathrm r}.
$$

The initial choice will therefore be

$$
\boxed{
\Delta t=
\min\left(
0.01\tau_{\mathrm r},
\frac{0.10r}{v_{\max}}
\right).
}
$$

For the official reference parameters,
$0.01\tau_{\mathrm r}=0.0424\ \mathrm{ps}$, while the displacement condition
gives a nominal ceiling of approximately $0.0282\ \mathrm{ps}$.

Integrated tests showed that using this ceiling directly left no margin after
collisions accelerated some particles. The automatic baseline therefore uses
20% of the nominal ceiling. Its actual fixed step is
$0.005647962\ \mathrm{ps}$, giving 35,411 steps over 200 ps. The physical
acceptance limit remains $0.10r=0.016\ \mathrm{nm}$ per step.

A user may explicitly request any initial step up to the nominal ceiling, but
the runtime still rejects the run transactionally if later dynamics exceed the
displacement limit.

The physics time step remains fixed during one simulation. If the criterion is
violated, that run fails validation and must be repeated with a smaller step.

## Simulation sequence

For each fixed physics step:

1. randomize any small-particle directions whose independent timers have
   expired;
2. advance all positions by $\Delta t$;
3. resolve radius-aware wall crossings;
4. test each small particle against the large particle;
5. correct overlaps and apply impulses only to approaching pairs;
6. re-apply wall limits and repeat the collision pass if simultaneous contacts
   remain unresolved;
7. record the large particle's position, velocity, and diagnostics; and
8. render an animation frame only when the display schedule requests one.

Testing only small–large pairs makes the baseline collision search
$O(N)$ per time step. An explicit small–small extension would require a
spatial grid or another neighbour-search method rather than an unoptimized
$O(N^2)$ loop.

## Step 6 integrated simulation engine

**advance_simulation_step** combines one complete physics step:

1. snapshot the mutable state and future random stream;
2. perform scheduled resets, free motion, and initial wall reflections;
3. detect and resolve all current small–large contacts;
4. re-apply radius-aware wall reflections after positional correction;
5. repeat contact passes until no contact remains;
6. enforce momentum, restitution, energy, penetration, and displacement
   tolerances;
7. commit the exact fixed-grid time; and
8. restore the snapshot and random stream if any operation fails.

The measured reference configuration required at most 11 contact passes in one
step. The validated ceiling is 16, which provides margin while still detecting
a failure to converge.

**run_simulation** executes the complete grid and records:

- tracer position and velocity at every physics step;
- small-particle positions only at selected display frames;
- resets, wall impacts, contacts, impulses, and collision passes per step;
- maximum displacement and residual penetration;
- maximum normalized momentum, restitution, and energy-identity errors; and
- total kinetic-energy change caused specifically by collision impulses.

For the seed-2026 reference run with $N=1000$, $C=1$, and
$t_{\max}=200\ \mathrm{ps}$, the verified engine completed:

| Quantity | Measured result |
| --- | ---: |
| Fixed physics steps | 35,411 |
| Direction resets | 47,201 |
| Small-particle wall impacts | 14,447 |
| Large-particle wall impacts | 0 |
| Small–large contacts | 4,307 |
| Applied impulses | 3,721 |
| Maximum contact passes in one step | 10 |
| Maximum one-step displacement | $0.006351287\ \mathrm{nm}$ |
| Allowed one-step displacement | $0.016000000\ \mathrm{nm}$ |
| Maximum normalized momentum error | $3.97\times10^{-16}$ |
| Maximum normalized restitution error | $1.06\times10^{-15}$ |
| Maximum normalized energy-identity error | $1.74\times10^{-15}$ |
| Maximum residual penetration | $0\ \mathrm{nm}$ |
| Final tracer displacement in this one run | $0.644497452\ \mathrm{nm}$ |

The single final displacement is a reproducibility check, not a statistical
conclusion. Step 8 uses ensembles rather than interpreting one trajectory.

## Step 7 numerical validation

The independent validation program separates exact deterministic convergence
from chaotic many-particle behaviour.

### Controlled collision convergence

A single analytical head-on collision was repeated over 61 different collision
phases. This avoids accidentally making a coarse grid appear exact merely
because contact happens to fall on one of its time points.

| Steps over 2 ps | $\Delta t$ (ps) | RMS endpoint error (nm) | Observed order |
| ---: | ---: | ---: | ---: |
| 16 | 0.125000 | 0.0567865 | — |
| 32 | 0.062500 | 0.0281803 | 1.01086 |
| 64 | 0.031250 | 0.0140628 | 1.00280 |
| 128 | 0.015625 | 0.00701846 | 1.00266 |

Every halving reduces the RMS error by approximately two, demonstrating the
expected first-order convergence of finite-step collision detection and
overlap correction.

### Complete reference refinement

The full seed-2026, 1,000-particle, 200 ps simulation was then run at the
baseline, half step, and quarter step:

| Refinement | Steps | Contacts | Impulses | Max step distance (nm) | RMS path difference from previous (nm) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| $1$ | 35,411 | 4,307 | 3,721 | 0.00635129 | — |
| $2$ | 70,822 | 3,982 | 3,725 | 0.00307115 | 1.55259 |
| $4$ | 141,644 | 3,960 | 3,789 | 0.00160640 | 0.787715 |

The individual trajectories do not converge point by point. That is expected:
small changes in collision timing alter later collision order and thermal-bath
directions, so a Brownian trajectory is chaotic. Claiming otherwise would be a
misleading validation criterion.

The number of physically applied impulses is stable, however:
$3721,3725,3789$, a relative span of $1.816\%$. Separating contact
corrections decrease with refinement because shallower overlaps need fewer
positional adjustments.

All three complete runs also pass:

- finite coordinates and radius-aware wall geometry;
- no overlap in any recorded frame;
- the $0.016\ \mathrm{nm}$ displacement limit;
- normalized momentum, restitution, and energy errors below $10^{-12}$;
- residual penetration below $10^{-9}(r+R)$;
- contact convergence within 16 passes; and
- exact equal-seed reproduction of every recorded output.

The saved evidence is available as:

- [complete validation report](validation/reference_validation.json);
- [controlled convergence data](validation/controlled_collision_convergence.csv);
  and
- [reference refinement data](validation/reference_time_step_refinement.csv).

Step 8 therefore compares ensemble means, confidence intervals, MSD, and
effective diffusion estimates rather than individual chaotic paths.

## Step 8 ensemble statistics and parameter experiments

The final design uses:

- 64 baseline seeds, 3000–3063;
- the same 64 seeds at half the baseline time step;
- the first 12 seeds at every parameter-comparison level;
- the fixed MSD fitting window $20\leq t\leq100\ \mathrm{ps}$;
- 2,000 fixed-seed bootstrap resamples for diffusion intervals; and
- one factor changed at a time.

An initial 32-run baseline and 16-run time-step comparison was too noisy to
pass the unchanged linearity and time-step criteria. The fitting window and
thresholds were not altered. Instead, the model's automatic step was promoted
to the previously tested half step, the two main ensembles were expanded to 64
runs, and every simulation was regenerated. This decision and both failed
diagnostics were reported during development rather than hidden.

### Baseline statistical checks

All final checks pass:

| Check | Measured result | Criterion |
| --- | --- | --- |
| Mean horizontal displacement | $-0.2055\ \mathrm{nm}$; 95% CI $[-0.4321,0.0211]$ | CI contains zero |
| Mean vertical displacement | $0.0912\ \mathrm{nm}$; 95% CI $[-0.1342,0.3167]$ | CI contains zero |
| Horizontal–vertical spread difference | $0.0417\ \mathrm{nm^2}$; 95% CI $[-0.3530,0.4364]$ | CI contains zero |
| Effective diffusion coefficient | $2.2524\times10^{-3}\ \mathrm{nm^2\,ps^{-1}}$ | Bootstrap lower limit positive |
| Diffusion 95% bootstrap CI | $[1.5593,3.0096]\times10^{-3}\ \mathrm{nm^2\,ps^{-1}}$ | Positive |
| MSD linearity over 20–100 ps | $R^2=0.983239$ | $R^2\geq0.90$ |
| Baseline versus half-step $D$ | Relative difference $5.679\%$; intervals overlap | Difference below 25% |
| Independent 32-seed halves | Both $D>0$; intervals overlap | Same conclusion |
| Numerical validity | 224 of 224 unique runs pass | No omitted run |

The zero-containing mean intervals and paired spread interval support the
expected absence of directional bias. The positive approximately linear MSD
supports an intermediate diffusive regime in this model.

### Controlled parameter results

The comparison ensembles use the same 12 seeds at every level:

| Experiment | Level | $D$ ($\mathrm{nm^2\,ps^{-1}}$) | Bootstrap 95% CI | Mean impulses per ps |
| --- | ---: | ---: | ---: | ---: |
| Particle count | 250 | 0.019157 | [0.011238, 0.027471] | 4.756 |
| Particle count | 500 | 0.003257 | [0.000863, 0.006309] | 9.556 |
| Particle count | 1000 | 0.001872 | [0.000520, 0.003668] | 19.015 |
| Mass ratio $M/m$ | 5 | 0.001369 | [0.000611, 0.002132] | 20.210 |
| Mass ratio $M/m$ | 10 | 0.001872 | [0.000520, 0.003668] | 19.015 |
| Mass ratio $M/m$ | 20 | 0.001793 | [0.000569, 0.003169] | 18.685 |
| Restitution $C$ | 0.5 | 0.001912 | [0.000547, 0.003487] | 21.194 |
| Restitution $C$ | 0.8 | 0.001968 | [0.000599, 0.003564] | 19.659 |
| Restitution $C$ | 1.0 | 0.001872 | [0.000520, 0.003668] | 19.015 |
| Knudsen parameter | 7.5 | 0.001578 | [0.000210, 0.003416] | 18.593 |
| Knudsen parameter | 15 | 0.001872 | [0.000520, 0.003668] | 19.015 |
| Knudsen parameter | 30 | 0.001553 | [0.000907, 0.002325] | 18.870 |

Increasing $N$ raises the collision rate but strongly reduces the fitted tracer
diffusion in this finite model. The numerous impacts more frequently oppose
one another, while sparse cases permit longer unbalanced tracer excursions.
This is a result of the simplified scaling model, not a universal claim about
changing the real molecular density.

The mass-ratio, restitution, and Knudsen confidence intervals overlap broadly,
so these 12-run comparisons do not establish clear monotonic effects. Their
measured values are retained rather than over-interpreted.

Machine-readable evidence:

- [complete analysis report](analysis/analysis_report.json);
- [ensemble summaries](analysis/ensemble_summary.csv);
- [parameter comparisons](analysis/experiment_comparisons.csv);
- [baseline MSD and confidence bands](analysis/baseline_msd.csv); and
- [all 224 run-level metrics](analysis/run_metrics.csv).

## Step 9 scientific figures and animation

The final visuals are generated by code rather than edited by hand. Statistical
panels read the committed Step 8 CSV and JSON files directly, while validation
panels read the committed Step 7 CSV files. Those ensembles are not rerun or
selectively filtered during figure generation. Only the reproducible seed-2026
reference simulation is executed again to obtain the particle scene and GIF.

Run the complete visual pipeline from the repository root with:

    python3 -m task02_brownian_motion.create_task02_visuals

The command writes four static figures in both 300 dpi PNG and editable SVG
form, plus one 180-frame GIF:

| Asset | Evidence shown | Intended use |
| --- | --- | --- |
| [reference particle scene](figures/reference_particle_scene.png) | Final small-particle positions, the scale-correct tracer, and its complete centre trail | Physical model and reference result |
| [baseline statistics](figures/baseline_statistics.png) | 64-run MSD, fixed 20–100 ps fit, confidence band, and endpoint cloud | Main evidence for unbiased diffusion |
| [parameter experiments](figures/parameter_experiments.png) | Four one-factor comparisons with bootstrap intervals and marked baselines | Results and limitations |
| [numerical validation](figures/numerical_validation.png) | Controlled first-order convergence and full reference refinement | Numerical credibility |
| [reference animation](figures/reference_animation.gif) | Fixed-axis molecular motion, tracer motion, and accumulated trail over 200 ps | Presentation playback |

The SVG counterpart of every static PNG is stored in the same directory. The
[visual manifest](figures/visual_manifest.json) records the source, caption,
reference settings, resolution, frame count, and frame rate for the package.

The graphics use a colour-vision-accessible palette, fixed physical axes, SI-
derived units, and explicit confidence intervals. The tracer is translucent
and its centre path is drawn above it because the reference radius is larger
than the tracer's displacement; hiding that path behind an opaque final disc
would obscure the Brownian motion. Start, midpoint, and final animation frames
were visually inspected after generation.

## Step 10 presentation package

The final [Task 2 PowerPoint pack](../presentation/task02/README.md) converts the
scientific evidence into one editable 16:9 slide for the three-minute
competition screencast. It uses the reference GIF as the model visual and the
64-run MSD/endpoints figure as the main evidence. Three visible result lines
report absence of significant drift, the fitted diffusion result, and the
time-step/statistical validation without crowding the slide.

The pack includes:

- an editable PowerPoint with the GIF and final narration embedded;
- a high-resolution rendered preview;
- a 17–18-second competition script with timed visual cues;
- expanded and rehearsal scripts for understanding;
- pronunciation guidance and likely-question answers;
- a static scene fallback and optional parameter/validation figures; and
- a pinned generator that rebuilds the deck from the Step 9 assets.

The PowerPoint package was structurally checked, its embedded GIF and speaker
notes were verified inside the file, and the slide was rendered through
LibreOffice for visual inspection. The PDF preview is necessarily static, but
the PowerPoint media relationship retains the original 180-frame GIF.

## Theoretical statistical behaviour

The system has no preferred direction. Across many independent simulations,
the large-particle displacement should therefore satisfy

$$
\left\langle X(t)-X(0)\right\rangle\approx0,
\qquad
\left\langle Y(t)-Y(0)\right\rangle\approx0.
$$

After the initial inertial regime and before wall confinement dominates,
ordinary two-dimensional diffusion predicts

$$
\left\langle
\left\lVert\mathbf X(t)-\mathbf X(0)\right\rVert^2
\right\rangle
\approx4Dt,
$$

where $D$ is the effective diffusion coefficient of this model.

The simulation may show three regimes:

1. a short ballistic transient, where inertia is important;
2. an intermediate diffusive region, where MSD is approximately linear in
   time; and
3. a late confined region, where reflecting walls cause the MSD to flatten.

The diffusion law will be tested only over a pre-declared intermediate window,
not selected afterward to make the graph appear linear.

## Numerical success criteria

The implementation must pass all of the following deterministic checks:

1. all parameters are finite and physically valid;
2. the large particle begins at the centre with zero velocity;
3. every initial small particle lies within the domain and outside the large
   particle;
4. equal seeds reproduce identical complete trajectories;
5. no coordinate or velocity becomes NaN or infinite;
6. every particle centre remains inside its radius-aware wall limits;
7. collision impulses are applied only to approaching pairs;
8. post-collision relative normal speed satisfies the restitution equation;
9. normalized momentum error per collision is below $10^{-12}$;
10. relative kinetic-energy error for $C=1$ is below $10^{-12}$;
11. measured energy loss for $C<1$ agrees with the analytical expression;
12. residual penetration after overlap correction is below
    $10^{-9}(r+R)$; and
13. the maximum distance travelled in one physics step never exceeds
    $0.10r$.

The statistical analysis must then demonstrate that:

1. 95% confidence intervals for mean horizontal and vertical displacement
   include zero;
2. horizontal and vertical spreading are statistically consistent;
3. the large-particle MSD has a positive approximately linear intermediate
   region;
4. the fitted diffusion result is stable when the time step is halved; and
5. conclusions are reproduced with independent random seeds.

## Planned parameter experiments

After validating the reference run, controlled experiments will vary one
quantity at a time:

| Experiment | Values to compare | Question |
| --- | --- | --- |
| Particle count | several values of $N$ | Do more molecules increase the collision rate and diffusion? |
| Mass ratio | several values of $M/m$ | Does a heavier tracer respond less strongly? |
| Restitution | $C=1,0.8,0.5$ | How does inelasticity change energy and motion? |
| Randomization scale | several $K_n$ values | How does directional persistence affect diffusion? |
| Time-step convergence | $\Delta t,\Delta t/2,\Delta t/4$ | Are results independent of numerical resolution? |

Exact experimental values and ensemble sizes will be chosen before running the
analysis and recorded with the results.

## Required outputs

Steps 2 through 10 provide:

- a tested Python simulation engine;
- a polished animation of the small particles and large tracer;
- a trail of the large particle from its starting position;
- collision, momentum, energy, and time-step diagnostics;
- ensemble mean-displacement and MSD plots;
- parameter-comparison figures;
- reproducible CSV results;
- a scientific discussion of assumptions and limitations; and
- a one-slide PowerPoint pack with timed narration.

## Model limitations

The baseline deliberately simplifies real Brownian motion:

- it is two-dimensional;
- small particles use one prescribed speed rather than a full Maxwell speed
  distribution;
- direction resets replace explicit molecular collisions;
- particle interactions are instantaneous hard-contact impulses;
- the reference mass and radius ratios are chosen for visible computational
  behaviour rather than complete physical realism;
- the reflecting container introduces confinement; and
- there is no fluid drag, hydrodynamic interaction, rotation, gravity, or
  three-dimensional motion.

These are declared modelling choices. Conclusions will be limited to this
simulation rather than presented as exact predictions for a real pollen grain.

## Step 2 completion condition

Step 2 is complete when this document:

1. matches the official Task 2 wording;
2. defines every variable, unit, assumption, and initial condition;
3. provides a sign-consistent two-dimensional collision rule;
4. states deterministic and statistical pass criteria;
5. separates the baseline randomization model from the optional explicit
   small–small collision extension; and
6. renders correctly on GitHub.

These six conditions are satisfied by the current specification.

## Step 3 completion condition

Step 3 is complete when the software:

1. validates every physical and numerical input;
2. derives the reference speed, reset interval, and safe initial time step;
3. creates a fixed time grid ending exactly at $t_{\max}$;
4. initializes valid particle geometry and velocities reproducibly;
5. separates immutable configuration, mutable state, and immutable results;
6. stores animation data without retaining an unnecessary full particle
   history;
7. documents the architectural trade-offs; and
8. passes all architecture tests without implementing later physics early.

All eight conditions are satisfied.

## Step 4 completion condition

Step 4 is complete when:

1. expired direction timers reset before movement;
2. reset angles are independent and reproducible from the recorded seed;
3. resets restore the prescribed molecular speed and advance by one exact
   interval;
4. constant-velocity position updates match the analytical equation;
5. small and large particles use their own radii at every wall;
6. wall reflections conserve speed and handle corners and repeated crossings;
7. state time advances only to exact fixed-grid values;
8. unsafe displacement is rejected before any partial mutation;
9. complete repeated transport remains finite and within the container; and
10. the official 200 ps reference transport passes all 35,411 steps.

All ten conditions are satisfied by the implementation and regression tests.

## Step 5 completion condition

Step 5 is complete when:

1. only touching or overlapping small–large pairs are selected;
2. the contact normal and approaching condition use the documented sign
   convention;
3. separating contacts receive no impulse;
4. overlap correction is mass weighted and leaves negligible penetration;
5. coincident centres fail without partial state mutation;
6. normal restitution is satisfied for every $0\leq C\leq1$;
7. tangential relative motion is unchanged;
8. vector momentum is conserved to normalized error below $10^{-12}$;
9. elastic energy is conserved to normalized error below $10^{-12}$;
10. inelastic energy loss matches the reduced-mass identity below
    $10^{-12}$; and
11. official-scale randomized stress tests pass all numerical limits.

All eleven conditions are satisfied.

## Step 6 completion condition

Step 6 is complete when:

1. one public operation executes the approved reset-motion-wall-collision
   order;
2. post-collision wall correction and repeated contact passes converge;
3. every complete step rolls back state and random numbers on failure;
4. the automatic baseline has measured margin below the displacement limit;
5. complete runs record exact fixed-grid tracer histories;
6. display frames include the initial and final small-particle states;
7. per-step counts and aggregate numerical errors are immutable;
8. equal seeds reproduce every recorded trajectory and diagnostic history;
9. the full 1,000-particle, 200 ps reference run passes all runtime limits; and
10. a command-line entry point runs on either computer.

All ten conditions are satisfied.

## Step 7 completion condition

Step 7 is complete when:

1. a controlled collision study averages over different grid phases;
2. RMS endpoint error decreases at every time-step halving;
3. observed convergence order is at least $0.9$;
4. baseline, half-step, and quarter-step reference runs all complete;
5. every refined run passes geometry and numerical-identity limits;
6. the automatic baseline retains measured displacement margin;
7. refined applied-impulse counts have relative span below $2\%$;
8. equal seeds reproduce all recorded outputs exactly;
9. chaotic pointwise path divergence is reported rather than hidden; and
10. machine-readable JSON and CSV evidence can be regenerated by one command.

All ten conditions are satisfied.

## Step 8 completion condition

Step 8 is complete when:

1. seed sets, fit window, bootstrap count, and parameter levels are fixed;
2. mean horizontal and vertical 95% intervals include zero;
3. the paired horizontal–vertical spread interval includes zero;
4. the diffusion confidence interval is positive;
5. intermediate-window MSD has $R^2\geq0.90$;
6. baseline and half-step $D$ differ by less than 25% with overlapping
   intervals;
7. independent seed halves reproduce a positive overlapping $D$ conclusion;
8. particle count, mass ratio, restitution, and Knudsen level are varied one at
   a time;
9. every ensemble run passes the deterministic numerical limits;
10. failed preliminary statistical checks and the sample-size response are
    reported transparently; and
11. JSON and CSV outputs can be regenerated through one cached command.

All eleven conditions are satisfied.

## Step 9 completion condition

Step 9 is complete when:

1. statistical figures are generated directly from committed Step 8 evidence;
2. validation figures are generated directly from committed Step 7 evidence;
3. no ensemble run is silently rerun, removed, or selected during plotting;
4. the reference scene uses the exact particle and container dimensions;
5. the complete tracer trail remains visible despite the large tracer radius;
6. the animation uses fixed axes and includes the initial and final states;
7. every static figure is available as 300 dpi PNG and editable SVG;
8. captions and generation settings are recorded in a JSON manifest;
9. focused tests verify figure saving and GIF frame count;
10. the start, midpoint, and final animation frames are visually inspected; and
11. one command regenerates the complete visual package.

All eleven conditions are satisfied.

## Step 10 completion condition

Step 10 is complete when:

1. one 16:9 slide presents a single clear scientific claim;
2. the reference animation and strongest ensemble evidence remain readable;
3. visible slide text is limited to three result lines;
4. the competition narration fits approximately 17–18 seconds;
5. speaker notes contain the exact final script and timed visual cues;
6. expanded rehearsal material explains the model and limitations accurately;
7. image alternative text and a static animation fallback are supplied;
8. the PowerPoint is editable and can be rebuilt from pinned dependencies;
9. the embedded GIF and notes are verified inside the PowerPoint package;
10. a high-resolution render is visually inspected for clipping and scale; and
11. the full Task 2 report remains linked for supporting detail.

All eleven conditions are satisfied. Task 2 is complete.
