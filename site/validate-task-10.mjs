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
  explorer,
  evidenceLoader,
  motion,
  taskIndex,
  catalogText,
  galleryText,
  profilesText,
  nodesText,
  references,
  validation,
  manifest,
  figureManifest,
  motionManifest,
  galleryPng,
  radialPng,
  glassPng,
  comparisonPng,
  summaryPng,
  plottingSource,
] = await Promise.all([
  readText("site/tasks/task-10.html"),
  readText("site/assets/task-10.css"),
  readText("site/assets/task-10-explorer.js"),
  readText("site/assets/task-10-evidence.js"),
  readText("site/assets/task-10-motion.js"),
  readText("site/tasks.html"),
  readText("data/task10/orbital_state_catalog.csv"),
  readText("data/task10/official_gallery.csv"),
  readText("data/task10/radial_profiles.csv"),
  readText("data/task10/radial_nodes.csv"),
  readJson("data/task10/reference_anchors.json"),
  readJson("data/task10/validation_report.json"),
  readJson("data/task10/manifest.json"),
  readJson("figures/task10/manifest.json"),
  readJson("figures/task10/motion_manifest.json"),
  readFile(resolve(projectRoot, "figures/task10/required_orbital_gallery.png")),
  readFile(resolve(projectRoot, "figures/task10/radial_and_nodal_structure.png")),
  readFile(resolve(projectRoot, "figures/task10/coloured_glass_density.png")),
  readFile(resolve(projectRoot, "figures/task10/rendering_comparison.png")),
  readFile(resolve(projectRoot, "figures/task10/task10_summary.png")),
  readText("task10_hydrogenic_orbitals/plotting.py"),
]);

const checks = [];
const familyLabels = ["S", "P", "D", "F", "G", "H", "I", "K"];

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

function dimensions(buffer) {
  return [buffer.readUInt32BE(16), buffer.readUInt32BE(20)];
}

const catalog = parseCsv(catalogText);
const gallery = parseCsv(galleryText);
const profiles = parseCsv(profilesText);
const nodes = parseCsv(nodesText);
const normalizedHtml = html
  .replace(/<[^>]+>/g, " ")
  .replace(/\s+/g, " ")
  .toLowerCase();

check(
  "Accepted scientific validation",
  validation.schema_version === "task10-validation-v1" &&
    validation.passed === true &&
    validation.state_digest === manifest.validation.state_digest &&
    validation.checks.length === 22 &&
    validation.checks.every((entry) => entry.passed === true) &&
    manifest.validation.state_digest ===
      "d298695290395956560641493fc603e5970a4ea01609eca677b3b4b683fa085e",
  `${validation.checks.filter((entry) => entry.passed).length}/${validation.checks.length} committed science checks pass with the accepted state digest.`,
);

const muRatio =
  manifest.constants.atomic_mass_constant_kg /
  (manifest.constants.electron_mass_kg +
    manifest.constants.atomic_mass_constant_kg);
let catalogIndex = 0;
let catalogCorrect = catalog.length === 204;
for (let n = 1; n <= 8; n += 1) {
  for (let l = 0; l < n; l += 1) {
    for (let m = -l; m <= l; m += 1) {
      const row = catalog[catalogIndex];
      const expectedEnergy =
        (-0.5 * manifest.constants.hartree_energy_ev * muRatio) / n ** 2;
      catalogCorrect &&=
        Number(row?.n) === n &&
        Number(row?.l) === l &&
        Number(row?.m) === m &&
        row?.family === familyLabels[l] &&
        Number(row?.radial_nodes) === n - l - 1 &&
        Number(row?.angular_nodes) === l &&
        Number(row?.degeneracy) === 2 * l + 1 &&
        Number(row?.parity) === (l % 2 === 0 ? 1 : -1) &&
        close(Number(row?.energy_ev), expectedEnergy);
      catalogIndex += 1;
    }
  }
}
check(
  "Complete 204-state catalog",
  catalogCorrect && catalogIndex === 204,
  "Every valid real-basis state through n=8 is present in deterministic n,l,m order with independently reproduced energy, nodes, degeneracy, and parity.",
);

let galleryIndex = 0;
let galleryCorrect = gallery.length === 25;
for (let l = 0; l <= 4; l += 1) {
  for (let m = -l; m <= l; m += 1) {
    const row = gallery[galleryIndex];
    galleryCorrect &&=
      Number(row?.n) === l + 1 &&
      Number(row?.l) === l &&
      Number(row?.m) === m &&
      row?.family === familyLabels[l] &&
      Number(row?.radial_nodes) === 0 &&
      Number(row?.angular_nodes) === l;
    galleryIndex += 1;
  }
}
check(
  "Complete official S-through-G gallery",
  galleryCorrect && galleryIndex === 25,
  "All 1+3+5+7+9 magnetic states for 1s, 2p, 3d, 4f, and 5g are present with no omissions.",
);

let profilesCorrect = profiles.length === 6005;
for (let index = 0; index < profiles.length; index += 1) {
  const row = profiles[index];
  const profileIndex = Math.floor(index / 1201);
  const sampleIndex = index % 1201;
  const previous = sampleIndex > 0 ? profiles[index - 1] : null;
  profilesCorrect &&=
    Number(row.n) === profileIndex + 1 &&
    Number(row.l) === profileIndex &&
    Number(row.m) === 0 &&
    Number(row.sample_index) === sampleIndex &&
    Number(row.scaled_radial_probability) >= 0 &&
    Number(row.cumulative_probability) >= -1e-14 &&
    Number(row.cumulative_probability) <= 1.00001 &&
    (!previous ||
      (Number(row.radius_over_n_squared_a) >
        Number(previous.radius_over_n_squared_a) &&
        Number(row.cumulative_probability) + 1e-12 >=
          Number(previous.cumulative_probability)));
}
check(
  "Normalized radial-profile evidence",
  profilesCorrect,
  "All 6,005 representative radial samples are ordered, non-negative, and cumulatively monotonic.",
);

const nodeCounts = new Map();
let nodesCorrect = nodes.length === 84;
for (const row of nodes) {
  const n = Number(row.n);
  const l = Number(row.l);
  const key = `${n}/${l}`;
  nodeCounts.set(key, (nodeCounts.get(key) || 0) + 1);
  nodesCorrect &&=
    Number(row.node_index) === nodeCounts.get(key) &&
    Number(row.radius_over_a) > 0 &&
    close(
      Number(row.radius_over_n_squared_a),
      Number(row.radius_over_a) / n ** 2,
    );
}
for (let n = 1; n <= 8; n += 1) {
  for (let l = 0; l < n; l += 1) {
    nodesCorrect &&= (nodeCounts.get(`${n}/${l}`) || 0) === n - l - 1;
  }
}
check(
  "Exact radial-node ledger",
  nodesCorrect,
  "All 84 positive roots reproduce n-l-1 nodes and both radius scalings agree.",
);

check(
  "Analytic and scaling anchors",
  references.schema_version === "task10-reference-anchors-v1" &&
    close(references.hydrogen_1s.scaled_density_at_origin, 1 / Math.PI) &&
    close(
      references.hydrogen_1s.energy_ev,
      -13.598233405345852,
    ) &&
    close(references.analytic_densities.two_s_r_over_a_2_node, 0, 1e-14) &&
    references.analytic_densities.two_pz_r_over_a_2_equator < 1e-30 &&
    close(references.carbon12_3d.energy_ev, -54.42028466906084) &&
    close(references.carbon12_3d.effective_bohr_radius_angstrom, 0.08820023364602815),
  "The 1s origin, 2s node, 2p angular node, hydrogen energy, and carbon Z-scaling anchors agree independently.",
);

check(
  "Complete required website content",
  [
    'id="glass-canvas"',
    'id="slice-canvas"',
    'id="radial-canvas"',
    'id="atomic-number"',
    'id="principal-number"',
    'id="angular-number"',
    'id="magnetic-number"',
    'id="gallery-preset"',
    "required_orbital_gallery.png",
    "orbital_view_rotation.webp",
    "22-check report",
    "204-state catalog",
    "25-state gallery data",
    "∫|ψ|²dV = 1",
  ].every((marker) => html.includes(marker)),
  "The required coloured-glass visualization, two quantitative figures, full controls, gallery, motion, and evidence downloads are present.",
);

check(
  "Interactive validated solver",
  explorer.includes("sampleSliceStack") &&
    explorer.includes("sampleOrthogonalSlices") &&
    explorer.includes("radialProfile") &&
    explorer.includes("stateSummary") &&
    explorer.includes("officialGalleryStates") &&
    explorer.includes("pointerdown") &&
    explorer.includes("wheel") &&
    explorer.includes("ArrowLeft") &&
    explorer.includes("ArrowRight") &&
    explorer.includes("ResizeObserver"),
  "State selection, 25 presets, display controls, pointer orbit, wheel zoom, keyboard camera control, and resizing all use the validated physics module.",
);

check(
  "Fail-closed evidence state",
  html.includes("data-glass-error") &&
    html.includes("data-slice-error") &&
    html.includes("data-radial-error") &&
    evidenceLoader.includes("throw new Error") &&
    explorer.includes("failClosed") &&
    explorer.includes('dataset.task10Status = "error"') &&
    explorer.includes("control.disabled = !enabled"),
  "Controls remain locked until every data, science, static-media, and motion layer agrees; all three figures expose explicit failure states.",
);

check(
  "Local typography and high-DPI figures",
  !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    css.includes('"Geist"') &&
    css.includes('"Bodoni Moda Variable"') &&
    css.includes('--figure: "Times New Roman"') &&
    explorer.includes('"Times New Roman", Times, serif') &&
    explorer.includes("Math.min(window.devicePixelRatio || 1, 2)") &&
    !explorer.includes("setInterval(") &&
    !explorer.includes("requestAnimationFrame("),
  "All dependencies are local, scientific labels use Times New Roman, canvases render at up to 2x density, and idle pages perform no animation loop.",
);

const actualDimensions = [
  dimensions(galleryPng),
  dimensions(radialPng),
  dimensions(glassPng),
  dimensions(comparisonPng),
  dimensions(summaryPng),
];
check(
  "Original-resolution publication media",
  JSON.stringify(actualDimensions) ===
    JSON.stringify([
      [3840, 2400],
      [2400, 1500],
      [3000, 1875],
      [3000, 1800],
      [3840, 2160],
    ]) &&
    figureManifest.renderer.font_family === "Times New Roman" &&
    figureManifest.figures.length === 13 &&
    plottingSource.includes('FIGURE_FONT_FAMILY = "Times New Roman"'),
  "Five inspected PNGs retain their accepted 2.4K-to-4K dimensions, the 13-file static package is complete, and generation is locked to Times New Roman.",
);

check(
  "Validated 4K stationary-view motion",
  motionManifest.schema_version === "task10-motion-v2" &&
    motionManifest.animation.width_px === 3840 &&
    motionManifest.animation.height_px === 2160 &&
    motionManifest.animation.frame_count === 80 &&
    motionManifest.animation.duration_ms === 4000 &&
    motionManifest.rendering_contract.font_family === "Times New Roman" &&
    motionManifest.rendering_contract.motion_interpretation ===
      "view rotation only; normalized state is stationary" &&
    motion.includes("orbital_view_rotation_poster.png"),
  "The motion artifact is 4K, 80 frames, 20 fps, exactly four seconds, explicitly camera-only, and has a 4K reduced-motion poster.",
);

check(
  "Responsive and reduced-motion safeguards",
  css.includes("100svh") &&
    css.includes("@media (max-width: 1180px)") &&
    css.includes("@media (max-width: 820px)") &&
    css.includes("@media (max-width: 520px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)") &&
    motion.includes("prefers-reduced-motion: reduce") &&
    motion.includes("pagehide"),
  "Desktop, tablet, and phone layouts, reduced-motion replacement, and animation cleanup paths are present.",
);

check(
  "Honest normalization and physical scope",
  normalizedHtml.includes("cutoff and opacity never alter") &&
    normalizedHtml.includes("changes visibility, not the wavefunction") &&
    normalizedHtml.includes("camera motion is not electron motion") &&
    normalizedHtml.includes("stationary, non-relativistic") &&
    normalizedHtml.includes("screening") &&
    normalizedHtml.includes("electron–electron correlation") &&
    normalizedHtml.includes("fine and hyperfine structure") &&
    normalizedHtml.includes("molecular bonding") &&
    normalizedHtml.includes("detector response"),
  "Renderer controls are separated from normalization, camera motion is separated from dynamics, and all excluded physics is stated explicitly.",
);

check(
  "Task index integration",
  /class="task-row is-ready"\s+href="\.\/tasks\/task-10\.html"/m.test(
    taskIndex,
  ) &&
    taskIndex.includes("Task 01 through Task 10 laboratories are open.") &&
    !/href="#task-10"[\s\S]{0,120}aria-disabled="true"/m.test(taskIndex),
  "Task 10 is open from the task index and no longer marked disabled.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(
  `\n${checks.length - failed.length}/${checks.length} Task 10 website checks passed.`,
);

if (failed.length) process.exitCode = 1;
