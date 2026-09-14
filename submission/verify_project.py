"""One-command scientific and artifact verification for Tasks 1–10."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_DIRECTORY = ROOT / "submission"


@dataclass(frozen=True)
class CommandStep:
    """One reproducibility or validation command."""

    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class StepResult:
    """Serializable result from one command."""

    name: str
    command: tuple[str, ...]
    returncode: int
    elapsed_seconds: float
    output_tail: str


def _python_module(name: str, *arguments: str) -> tuple[str, ...]:
    return (sys.executable, "-m", name, *arguments)


def _unittest_step(task_directory: str) -> CommandStep:
    return CommandStep(
        name=f"{task_directory} tests",
        command=(
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            task_directory,
            "-t",
            ".",
            "-p",
            "test_*.py",
        ),
    )


def _environment() -> dict[str, str]:
    """Return the versions that materially affect regenerated artifacts."""

    import matplotlib
    import numpy
    import PIL
    import scipy
    from matplotlib import font_manager

    if shutil.which("node") is None:
        raise RuntimeError("Node.js is required for the JavaScript checks. Install Node.js and retry.")
    font_path = font_manager.findfont(
        "Times New Roman",
        fallback_to_default=False,
    )
    return {
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "pillow": PIL.__version__,
        "times_new_roman": font_path,
        "platform": sys.platform,
    }


def _run(step: CommandStep) -> StepResult:
    """Run one step while preserving its complete output in the terminal."""

    display = " ".join(step.command)
    print(f"\n=== {step.name} ===", flush=True)
    print(display, flush=True)
    started = time.perf_counter()
    environment = os.environ.copy()
    environment.update(
        {
            "MPLBACKEND": "Agg",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": str(ROOT),
        }
    )
    try:
        process = subprocess.run(
            step.command,
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as error:
        process = subprocess.CompletedProcess(step.command, 1, stdout=str(error))
    elapsed = time.perf_counter() - started
    output = process.stdout or ""
    print(output, end="" if output.endswith("\n") else "\n", flush=True)
    status = "PASS" if process.returncode == 0 else "FAIL"
    print(f"[{status}] {step.name} ({elapsed:.2f} s)", flush=True)
    return StepResult(
        name=step.name,
        command=step.command,
        returncode=process.returncode,
        elapsed_seconds=elapsed,
        output_tail=output[-4000:],
    )


def _saved_task2_check() -> StepResult:
    """Validate the committed high-cost refinement evidence without rerunning it."""

    started = time.perf_counter()
    report_path = (
        ROOT / "task02_brownian_motion/validation/reference_validation.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = report.get("reference_refinement", [])
    checks = report.get("checks", [])
    factors = [row.get("refinement_factor") for row in rows]
    passed = (
        report.get("passed") is True
        and len(checks) == 9
        and all(check.get("passed") is True for check in checks)
        and factors == [1, 2, 4]
    )
    message = (
        f"saved Task 2 report: {len(checks)}/9 checks pass; "
        f"refinement factors={factors}"
    )
    print(f"\n=== Task 2 saved full-refinement evidence ===\n{message}")
    print(f"[{'PASS' if passed else 'FAIL'}] Task 2 saved refinement")
    return StepResult(
        name="Task 2 saved full-refinement evidence",
        command=("internal-json-check", str(report_path.relative_to(ROOT))),
        returncode=0 if passed else 1,
        elapsed_seconds=time.perf_counter() - started,
        output_tail=message,
    )


def _markdown_link_check() -> StepResult:
    """Resolve all local Markdown links outside vendored dependencies."""

    started = time.perf_counter()
    pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    missing: list[str] = []
    checked = 0
    for document in ROOT.rglob("*.md"):
        relative_document = document.relative_to(ROOT)
        if any(
            part in {".git", "node_modules", ".venv", "venv", "env", "release"}
            for part in relative_document.parts
        ):
            continue
        if relative_document.parts[:2] == ("site", "vendor"):
            continue
        text = document.read_text(encoding="utf-8")
        for target in pattern.findall(text):
            normalized = target.strip().strip("<>")
            if not normalized or normalized.startswith(
                ("http://", "https://", "#", "mailto:")
            ):
                continue
            path_text = normalized.split("#", 1)[0]
            if not path_text:
                continue
            checked += 1
            if not (document.parent / path_text).resolve().exists():
                missing.append(
                    f"{document.relative_to(ROOT)} -> {normalized}"
                )
    message = (
        f"{checked} local links resolved"
        if not missing
        else "missing links:\n" + "\n".join(missing)
    )
    print(f"\n=== Project document links ===\n{message}")
    print(f"[{'PASS' if not missing else 'FAIL'}] Project document links")
    return StepResult(
        name="Project document links",
        command=("internal-markdown-link-check",),
        returncode=0 if not missing else 1,
        elapsed_seconds=time.perf_counter() - started,
        output_tail=message[-4000:],
    )


def _powerpoint_portability_check() -> StepResult:
    """Reject local filesystem URLs in every delivered PowerPoint."""

    started = time.perf_counter()
    offenders: list[str] = []
    presentations = sorted((ROOT / "presentation").glob("task*/*.pptx"))
    presentations.extend(sorted((ROOT / "presentation/master").glob("*.pptx")))
    for presentation in presentations:
        with zipfile.ZipFile(presentation) as archive:
            if archive.testzip() is not None:
                offenders.append(f"corrupt archive: {presentation.name}")
                continue
            for name in archive.namelist():
                if not name.endswith((".xml", ".rels")):
                    continue
                content = archive.read(name)
                if b"/Users/" in content or b"file://" in content:
                    offenders.append(
                        f"{presentation.relative_to(ROOT)}::{name}"
                    )
    message = (
        f"{len(presentations)} PowerPoints contain no local-machine links"
        if not offenders
        else "offenders:\n" + "\n".join(offenders)
    )
    print(f"\n=== PowerPoint portability ===\n{message}")
    print(f"[{'PASS' if not offenders else 'FAIL'}] PowerPoint portability")
    return StepResult(
        name="PowerPoint portability",
        command=("internal-pptx-portability-check",),
        returncode=0 if not offenders else 1,
        elapsed_seconds=time.perf_counter() - started,
        output_tail=message[-4000:],
    )


def _ensure_npm_dependencies(directory: Path) -> None:
    """Install a locked presentation dependency tree only when absent."""

    if (directory / "node_modules").is_dir():
        return
    if shutil.which("npm") is None:
        raise RuntimeError("npm is required for presentation regeneration")
    result = _run(
        CommandStep(
            name=f"Install locked dependencies in {directory.relative_to(ROOT)}",
            command=("npm", "ci", "--prefix", str(directory.relative_to(ROOT))),
        )
    )
    if result.returncode != 0:
        raise RuntimeError(f"npm ci failed in {directory}")


def _generation_steps(workers: int) -> tuple[CommandStep, ...]:
    """Return the dependency-ordered full evidence regeneration commands."""

    return (
        CommandStep("Generate Task 1 single walk", _python_module("task01_random_walk.plot_single_walk")),
        CommandStep("Generate Task 1 ensemble", _python_module("task01_random_walk.plot_walk_ensemble")),
        CommandStep("Generate Task 1 statistics", _python_module("task01_random_walk.statistical_analysis")),
        CommandStep("Generate Task 1 animation", _python_module("task01_random_walk.animate_random_walk")),
        CommandStep("Generate Task 1 web evidence", _python_module("task01_random_walk.generate_web_validation")),
        CommandStep("Generate Task 1 dimensional evidence", _python_module("task01_random_walk.generate_dimensional_validation")),
        CommandStep("Run full Task 2 refinement", _python_module("task02_brownian_motion.validate_task02")),
        CommandStep(
            "Generate Task 2 ensembles",
            _python_module("task02_brownian_motion.analyze_task02", "--workers", str(workers)),
        ),
        CommandStep("Generate Task 2 visuals", _python_module("task02_brownian_motion.create_task02_visuals")),
        CommandStep("Generate Task 2 web evidence", _python_module("task02_brownian_motion.generate_web_evidence")),
        CommandStep("Generate Task 2 extension evidence", _python_module("task02_brownian_motion.generate_extension_evidence")),
        CommandStep("Generate Task 3 evidence", _python_module("task03_thermal_radiation.generate_task03")),
        CommandStep("Generate Task 3 Debye evidence", _python_module("task03_thermal_radiation.generate_debye_validation")),
        CommandStep("Generate Task 4 evidence", _python_module("task04_photoelectric_effect.generate_task04", "--with-animation")),
        CommandStep("Generate Task 5 evidence", _python_module("task05_hydrogen_spectrum.generate_task05")),
        CommandStep("Generate Task 5 reduced-mass evidence", _python_module("task05_hydrogen_spectrum.generate_reduced_mass_extension")),
        CommandStep("Generate Task 6 evidence", _python_module("task06_electron_diffraction.generate_task06")),
        CommandStep("Generate Task 6 relativistic evidence", _python_module("task06_electron_diffraction.generate_relativistic_extension")),
        CommandStep("Generate Task 7 evidence", _python_module("task07_particle_in_box.generate_task07")),
        CommandStep("Generate Task 7 superposition evidence", _python_module("task07_particle_in_box.generate_superposition_extension")),
        CommandStep("Generate Task 8 core evidence", _python_module("task08_quantum_cryptography.generate_task08")),
        CommandStep("Generate Task 8 sampling evidence", _python_module("task08_quantum_cryptography.generate_task08_statistics")),
        CommandStep("Generate Task 8 figures", _python_module("task08_quantum_cryptography.generate_task08_figures")),
        CommandStep("Generate Task 9 kinematics", _python_module("task09_compton_scattering.generate_task09")),
        CommandStep("Generate Task 9 cross section", _python_module("task09_compton_scattering.generate_task09_cross_section")),
        CommandStep("Generate Task 9 figures", _python_module("task09_compton_scattering.generate_task09_figures")),
        CommandStep("Generate Task 9 animation", _python_module("task09_compton_scattering.animation")),
        CommandStep("Generate Task 9 media manifest", _python_module("task09_compton_scattering.generate_task09_media_manifest")),
        CommandStep("Generate Task 10 core evidence", _python_module("task10_hydrogenic_orbitals.generate_task10")),
        CommandStep("Generate Task 10 figures", _python_module("task10_hydrogenic_orbitals.generate_task10_figures")),
        CommandStep("Generate Task 10 motion", _python_module("task10_hydrogenic_orbitals.generate_task10_motion")),
        CommandStep("Generate advanced extension evidence", _python_module("submission.generate_advanced_extensions")),
        CommandStep("Generate advanced extension figures", _python_module("submission.generate_advanced_figures")),
        CommandStep("Build Task 1–2 summaries", (sys.executable, "presentation/build_task01_task02_summaries.py")),
        CommandStep("Build Task 1–6 decks", ("npm", "run", "build:tasks1-6", "--prefix", "presentation")),
        CommandStep("Build Task 7 deck", ("npm", "run", "build", "--prefix", "presentation/task07")),
        CommandStep("Build Task 8 deck", ("npm", "run", "build", "--prefix", "presentation/task08")),
        CommandStep("Build Task 9 deck", ("npm", "run", "build", "--prefix", "presentation/task09")),
        CommandStep("Build Task 10 deck", ("npm", "run", "build", "--prefix", "presentation/task10")),
        CommandStep("Build master deck", ("npm", "run", "build:master", "--prefix", "presentation")),
        CommandStep("Render Task 1–6 previews", ("bash", "presentation/render_task_previews.sh")),
        CommandStep("Render Task 7 preview", ("npm", "run", "preview", "--prefix", "presentation/task07")),
        CommandStep("Render Task 8 preview", ("npm", "run", "preview", "--prefix", "presentation/task08")),
        CommandStep("Render Task 9 preview", ("npm", "run", "preview", "--prefix", "presentation/task09")),
        CommandStep("Render Task 10 preview", ("npm", "run", "preview", "--prefix", "presentation/task10")),
        CommandStep("Render master deck and PDF", ("bash", "presentation/master/render_master_preview.sh")),
        CommandStep("Build master contact sheet", (sys.executable, "presentation/master/create_contact_sheet.py")),
    )


def _validation_steps(full_task2: bool) -> tuple[CommandStep, ...]:
    steps: list[CommandStep] = [
        _unittest_step(f"task{number:02d}_{name}")
        for number, name in (
            (1, "random_walk"),
            (2, "brownian_motion"),
            (3, "thermal_radiation"),
            (4, "photoelectric_effect"),
            (5, "hydrogen_spectrum"),
            (6, "electron_diffraction"),
            (7, "particle_in_box"),
            (8, "quantum_cryptography"),
            (9, "compton_scattering"),
            (10, "hydrogenic_orbitals"),
        )
    ]
    if full_task2:
        steps.append(
            CommandStep(
                "Full Task 2 time-step refinement",
                _python_module("task02_brownian_motion.validate_task02"),
            )
        )
    steps.extend(
        (
            CommandStep("Task 3 science gate", _python_module("task03_thermal_radiation.validate_task03")),
            CommandStep("Task 4 science gate", _python_module("task04_photoelectric_effect.validate_task04")),
            CommandStep("Task 5 science gate", _python_module("task05_hydrogen_spectrum.validate_task05")),
            CommandStep("Task 6 science gate", _python_module("task06_electron_diffraction.validate_task06")),
            CommandStep("Task 7 final gate", _python_module("task07_particle_in_box.validate_task07_final")),
            CommandStep("Task 8 final gate", _python_module("task08_quantum_cryptography.validate_task08_final")),
            CommandStep("Task 9 final gate", _python_module("task09_compton_scattering.validate_task09_final")),
            CommandStep("Task 10 final gate", _python_module("task10_hydrogenic_orbitals.validate_task10_final")),
            CommandStep("Advanced extension evidence gate", _python_module("submission.validate_advanced_extensions")),
            CommandStep("Advanced extension figure gate", _python_module("submission.validate_advanced_figures")),
            CommandStep("Advanced lab static gate", ("node", "site/validate-advanced.mjs")),
            CommandStep("Task presentations", (sys.executable, "presentation/validate_task_presentations.py")),
            CommandStep("Presentation typography", (sys.executable, "presentation/validate_typography.py")),
            CommandStep("Master presentation", (sys.executable, "presentation/master/validate_master_presentation.py")),
            CommandStep("Website assets and links", _python_module("submission.validate_site")),
        )
    )
    steps.extend(
        CommandStep(f"Task {number} website gate", ("node", f"site/validate-task-{number:02d}.mjs"))
        for number in range(1, 11)
    )
    steps.append(_unittest_step("submission"))
    return tuple(steps)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate or verify the complete BPhO Tasks 1–10 project."
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="regenerate all accepted evidence before validation",
    )
    parser.add_argument(
        "--full-task2",
        action="store_true",
        help="rerun the expensive full Task 2 time-step refinement",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="parallel workers for Task 2 ensemble regeneration",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=SUBMISSION_DIRECTORY / "latest_verification.json",
        help="JSON result path",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    if options.workers < 1:
        raise SystemExit("--workers must be at least 1")

    started = time.perf_counter()
    results: list[StepResult] = []
    environment: dict[str, str]
    try:
        environment = _environment()
    except Exception as error:
        print(f"Environment preflight failed: {error}", file=sys.stderr)
        return 1

    if options.regenerate:
        for executable in (os.environ.get("SOFFICE", "soffice"), os.environ.get("PDFTOPPM", "pdftoppm"), "bash", "npm"):
            if shutil.which(executable) is None:
                print(f"Regeneration requires {executable}; see submission/README.md.", file=sys.stderr)
                return 1
        for directory in (
            ROOT / "presentation",
            ROOT / "presentation/task07",
            ROOT / "presentation/task08",
            ROOT / "presentation/task09",
            ROOT / "presentation/task10",
        ):
            _ensure_npm_dependencies(directory)
        for step in _generation_steps(options.workers):
            result = _run(step)
            results.append(result)
            if result.returncode != 0:
                break

    if not results or results[-1].returncode == 0:
        if not options.full_task2 and not options.regenerate:
            results.append(_saved_task2_check())
        for step in _validation_steps(
            full_task2=options.full_task2 and not options.regenerate
        ):
            result = _run(step)
            results.append(result)
            if result.returncode != 0:
                break

    if not results or results[-1].returncode == 0:
        results.append(_markdown_link_check())
    if not results or results[-1].returncode == 0:
        results.append(_powerpoint_portability_check())

    passed = bool(results) and all(result.returncode == 0 for result in results)
    report = {
        "project": "BPhO Computational Challenge 2026 Tasks 1–10",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "regenerate-and-validate" if options.regenerate else "validate",
        "full_task2_rerun": bool(options.regenerate or options.full_task2),
        "passed": passed,
        "elapsed_seconds": time.perf_counter() - started,
        "environment": environment,
        "steps": [asdict(result) for result in results],
    }
    report_path = options.report
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("\n=== FINAL RESULT ===")
    print("PASS" if passed else "FAIL")
    print(f"elapsed: {report['elapsed_seconds']:.2f} s")
    print(f"report: {report_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
