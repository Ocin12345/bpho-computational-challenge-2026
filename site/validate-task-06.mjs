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
  diffractionScript,
  relativityScript,
  evidenceLoader,
  navigation,
  taskIndex,
  sweepText,
  orderText,
  fitText,
  validation,
  manifest,
  relativisticExtension,
  ringPng,
  summaryPng,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-06.html"),
  readText("site/assets/task-06.css"),
  readText("site/assets/task-06-minimal.css"),
  readText("site/assets/task-06-diffraction.js"),
  readText("site/assets/task-06-relativity.js"),
  readText("site/assets/task-06-evidence.js"),
  readText("site/assets/task-06-navigation.js"),
  readText("site/tasks.html"),
  readText("data/task06/voltage_sweep.csv"),
  readText("data/task06/diffraction_orders.csv"),
  readText("data/task06/validation_fits.csv"),
  readJson("data/task06/validation_report.json"),
  readJson("data/task06/manifest.json"),
  readJson("data/task06/relativistic_extension.json"),
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
const speedOfLightMPerS = 299792458;

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
    'id="relativity-chart"',
    'id="accelerating-voltage"',
    'data-voltage-preset="1000"',
    'data-voltage-preset="3000"',
    'data-voltage-preset="5000"',
    'data-family="d1"',
    'data-family="d2"',
    "x = r sin(2φ)",
    "y = 2r sin φ",
    "Bragg orders and screen orders",
    "ring_radius_vs_voltage.svg",
  ].every((marker) => html.includes(marker)) &&
    !html.includes('id="evidence"'),
  "The exact screen, graphite-spacing graph, voltage controls, geometric domains, and figures remain without a separate evidence section.",
);

check(
  "Judge-facing task structure",
  [
    'href="#experiment"',
    'href="#plot"',
    'href="#method"',
    'href="#validation"',
    'id="experiment"',
    'id="plot"',
    'id="method"',
    'id="validation"',
    "Official Task 06 of 10",
  ].every((marker) => html.includes(marker)) &&
    !html.includes('<body class="video-cut"'),
  "Experiment, Plot, Method, and Validation are reachable without shared video-cut hiding.",
);

check(
  "Visible angle and geometry definitions",
  html.includes("Bragg glancing angle") &&
    html.includes("total beam deflection") &&
    html.includes("x and y are different observables") &&
    html.includes("no small-angle approximation") &&
    html.includes("negligible kinetic energy"),
  "The Method explicitly defines theta, phi=2theta, x, y, and the official assumptions.",
);

check(
  "Evidence-driven live diagnostics",
  [
    "data-live-diagnostics",
    "data-diagnostic-voltage",
    "data-diagnostic-wavelength",
    "data-d1-theta",
    "data-d1-phi",
    "data-d1-live-radius",
    "data-d2-theta",
    "data-d2-phi",
    "data-d2-live-radius",
  ].every((marker) => html.includes(marker)) &&
    diffractionScript.includes("updateDiagnostics") &&
    diffractionScript.includes("phiRad / 2"),
  "Both first-order families expose live theta, phi, q, and photographic radius from checked evidence.",
);

check(
  "Controlled sweep reset and export",
  html.includes("data-sweep-toggle") &&
    html.includes("data-reset-model") &&
    html.includes("data-export-csv") &&
    diffractionScript.includes("startSweep") &&
    diffractionScript.includes("pauseSweep") &&
    diffractionScript.includes("setVoltage(3000)") &&
    diffractionScript.includes("buildExportCsv"),
  "Task 6 provides a pausable 1-5 kV sweep, a 3 kV reset, and evidence-derived CSV export.",
);

check(
  "Judge-facing validation evidence",
  html.includes("42/42 Python tests") &&
    html.includes("39/39 independent physics checks") &&
    html.includes("15/15 static website checks") &&
    html.includes("Internal consistency recovery") &&
    html.includes("data-d1-theoretical-gradient") &&
    html.includes("data-d2-theoretical-gradient") &&
    html.includes("data-d1-intercept") &&
    html.includes("data-d2-intercept") &&
    diffractionScript.includes("populateValidationEvidence"),
  "Visible validation distinguishes physical derivation, fitted evidence, and implementation checks.",
);

check(
  "Loaded advanced relativistic extension",
  html.includes('src="../assets/task-06-relativity.js') &&
    html.includes("Advanced Extension — Relativistic Correction") &&
    html.indexOf('src="../assets/task-06-relativity.js') >
      html.indexOf('src="../assets/task-06-diffraction.js'),
  "The validated relativistic comparison is explicitly secondary and its browser module is loaded.",
);

const extensionRecords = relativisticExtension.records;
check(
  "Validated relativistic precision extension",
  relativisticExtension.schema_version === "task06-relativistic-extension-v1" &&
    relativisticExtension.status ===
      "secondary precision extension; official baseline preserved" &&
    relativisticExtension.validation?.passed === true &&
    relativisticExtension.validation?.check_count === 10 &&
    relativisticExtension.validation?.checks.every((entry) => entry.passed === true) &&
    extensionRecords.length === 401 &&
    extensionRecords.every((record, index) => {
      const baseline = sweep[index];
      const voltage = 1000 + index * 10;
      const kinetic = constants.elementary_charge_c * voltage;
      const expectedRelativistic =
        (constants.planck_constant_j_s * speedOfLightMPerS) /
        Math.sqrt(
          kinetic *
            (kinetic +
              2 *
                constants.electron_mass_kg *
                speedOfLightMPerS ** 2),
        );
      return (
        record.voltage_v === voltage &&
        relativeError(
          record.wavelength_nonrel_pm,
          Number(baseline.wavelength_pm),
        ) < 5e-13 &&
        relativeError(
          record.wavelength_rel_pm * 1e-12,
          expectedRelativistic,
        ) < 5e-13 &&
        record.wavelength_correction_percent < 0 &&
        record.d1.radius_shift_um < 0 &&
        record.d2.radius_shift_um < 0
      );
    }) &&
    html.includes("Relativistic comparison") &&
    html.includes("data-wavelength-correction") &&
    html.includes("relativistic_extension.json") &&
    relativityScript.includes("validateEvidence") &&
    relativityScript.includes("firstOrderRadiusM"),
  "401 relativistic records pass 10/10 checks while reproducing every official non-relativistic baseline wavelength.",
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
    diffractionScript.includes('new CustomEvent("task06:voltage"') &&
    diffractionScript.includes("data-voltage-preset"),
  "Slider, presets, family controls, chart-point selection, and keyboard voltage stepping are implemented.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-screen-loading") &&
    html.includes("data-screen-error") &&
    html.includes("data-validation-error") &&
    evidenceLoader.includes("throw new Error") &&
    diffractionScript.includes('dataset.task06Status = "error"') &&
    diffractionScript.includes("disableControls()"),
  "Loading and local error states keep controls unavailable when checked diffraction data fail to load.",
);

check(
  "Local classical typography and restrained navigation",
  html.includes("task-06-minimal.css") &&
    html.includes("task-06-navigation.js") &&
    !html.includes("gsap.min.js") &&
    !html.includes("task-06-motion.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    minimalCss.includes('--serif: "Times New Roman"') &&
    minimalCss.includes("color-scheme: light") &&
    diffractionScript.match(/"Times New Roman"/g)?.length >= 5 &&
    navigation.includes("IntersectionObserver"),
  "The page uses a local Times-led light theme, restrained section navigation, and no motion framework.",
);

check(
  "High-DPI and idle-stable figures",
  diffractionScript.includes("canvas.clientWidth") &&
    diffractionScript.includes("canvas.clientHeight") &&
    diffractionScript.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    relativityScript.includes("canvas.clientWidth") &&
    relativityScript.includes("canvas.clientHeight") &&
    relativityScript.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !diffractionScript.includes("requestAnimationFrame(draw") &&
    !diffractionScript.includes("setInterval(") &&
    !relativityScript.includes("setInterval("),
  "All three canvases render at up to 2x density and perform no continuous idle repaint.",
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
  minimalCss.includes("100dvh") &&
    minimalCss.includes("@media (max-width: 620px)") &&
    minimalCss.includes("@media (prefers-reduced-motion: reduce)") &&
    diffractionScript.includes("pagehide") &&
    relativityScript.includes("pagehide"),
  "Dynamic viewport, mobile layouts, reduced-motion handling, and cleanup paths are present.",
);

check(
  "Honest extension and intensity boundary",
  html.includes("non-relativistic result remains the baseline") &&
    html.includes("Negative Δx means") &&
    html.includes("Width and glow are schematic") &&
    !html.includes("Automatic ring animation") &&
    !relativityScript.includes("requestAnimationFrame") &&
    !relativityScript.includes("setInterval("),
  "The implemented precision comparison remains secondary, quantitative, and separate from unmodelled intensity or decorative motion.",
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
