from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class JudgeFacingPageTests(unittest.TestCase):
    def test_gold_sections_and_numerical_evidence_are_present(self) -> None:
        html = (ROOT / "site/tasks/task-07.html").read_text(encoding="utf-8")
        script = (ROOT / "site/assets/task-07-laboratory.js").read_text(
            encoding="utf-8"
        )
        evidence = (ROOT / "site/assets/task-07-evidence.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            'href="#state">Experiment',
            'href="#spectrum">Plot',
            'href="#method">Method',
            'href="#validation">Validation',
            'id="numerical-moments-table"',
            'Δx<sub>num</sub>',
            'Δx<sub>reference</sub>',
            '(ΔxΔp / ℏ)<sub>reference</sub>',
            'id="convergence-canvas"',
            'id="method"',
            'id="validation"',
            'data-validation-overlap',
            'data-reset-state',
            'numerical_moments.csv',
            'uncertainty_convergence.csv',
        ):
            self.assertIn(marker, html + script + evidence)
        self.assertIn("Rescaled wavefunction shape", html + script)
        self.assertIn("minimumProductOrder.toFixed(3)", script)
        self.assertNotIn('id="superposition"', html)


if __name__ == "__main__":
    unittest.main()
