# Task 2 Full Time-Step Convergence Closeout

Closeout date: 22 July 2026

The full official-scale Task 2 validation was rerun from the repository root:

```bash
python3 -m task02_brownian_motion.validate_task02
```

The run completed successfully and atomically refreshed:

- `task02_brownian_motion/validation/reference_validation.json`;
- `task02_brownian_motion/validation/controlled_collision_convergence.csv`; and
- `task02_brownian_motion/validation/reference_time_step_refinement.csv`.

## Controlled collision convergence

| Steps | $\Delta t$ / ps | RMS endpoint error / nm | Observed order |
| ---: | ---: | ---: | ---: |
| 16 | 0.125000 | $5.678655\times10^{-2}$ | — |
| 32 | 0.062500 | $2.818027\times10^{-2}$ | 1.010864 |
| 64 | 0.031250 | $1.406282\times10^{-2}$ | 1.002799 |
| 128 | 0.015625 | $7.018461\times10^{-3}$ | 1.002660 |

The RMS error decreases at every halving and the minimum measured order is
1.002660, satisfying the declared first-order threshold of 0.9.

## Complete reference refinement

| Refinement | Steps | $\Delta t$ / ps | Applied impulses | Maximum one-step displacement / nm |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 35,411 | 0.0056479625 | 3,721 | 0.0063512873 |
| 2 | 70,822 | 0.0028239812 | 3,725 | 0.0030711493 |
| 4 | 141,644 | 0.0014119906 | 3,789 | 0.0016063988 |

The applied-impulse relative span is 1.816%, below the declared 2% threshold.
The maximum normalized collision-identity error is
$2.169041\times10^{-15}$, residual penetration is zero, the collision solver
uses at most 10 of its 16 allowed passes and repeated equal-seed compact runs
match bit for bit.

## Final decision

All 9/9 full-refinement checks pass. The previously documented release caveat
that this expensive study had not been rerun during presentation polishing is
therefore closed. Chaotic pointwise paths are still not expected to coincide
under refinement; the accepted physical comparisons are convergence in the
controlled collision, valid geometry and identities, reduced step distance and
stable event statistics.
