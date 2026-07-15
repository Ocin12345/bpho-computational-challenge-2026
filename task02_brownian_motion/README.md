# Task 2: Brownian Motion from Particle Collisions

## Status

Steps 2 and 3 are complete. This document fixes the mathematical model, and the
Python architecture now provides validated parameters, a reproducible initial
state, an exact fixed time grid, and memory-aware result containers.

Motion, wall reflections, direction-reset updates, and particle collisions have
not yet been implemented. They begin in Step 4.

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

An optional later extension may replace direction randomization with explicit
small–small hard-disc collisions. The two modes must remain separate.

## Step 3 software architecture

The architecture is deliberately small: one NumPy-based module, one test
module, and one decision record. This is enough for a transparent scientific
simulation without introducing application frameworks.

| Component | Responsibility |
| --- | --- |
| **BrownianParameters** | Immutable, validated physical and numerical inputs plus derived quantities |
| **FixedTimeGrid** | Read-only, uniformly spaced times that end exactly at $t_{\max}$ |
| **SimulationState** | Mutable current positions, velocities, reset times, time, and step index |
| **SimulationContext** | Parameters, grid, frame schedule, initial state, random stream, and validation report |
| **BrownianSimulationResult** | Read-only large-particle history and sampled small-particle display frames |

Initialization uses four independent random-number streams derived from one
recorded seed: positions, initial directions, initial reset phases, and future
resets. The same parameters and seed therefore reproduce the same state without
coupling unrelated random choices.

The large particle's position and velocity will be retained at every physics
step for analysis. Small-particle positions will be saved only at up to 240
selected display frames. For the reference grid this reduces small-position
storage from about $113\ \mathrm{MB}$ to about $3.8\ \mathrm{MB}$.

Files:

- [architecture and initialization module](brownian_motion.py);
- [architecture tests](test_brownian_motion.py); and
- [ADR-001: fixed-step NumPy array model](architecture/ADR-001-fixed-step-array-model.md).

Run the Task 2 tests from the repository root with:

    python3 -m unittest discover -s task02_brownian_motion -p 'test_*.py' -v

The module intentionally contains no motion or collision update function yet.
That boundary keeps Step 3 testable before Step 4 changes particle state.

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
gives approximately $0.0282\ \mathrm{ps}$. We will begin with the safer value
and monitor the criterion throughout the run.

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

The completed Task 2 package will eventually include:

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

All eight conditions are now satisfied. The next stage is Step 4: implement and
test free motion, reflecting walls, and scheduled direction resets. Small–large
collision impulses remain isolated until Step 5.
