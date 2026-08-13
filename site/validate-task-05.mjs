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
  goldCss,
  atlasScript,
  extensionScript,
  evidenceLoader,
  navigation,
  taskIndex,
  levelText,
  transitionText,
  limitText,
  validation,
  manifest,
  extensionTransitionText,
  extensionEvidence,
  requiredPng,
  requiredSvg,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-05.html"),
  readText("site/assets/task-05.css"),
  readText("site/assets/task-05-minimal.css"),
  readText("site/assets/task-05-gold.css").catch(() => ""),
  readText("site/assets/task-05-atlas.js"),
  readText("site/assets/task-05-extension.js"),
  readText("site/assets/task-05-evidence.js"),
  readText("site/assets/task-05-navigation.js"),
  readText("site/tasks.html"),
  readText("data/task05/energy_levels.csv"),
  readText("data/task05/emission_transitions.csv"),
  readText("data/task05/series_limits.csv"),
  readJson("data/task05/validation_report.json"),
  readJson("data/task05/reproducibility_manifest.json"),
  readText("data/task05/reduced_mass_transitions.csv"),
  readJson("data/task05/reduced_mass_validation.json"),
  readFile(resolve(projectRoot, "figures/task05/photon_energy_vs_wavelength.png")),
  readText("figures/task05/photon_energy_vs_wavelength.svg"),
  readText("task05_hydrogen_spectrum/plotting.py"),
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

const levels = parseCsv(levelText);
const transitions = parseCsv(transitionText);
const limits = parseCsv(limitText);
const extensionTransitions = parseCsv(extensionTransitionText);
const constants = manifest.constants;

check(
  "Accepted reduced-mass extension evidence",
  extensionEvidence.schema_version === "task05-reduced-mass-v1" &&
    extensionEvidence.status === "accepted_optional_extension" &&
    extensionEvidence.baseline_model ===
      "ideal stationary-nucleus Bohr hydrogen" &&
    extensionEvidence.validation.passed === true &&
    extensionEvidence.validation.check_count === 12 &&
    extensionEvidence.validation.checks.length === 12 &&
    extensionEvidence.validation.checks.every((entry) => entry.passed) &&
    extensionTransitions.length === 45,
  `${extensionEvidence.validation.checks.filter((entry) => entry.passed).length}/12 separate extension checks pass for all ${extensionTransitions.length} transitions.`,
);

check(
  "Reduced-mass physics identities",
  extensionTransitions.every((transition) => {
    const ratio = extensionEvidence.constants.electron_proton_mass_ratio;
    const factor = extensionEvidence.constants.reduced_mass_factor;
    const idealEnergy = Number(transition.ideal_energy_ev);
    const correctedEnergy = Number(transition.corrected_energy_ev);
    const idealWavelength = Number(transition.ideal_wavelength_nm);
    const correctedWavelength = Number(transition.corrected_wavelength_nm);
    return (
      correctedEnergy < idealEnergy &&
      correctedWavelength > idealWavelength &&
      relativeError(correctedEnergy, idealEnergy * factor) < 5e-13 &&
      relativeError(correctedWavelength, idealWavelength * (1 + ratio)) <
        5e-13 &&
      relativeError(correctedEnergy * correctedWavelength, constants.hc_ev_nm) <
        5e-13
    );
  }),
  "Every extension line follows the CODATA electron-proton mass ratio, lengthens wavelength, lowers energy, and preserves Eλ=hc.",
);

check(
  "Accepted validation report",
  validation.schema_version === "task05-validation-v1" &&
    validation.passed === true &&
    validation.checks.length === 30 &&
    validation.checks.every((entry) => entry.passed === true) &&
    [
      'id="validation"',
      "Energy-scale invariant",
      "Independent Rydberg route",
      "Formula consistency, not experiment",
      "58/58",
      'data-validation-transitions',
      'data-rydberg-residual',
      'data-energy-scale',
    ].every((marker) => html.includes(marker)) &&
    atlasScript.includes("populateValidationEvidence") &&
    atlasScript.includes("rydberg_constant_per_m"),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} checks pass and their formula-consistency evidence is exposed on-page.`,
);

check(
  "Complete Bohr catalogue",
  levels.length === 10 &&
    levels.every(
      (level, index) =>
        Number(level.n) === index + 1 &&
        relativeError(
          Number(level.energy_ev),
          -constants.rydberg_energy_ev / (index + 1) ** 2,
        ) < 5e-13,
    ) &&
    transitions.length === 45 &&
    new Set(
      transitions.map(
        (transition) => `${transition.initial_n}-${transition.final_n}`,
      ),
    ).size === 45,
  "Ten exact levels and all 45 unique downward pairs are present.",
);

check(
  "Photon identities and classification",
  transitions.every((transition) => {
    const initial = Number(transition.initial_n);
    const final = Number(transition.final_n);
    const energy = Number(transition.photon_energy_ev);
    const wavelength = Number(transition.wavelength_nm);
    const frequency = Number(transition.frequency_hz);
    const expectedEnergy =
      constants.rydberg_energy_ev * (1 / final ** 2 - 1 / initial ** 2);
    const expectedRegion =
      wavelength < 380 ? "ultraviolet" : wavelength <= 750 ? "visible" : "infrared";
    return (
      initial > final &&
      energy > 0 &&
      relativeError(energy, expectedEnergy) < 5e-13 &&
      relativeError(energy * wavelength, constants.hc_ev_nm) < 5e-13 &&
      relativeError(
        frequency * Number(transition.wavelength_m),
        constants.speed_of_light_m_s,
      ) < 5e-13 &&
      transition.spectral_region === expectedRegion
    );
  }),
  "Every stored emission satisfies ΔE, Eλ=hc, fλ=c, and the declared 380–750 nm convention.",
);

check(
  "Analytical series limits",
  limits.length === 5 &&
    limits.every((limit, index) => {
      const final = index + 1;
      return (
        Number(limit.final_n) === final &&
        relativeError(
          Number(limit.limit_energy_ev),
          constants.rydberg_energy_ev / final ** 2,
        ) < 5e-13 &&
        relativeError(
          Number(limit.limit_wavelength_nm),
          (final ** 2 / constants.rydberg_constant_per_m) * 1e9,
        ) < 5e-13
      );
    }) &&
    [
      "approximate screen colour",
      "neutral pseudocolours",
      "Equal line heights",
      "hydrogen_series_convergence.svg",
      'id="convergence"',
    ].every((marker) => html.includes(marker)) &&
    atlasScript.includes('if (wavelengthNm < 380) return "#64748b"') &&
    atlasScript.includes('if (wavelengthNm > 750) return "#8a8178"') &&
    atlasScript.includes("formatRegion"),
  "Five analytical limits are exposed with honest visible-colour and UV/IR pseudocolour conventions.",
);

check(
  "Judge-facing method and model boundary",
  [
    'href="#spectrum"',
    'href="#atlas"',
    'href="#balmer"',
    'href="#model"',
    'href="#validation"',
    'id="energy-level-stage"',
    'id="emission-energy-chart"',
    'id="transition-selector"',
    'id="model"',
    "Method",
    "ideal calculated vacuum wavelengths",
    "656.112 nm",
    "stationary,",
    "infinitely massive proton",
    "Lyman",
    "Balmer",
    "Paschen",
    "Brackett",
    "Pfund",
    'data-download-transition-csv',
  ].every((marker) => html.includes(marker)) &&
    !html.includes('class="video-cut"'),
  "The five-route judge navigation exposes the ideal-model method, series map, H-alpha anchor, model boundary, and catalogue download.",
);

check(
  "Interactive atlas and synchronized line spectrum",
  atlasScript.includes("handleChartPointerMove") &&
    atlasScript.includes("handleChartKeydown") &&
    atlasScript.includes('"ArrowLeft"') &&
    atlasScript.includes('"ArrowRight"') &&
    atlasScript.includes('"Home"') &&
    atlasScript.includes('"End"') &&
    atlasScript.includes("transitionSelector.addEventListener") &&
    atlasScript.includes("ResizeObserver") &&
    atlasScript.includes("state.visibleOnly") &&
    atlasScript.includes("updateBalmerSelection") &&
    atlasScript.includes("data-transition-index") &&
    atlasScript.includes("downloadTransitionCsv"),
  "Pointer, keyboard, filters, transition controls, selected-line highlighting, and CSV export are implemented.",
);

check(
  "Visible and initialized reduced-mass extension",
  [
    'id="mass-transition-selector"',
    'id="mass-comparison-chart"',
    "When the proton is allowed to move",
    "Equal marker heights show",
    "reduced_mass_transitions.csv",
    "data-download-mass-chart",
  ].every((marker) => html.includes(marker)) &&
    extensionScript.includes("validateEvidence") &&
    extensionScript.includes("ResizeObserver") &&
    extensionScript.includes("canvas.toBlob") &&
    extensionScript.includes('dataset.task05ExtensionStatus = "ready"') &&
    !extensionScript.includes("requestAnimationFrame") &&
    !extensionScript.includes("setInterval(") &&
    html.includes('data-task="05"') &&
    html.includes("../assets/task-05-extension.js") &&
    goldCss.includes(".extension-section"),
  "The accepted 45-line moving-proton comparison is loaded, validated, visible, and downloadable.",
);

check(
  "Fail-closed evidence state without dormant loading",
  html.includes("data-instrument-loading") &&
    html.includes("data-instrument-error") &&
    html.includes("data-atlas-error") &&
    evidenceLoader.includes("throw new Error") &&
    atlasScript.includes('dataset.task05Status = "error"') &&
    atlasScript.includes("disableControls()") &&
    extensionScript.includes('dataset.task05ExtensionStatus = "error"') &&
    html.includes("data-mass-error"),
  "Both evidence loaders fail closed, while the extension script resolves the visible loading state to ready or explicit error.",
);

check(
  "Local typography and restrained presentation",
    html.includes("../assets/task-05-minimal.css") &&
    html.includes("../assets/task-05-gold.css") &&
    html.includes("../assets/task-video.css") &&
    html.includes("../assets/task-05-navigation.js") &&
    !html.includes("gsap.min.js") &&
    !html.includes("ScrollTrigger.min.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    minimalCss.includes('--serif: "Times New Roman"') &&
    minimalCss.includes(".section-nav") &&
    atlasScript.match(/"Times New Roman"/g)?.length >= 8,
  "The interface uses local formal typography, simple section navigation, and no decorative motion dependency.",
);

check(
  "High-DPI and idle-stable figures",
  atlasScript.includes("canvas.clientWidth") &&
    atlasScript.includes("canvas.clientHeight") &&
    atlasScript.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !atlasScript.includes("requestAnimationFrame(draw") &&
    !atlasScript.includes("setInterval("),
  "Both canvases render at up to 2x density and perform no continuous idle repaint.",
);

const requiredWidth = requiredPng.readUInt32BE(16);
const requiredHeight = requiredPng.readUInt32BE(20);
check(
  "Original-resolution scientific figure",
  requiredWidth === 3840 &&
    requiredHeight === 2160 &&
    requiredSvg.includes("<svg") &&
    plottingSource.includes('"font.family": "Times New Roman"') &&
    requiredSvg.includes("45 declared level differences"),
  `${requiredWidth}×${requiredHeight} PNG and editable Times New Roman SVG agree with the accepted required graph.`,
);

check(
  "Responsive and reduced-motion safeguards",
  minimalCss.includes("100dvh") &&
    minimalCss.includes("@media (max-width: 760px)") &&
    minimalCss.includes("@media (prefers-reduced-motion: reduce)") &&
    navigation.includes("IntersectionObserver") &&
    minimalCss.includes(".extension-section") &&
    minimalCss.includes(".mass-table-wrap") &&
    goldCss.includes("@media (max-width: 760px)") &&
    goldCss.includes("overflow-x: auto"),
  "Dynamic viewport, mobile section navigation, validation tables, reduced motion, and section tracking are present.",
);

check(
  "Honest extension boundary",
  html.includes("leading reduced-mass correction accounts for proton motion") &&
    html.includes("Energy eigenstates are not literal planetary paths") &&
    html.includes("does not calculate line strength") &&
    html.includes("not a precision fit to measured hydrogen") &&
    !html.includes("electron-orbit animation"),
  "The reduced-mass result remains separate from the baseline and excludes orbital, intensity, linewidth, and precision-spectroscopy claims.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-05\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-05"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 5 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(
  `\n${checks.length - failed.length}/${checks.length} Task 5 website checks passed.`,
);

if (failed.length) process.exitCode = 1;
