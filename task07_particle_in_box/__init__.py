"""BPhO Computational Challenge 2026 — Task 7 particle in a box."""

from task07_particle_in_box.analysis import (
    NumericalSolution,
    Task07StudyResult,
    build_task07_study,
    solve_numerical_box,
)
from task07_particle_in_box.configuration import (
    DEFAULT_CONFIGURATION,
    Task07Configuration,
)

__all__ = [
    "DEFAULT_CONFIGURATION",
    "NumericalSolution",
    "Task07Configuration",
    "Task07StudyResult",
    "build_task07_study",
    "solve_numerical_box",
]
