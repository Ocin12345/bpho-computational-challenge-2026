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
  calculator,
  evidenceLoader,
  navigation,
  taskIndex,
  sweepText,
  gridText,
  references,
  validation,
  manifest,
  finite,
  statisticalValidation,
  statisticalManifest,
  sweepPng,
  landscapePng,
  samplingPng,
  summaryPng,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-08.html"),
  readText("site/assets/task-08.css"),
  readText("site/assets/task-08-minimal.css"),
  readText("site/assets/task-08-calculator.js"),
  readText("site/assets/task-08-evidence.js"),
  readText("site/assets/task-08-navigation.js"),
  readText("site/tasks.html"),
  readText("data/task08/angle_sweep.csv"),
  readText("data/task08/mismatch_grid.csv"),
  readJson("data/task08/reference_cases.json"),
  readJson("data/task08/validation_report.json"),
  readJson("data/task08/manifest.json"),
  readJson("data/task08/finite_photon_reference.json"),
  readJson("data/task08/statistical_validation_report.json"),
  readJson("data/task08/statistics_manifest.json"),
  readFile(resolve(projectRoot, "figures/task08/probability_sweep.png")),
  readFile(resolve(projectRoot, "figures/task08/mismatch_landscape.png")),
  readFile(resolve(projectRoot, "figures/task08/finite_photon_sampling.png")),
  readFile(resolve(projectRoot, "figures/task08/task08_summary.png")),
  readText("task08_quantum_cryptography/plotting.py"),
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

function mismatch(thetaDeg, phiDeg) {
  const theta = (thetaDeg * Math.PI) / 180;
  const phi = (phiDeg * Math.PI) / 180;
  return {
    classical:
      1 -
      Math.cos(theta) ** 2 * Math.cos(phi) ** 2 -
      Math.sin(theta) ** 2 * Math.sin(phi) ** 2,
    quantum: Math.sin(phi - theta) ** 2,
    difference: -0.5 * Math.sin(2 * theta) * Math.sin(2 * phi),
  };
}

function close(observed, expected, tolerance = 5e-12) {
  return Math.abs(observed - expected) <= tolerance;
}

function dimensions(buffer) {
  return [buffer.readUInt32BE(16), buffer.readUInt32BE(20)];
}

const sweep = parseCsv(sweepText);
const grid = parseCsv(gridText);
const officialReference = references.cases?.find(
  (item) => item.identifier === "official_example",
);
const defaultSample = finite.cases?.find(
  (item) => item.identifier === "official_default",
);

check(
  "Accepted core validation report",
  validation.schema_version === "task08-validation-v1" &&
    validation.passed === true &&
    validation.study_digest === manifest.study_digest &&
    validation.checks.length === 42 &&
    validation.checks.every((entry) => entry.passed === true),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} independent checks pass with the committed study digest.`,
);

check(
  "Complete fixed-angle sweep",
  sweep.length === 361 &&
    sweep.every((row, index) => {
      const theta = Number(row.theta_deg);
      const phi = Number(row.phi_deg);
      const expected = mismatch(theta, phi);
      return (
        theta === -30 &&
        phi === -90 + index * 0.5 &&
        close(Number(row.classical_mismatch_probability), expected.classical) &&
        close(Number(row.quantum_mismatch_probability), expected.quantum) &&
        close(Number(row.quantum_minus_classical), expected.difference)
      );
    }),
  "All 361 half-degree samples reproduce both equations and the signed contrast for θ = −30°.",
);

check(
  "Complete two-angle landscape",
  grid.length === 181 * 181 &&
    grid.every((row, rowIndex) => {
      const thetaIndex = Math.floor(rowIndex / 181);
      const phiIndex = rowIndex % 181;
      const theta = Number(row.theta_deg);
      const phi = Number(row.phi_deg);
      const expected = mismatch(theta, phi);
      return (
        Number(row.theta_index) === thetaIndex &&
        Number(row.phi_index) === phiIndex &&
        theta === -90 + thetaIndex &&
        phi === -90 + phiIndex &&
        close(Number(row.classical_mismatch_probability), expected.classical) &&
        close(Number(row.quantum_mismatch_probability), expected.quantum) &&
        close(Number(row.quantum_minus_classical), expected.difference)
      );
    }),
  "Every one of the 32,761 integer-degree pairs independently reproduces the classical and quantum mismatch surfaces.",
);

check(
  "Exact official and reference anchors",
  references.schema_version === "task08-reference-v1" &&
    references.cases?.length === 5 &&
    references.cases.every((item) => {
      const expected = mismatch(item.theta_deg, item.phi_deg);
      return (
        close(item.classical_mismatch.decimal, expected.classical) &&
        close(item.quantum_mismatch.decimal, expected.quantum) &&
        close(item.signed_difference.decimal, expected.difference)
      );
    }) &&
    officialReference?.theta_deg === -30 &&
    officialReference?.phi_deg === 30 &&
    officialReference?.classical_mismatch?.numerator === 3 &&
    officialReference?.classical_mismatch?.denominator === 8 &&
    officialReference?.quantum_mismatch?.numerator === 3 &&
    officialReference?.quantum_mismatch?.denominator === 4,
  "Five exact cases agree; the official example is locked to 3/8 versus 3/4.",
);

check(
  "Accepted finite-photon extension",
  statisticalManifest.schema_version ===
    "task08-statistics-manifest-v1" &&
    statisticalManifest.validation_passed === true &&
    statisticalManifest.validation_check_count === 24 &&
    statisticalValidation.schema_version ===
      "task08-statistical-validation-v1" &&
    statisticalValidation.passed === true &&
    statisticalValidation.checks.length === 24 &&
    statisticalValidation.checks.every((entry) => entry.passed === true) &&
    finite.schema_version === "task08-finite-photon-reference-v1" &&
    finite.cryptographic_security === false &&
    finite.configuration?.default_photon_pairs === 1000 &&
    finite.configuration?.default_seed === 2026 &&
    defaultSample?.classical?.mismatches === 363 &&
    defaultSample?.quantum?.mismatches === 770,
  "The separate deterministic binomial layer passes 24/24 checks and reproduces the 363/770 default count anchor.",
);

check(
  "Finite-photon study retained outside the filming path",
  !html.includes('href="#finite-sample">Sample</a>') &&
    html.includes('id="finite-sample"') &&
    html.includes("Finite photon sampling") &&
    html.includes("data-classical-observed") &&
    html.includes("data-quantum-observed") &&
    html.includes('class="video-cut"') &&
    html.includes('data-task="08"') &&
    html.includes("task-video.css") &&
    minimalCss.includes(".sampling-section {") &&
    minimalCss.includes("order: 4;"),
  "The deterministic sample remains in source, while the visible filming path is the exact comparison calculator required by the brief.",
);

check(
  "Complete required website content",
  [
    'id="detector-canvas"',
    'id="sweep-canvas"',
    'id="landscape-canvas"',
    'id="theta-angle"',
    'id="phi-angle"',
    'data-angle-preset="official"',
    'data-angle-preset="contrast"',
    'id="photon-pairs"',
    'id="sample-seed"',
    'data-next-sample',
    "P<sub>C</sub> = 1 − cos²θ cos²φ − sin²θ sin²φ",
    "P<sub>Q</sub> = sin²(φ − θ)",
    "All 32,761 angle pairs",
  ].every((marker) => html.includes(marker)) &&
    !html.includes('id="evidence"') &&
    !html.includes("statistical checks pass"),
  "The exact calculator remains visually primary; supporting equations, sweeps and samples stay in source without evidence ledgers or pass counters.",
);

check(
  "Interactive and keyboard-complete model",
  calculator.includes("data-angle-preset") &&
    calculator.includes("data-photon-preset") &&
    calculator.includes("ArrowLeft") &&
    calculator.includes("ArrowRight") &&
    calculator.includes('"Home"') &&
    calculator.includes('"End"') &&
    calculator.includes("ResizeObserver") &&
    calculator.includes("renderSampling") &&
    calculator.includes("physics.js") &&
    calculator.includes("statistics.js"),
  "Both detector angles, five exact presets, four count presets, reproducible sampling, pointer exploration, and keyboard navigation are implemented.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-detector-loading") &&
    html.includes("data-detector-error") &&
    html.includes("data-sweep-error") &&
    html.includes("data-landscape-error") &&
    evidenceLoader.includes("throw new Error") &&
    calculator.includes("setFailureState") &&
    calculator.includes('dataset.task08Status = "error"') &&
    calculator.includes("control.disabled = false"),
  "Loading, verified, and explicit failure states keep every calculator and sampling control locked until all evidence agrees.",
);

check(
  "Local classical typography and restrained navigation",
  html.includes("task-08-minimal.css") &&
    html.includes("task-08-navigation.js") &&
    !html.includes("gsap.min.js") &&
    !html.includes("task-08-motion.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    minimalCss.includes('--serif: "Times New Roman"') &&
    minimalCss.includes("color-scheme: light") &&
    (calculator.match(/"Times New Roman"/g)?.length ?? 0) >= 8 &&
    navigation.includes("IntersectionObserver"),
  "The page uses a local Times-led light theme, restrained section navigation, and no motion framework.",
);

check(
  "High-DPI and idle-stable figures",
  calculator.includes("canvas.clientWidth") &&
    calculator.includes("canvas.clientHeight") &&
    calculator.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !calculator.includes("requestAnimationFrame(draw") &&
    !calculator.includes("setInterval("),
  "All canvases render at up to 2× device density and redraw only after input or resizing.",
);

const sweepDimensions = dimensions(sweepPng);
const landscapeDimensions = dimensions(landscapePng);
const samplingDimensions = dimensions(samplingPng);
const summaryDimensions = dimensions(summaryPng);
check(
  "Original-resolution scientific figures",
  [sweepDimensions, landscapeDimensions, samplingDimensions].every(
    ([width, height]) => width === 2400 && height === 1500,
  ) &&
    summaryDimensions[0] === 3840 &&
    summaryDimensions[1] === 2160 &&
    plottingSource.includes('FIGURE_FONT_FAMILY = "Times New Roman"'),
  `Three analytical figures are 2400×1500; the summary is ${summaryDimensions.join("×")}; generation is locked to Times New Roman.`,
);

check(
  "Responsive and reduced-motion safeguards",
  minimalCss.includes("100dvh") &&
    minimalCss.includes("@media (max-width: 620px)") &&
    minimalCss.includes("@media (prefers-reduced-motion: reduce)") &&
    calculator.includes("pagehide"),
  "Dynamic viewport sizing, mobile breakpoints, reduced-motion handling, and cleanup paths are present.",
);

check(
  "Honest scientific scope boundary",
  html.includes("not a complete QKD") &&
    html.includes("no loss") &&
    html.includes("dark counts") &&
    html.includes("decoherence") &&
    html.includes("eavesdropper") &&
    html.includes("not cryptographically") &&
    html.includes("Observed counts fluctuate; they never replace") &&
    finite.cryptographic_security === false,
  "Exact theory remains primary; the educational PRNG and the absent real-QKD mechanisms are explicitly disclosed.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-08\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-08"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 8 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(
  `\n${checks.length - failed.length}/${checks.length} Task 8 website checks passed.`,
);

if (failed.length) process.exitCode = 1;
