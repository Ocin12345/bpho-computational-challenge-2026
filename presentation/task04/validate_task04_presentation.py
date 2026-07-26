"""Run the shared Task 4 presentation validator."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from presentation.validate_task_presentations import validate_task


if __name__ == "__main__":
    validate_task(4)
