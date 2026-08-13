#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const root = dirname(here);

const paths = {
  evidence: join(here, "data", "task-03-evidence.json"),
  debyeEvidence: join(here, "data", "task-03-debye-validation.json"),
  html: join(here, "tasks", "task-03.html"),
  css: join(here, "assets", "task-03.css"),
  minimalCss: join(here, "assets", "task-03-minimal.css"),
  simulation: join(here, "assets", "task-03-simulation.js"),
  extensionScript: join(here, "assets", "task-03-extension.js"),
  evidenceScript: join(here, "assets", "task-03-evidence.js"),
  navigationScript: join(here, "assets", "task-03-navigation.js"),
  taskIndex: join(here, "tasks.html"),
  sourceValidation: join(root, "data", "task03", "validation_report.json"),
};

const [
  evidenceText,
  debyeEvidenceText,
  html,
  css,
  minimalCss,
  simulation,
  extensionScript,
  evidenceScript,
  navigationScript,
  taskIndex,
  sourceText,
] =
  await Promise.all(Object.values(paths).map((path) => readFile(path, "utf8")));
const evidence = JSON.parse(evidenceText);
const debyeEvidence = JSON.parse(debyeEvidenceText);
const sourceValidation = JSON.parse(sourceText);

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

assert.equal(debyeEvidence.schema_version, 1);
assert.equal(debyeEvidence.accepted, true);
assert.equal(debyeEvidence.materials.length, 7);
assert.equal(debyeEvidence.curve.length, 251);
assert.equal(debyeEvidence.diagnostics.length, 6);
assert.equal(debyeEvidence.curve[0].debye_over_3r, 0);
assert.equal(debyeEvidence.curve[0].einstein_over_3r, 0);
assert.ok(
  debyeEvidence.curve
    .slice(1)
    .every(
      (point) =>
        point.debye_over_3r > point.einstein_over_3r &&
        point.debye_over_3r <= 1,
    ),
);
assert.ok(debyeEvidence.checks.low_temperature_cubic_relative_error < 1e-10);
assert.ok(debyeEvidence.checks.high_temperature_series_relative_error < 1e-12);
assert.ok(debyeEvidence.checks.quadrature_convergence_over_3r < 1e-11);

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
  'id="spectrum"',
  'id="einstein"',
  'id="method"',
  'id="validation"',
  'id="extension"',
  'aria-labelledby="debye-title" hidden',
  'class="section-nav"',
  'class="task-identity"',
  'data-temperature-preset="4000"',
  'data-planck-quantity="radiance"',
  'data-planck-quantity="exitance"',
  'data-planck-mode="single"',
  'data-planck-mode="compare"',
  'data-planck-legend',
  'data-material="C"',
  'data-evidence-content',
  'data-check-count',
  'data-wien-error',
  'data-integral-error',
  'data-collapse-error',
  'data-benchmark-body',
  'id="planck-evidence-chart"',
  'id="einstein-collapse-chart"',
  'id="debye-comparison-chart"',
  'id="debye-material"',
  'id="debye-temperature-ratio"',
  "From Einstein to Debye",
  "C<sub>V</sub> ∝ T<sup>3</sup>",
  "Required Planck radiance",
  "Einstein heat capacity",
  "../assets/task-03-simulation.js",
  "../assets/task-03-navigation.js",
  "../assets/task-03-minimal.css",
  "../assets/task-video.css",
  'class="video-cut"',
  'data-task="03"',
  'class="einstein-scroll-layout"',
].forEach((marker) => assert.ok(html.includes(marker), `Missing ${marker}`));

assert.ok(!html.includes('href="#extension"'));
assert.ok(html.includes("../assets/task-03-evidence.js"));
assert.ok(html.includes("Reference validation"));
assert.ok(html.includes("Material provenance"));

[
  "../assets/task-03-motion.js",
  "gsap.min.js",
  "ScrollTrigger.min.js",
  'class="validation-carousel"',
  'class="action-chapter"',
].forEach((marker) => assert.ok(!html.includes(marker), `Redundant ${marker}`));

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
assert.ok(css.includes(".material-selector button.is-active"));
assert.ok(css.includes("@media (max-width: 900px)"));
assert.ok(css.includes("@media (max-width: 620px)"));
assert.ok(css.includes("@media (prefers-reduced-motion: reduce)"));
assert.ok(minimalCss.includes('--serif: "Times New Roman"'));
assert.ok(minimalCss.includes(".section-nav"));
assert.ok(minimalCss.includes(".radiation-hero"));
assert.ok(minimalCss.includes(".einstein-workbench"));
assert.ok(minimalCss.includes(".debye-laboratory"));
assert.ok(minimalCss.includes(".debye-workspace"));
assert.ok(minimalCss.includes("#debye-comparison-chart"));
assert.ok(minimalCss.includes(".evidence-metrics"));
assert.ok(minimalCss.includes("@media (max-width: 760px)"));
assert.ok(minimalCss.includes("@media (prefers-reduced-motion: reduce)"));
assert.ok(!html.includes("family=Inter"));
assert.ok(!css.includes('--sans: "Inter"'));
assert.ok(!html.includes("01 ·"));
assert.ok(!html.includes("02 ·"));
assert.ok(!html.includes("03 ·"));
assert.ok(simulation.includes('"Times New Roman"'));
assert.ok(evidenceScript.includes('"Times New Roman"'));
assert.ok(simulation.includes("Math.expm1"));
assert.ok(extensionScript.includes("task-03-debye-validation.json"));
assert.ok(extensionScript.includes("window.devicePixelRatio"));
assert.ok(extensionScript.includes("interpolateCurve"));
assert.ok(!html.includes("Validation JSON"));
assert.ok(!minimalCss.includes("linear-gradient"));
assert.ok(!minimalCss.includes("radial-gradient"));
assert.ok(evidenceScript.includes("normalized_series"));
assert.ok(evidenceScript.includes("runMaterialTransition"));
assert.ok(evidenceScript.includes("startEvidenceReveal"));
assert.ok(navigationScript.includes("IntersectionObserver"));
assert.ok(navigationScript.includes("aria-current"));
assert.ok(simulation.includes("animateTemperatureTo"));
assert.ok(simulation.includes("Math.sin(phase)"));
assert.ok(simulation.includes('document.addEventListener("visibilitychange"'));

console.log("Task 03 website validation passed.");
console.log("  scientific source: 27 / 27 checks");
console.log("  Planck web series: 3 × 581 points");
console.log("  Einstein web series: 7 × 201 points");
console.log("  normalized curves: 7 × 201 points");
console.log("  Debye extension retained outside filming path: 251 validated normalized points across 7 solids");
console.log("  focused layout, controls, downloads and responsive rules: present");
