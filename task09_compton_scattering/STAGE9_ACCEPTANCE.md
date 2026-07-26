# Stage 9 acceptance — technical and user documentation

## Outcome

Stage 9 is accepted. Task 9 now has a complete user, scientific and reproducibility handoff with automated integrity checks.

## Delivered documents

- `README.md` — objective, equations, explorer instructions, principal results, evidence inventory, validation strategy and scope.
- `RESULTS_AND_INTERPRETATION.md` — full derivation, 90° and backscatter tables, curve interpretation, conservation analysis, extension reading and limitations.
- `REPRODUCIBILITY.md` — pinned environment, generation order, independent validation, browser setup, output inventory, determinism and manual anchor check.
- `requirements-task09.txt` — exact accepted NumPy, Matplotlib and Pillow versions.
- `documentation_validation.py` and `validate_task09_documentation.py` — machine-readable and command-line documentation acceptance.

## Acceptance evidence

| Check | Result |
|---|---:|
| Required documents present | 4/4 |
| Documentation integrity groups | 11/11 passed |
| Local documentation and evidence links | all resolve |
| Official energies and requested quantities | complete |
| Core equations and endpoint disclosures | complete |
| Numerical result anchors | complete |
| Extension separation and scope boundaries | explicit |
| Reproduction commands and evidence inventory | complete |
| Pinned Python versions | exact |
| Documentation corruption tests | pass |

## Reproduce

```bash
python3 -m task09_compton_scattering.validate_task09_documentation
python3 -m unittest task09_compton_scattering.test_documentation_validation
```

## Stage boundary

Stage 9 freezes the explanatory handoff. The competition PowerPoint, narration and presentation-specific visual inspection belong to Stage 10.
