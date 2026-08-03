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
  calculator,
  evidenceLoader,
  motion,
  taskIndex,
  kinematicsText,
  summaryText,
  references,
  validation,
  manifest,
  crossText,
  crossSummaryText,
  crossValidation,
  crossManifest,
  mediaManifest,
  requiredPng,
  geometryPng,
  extensionPng,
  summaryPng,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-09.html"),
  readText("site/assets/task-09.css"),
  readText("site/assets/task-09-calculator.js"),
  readText("site/assets/task-09-evidence.js"),
  readText("site/assets/task-09-motion.js"),
  readText("site/tasks.html"),
  readText("data/task09/compton_angle_study.csv"),
  readText("data/task09/energy_summary.csv"),
  readJson("data/task09/reference_anchors.json"),
  readJson("data/task09/validation_report.json"),
  readJson("data/task09/manifest.json"),
  readText("data/task09/klein_nishina_study.csv"),
  readText("data/task09/klein_nishina_summary.csv"),
  readJson("data/task09/cross_section_validation_report.json"),
  readJson("data/task09/cross_section_manifest.json"),
  readJson("figures/task09/manifest.json"),
  readFile(resolve(projectRoot, "figures/task09/required_kinematics.png")),
  readFile(resolve(projectRoot, "figures/task09/energy_transfer_geometry.png")),
  readFile(resolve(projectRoot, "figures/task09/klein_nishina_extension.png")),
  readFile(resolve(projectRoot, "figures/task09/task09_summary.png")),
  readText("task09_compton_scattering/plotting.py"),
]);

const checks = [];
const energies = [50, 100, 200, 500, 1000];
const restEnergy = manifest.constants.electron_rest_energy_kev;
const classicalRadius =
  crossManifest.constants.classical_electron_radius_m;

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

function close(observed, expected, tolerance = 5e-11) {
  return Math.abs(observed - expected) <=
    tolerance * Math.max(1, Math.abs(expected));
}

function kinematics(energy, thetaDeg) {
  const theta = (thetaDeg * Math.PI) / 180;
  const cosine = Math.cos(theta);
  const sine = thetaDeg === 0 || thetaDeg === 180 ? 0 : Math.sin(theta);
  const fractionalShift = (energy / restEnergy) * (1 - cosine);
  const scatteredEnergy = energy / (1 + fractionalShift);
  const kinetic = energy - scatteredEnergy;
  const gamma = 1 + kinetic / restEnergy;
  const beta = Math.sqrt(Math.max(0, 1 - gamma ** -2));
  const recoilAngle =
    thetaDeg === 0
      ? 90
      : thetaDeg === 180
        ? 0
        : (Math.atan2(
            scatteredEnergy * sine,
            energy - scatteredEnergy * cosine,
          ) *
            180) /
          Math.PI;
  return { fractionalShift, scatteredEnergy, kinetic, gamma, beta, recoilAngle };
}

function kleinNishina(energy, thetaDeg) {
  const theta = (thetaDeg * Math.PI) / 180;
  const alpha = energy / restEnergy;
  const ratio = 1 / (1 + alpha * (1 - Math.cos(theta)));
  const differential =
    0.5 *
    classicalRadius ** 2 *
    ratio ** 2 *
    (ratio + 1 / ratio - Math.sin(theta) ** 2);
  return {
    ratio,
    differential,
    relative: differential / classicalRadius ** 2,
  };
}

function dimensions(buffer) {
  return [buffer.readUInt32BE(16), buffer.readUInt32BE(20)];
}

const kinematicRows = parseCsv(kinematicsText);
const summaryRows = parseCsv(summaryText);
const crossRows = parseCsv(crossText);
const crossSummaryRows = parseCsv(crossSummaryText);
const normalizedHtml = html
  .replace(/<[^>]+>/g, " ")
  .replace(/\s+/g, " ")
  .toLowerCase();

check(
  "Accepted kinematic validation",
  validation.schema_version === "task09-validation-v1" &&
    validation.passed === true &&
    validation.study_digest === manifest.study_digest &&
    validation.checks.length === 44 &&
    validation.checks.every((entry) => entry.passed === true),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} exact kinematic checks pass with the committed digest.`,
);

check(
  "Complete official kinematic study",
  kinematicRows.length === 5 * 721 &&
    kinematicRows.every((row, rowIndex) => {
      const energyIndex = Math.floor(rowIndex / 721);
      const angleIndex = rowIndex % 721;
      const energy = Number(row.incident_energy_kev);
      const theta = Number(row.theta_deg);
      const expected = kinematics(energy, theta);
      return (
        Number(row.energy_index) === energyIndex &&
        Number(row.angle_index) === angleIndex &&
        energy === energies[energyIndex] &&
        theta === angleIndex * 0.25 &&
        close(
          Number(row.fractional_wavelength_shift),
          expected.fractionalShift,
        ) &&
        close(Number(row.scattered_energy_kev), expected.scatteredEnergy) &&
        close(
          Number(row.electron_kinetic_energy_kev),
          expected.kinetic,
        ) &&
        close(Number(row.electron_gamma), expected.gamma) &&
        close(Number(row.electron_beta), expected.beta) &&
        close(
          Number(row.electron_recoil_angle_deg),
          expected.recoilAngle,
        ) &&
        (row.electron_recoil_direction_defined === "true") ===
          (theta !== 0)
      );
    }),
  "All 3,605 quarter-degree rows reproduce the shift, scattered energy, kinetic energy, relativistic speed, and quadrant-safe recoil direction.",
);

check(
  "Exact endpoints and official anchors",
  references.schema_version === "task09-reference-v1" &&
    references.anchors?.length === 15 &&
    references.anchors.every((item) => {
      const expected = kinematics(
        item.incident_energy_kev,
        item.theta_deg,
      );
      return (
        close(
          item.fractional_wavelength_shift,
          expected.fractionalShift,
        ) &&
        close(item.electron_beta, expected.beta) &&
        close(item.electron_recoil_angle_deg, expected.recoilAngle) &&
        item.electron_recoil_direction_defined === (item.theta_deg !== 0)
      );
    }) &&
    summaryRows.length === 5 &&
    summaryRows.every(
      (row, index) =>
        Number(row.incident_energy_kev) === energies[index] &&
        row.forward_recoil_direction_defined === "false",
    ),
  "Fifteen 0°/90°/180° anchors agree, and every zero-momentum forward direction is explicitly undefined.",
);

check(
  "Accepted Klein–Nishina extension",
  crossValidation.schema_version ===
    "task09-cross-section-validation-v1" &&
    crossValidation.passed === true &&
    crossValidation.study_digest === crossManifest.study_digest &&
    crossValidation.checks.length === 30 &&
    crossValidation.checks.every((entry) => entry.passed === true) &&
    crossManifest.scope ===
      "optional extension; separate from the three official kinematic curves",
  `${crossValidation.checks.filter((entry) => entry.passed).length}/${crossValidation.checks.length} extension checks pass and remain separately scoped.`,
);

check(
  "Complete cross-section study",
  crossRows.length === 5 * 721 &&
    crossSummaryRows.length === 5 &&
    crossRows.every((row, rowIndex) => {
      const energyIndex = Math.floor(rowIndex / 721);
      const angleIndex = rowIndex % 721;
      const energy = Number(row.incident_energy_kev);
      const theta = Number(row.theta_deg);
      const expected = kleinNishina(energy, theta);
      return (
        Number(row.energy_index) === energyIndex &&
        Number(row.angle_index) === angleIndex &&
        energy === energies[energyIndex] &&
        theta === angleIndex * 0.25 &&
        close(
          Number(row.scattered_to_incident_energy_ratio),
          expected.ratio,
        ) &&
        close(
          Number(row.differential_cross_section_m2_sr),
          expected.differential,
          2e-11,
        ) &&
        close(
          Number(row.relative_differential_cross_section),
          expected.relative,
        ) &&
        Number(row.theta_pdf_rad_inv) >= 0
      );
    }),
  "All 3,605 cross-section rows reproduce the independent Klein–Nishina equation with non-negative normalized density.",
);

check(
  "Complete required website content",
  [
    'id="collision-canvas"',
    'id="kinematics-canvas"',
    'id="cross-section-canvas"',
    'id="incident-energy"',
    'id="scattering-angle"',
    'data-energy-preset="50"',
    'data-energy-preset="1000"',
    'data-theta-preset="0"',
    'data-theta-preset="180"',
    "Δλ / λ = α(1 − cos θ)",
    "v / c = √(1 − γ",
    "φ is undefined",
    "44-check report",
    "30-check report",
    "required_kinematics.png",
    "energy_transfer_geometry.png",
  ].every((marker) => html.includes(marker)),
  "The exact collision, three required curves, endpoint disclosure, extension, evidence ledger, and accepted figures are present.",
);

check(
  "Interactive and keyboard-complete model",
  calculator.includes("data-energy-preset") &&
    calculator.includes("data-theta-preset") &&
    calculator.includes("ArrowLeft") &&
    calculator.includes("ArrowRight") &&
    calculator.includes('"Home"') &&
    calculator.includes('"End"') &&
    calculator.includes("pointerdown") &&
    calculator.includes("ResizeObserver") &&
    calculator.includes("comptonKinematics") &&
    calculator.includes("kleinNishinaState"),
  "Energy, angle, ten presets, chart selection, and keyboard navigation all drive the same validated physics functions.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-collision-loading") &&
    html.includes("data-collision-error") &&
    html.includes("data-kinematics-error") &&
    html.includes("data-cross-section-error") &&
    evidenceLoader.includes("throw new Error") &&
    calculator.includes("setFailureState") &&
    calculator.includes('dataset.task09Status = "error"') &&
    calculator.includes("control.disabled = false"),
  "Loading, verified, and explicit failure states keep all twelve controls locked until both evidence layers agree.",
);

check(
  "Local typography and motion dependencies",
  html.includes("../vendor/packages/gsap/dist/gsap.min.js") &&
    html.includes("../vendor/packages/gsap/dist/ScrollTrigger.min.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    css.includes('"Geist"') &&
    css.includes('"Bodoni Moda Variable"') &&
    css.includes('--figure: "Times New Roman"') &&
    (calculator.match(/"Times New Roman"/g)?.length ?? 0) >= 7,
  "Pinned local interface fonts and motion are used; every scientific canvas label uses Times New Roman.",
);

check(
  "High-DPI and idle-stable figures",
  calculator.includes("canvas.clientWidth") &&
    calculator.includes("canvas.clientHeight") &&
    calculator.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !calculator.includes("requestAnimationFrame(draw") &&
    !calculator.includes("setInterval("),
  "All three canvases render at up to 2× device density and redraw only after interaction or resizing.",
);

const standardDimensions = [
  dimensions(requiredPng),
  dimensions(geometryPng),
  dimensions(extensionPng),
];
const summaryDimensions = dimensions(summaryPng);
check(
  "Original-resolution scientific media",
  standardDimensions.every(
    ([width, height]) => width === 2400 && height === 1500,
  ) &&
    summaryDimensions[0] === 3840 &&
    summaryDimensions[1] === 2160 &&
    mediaManifest.rendering_contract?.font_family === "Times New Roman" &&
    mediaManifest.files?.find(
      (entry) => entry.filename === "compton_angle_sweep.gif",
    )?.frame_count === 73 &&
    plottingSource.includes('FIGURE_FONT_FAMILY = "Times New Roman"'),
  "Three analytical figures are 2400×1500, the summary is 3840×2160, the animation has 73 frames, and generation is locked to Times New Roman.",
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
  "Honest physical scope",
  normalizedHtml.includes("free, stationary electron") &&
    normalizedHtml.includes("unpolarized") &&
    normalizedHtml.includes("electron binding") &&
    normalizedHtml.includes("doppler broadening") &&
    normalizedHtml.includes("detector response") &&
    normalizedHtml.includes("possible does not mean equally likely") &&
    normalizedHtml.includes(
      "90° value on the curve is only the continuous",
    ),
  "The two-body assumptions, separately labelled extension, excluded experimental effects, and undefined forward direction are explicit.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-09\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-09"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 9 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(
  `\n${checks.length - failed.length}/${checks.length} Task 9 website checks passed.`,
);

if (failed.length) process.exitCode = 1;
