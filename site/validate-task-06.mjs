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
  diffractionScript,
  evidenceLoader,
  motion,
  taskIndex,
  sweepText,
  orderText,
  fitText,
  validation,
  manifest,
  ringPng,
  summaryPng,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-06.html"),
  readText("site/assets/task-06.css"),
  readText("site/assets/task-06-diffraction.js"),
  readText("site/assets/task-06-evidence.js"),
  readText("site/assets/task-06-motion.js"),
  readText("site/tasks.html"),
  readText("data/task06/voltage_sweep.csv"),
  readText("data/task06/diffraction_orders.csv"),
  readText("data/task06/validation_fits.csv"),
  readJson("data/task06/validation_report.json"),
  readJson("data/task06/manifest.json"),
  readFile(resolve(projectRoot, "figures/task06/electron_diffraction_rings.png")),
  readFile(resolve(projectRoot, "figures/task06/task06_summary.png")),
  readText("task06_electron_diffraction/plotting.py"),
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
  return Math.abs(observed - expected) / Math.abs(expected);
}

const sweep = parseCsv(sweepText);
const orders = parseCsv(orderText);
const fits = parseCsv(fitText);
const constants = manifest.constants;
const config = manifest.configuration;

check(
  "Accepted validation report",
  validation.schema_version === "task06-validation-v1" &&
    validation.passed === true &&
    validation.study_digest === manifest.study_digest &&
    validation.checks.length === 39 &&
    validation.checks.every((entry) => entry.passed === true),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} independent checks pass.`,
);

check(
  "Complete voltage and order evidence",
  sweep.length === 401 &&
    sweep.every(
      (row, index) =>
        Number(row.voltage_v) === 1000 + index * 10 &&
        Number(row.voltage_kv) === (1000 + index * 10) / 1000,
    ) &&
    orders.length === 11386 &&
    orders.filter((row) => row.screen_visible === "true").length === 7927 &&
    manifest.catalogue_size === 11386 &&
    manifest.forward_screen_count === 7927,
  "401 exact voltage samples, 11,386 Bragg records, and 7,927 forward-screen records are present.",
);

check(
  "Non-relativistic wavelength model",
  sweep.every((row) => {
    const voltage = Number(row.voltage_v);
    const expected =
      constants.planck_constant_j_s /
      Math.sqrt(
        2 *
          constants.electron_mass_kg *
          constants.elementary_charge_c *
          voltage,
      );
    return relativeError(Number(row.wavelength_m), expected) < 5e-13;
  }),
  "Every wavelength follows h/sqrt(2 m_e e V) across the full 1–5 kV grid.",
);

check(
  "Exact screen geometry and domains",
  orders.every((row) => {
    const q = Number(row.bragg_ratio_q);
    const phi = Number(row.phi_rad);
    const radius = Number(row.photo_radius_m);
    const expectedRadius = config.tube_radius_m * Math.sin(2 * phi);
    const visible = q <= 1 / Math.sqrt(2);
    return (
      q > 0 &&
      q <= 1 &&
      relativeError(radius, expectedRadius) < 5e-12 &&
      (row.screen_visible === "true") === visible &&
      row.bragg_allowed === "true"
    );
  }),
  "All orders obey Bragg q≤1, x=r sin(2φ), and the independent q≤1/sqrt(2) screen rule.",
);

const firstOrderFits = fits.filter((fit) => fit.fit_kind === "first_order");
check(
  "Official spacing recovery",
  fits.length === 4 &&
    firstOrderFits.length === 2 &&
    firstOrderFits.every((fit) => {
      const expected = fit.spacing_id === "d1" ? 0.123 : 0.213;
      return (
        Number(fit.point_count) === 401 &&
        relativeError(Number(fit.recovered_spacing_nm), expected) < 1e-12 &&
        Number(fit.r_squared) === 1 &&
        Math.abs(Number(fit.unconstrained_intercept_v_inv_sqrt)) < 1e-12
      );
    }),
  "Both 401-point first-order fits pass through the origin, reach R²=1, and recover 0.123/0.213 nm.",
);

check(
  "Complete required website content",
  [
    'id="diffraction-screen"',
    'id="spacing-recovery-chart"',
    'id="accelerating-voltage"',
    'data-voltage-preset="1000"',
    'data-voltage-preset="3000"',
    'data-voltage-preset="5000"',
    'data-family="d1"',
    'data-family="d2"',
    "x = r sin(2φ)",
    "y = 2r sin φ",
    "Bragg can allow it",
    "straight_line_validation.svg",
    "electron_diffraction_rings.svg",
    "normalized_order_collapse.svg",
    "ring_radius_vs_voltage.svg",
  ].every((marker) => html.includes(marker)),
  "The exact screen, official graph, voltage controls, two geometric domains, figures, and evidence downloads are present.",
);

check(
  "Interactive and keyboard-complete model",
  diffractionScript.includes("ringCatalogue") &&
    diffractionScript.includes("handleVoltageKeydown") &&
    diffractionScript.includes("ArrowLeft") &&
    diffractionScript.includes("ArrowRight") &&
    diffractionScript.includes("PageDown") &&
    diffractionScript.includes("PageUp") &&
    diffractionScript.includes('"Home"') &&
    diffractionScript.includes('"End"') &&
    diffractionScript.includes("ResizeObserver") &&
    diffractionScript.includes("data-voltage-preset"),
  "Slider, presets, family controls, chart-point selection, and keyboard voltage stepping are implemented.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-screen-loading") &&
    html.includes("data-screen-error") &&
    html.includes("data-validation-error") &&
    html.includes('data-locked="false"') &&
    evidenceLoader.includes("throw new Error") &&
    diffractionScript.includes('dataset.task06Status = "error"') &&
    diffractionScript.includes('dataset.locked = "false"') &&
    diffractionScript.includes("disableControls()"),
  "Loading, verified, and explicit locked-error states prevent unvalidated interaction.",
);

check(
  "Local typography and motion dependencies",
  html.includes("../vendor/packages/gsap/dist/gsap.min.js") &&
    html.includes("../vendor/packages/gsap/dist/ScrollTrigger.min.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    css.includes('"Geist"') &&
    css.includes('"Bodoni Moda Variable"') &&
    css.includes('--figure: "Times New Roman"') &&
    !css.includes('"Inter"') &&
    diffractionScript.match(/"Times New Roman"/g)?.length >= 5,
  "Pinned local interface fonts and motion are used; all scientific canvas text uses Times New Roman.",
);

check(
  "High-DPI and idle-stable figures",
  diffractionScript.includes("canvas.clientWidth") &&
    diffractionScript.includes("canvas.clientHeight") &&
    diffractionScript.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !diffractionScript.includes("requestAnimationFrame(draw") &&
    !diffractionScript.includes("setInterval("),
  "Both canvases render at up to 2x density and perform no continuous idle repaint.",
);

const ringDimensions = [
  ringPng.readUInt32BE(16),
  ringPng.readUInt32BE(20),
];
const summaryDimensions = [
  summaryPng.readUInt32BE(16),
  summaryPng.readUInt32BE(20),
];
check(
  "Original-resolution scientific figures",
  ringDimensions[0] === 2400 &&
    ringDimensions[1] === 1500 &&
    summaryDimensions[0] === 3840 &&
    summaryDimensions[1] === 2160 &&
    plottingSource.includes('"font.family": "Times New Roman"'),
  `Ring model is ${ringDimensions.join("×")}; summary is ${summaryDimensions.join("×")}; generation uses Times New Roman.`,
);

check(
  "Responsive and reduced-motion safeguards",
  css.includes("100dvh") &&
    css.includes("@media (max-width: 767px)") &&
    css.includes("@media (max-width: 410px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)") &&
    motion.includes("prefers-reduced-motion: reduce") &&
    motion.includes("pagehide"),
  "Dynamic viewport, strict mobile layouts, reduced-motion handling, and cleanup paths are present.",
);

check(
  "Honest extension and intensity boundary",
    html.includes("Automatic ring animation and relativistic comparison remain") &&
    html.includes("Width and glow are schematic") &&
    html.includes("Not implied") &&
    html.includes("−0.244%"),
  "The page separates user-controlled geometry from deferred animation, relativity, and unmodelled intensity.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-06\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-06"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 6 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(
  `\n${checks.length - failed.length}/${checks.length} Task 6 website checks passed.`,
);

if (failed.length) process.exitCode = 1;
