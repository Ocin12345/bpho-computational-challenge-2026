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

const [html, css, minimalCss, simulation, extensionRenderer, evidenceRenderer, evidence, extensionEvidence, reference, analysis] =
  await Promise.all([
    readText("site/tasks/task-02.html"),
    readText("site/assets/task-02.css"),
    readText("site/assets/task-02-minimal.css"),
    readText("site/assets/task-02-simulation.js"),
    readText("site/assets/task-02-extension.js"),
    readText("site/assets/task-02-evidence.js"),
    readJson("site/data/task-02-evidence.json"),
    readJson("site/data/task-02-extension-evidence.json"),
    readJson("task02_brownian_motion/validation/reference_validation.json"),
    readJson("task02_brownian_motion/analysis/analysis_report.json"),
  ]);

check(
  "Local dependency policy",
  !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    !html.includes("gsap.min.js") &&
    !html.includes("ScrollTrigger.min.js"),
  "Task 2 uses local assets only and carries no decorative animation dependency.",
);
check(
  "Typography standard",
  minimalCss.includes('"Times New Roman"') &&
    evidenceRenderer.includes('"Times New Roman"') &&
    !minimalCss.includes('"Inter"') &&
    !evidenceRenderer.includes('"Inter"'),
  "The visible interface and scientific canvases use formal Times-based typography.",
);
check(
  "Judge-facing task structure",
  html.includes('href="#simulation"') &&
    html.includes('href="#plot"') &&
    html.includes('href="#method"') &&
    html.includes('href="#validation"') &&
    html.includes('id="plot"') &&
    html.includes('id="method"') &&
    html.includes('id="validation"') &&
    html.includes("task-02-evidence.js"),
  "Task 2 exposes Simulation, Plot, Method, and Validation in the judge-facing navigation.",
);
check(
  "Official task framing",
  html.includes("Official Task 02 of 10") &&
    html.includes('href="../tasks.html"') &&
    html.includes("Brownian Motion"),
  "The page identifies the official task and retains a reliable route to All Tasks.",
);
check(
  "Locked reference evidence",
  html.includes("Reference validation run") &&
    html.includes("not relabelled when live controls change") &&
    html.includes("20–100 ps") &&
    html.includes("data-fit-equation") &&
    html.includes("data-mean-x") &&
    html.includes("data-mean-y"),
  "Stored ensemble evidence is visibly distinguished from the live simulation and states its fit interval.",
);
check(
  "Transparent physical parameters",
  html.includes("Physical parameters") &&
    html.includes("data-model-particle-count") &&
    html.includes("data-model-large-mass") &&
    html.includes("data-model-mass-ratio") &&
    html.includes("4.8106 × 10⁻²⁶ kg") &&
    html.includes("0.16 nm") &&
    html.includes("1.60 nm") &&
    simulation.includes("outputs.modelParticleCount.textContent") &&
    simulation.includes("outputs.modelLargeMass.textContent"),
  "N, m, r, M, R, and M/m are visible, with live values updated from the actual simulation state.",
);
check(
  "Model assumptions disclosed",
  html.includes('class="model-assumptions"') &&
    html.includes("Hard discs") &&
    html.includes("Reflective enclosure") &&
    html.includes("No gas–gas collisions") &&
    html.includes("Direction reorientation") &&
    html.includes("Equal-speed heat bath") &&
    html.includes("Browser visualization") &&
    html.includes("Python reference analysis"),
  "The simplified browser model and the separate Python reference analysis are described without implying full molecular dynamics.",
);
check(
  "Responsive and reduced-motion safeguards",
  minimalCss.includes("100dvh") &&
    minimalCss.includes("@media (max-width: 680px)") &&
    minimalCss.includes("@media (prefers-reduced-motion: reduce)"),
  "The page has mobile, dynamic viewport and reduced-motion handling.",
);
check(
  "High-DPI canvas sizing",
  simulation.includes("canvas.clientWidth") &&
    simulation.includes("canvas.clientHeight") &&
    evidenceRenderer.includes("canvas.clientWidth") &&
    evidenceRenderer.includes("canvas.clientHeight") &&
    extensionRenderer.includes("target.clientWidth") &&
    extensionRenderer.includes("target.clientHeight"),
  "Simulation and evidence canvases size from untransformed CSS dimensions.",
);
check(
  "Hard-disc study retained outside the official task path",
  html.includes('id="extension"') &&
    html.includes('id="extension"') && html.includes('hidden') &&
    html.includes('value="random-reset"') &&
    html.includes('value="hard-disc"') &&
    !html.includes('href="#extension"') &&
    !html.includes("task-02-extension.js") &&
    extensionRenderer.includes('state.mode === "hard-disc"') &&
    extensionRenderer.includes('state.mode === "random-reset"'),
  "The accepted heat-bath comparison remains in source while the official Task 2 page stays focused on the required model.",
);
check(
  "Mutually exclusive bath physics",
  extensionEvidence.accepted === true &&
    extensionEvidence.modes.random_reset.direction_resets > 0 &&
    extensionEvidence.modes.random_reset.small_small_impulses === 0 &&
    extensionEvidence.modes.hard_disc.direction_resets === 0 &&
    extensionEvidence.modes.hard_disc.small_small_impulses > 0,
  "Direction randomization and gas-gas contacts are never active in the same model.",
);
check(
  "Hard-disc conservation evidence",
  extensionEvidence.controlled_collisions.sample_count >= 2000 &&
    extensionEvidence.controlled_collisions.maximum_normalized_momentum_error < 1e-12 &&
    extensionEvidence.controlled_collisions.maximum_normalized_energy_error < 1e-12 &&
    Math.abs(extensionEvidence.modes.hard_disc.relative_kinetic_energy_drift) < 1e-12,
  `${extensionEvidence.controlled_collisions.sample_count} controlled pairs; momentum and energy errors remain below 1e-12.`,
);
check(
  "Extension interaction safeguards",
  extensionRenderer.includes("IntersectionObserver") &&
    extensionRenderer.includes("prefers-reduced-motion: reduce") &&
    extensionRenderer.includes('laboratory.dataset.accepted = "false"') &&
    minimalCss.includes("#extension-bath-canvas:focus-visible") &&
    minimalCss.includes(".bath-mode-picker input:focus-visible"),
  "The extension pauses off-screen, respects reduced motion, and exposes keyboard focus and fail-closed evidence.",
);
check(
  "Quantitative plot and validation output",
  html.includes('id="msd-chart"') &&
    html.includes('id="endpoint-chart"') &&
    html.includes('id="convergence-chart"') &&
    html.match(/data-export-figure=/g)?.length === 3 &&
    evidenceRenderer.includes("drawMsdChart") &&
    evidenceRenderer.includes("drawEndpointChart") &&
    evidenceRenderer.includes("drawConvergenceChart"),
  "The page exposes one principal MSD plot, concise endpoint evidence, convergence evidence, and figure exports.",
);
check(
  "Focused collision animation",
    css.includes("playback-particle 7.5s") &&
    css.includes("playback-tracer 7.5s") &&
    minimalCss.includes("prefers-reduced-motion") &&
    html.includes("Approach, impulse, separation") &&
    html.includes("J=-(1+C)\\mu g_n") &&
    !html.includes("task-02-motion.js"),
  "The physical collision loop and reduced-mass derivation remain, while page-level decorative choreography is removed.",
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
    evidence.validation.controlled_convergence.length >= 4 &&
    evidence.validation.minimum_observed_order > 0.99 &&
    evidence.validation.maximum_residual_penetration_nm === 0 &&
    html.includes("data-convergence-order") &&
    html.includes("data-residual-penetration"),
  `Worst normalized collision error=${evidence.validation.worst_normalized_collision_error}.`,
);
check(
  "Unbiased ensemble result",
  evidence.ensemble.final_mean_x_ci_nm[0] <= 0 &&
    evidence.ensemble.final_mean_x_ci_nm[1] >= 0 &&
    evidence.ensemble.final_mean_y_ci_nm[0] <= 0 &&
    evidence.ensemble.final_mean_y_ci_nm[1] >= 0 &&
    evidenceRenderer.includes("outputs.meanX.textContent") &&
    evidenceRenderer.includes("outputs.meanY.textContent"),
  "Both final mean-displacement confidence intervals include zero and are exposed by the renderer.",
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
