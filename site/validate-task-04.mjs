#!/usr/bin/env node

import assert from "node:assert/strict";
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
  simulation,
  evidenceLoader,
  motion,
  taskIndex,
  cutoffText,
  validation,
  manifest,
] = await Promise.all([
  readText("site/tasks/task-04.html"),
  readText("site/assets/task-04.css"),
  readText("site/assets/task-04-simulation.js"),
  readText("site/assets/task-04-evidence.js"),
  readText("site/assets/task-04-motion.js"),
  readText("site/tasks.html"),
  readText("data/task04/material_cutoffs.csv"),
  readJson("data/task04/validation_report.json"),
  readJson("data/task04/reproducibility_manifest.json"),
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

const materials = parseCsv(cutoffText);
const constants = manifest.constants;

check(
  "Accepted validation report",
  validation.schema_version === "task04-v1" &&
    validation.passed === true &&
    validation.checks.length === 43 &&
    validation.checks.every((entry) => entry.passed === true),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} independent checks pass.`,
);

check(
  "Official nine-metal table",
  materials.length === 9 &&
    manifest.official_materials.length === 9 &&
    materials.every((material, index) => {
      const official = manifest.official_materials[index];
      return (
        material.material === official.name &&
        material.symbol === official.symbol &&
        Number(material.work_function_ev) === official.work_function_ev
      );
    }),
  `${materials.length} cut-off records match the frozen official order.`,
);

check(
  "Analytical cut-offs",
  materials.every((material) => {
    const workFunction = Number(material.work_function_ev);
    const expectedFrequency = workFunction / constants.planck_over_charge_v_s;
    const expectedWavelength =
      (constants.speed_of_light_m_s / expectedFrequency) * 1e9;
    const frequencyError =
      Math.abs(Number(material.cutoff_frequency_hz) - expectedFrequency) /
      expectedFrequency;
    const wavelengthError =
      Math.abs(Number(material.cutoff_wavelength_nm) - expectedWavelength) /
      expectedWavelength;
    return frequencyError < 5e-13 && wavelengthError < 5e-13;
  }),
  "Every stored f0=W/h and lambda0=hc/W agrees within 5e-13 relative error.",
);

const overlap = materials.filter((material) =>
  ["Ag", "Al", "Pb"].includes(material.symbol),
);
check(
  "Honest overlapping materials",
  overlap.length === 3 &&
    new Set(overlap.map((material) => material.work_function_ev)).size === 1 &&
    new Set(overlap.map((material) => material.cutoff_frequency_hz)).size === 1 &&
    new Set(overlap.map((material) => material.cutoff_wavelength_nm)).size === 1 &&
    html.includes("Ag, Al and Pb overlap exactly") &&
    simulation.includes("Ag = Al = Pb exactly"),
  "Ag, Al and Pb share the supplied 4.3 eV work function and are labelled as one overlap.",
);

check(
  "Complete required and extension content",
  [
    'id="photoelectric-stage"',
    'id="stopping-potential-chart"',
    'data-threshold-preset="below"',
    'data-threshold-preset="at"',
    'data-threshold-preset="above"',
    'data-axis-mode="frequency"',
    'data-axis-mode="wavelength"',
    "Show mathematical extrapolation",
    "43 independent checks",
    "photoelectric_demo.gif",
    "stopping_voltage_frequency.svg",
    "stopping_voltage_wavelength.svg",
    "Intensity changes the illustrative emission rate",
  ].every((marker) => html.includes(marker)),
  "The required graph, threshold states, model boundary, evidence, and optional extension are present.",
);

check(
  "Local dependency and typography policy",
  html.includes("../vendor/packages/gsap/dist/gsap.min.js") &&
    html.includes("../vendor/packages/gsap/dist/ScrollTrigger.min.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    css.includes('"Geist"') &&
    css.includes('"Bodoni Moda Variable"') &&
    css.includes('--figure: "Times New Roman"') &&
    !css.includes('"Inter"'),
  "Pinned local motion and fonts are used; scientific canvases use Times New Roman.",
);

check(
  "High-DPI interactive figures",
  simulation.includes("canvas.clientWidth") &&
    simulation.includes("canvas.clientHeight") &&
    simulation.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    simulation.match(/"Times New Roman"/g)?.length >= 8,
  "Both canvases size from CSS pixels and render at up to 2x density.",
);

check(
  "Fail-closed evidence states",
  html.includes("data-chamber-loading") &&
    html.includes("data-chamber-error") &&
    html.includes("data-chart-error") &&
    html.includes('data-locked="false"') &&
    evidenceLoader.includes("throw new Error") &&
    simulation.includes('dataset.task04Status = "error"') &&
    simulation.includes('dataset.locked = "false"'),
  "Loading, success, and explicit unlocked error states are implemented.",
);

check(
  "Responsive and reduced-motion safeguards",
  css.includes("100dvh") &&
    css.includes("@media (max-width: 767px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)") &&
    motion.includes("prefers-reduced-motion: reduce") &&
    motion.includes("pagehide"),
  "Dynamic viewport, strict mobile, reduced-motion, and cleanup paths are present.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-04\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-04"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 4 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(`\n${checks.length - failed.length}/${checks.length} Task 4 website checks passed.`);

if (failed.length) process.exitCode = 1;
