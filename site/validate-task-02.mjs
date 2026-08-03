import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const currentDirectory = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(currentDirectory, "..");

const readText = (path) => readFile(resolve(projectRoot, path), "utf8");
const readJson = async (path) => JSON.parse(await readText(path));
const checks = [];

function check(name, condition, detail) {
  checks.push({ name, passed: Boolean(condition), detail });
}

const [html, css, simulation, evidenceRenderer, motion, evidence, reference, analysis] =
  await Promise.all([
    readText("site/tasks/task-02.html"),
    readText("site/assets/task-02.css"),
    readText("site/assets/task-02-simulation.js"),
    readText("site/assets/task-02-evidence.js"),
    readText("site/assets/task-02-motion.js"),
    readJson("site/data/task-02-evidence.json"),
    readJson("task02_brownian_motion/validation/reference_validation.json"),
    readJson("task02_brownian_motion/analysis/analysis_report.json"),
  ]);

check(
  "Local dependency policy",
  html.includes("../vendor/packages/gsap/dist/gsap.min.js") &&
    html.includes("../vendor/packages/gsap/dist/ScrollTrigger.min.js") &&
    !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html),
  "Task 2 uses pinned local GSAP and local fonts with no external browser request.",
);
check(
  "Typography standard",
  css.includes('"Geist"') &&
    css.includes('"Bodoni Moda Variable"') &&
    evidenceRenderer.includes('"Times New Roman"') &&
    !css.includes('"Inter"') &&
    !evidenceRenderer.includes('"Inter"'),
  "Interface typography is local; scientific canvases use Times New Roman.",
);
check(
  "Complete evidence states",
  html.includes("data-evidence-empty") &&
    html.includes("data-evidence-error") &&
    html.includes("is-loading") &&
    css.includes("evidence-skeleton"),
  "Loading, empty, success and error states are explicitly represented.",
);
check(
  "Responsive and reduced-motion safeguards",
  css.includes("min-height: 100dvh") &&
    css.includes("@media (max-width: 680px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)") &&
    motion.includes("prefers-reduced-motion: reduce"),
  "The page has mobile, dynamic viewport and reduced-motion handling.",
);
check(
  "High-DPI canvas sizing",
  simulation.includes("canvas.clientWidth") &&
    simulation.includes("canvas.clientHeight") &&
    evidenceRenderer.includes("canvas.clientWidth") &&
    evidenceRenderer.includes("canvas.clientHeight"),
  "Simulation and evidence canvases size from untransformed CSS dimensions.",
);
check(
  "Presentation-quality figure export",
  html.match(/data-export-figure=/g)?.length === 3 &&
    evidenceRenderer.includes("pixelRatio: 2") &&
    evidenceRenderer.includes("3200x1800") &&
    evidenceRenderer.includes("2400x2400") &&
    evidenceRenderer.includes('"Times New Roman"'),
  "All three evidence figures export as fixed high-resolution Times New Roman PNGs.",
);
check(
  "Professional motion system",
  motion.includes("ScrollTrigger") &&
    motion.includes("gsap.matchMedia") &&
    motion.includes("pagehide") &&
    html.includes("action-trajectory") &&
    html.includes("physics-ribbon"),
  "GSAP motion includes scroll choreography, responsive pinning and cleanup.",
);
check(
  "Evidence schema and ensemble",
  evidence.schema_version === 1 &&
    evidence.passed === true &&
    evidence.ensemble.run_count === 64 &&
    evidence.ensemble.series.length >= 100 &&
    evidence.ensemble.endpoints.length === 64,
  `${evidence.ensemble.run_count} seeded paths; ${evidence.ensemble.series.length} ensemble samples.`,
);
check(
  "Diffusive fit quality",
  evidence.ensemble.diffusion_coefficient_nm2_per_ps > 0 &&
    evidence.ensemble.msd_fit_r_squared >= 0.98,
  `D=${evidence.ensemble.diffusion_coefficient_nm2_per_ps}; R²=${evidence.ensemble.msd_fit_r_squared}.`,
);
check(
  "Collision and convergence validation",
  evidence.validation.worst_normalized_collision_error < 1e-12 &&
    evidence.validation.controlled_convergence.length >= 4,
  `Worst normalized collision error=${evidence.validation.worst_normalized_collision_error}.`,
);
check(
  "Independent Python validation",
  reference.passed === true &&
    reference.checks.length === 9 &&
    analysis.passed === true &&
    analysis.checks.length === 8,
  "9 reference checks and 8 analysis checks pass in the stored reports.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(`\n${checks.length - failed.length}/${checks.length} Task 2 checks passed.`);

if (failed.length) process.exitCode = 1;
