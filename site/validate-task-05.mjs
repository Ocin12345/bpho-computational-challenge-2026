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
  atlasScript,
  evidenceLoader,
  motion,
  taskIndex,
  levelText,
  transitionText,
  limitText,
  validation,
  manifest,
  requiredPng,
  requiredSvg,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-05.html"),
  readText("site/assets/task-05.css"),
  readText("site/assets/task-05-atlas.js"),
  readText("site/assets/task-05-evidence.js"),
  readText("site/assets/task-05-motion.js"),
  readText("site/tasks.html"),
  readText("data/task05/energy_levels.csv"),
  readText("data/task05/emission_transitions.csv"),
  readText("data/task05/series_limits.csv"),
  readJson("data/task05/validation_report.json"),
  readJson("data/task05/reproducibility_manifest.json"),
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
const constants = manifest.constants;

check(
  "Accepted validation report",
  validation.schema_version === "task05-validation-v1" &&
    validation.passed === true &&
    validation.checks.length === 30 &&
    validation.checks.every((entry) => entry.passed === true),
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} independent checks pass.`,
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
    }),
  "Five finite-series destinations agree with E∞=ER/nf² and λ∞=nf²/R∞.",
);

check(
  "Complete required website content",
  [
    'id="energy-level-stage"',
    'id="emission-energy-chart"',
    'id="transition-selector"',
    'data-series="Lyman"',
    'data-series="Balmer"',
    'data-visible-only',
    "Forty-five emissions",
    "Equal line heights show wavelength position",
    "photon_energy_vs_wavelength.svg",
    "bohr_energy_level_diagram.svg",
    "balmer_visible_spectrum.svg",
    "hydrogen_series_convergence.svg",
    "30/30 independent checks",
  ].every((marker) => html.includes(marker)),
  "The required graph, level model, complete explorer, Balmer window, convergence, evidence, and downloads are present.",
);

check(
  "Interactive and keyboard-complete atlas",
  atlasScript.includes("handleChartPointerMove") &&
    atlasScript.includes("handleChartKeydown") &&
    atlasScript.includes('"ArrowLeft"') &&
    atlasScript.includes('"ArrowRight"') &&
    atlasScript.includes('"Home"') &&
    atlasScript.includes('"End"') &&
    atlasScript.includes("transitionSelector.addEventListener") &&
    atlasScript.includes("ResizeObserver") &&
    atlasScript.includes("state.visibleOnly"),
  "Pointer, select, previous/next, series filter, visible-window toggle, and keyboard navigation are implemented.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-instrument-loading") &&
    html.includes("data-instrument-error") &&
    html.includes("data-atlas-error") &&
    html.includes('data-locked="false"') &&
    evidenceLoader.includes("throw new Error") &&
    atlasScript.includes('dataset.task05Status = "error"') &&
    atlasScript.includes('dataset.locked = "false"') &&
    atlasScript.includes("disableControls()"),
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
    atlasScript.match(/"Times New Roman"/g)?.length >= 8,
  "Pinned local interface fonts and motion are used; all scientific canvas text uses Times New Roman.",
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
  css.includes("100dvh") &&
    css.includes("@media (max-width: 767px)") &&
    css.includes("@media (max-width: 410px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)") &&
    motion.includes("prefers-reduced-motion: reduce") &&
    motion.includes("pagehide"),
  "Dynamic viewport, strict mobile layouts, reduced-motion handling, and cleanup paths are present.",
);

check(
  "Honest extension boundary",
  html.includes("A classical “electron orbit” animation was intentionally deferred") &&
    html.includes("Equal line strength") &&
    html.includes("Preferred future extension") &&
    !html.includes("electron-orbit animation"),
  "The page explains why decorative orbital motion and unmodelled spectral claims are excluded.",
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
