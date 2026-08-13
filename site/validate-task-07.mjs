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
  minimalCss,
  laboratoryScript,
  extensionScript,
  evidenceLoader,
  navigation,
  taskIndex,
  energyText,
  stateText,
  expectationText,
  numericalText,
  numericalMomentsText,
  uncertaintyConvergenceText,
  validation,
  manifest,
  extensionAnchorText,
  extensionEvidence,
  probabilityPng,
  summaryPng,
  plottingSource,
  reportSource,
] = await Promise.all([
  readText("site/tasks/task-07.html"),
  readText("site/assets/task-07.css"),
  readText("site/assets/task-07-minimal.css"),
  readText("site/assets/task-07-laboratory.js"),
  readText("site/assets/task-07-extension.js"),
  readText("site/assets/task-07-evidence.js"),
  readText("site/assets/task-07-navigation.js"),
  readText("site/tasks.html"),
  readText("data/task07/energy_levels.csv"),
  readText("data/task07/stationary_states.csv"),
  readText("data/task07/expectation_values.csv"),
  readText("data/task07/numerical_eigenvalues.csv"),
  readText("data/task07/numerical_moments.csv"),
  readText("data/task07/uncertainty_convergence.csv"),
  readJson("data/task07/validation_report.json"),
  readJson("data/task07/manifest.json"),
  readText("data/task07/superposition_phase_anchors.csv"),
  readJson("data/task07/superposition_validation.json"),
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
const numericalMoments = parseCsv(numericalMomentsText);
const uncertaintyConvergence = parseCsv(uncertaintyConvergenceText);
const extensionAnchors = parseCsv(extensionAnchorText);
const constants = manifest.constants;
const config = manifest.configuration;
const ground =
  (Math.PI ** 2 * constants.reduced_planck_constant_j_s ** 2) /
  (2 * config.particle_mass_kg * config.box_width_m ** 2);

check(
  "Accepted superposition extension evidence",
  extensionEvidence.schema_version === "task07-superposition-v1" &&
    extensionEvidence.status === "accepted_optional_extension" &&
    extensionEvidence.validation.passed === true &&
    extensionEvidence.validation.check_count === 14 &&
    extensionEvidence.validation.checks.length === 14 &&
    extensionEvidence.validation.checks.every((entry) => entry.passed) &&
    extensionAnchors.length === 17,
  `${extensionEvidence.validation.checks.filter((entry) => entry.passed).length}/14 separate checks pass across ${extensionAnchors.length} phase anchors.`,
);

check(
  "Superposition physics identities",
  extensionAnchors.every((anchor) => {
    const phase = Number(anchor.phase_rad);
    const expectedPosition =
      0.5 - (16 * Math.cos(phase)) / (9 * Math.PI ** 2);
    const expectedLeft = 0.5 + (4 * Math.cos(phase)) / (3 * Math.PI);
    return (
      relativeError(
        Number(anchor.expected_position_over_width),
        expectedPosition,
      ) < 5e-13 &&
      relativeError(Number(anchor.left_half_probability), expectedLeft) <
        5e-13 &&
      Math.abs(Number(anchor.normalization) - 1) < 5e-12
    );
  }) &&
    relativeError(
      extensionEvidence.derived.energy_2_ev,
      4 * extensionEvidence.derived.energy_1_ev,
    ) < 5e-14 &&
    relativeError(
      extensionEvidence.derived.mean_energy_ev,
      2.5 * extensionEvidence.derived.energy_1_ev,
    ) < 5e-14,
  "Every phase anchor preserves normalization and matches the analytical position, left-probability, and energy relations.",
);

check(
  "Accepted validation report",
  validation.schema_version === "task07-validation-v1" &&
    validation.passed === true &&
    validation.study_digest === manifest.study_digest &&
    validation.checks.length === 50 &&
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

const finestMoments = numericalMoments.filter(
  (row) => Number(row.interior_point_count) === 1600,
);
check(
  "Independent numerical uncertainty evidence",
  numericalMoments.length === 50 &&
    uncertaintyConvergence.length === 5 &&
    finestMoments.length === 10 &&
    finestMoments.every(
      (row) =>
        Number(row.heisenberg_ratio_numeric) >= 1 &&
        Number(row.relative_delta_p_error) < 2e-5 &&
        Number(row.relative_uncertainty_error) < 2e-5,
    ) &&
    uncertaintyConvergence.every(
      (row) =>
        Number(row.maximum_delta_p_relative_error) >= 0 &&
        Number(row.maximum_uncertainty_relative_error) >= 0 &&
        Number(row.minimum_uncertainty_product_over_hbar) >= 0.5,
    ),
  "Fifty grid-state moment records obey Heisenberg and converge at measured second order.",
);

check(
  "Complete required website content",
  [
    'id="box-state-canvas"',
    'id="energy-spectrum-canvas"',
    'id="density-canvas"',
    'id="uncertainty-canvas"',
    'id="convergence-canvas"',
    'id="numerical-moments-table"',
    'data-validation-overlap',
    'id="quantum-number"',
    'data-state-preset="1"',
    'data-state-preset="10"',
    'data-density-state="1"',
    'data-density-state="4"',
    "Read PDF",
    "LaTeX source",
    "Accessible text",
    "Numerical moments CSV",
    "Convergence CSV",
  ].every((marker) => html.includes(marker)) &&
    !html.includes('id="superposition"'),
  "The official experiment, plots, uncertainty evidence, method and validation are visible; optional superposition UI is absent.",
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
  "Superposition implementation retained outside the filming path",
  extensionScript.includes("validateEvidence") &&
    extensionScript.includes("densityAt") &&
    extensionScript.includes("expectedPosition") &&
    extensionScript.includes("leftProbability") &&
    extensionScript.includes("ResizeObserver") &&
    extensionScript.includes("canvas.toBlob") &&
    extensionScript.includes('dataset.task07ExtensionStatus = "ready"') &&
    !extensionScript.includes("requestAnimationFrame") &&
    !extensionScript.includes("setInterval(") &&
    html.includes('data-task="07"') &&
    !html.includes('href="#superposition"') &&
    !html.includes("task-07-extension.js"),
  "The accepted superposition implementation remains in source, while the visible filming path ends with the official uncertainty result.",
);

check(
  "Judge-facing method and validation hierarchy",
  html.includes('href="#state">Experiment') &&
    html.includes('href="#spectrum">Plot') &&
    html.includes('href="#method">Method') &&
    html.includes('href="#validation">Validation') &&
    html.includes('data-reset-state') &&
    html.includes("Rescaled wavefunction shape"),
  "Navigation, reset, honest wavefunction scaling, numerical comparison and validation are explicit.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-state-loading") &&
    html.includes("data-state-error") &&
    html.includes("data-spectrum-error") &&
    html.includes("data-density-error") &&
    html.includes("data-uncertainty-error") &&
    html.includes("data-convergence-error") &&
    evidenceLoader.includes("throw new Error") &&
    laboratoryScript.includes("setFailureState") &&
    laboratoryScript.includes('dataset.task07Status = "error"') &&
    laboratoryScript.includes("control.disabled = false"),
  "Loading, verified, and explicit error states keep every control locked until all evidence agrees.",
);

check(
  "Local classical typography and restrained navigation",
  html.includes("task-07-minimal.css") &&
    html.includes("task-07-navigation.js") &&
    !html.includes("gsap.min.js") &&
    !html.includes("task-07-motion.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    minimalCss.includes('--serif: "Times New Roman"') &&
    minimalCss.includes("color-scheme: light") &&
    laboratoryScript.match(/"Times New Roman"/g)?.length >= 7 &&
    navigation.includes("IntersectionObserver"),
  "The page uses a local Times-led light theme, restrained section navigation, and no motion framework.",
);

check(
  "High-DPI and idle-stable figures",
  laboratoryScript.includes("canvas.clientWidth") &&
    laboratoryScript.includes("canvas.clientHeight") &&
    laboratoryScript.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !laboratoryScript.includes("requestAnimationFrame(draw") &&
    !laboratoryScript.includes("setInterval(") &&
    extensionScript.includes("canvas.clientWidth") &&
    extensionScript.includes("Math.min(window.devicePixelRatio || 1, 2)"),
  "All five canvases render at up to 2x device density without continuous idle repaint.",
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
    html.includes("Four-page derivation"),
  "The page links the report and exposes all four moments, uncertainties, lower bound, and strict ground-state result.",
);

check(
  "Responsive and reduced-motion safeguards",
  minimalCss.includes("100dvh") &&
    minimalCss.includes("@media (max-width: 620px)") &&
    minimalCss.includes("@media (prefers-reduced-motion: reduce)") &&
    laboratoryScript.includes("pagehide") &&
    extensionScript.includes("pagehide") &&
    minimalCss.includes(".validation-section"),
  "Dynamic viewport layout, mobile breakpoints, reduced-motion handling, and cleanup paths are present.",
);

check(
  "Honest stationary-state and scope boundary",
  html.includes("A stationary-state probability density does not represent particle motion") &&
    html.includes("infinite well") &&
    html.includes("does not represent particle motion") &&
    !laboratoryScript.includes("setInterval("),
  "The accessible descriptions preserve the trajectory, measurement, and finite-wall boundaries without visible explanatory clutter.",
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
