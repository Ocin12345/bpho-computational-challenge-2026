#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const currentDirectory = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(currentDirectory, "..");
const readText = (path) => readFile(resolve(projectRoot, path), "utf8");
const readJson = async (path) => JSON.parse(await readText(path));

const [
  html,
  css,
  laboratoryScript,
  evidenceLoader,
  motion,
  taskIndex,
  energyText,
  stateText,
  expectationText,
  numericalText,
  validation,
  manifest,
  probabilityPng,
  summaryPng,
  plottingSource,
  reportSource,
] = await Promise.all([
  readText("site/tasks/task-07.html"),
  readText("site/assets/task-07.css"),
  readText("site/assets/task-07-laboratory.js"),
  readText("site/assets/task-07-evidence.js"),
  readText("site/assets/task-07-motion.js"),
  readText("site/tasks.html"),
  readText("data/task07/energy_levels.csv"),
  readText("data/task07/stationary_states.csv"),
  readText("data/task07/expectation_values.csv"),
  readText("data/task07/numerical_eigenvalues.csv"),
  readJson("data/task07/validation_report.json"),
  readJson("data/task07/manifest.json"),
  readFile(resolve(projectRoot, "figures/task07/probability_densities.png")),
  readFile(resolve(projectRoot, "figures/task07/task07_summary.png")),
  readText("task07_particle_in_box/plotting.py"),
  readText("reports/task07/particle_in_box_uncertainty.tex"),
]);

const checks = [];

function check(name, condition, detail) {
  checks.push({ name, passed: Boolean(condition), detail });
}

function parseCsv(text) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.map((line) =>
    Object.fromEntries(
      line.split(",").map((field, index) => [headers[index], field]),
    ),
  );
}

function relativeError(observed, expected) {
  return expected === 0
    ? Math.abs(observed)
    : Math.abs(observed - expected) / Math.abs(expected);
}

const energies = parseCsv(energyText);
const states = parseCsv(stateText);
const expectations = parseCsv(expectationText);
const numerical = parseCsv(numericalText);
const constants = manifest.constants;
const config = manifest.configuration;
const ground =
  (Math.PI ** 2 * constants.reduced_planck_constant_j_s ** 2) /
  (2 * config.particle_mass_kg * config.box_width_m ** 2);

check(
  "Accepted validation report",
  validation.schema_version === "task07-validation-v1" &&
    validation.passed === true &&
    validation.study_digest === manifest.study_digest &&
    validation.checks.length === 37 &&
    validation.checks.every((entry) => entry.passed === true),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} independent checks pass.`,
);

check(
  "Complete discrete energy spectrum",
  energies.length === 10 &&
    energies.every((row, index) => {
      const n = Number(row.quantum_number_n);
      return (
        n === index + 1 &&
        relativeError(Number(row.energy_j), ground * n ** 2) < 5e-12 &&
        relativeError(Number(row.energy_over_ground), n ** 2) < 5e-12 &&
        (n < 10
          ? relativeError(Number(row.gap_to_next_j), ground * (2 * n + 1)) <
            5e-12
          : row.gap_to_next_j === "")
      );
    }),
  "Ten positive-integer states obey E_n/E_1=n², with exact increasing level gaps.",
);

check(
  "Complete normalized stationary states",
  states.length === 8004 &&
    states.every((row, rowIndex) => {
      const positionIndex = Math.floor(rowIndex / 4);
      const n = (rowIndex % 4) + 1;
      const u = positionIndex / 2000;
      const observedPsi =
        Number(row.wavefunction_m_neg_half) *
        Math.sqrt(config.box_width_m / 2);
      return (
        Number(row.position_index) === positionIndex &&
        Number(row.quantum_number_n) === n &&
        Math.abs(Number(row.position_over_box_width) - u) < 1e-14 &&
        Math.abs(observedPsi - Math.sin(n * Math.PI * u)) < 2e-14 &&
        Math.abs(
          Number(row.box_width_times_density) -
            2 * Math.sin(n * Math.PI * u) ** 2,
        ) < 5e-13
      );
    }),
  "All 8,004 samples for n=1–4 obey the boundary-conditioned wavefunction and Born density.",
);

check(
  "Complete uncertainty extension data",
  expectations.length === 10 &&
    expectations.every((row, index) => {
      const n = index + 1;
      const expectedProduct = Math.sqrt((n ** 2 * Math.PI ** 2) / 12 - 0.5);
      return (
        Number(row.quantum_number_n) === n &&
        relativeError(Number(row.expected_x_m), config.box_width_m / 2) <
          5e-12 &&
        Number(row.expected_p_kg_m_s) === 0 &&
        relativeError(
          Number(row.delta_x_delta_p_over_hbar),
          expectedProduct,
        ) < 5e-12 &&
        Number(row.delta_x_delta_p_over_hbar) >= 0.5
      );
    }),
  "All ten states include both moments, both standard deviations, and ΔxΔp/ℏ≥0.5.",
);

const finest = numerical.filter(
  (row) => Number(row.interior_point_count) === 1600,
);
check(
  "Independent finite-difference convergence",
  numerical.length === 50 &&
    new Set(numerical.map((row) => Number(row.interior_point_count))).size ===
      5 &&
    numerical.every(
      (row) =>
        Number(row.observed_convergence_order) >= 1.998 &&
        Number(row.observed_convergence_order) <= 2.001,
    ) &&
    finest.length === 10 &&
    Math.max(...finest.map((row) => Number(row.relative_energy_error))) <
      3.21e-5 &&
    finest.every(
      (row) => Number(row.finest_grid_absolute_overlap) > 0.9999999999999,
    ),
  "Five grids and fifty eigenpairs converge at order two; finest-grid states meet the accepted errors and overlaps.",
);

check(
  "Complete required website content",
  [
    'id="box-state-canvas"',
    'id="energy-spectrum-canvas"',
    'id="density-canvas"',
    'id="uncertainty-canvas"',
    'id="quantum-number"',
    'data-state-preset="1"',
    'data-state-preset="10"',
    'data-density-state="1"',
    'data-density-state="4"',
    "E<sub>n</sub> = n²π²ℏ² / 2ma²",
    "37/37",
    "Read PDF",
    "LaTeX source",
    "Accessible text",
    "energy_level_wavefunctions.png",
    "wavefunctions_and_density.png",
    "uncertainty_principle.png",
  ].every((marker) => html.includes(marker)),
  "The state laboratory, both official plots, full extension proof, numerical evidence, and accepted figures are present.",
);

check(
  "Interactive and keyboard-complete model",
  laboratoryScript.includes("selectState") &&
    laboratoryScript.includes("nearestSpectrumPoint") &&
    laboratoryScript.includes("ArrowLeft") &&
    laboratoryScript.includes("ArrowRight") &&
    laboratoryScript.includes('"Home"') &&
    laboratoryScript.includes('"End"') &&
    laboratoryScript.includes("ResizeObserver") &&
    laboratoryScript.includes("data-density-state") &&
    laboratoryScript.includes("data-state-preset"),
  "The discrete selector, state presets, view modes, density filters, marker selection, and keyboard navigation are implemented.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-state-loading") &&
    html.includes("data-state-error") &&
    html.includes("data-spectrum-error") &&
    html.includes("data-density-error") &&
    html.includes("data-uncertainty-error") &&
    evidenceLoader.includes("throw new Error") &&
    laboratoryScript.includes("setFailureState") &&
    laboratoryScript.includes('dataset.task07Status = "error"') &&
    laboratoryScript.includes("control.disabled = false"),
  "Loading, verified, and explicit error states keep every control locked until all evidence agrees.",
);

check(
  "Local typography and motion dependencies",
  html.includes("../vendor/packages/gsap/dist/gsap.min.js") &&
    html.includes("../vendor/packages/gsap/dist/ScrollTrigger.min.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    css.includes('"Geist"') &&
    css.includes('"Bodoni Moda Variable"') &&
    css.includes('--figure: "Times New Roman"') &&
    laboratoryScript.match(/"Times New Roman"/g)?.length >= 8,
  "Pinned local interface fonts and motion are used; every scientific canvas uses Times New Roman.",
);

check(
  "High-DPI and idle-stable figures",
  laboratoryScript.includes("canvas.clientWidth") &&
    laboratoryScript.includes("canvas.clientHeight") &&
    laboratoryScript.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !laboratoryScript.includes("requestAnimationFrame(draw") &&
    !laboratoryScript.includes("setInterval("),
  "All four canvases render at up to 2x device density without continuous idle repaint.",
);

const probabilityDimensions = [
  probabilityPng.readUInt32BE(16),
  probabilityPng.readUInt32BE(20),
];
const summaryDimensions = [
  summaryPng.readUInt32BE(16),
  summaryPng.readUInt32BE(20),
];
check(
  "Original-resolution scientific figures",
  probabilityDimensions[0] === 2400 &&
    probabilityDimensions[1] === 1500 &&
    summaryDimensions[0] === 3840 &&
    summaryDimensions[1] === 2160 &&
    plottingSource.includes('FIGURE_FONT_FAMILY = "Times New Roman"'),
  `Probability plot is ${probabilityDimensions.join("×")}; summary is ${summaryDimensions.join("×")}; generation is locked to Times New Roman.`,
);

check(
  "Analytical extension is complete",
  reportSource.includes("\\langle x\\rangle") &&
    reportSource.includes("\\langle x^2\\rangle") &&
    reportSource.includes("\\langle p\\rangle") &&
    reportSource.includes("\\langle p^2\\rangle") &&
    reportSource.includes("\\Delta x") &&
    reportSource.includes("\\Delta p") &&
    reportSource.includes("\\frac{\\hbar}{2}") &&
    html.includes("0.567862ℏ") &&
    html.includes("Four-page accepted extension"),
  "The page links the accepted report and exposes all four moments, uncertainties, lower bound, and strict ground-state result.",
);

check(
  "Responsive and reduced-motion safeguards",
  css.includes("100svh") &&
    css.includes("@media (max-width: 820px)") &&
    css.includes("@media (max-width: 520px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)") &&
    motion.includes("prefers-reduced-motion: reduce") &&
    motion.includes("pagehide"),
  "Dynamic viewport layout, two mobile breakpoints, reduced-motion handling, and cleanup paths are present.",
);

check(
  "Honest stationary-state and scope boundary",
  html.includes("No curve is animated as particle motion") &&
    html.includes("stationary density does not move") &&
    html.includes("infinite wall") &&
    html.includes("Normalized plots preserve") &&
    !laboratoryScript.includes("setInterval("),
  "The page distinguishes phase from observable density and keeps the infinite-well model and animation boundary explicit.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-07\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-07"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 7 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(
  `\n${checks.length - failed.length}/${checks.length} Task 7 website checks passed.`,
);

if (failed.length) process.exitCode = 1;
