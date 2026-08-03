#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const root = dirname(here);

const paths = {
  evidence: join(here, "data", "task-03-evidence.json"),
  html: join(here, "tasks", "task-03.html"),
  css: join(here, "assets", "task-03.css"),
  simulation: join(here, "assets", "task-03-simulation.js"),
  evidenceScript: join(here, "assets", "task-03-evidence.js"),
  motionScript: join(here, "assets", "task-03-motion.js"),
  vendorPackage: join(here, "vendor", "package.json"),
  vendorLock: join(here, "vendor", "package-lock.json"),
  taskIndex: join(here, "tasks.html"),
  sourceValidation: join(root, "data", "task03", "validation_report.json"),
};

const [
  evidenceText,
  html,
  css,
  simulation,
  evidenceScript,
  motionScript,
  vendorPackageText,
  vendorLockText,
  taskIndex,
  sourceText,
] =
  await Promise.all(Object.values(paths).map((path) => readFile(path, "utf8")));
const evidence = JSON.parse(evidenceText);
const sourceValidation = JSON.parse(sourceText);
const vendorPackage = JSON.parse(vendorPackageText);
const vendorLock = JSON.parse(vendorLockText);

const relativeError = (observed, expected) =>
  Math.abs(observed - expected) / Math.abs(expected);
const round4 = (value) => Number(value.toFixed(4));

assert.equal(evidence.schema_version, 1);
assert.equal(evidence.task, "03");
assert.equal(evidence.validation.passed, true);
assert.equal(evidence.validation.passed_checks, 27);
assert.equal(evidence.validation.total_checks, 27);
assert.equal(sourceValidation.passed, true);
assert.equal(sourceValidation.checks.length, 27);
assert.ok(sourceValidation.checks.every((check) => check.passed));
assert.equal(evidence.generated_from.length, 6);

const constants = evidence.constants;
for (const temperature of [4000, 5000, 6000]) {
  const series = evidence.planck.series[String(temperature)];
  const validation = evidence.planck.validation.find(
    (row) => row.temperature_k === temperature,
  );
  assert.equal(series.length, 581);
  assert.ok(
    series.every(
      (point) =>
        Number.isFinite(point.wavelength_nm) &&
        Number.isFinite(point.exitance_w_m2_nm) &&
        Number.isFinite(point.radiance_w_m2_sr_nm) &&
        point.exitance_w_m2_nm >= 0,
    ),
  );
  for (let index = 1; index < series.length; index += 1) {
    assert.ok(series[index].wavelength_nm > series[index - 1].wavelength_nm);
  }
  assert.ok(
    series.every(
      (point) =>
        relativeError(
          point.exitance_w_m2_nm,
          Math.PI * point.radiance_w_m2_sr_nm,
        ) < 1e-12,
    ),
  );

  const wienPeakNm =
    (constants.wien_displacement_m_k / temperature) * 1e9;
  const exactExitance =
    constants.stefan_boltzmann_w_m2_k4 * temperature ** 4;
  assert.ok(relativeError(validation.wien_peak_nm, wienPeakNm) < 1e-12);
  assert.ok(
    relativeError(validation.stefan_boltzmann_w_m2, exactExitance) < 1e-12,
  );
  assert.ok(
    relativeError(
      validation.stefan_boltzmann_radiance_w_m2_sr,
      exactExitance / Math.PI,
    ) < 1e-12,
  );
  assert.ok(
    relativeError(
      validation.numerical_exitance_w_m2,
      Math.PI * validation.numerical_radiance_w_m2_sr,
    ) < 1e-12,
  );
  assert.ok(validation.peak_relative_error < 1e-5);
  assert.ok(validation.integral_relative_error < 2e-9);
}

assert.equal(evidence.einstein.materials.length, 7);
assert.ok(
  Math.abs(
    evidence.einstein.high_temperature_limit_j_mol_k -
      3 * constants.gas_constant_j_mol_k,
  ) < 1e-12,
);

for (const material of evidence.einstein.materials) {
  const series = evidence.einstein.series[material.symbol];
  const normalized = evidence.einstein.normalized_series[material.symbol];
  assert.equal(series.length, 201);
  assert.equal(normalized.length, 201);
  assert.equal(series[0].temperature_k, 0);
  assert.equal(series[0].cv_j_mol_k, 0);
  assert.ok(
    series.every(
      (point) =>
        point.cv_j_mol_k >= 0 &&
        point.cv_j_mol_k <=
          evidence.einstein.high_temperature_limit_j_mol_k,
    ),
  );
  for (let index = 1; index < series.length; index += 1) {
    assert.ok(series[index].cv_j_mol_k >= series[index - 1].cv_j_mol_k);
  }

  const frequencyFromTemperature =
    (constants.boltzmann_j_k * material.einstein_temperature_k) /
    constants.planck_j_s;
  assert.ok(
    relativeError(material.einstein_frequency_hz, frequencyFromTemperature) <
      1e-10,
  );
  assert.equal(
    round4(material.einstein_frequency_hz / 1e13),
    material.official_frequency_1e13_hz,
  );
}

const normalizedSymbols = Object.keys(
  evidence.einstein.normalized_series,
);
const normalizedReference =
  evidence.einstein.normalized_series[normalizedSymbols[0]];
for (const symbol of normalizedSymbols.slice(1)) {
  const series = evidence.einstein.normalized_series[symbol];
  const largestDifference = Math.max(
    ...series.map((point, index) =>
      Math.abs(point.cv_over_3r - normalizedReference[index].cv_over_3r),
    ),
  );
  assert.ok(largestDifference <= 1e-12);
}

[
  'id="planck-live-chart"',
  'id="einstein-chart"',
  'id="planck-evidence-chart"',
  'id="einstein-collapse-chart"',
  'data-temperature-preset="4000"',
  'data-planck-quantity="radiance"',
  'data-planck-quantity="exitance"',
  'data-evidence-quantity="radiance"',
  'data-evidence-quantity="exitance"',
  'data-material="C"',
  "Required Planck radiance",
  "Every item in the Task 3 brief",
  "gold, copper and iron",
  "../data/task-03-evidence.js",
  "../assets/task-03-simulation.js",
  "../assets/task-03-evidence.js",
  "../assets/task-03-motion.js",
  "../vendor/packages/gsap/dist/gsap.min.js",
  "ScrollTrigger.min.js",
  'class="spectrum-scan"',
  "orb-orbit--one",
  'class="constants-marquee"',
  'class="einstein-scroll-layout"',
  'class="validation-carousel"',
  'data-verdict-slide',
  'class="action-chapter"',
  "../../data/task03/validation_report.json",
].forEach((marker) => assert.ok(html.includes(marker), `Missing ${marker}`));

assert.equal(vendorPackage.dependencies.gsap, "3.15.0");
assert.equal(vendorPackage.dependencies.geist, "1.7.2");
assert.equal(vendorPackage.dependencies["@fontsource-variable/bodoni-moda"], "5.3.0");
assert.equal(vendorPackage.dependencies["@fontsource-variable/cormorant"], "5.3.0");
assert.equal(vendorLock.lockfileVersion, 3);

assert.ok(taskIndex.includes('href="./tasks/task-03.html"'));
assert.ok(
  /class="task-row is-ready"\s+href="\.\/tasks\/task-03\.html"/m.test(
    taskIndex,
  ),
);
assert.ok(
  taskIndex.includes(
    "Task 01 through Task 10 laboratories are open.",
  ),
);
assert.ok(!/href="#task-03"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex));

assert.ok(css.includes('--figure: "Times New Roman"'));
assert.ok(css.includes('font-family: "Geist"'));
assert.ok(css.includes("Geist-Variable.woff2"));
assert.ok(css.includes("grid-template-columns: repeat(6, minmax(0, 1fr))"));
assert.ok(css.includes("grid-auto-flow: dense"));
assert.ok(css.includes("@keyframes constants-marquee"));
assert.ok(css.includes(".material-selector button.is-active"));
assert.ok(css.includes("@media (max-width: 900px)"));
assert.ok(css.includes("@media (max-width: 620px)"));
assert.ok(css.includes("@media (prefers-reduced-motion: reduce)"));
assert.ok(!html.includes("family=Inter"));
assert.ok(!css.includes('--sans: "Inter"'));
assert.ok(!html.includes("01 ·"));
assert.ok(!html.includes("02 ·"));
assert.ok(!html.includes("03 ·"));
assert.ok(simulation.includes('"Times New Roman"'));
assert.ok(evidenceScript.includes('"Times New Roman"'));
assert.ok(simulation.includes("Math.expm1"));
assert.ok(evidenceScript.includes("normalized_series"));
assert.ok(evidenceScript.includes("runMaterialTransition"));
assert.ok(evidenceScript.includes("startEvidenceReveal"));
assert.ok(motionScript.includes("IntersectionObserver"));
assert.ok(motionScript.includes("prefers-reduced-motion"));
assert.ok(motionScript.includes("gsap.registerPlugin(ScrollTrigger)"));
assert.ok(motionScript.includes("pin: heading"));
assert.ok(motionScript.includes("data-verdict-slide"));
assert.ok(simulation.includes("animateTemperatureTo"));
assert.ok(simulation.includes("Math.sin(phase)"));

console.log("Task 03 website validation passed.");
console.log("  scientific source: 27 / 27 checks");
console.log("  Planck web series: 3 × 581 points");
console.log("  Einstein web series: 7 × 201 points");
console.log("  normalized curves: 7 × 201 points");
console.log("  index, controls, downloads, fonts and responsive rules: present");
