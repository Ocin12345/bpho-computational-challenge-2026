# Task 10 Stage 9 Acceptance — Results and Reproducibility

Status: **PASS**

## Delivered documents

- `README.md` — official objective, equations, explorer instructions, central
  results, evidence inventory, validation strategy and scope.
- `RESULTS_AND_INTERPRETATION.md` — complete S–G family table, normalized model,
  energy/length anchors, nodes, degeneracy, charge scaling, renderer reading
  guide and physical limitations.
- `REPRODUCIBILITY.md` — accepted environment, deterministic build order,
  independent and browser validation, output inventory, integrity details and
  manual application anchors.
- `requirements-task10.txt` — exact accepted NumPy, Matplotlib and Pillow
  versions.
- `documentation_validation.py` and `validate_task10_documentation.py` —
  deterministic library and command-line documentation acceptance.

## Acceptance evidence

| Check | Result |
|---|---:|
| Required documents | 4/4 present |
| Documentation integrity groups | 13/13 passed |
| Local documentation/evidence links | 44/44 resolve |
| Official S–G gallery and 25-state count | complete |
| Normalization and coordinate equations | complete |
| Hydrogen, 3d, carbon and analytic anchors | complete |
| Nodes, degeneracy and \(Z\)-scaling | complete |
| Threshold, isosurface and motion caveats | explicit |
| One-electron scope and exclusions | explicit |
| Data, figure, motion and browser commands | complete |
| 4K motion and fallback inventory | complete |
| Python dependency pins | exact |
| Documentation corruption tests | 4/4 passed |

The corruption suite confirms that a missing local evidence link, removal of the
“not electron motion” interpretation or removal of the one-electron point-Coulomb
scope causes acceptance to fail.

## Reproduce

```bash
python3 -m task10_hydrogenic_orbitals.validate_task10_documentation
python3 -m unittest task10_hydrogenic_orbitals.test_documentation_validation
```

Stage 9 is complete. Stage 10 may now build the single-slide competition deck
from the accepted 4K summary and frozen narration.
