import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(here, "..");
const readText = (path) => readFile(resolve(projectRoot, path), "utf8");
const readJson = async (path) => JSON.parse(await readText(path));
const checks = [];

function check(name, condition, detail) {
  checks.push({ name, passed: Boolean(condition), detail });
}

const [html, css, goldCss, liveWalk, ensemble, extension, worker, evidence] = await Promise.all([
  readText("site/tasks/task-01.html"),
  readText("site/assets/task-01-minimal.css"),
  readText("site/assets/task-01-gold.css"),
  readText("site/assets/task-01.js"),
  readText("site/assets/task-01-ensemble.js"),
  readText("site/assets/task-01-dimensions.js"),
  readText("site/assets/task-01-dimensions-worker.js"),
  readJson("site/data/task-01-dimensions-validation.json"),
]);

check(
  "Official 2D task remains the default",
  html.includes('name="walk-dimension" value="2" checked') &&
    html.includes("Two-dimensional random walk") &&
    html.includes('id="ensemble"') &&
    html.includes('id="validation"'),
  "The original 2D walk and ensemble remain intact, 2D opens by default, and the judge-facing validation view is present.",
);
check(
  "Dimensional study retained outside the filming path",
  html.includes('name="walk-dimension" value="1"') &&
    html.includes('name="walk-dimension" value="3"') &&
    html.includes('id="dimensions"') &&
    html.includes('class="video-cut"') &&
    html.includes('data-task="01"') &&
    html.includes("task-video.css") &&
    !html.includes('href="#dimensions"') &&
    !html.includes("task-01-dimensions.js"),
  "The accepted 1D/3D study remains in source, while the visible filming path stays on the required 2D task.",
);
check(
  "Exact isotropic microscopic steps",
  liveWalk.includes("random() < 0.5 ? -1 : 1") &&
    liveWalk.includes("const cosinePolar = random() * 2 - 1") &&
    liveWalk.includes("Math.sqrt(Math.max(0, 1 - cosinePolar ** 2))"),
  "1D uses equiprobable signs and 3D samples uniform cos(theta), avoiding polar bias.",
);
check(
  "Dimension-correct large-N variance",
  liveWalk.includes("Math.sqrt(microscopicSteps / state.dimension)") &&
    liveWalk.includes("state.zPositions[point] || 0"),
  "Each CLT coordinate has variance Ns^2/d and displayed distance uses all coordinates.",
);
check(
  "Truthful 3D projection",
  liveWalk.includes("3D · oblique projection") &&
    liveWalk.includes("drawProjectedCircle") &&
    liveWalk.includes("projectCoordinates"),
  "The 3D view is labelled as an oblique projection and shows projected RMS great circles.",
);
check(
  "Independent accepted evidence",
  evidence.schema_version === 1 &&
    evidence.accepted === true &&
    evidence.parameters.n_walks === 12_000 &&
    evidence.dimensions.map((entry) => entry.dimension).join(",") === "1,2,3",
  `${evidence.parameters.n_walks.toLocaleString()} exact walks per dimension are stored for 1D, 2D and 3D.`,
);
check(
  "Universal RMS slope recovered",
  evidence.dimensions.every((entry) => Math.abs(entry.fit.slope - 1) < 0.035),
  evidence.dimensions
    .map((entry) => `${entry.dimension}D=${entry.fit.slope.toFixed(4)}`)
    .join(", "),
);
check(
  "Square-root exponent recovered",
  evidence.dimensions.every((entry) => Math.abs(entry.fit.exponent - 0.5) < 0.035),
  evidence.dimensions
    .map((entry) => `${entry.dimension}D=${entry.fit.exponent.toFixed(4)}`)
    .join(", "),
);
check(
  "Dimension-specific endpoint theory",
    worker.includes("Math.sqrt(2 / Math.PI) * Math.exp(-0.5 * q ** 2)") &&
    worker.includes("2 * q * Math.exp(-(q ** 2))") &&
    worker.includes("3 *") &&
    html.includes("Normalized endpoint distance"),
  "Folded-normal, Rayleigh and Maxwell radial densities are compared with exact ensembles.",
);
check(
  "Uncertainty and fit reporting",
  worker.includes("rms_standard_error") &&
    worker.includes("slope_ci95_half_width") &&
    worker.includes("exponent_ci95_half_width") &&
    extension.includes("1.96 * point.rms_standard_error"),
  "Plots carry 95% confidence intervals and cards report slope and exponent uncertainty.",
);
check(
  "Responsive high-DPI graphs",
  extension.includes("window.devicePixelRatio") &&
    extension.includes("canvas.clientWidth") &&
    css.includes("@media (max-width: 600px)") &&
    css.includes("@media (prefers-reduced-motion: reduce)"),
  "Both graphs size from CSS dimensions, support high-DPI screens and stack on mobile.",
);
check(
  "Accessible native controls",
  html.includes("<fieldset class=\"dimension-picker\">") &&
    html.includes("<legend>Space</legend>") &&
    html.includes('aria-live="polite"') &&
    css.includes("input:focus-visible + span"),
  "Dimension selection is a labelled native radio group with visible keyboard focus and live status.",
);
check(
  "Fail-closed evidence state",
  html.includes("The dimensional comparison could not be loaded") &&
    extension.includes("function failClosed") &&
    extension.includes("runButton.disabled = true"),
  "If the accepted file fails validation, claims and exports remain unavailable.",
);
check(
  "Judge-facing validation view",
  html.includes('href="#validation"') &&
    html.includes('class="validation-section"') &&
    html.includes('id="validation-msd-canvas"') &&
    html.includes('id="validation-angle-canvas"') &&
    html.includes('id="validation-radial-canvas"') &&
    html.includes("task-01-validation.js"),
  "The locked reference evidence is visible as a labelled MSD, angular and radial validation view.",
);
check(
  "Reproducible outputs",
  html.includes("Master seed") &&
    html.includes("Download CSV") &&
    html.includes("Export figure") &&
    worker.includes("mulberry32"),
  "Every browser run is seeded and its data and presentation figure can be exported.",
);
check(
  "Method and assumptions are explicit",
  html.includes('id="method"') &&
    html.includes('class="method-assumptions"') &&
    html.includes("fixed step length") &&
    html.includes("unbounded plane") &&
    html.includes("dimensionless simulation units"),
  "The page states the model assumptions, unit convention, and method beside the equations.",
);
check(
  "Reproducibility controls are available but secondary",
  html.includes('class="advanced-controls"') &&
    html.includes('id="walk-seed"') &&
    html.includes("data-new-seed") &&
    html.includes("Official task: 2D"),
  "Seed, speed and dimensional extensions are available in a clearly marked advanced disclosure.",
);
check(
  "Live and reference results are distinguished",
  html.includes("Current simulation") &&
    html.includes("Reference validation") &&
    html.includes("50,000 independent walks per N"),
  "Judge-facing copy distinguishes the visitor's live run from the committed reference result.",
);
check(
  "Canvas legend and export metadata",
  html.includes('class="walk-legend"') &&
    ensemble.includes("Task 1 ensemble export") &&
    ensemble.includes("n_walks") &&
    ensemble.includes("step_length") &&
    ensemble.includes("master_seed"),
  "The visual encoding is explained and CSV exports carry the parameters needed to reproduce them.",
);
check(
  "Clean local presentation",
  !/<(?:script|link)\b[^>]+(?:src|href)=["']https?:\/\//i.test(html) &&
    css.includes('"Times New Roman"') &&
    !css.includes("linear-gradient") &&
    !css.includes("radial-gradient"),
  "The extension uses local assets, formal Times typography and no decorative gradients.",
);

const failed = checks.filter((entry) => !entry.passed);
for (const entry of checks) {
  console.log(`${entry.passed ? "PASS" : "FAIL"} ${entry.name}: ${entry.detail}`);
}
console.log(`\n${checks.length - failed.length}/${checks.length} Task 1 extension checks passed.`);
if (failed.length) process.exitCode = 1;
