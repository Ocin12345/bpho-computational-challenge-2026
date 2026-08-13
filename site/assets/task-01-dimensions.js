const laboratory = document.querySelector("[data-dimensions-laboratory]");
const form = document.querySelector("[data-dimensions-form]");
const runButton = document.querySelector("[data-run-dimensions]");
const statusText = document.querySelector("[data-dimensions-status]");
const progressBar = document.querySelector("[data-dimensions-progress]");
const errorMessage = document.querySelector("[data-dimensions-error]");
const downloadButton = document.querySelector("[data-download-dimensions]");
const exportButton = document.querySelector("[data-export-dimensions]");
const distributionCanvas = document.querySelector("#dimensions-distribution-canvas");
const scalingCanvas = document.querySelector("#dimensions-scaling-canvas");
const distributionContext = distributionCanvas.getContext("2d");
const scalingContext = scalingCanvas.getContext("2d");

const controls = {
  walks: document.querySelector("#dimensions-walk-count"),
  maxSteps: document.querySelector("#dimensions-max-steps"),
  stepSize: document.querySelector("#dimensions-step-size"),
  seed: document.querySelector("#dimensions-seed"),
};

const COLOURS = {
  1: "#315c8a",
  2: "#a4432f",
  3: "#8a6b22",
};
const INK = "#22221f";
const MUTED = "#6b6962";
const LINE = "#deddd6";
const FONT = '"Times New Roman", Times, serif';

let currentPayload = null;
let worker = null;
let resizeFrame = 0;

function setCanvasSize(canvas, context) {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(canvas.clientWidth * ratio));
  const height = Math.max(1, Math.round(canvas.clientHeight * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { width: canvas.clientWidth, height: canvas.clientHeight };
}

function validatePayload(payload) {
  if (!payload || payload.schema_version !== 1 || payload.accepted !== true) {
    throw new Error("The accepted dimensional evidence is unavailable.");
  }
  if (!Array.isArray(payload.dimensions) || payload.dimensions.length !== 3) {
    throw new Error("Dimensional evidence must contain 1D, 2D and 3D results.");
  }
  for (const [index, entry] of payload.dimensions.entries()) {
    if (
      entry.dimension !== index + 1 ||
      !Array.isArray(entry.scaling) ||
      entry.scaling.length < 6 ||
      !Array.isArray(entry.distribution?.density) ||
      entry.distribution.density.length !== entry.distribution.theory_density?.length ||
      !Number.isFinite(entry.fit?.slope) ||
      !Number.isFinite(entry.fit?.exponent)
    ) {
      throw new Error("Dimensional evidence has an invalid structure.");
    }
  }
  return payload;
}

function line(context, x1, y1, x2, y2, colour = LINE, width = 1) {
  context.strokeStyle = colour;
  context.lineWidth = width;
  context.beginPath();
  context.moveTo(x1, y1);
  context.lineTo(x2, y2);
  context.stroke();
}

function drawDistribution() {
  if (!currentPayload) return;
  const { width, height } = setCanvasSize(distributionCanvas, distributionContext);
  const context = distributionContext;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  const left = 46;
  const right = 16;
  const top = 22;
  const bottom = 34;
  const gap = 16;
  const panelHeight = (height - top - bottom - gap * 2) / 3;
  const plotWidth = width - left - right;
  const qMaximum = 3.6;

  currentPayload.dimensions.forEach((entry, panelIndex) => {
    const panelTop = top + panelIndex * (panelHeight + gap);
    const panelBottom = panelTop + panelHeight;
    const values = [...entry.distribution.density, ...entry.distribution.theory_density];
    const maximumDensity = Math.max(...values) * 1.12;
    const xFor = (q) => left + (q / qMaximum) * plotWidth;
    const yFor = (density) => panelBottom - (density / maximumDensity) * panelHeight;

    context.fillStyle = "#fafaf8";
    context.fillRect(left, panelTop, plotWidth, panelHeight);
    for (let tick = 0; tick <= 3; tick += 1) {
      const y = panelTop + (tick / 3) * panelHeight;
      line(context, left, y, width - right, y, "#ecebe6");
    }

    const centres = entry.distribution.bin_centres;
    const binWidth = plotWidth / centres.length;
    context.fillStyle = `${COLOURS[entry.dimension]}32`;
    context.strokeStyle = COLOURS[entry.dimension];
    context.lineWidth = 0.7;
    entry.distribution.density.forEach((density, index) => {
      const x = xFor(centres[index]) - binWidth * 0.42;
      const y = yFor(density);
      const barHeight = panelBottom - y;
      context.fillRect(x, y, binWidth * 0.84, barHeight);
      context.strokeRect(x, y, binWidth * 0.84, barHeight);
    });

    context.strokeStyle = INK;
    context.lineWidth = 1.7;
    context.beginPath();
    entry.distribution.theory_density.forEach((density, index) => {
      const x = xFor(centres[index]);
      const y = yFor(density);
      if (index === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.stroke();

    line(context, left, panelBottom, width - right, panelBottom, "#aaa8a0");
    context.fillStyle = INK;
    context.font = `700 13px ${FONT}`;
    context.textAlign = "left";
    context.textBaseline = "top";
    context.fillText(`${entry.dimension}D`, left + 7, panelTop + 6);

    if (panelIndex === 2) {
      context.fillStyle = MUTED;
      context.font = `11px ${FONT}`;
      context.textAlign = "center";
      for (let q = 0; q <= 3; q += 1) {
        context.fillText(String(q), xFor(q), panelBottom + 7);
      }
      context.font = `italic 13px ${FONT}`;
      context.fillText("q = |R| / (s√N)", left + plotWidth / 2, height - 16);
    }
  });

  context.save();
  context.translate(14, height / 2);
  context.rotate(-Math.PI / 2);
  context.fillStyle = MUTED;
  context.font = `12px ${FONT}`;
  context.textAlign = "center";
  context.fillText("Probability density", 0, 0);
  context.restore();
}

function drawScaling() {
  if (!currentPayload) return;
  const { width, height } = setCanvasSize(scalingCanvas, scalingContext);
  const context = scalingContext;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  const left = 56;
  const right = 18;
  const top = 42;
  const bottom = 48;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const maxStep = Math.max(
    ...currentPayload.dimensions.flatMap((entry) => entry.scaling.map((point) => point.n_steps)),
  );
  const maximum = Math.sqrt(maxStep) * 1.08;
  const xFor = (value) => left + (value / maximum) * plotWidth;
  const yFor = (value) => top + plotHeight - (value / maximum) * plotHeight;

  context.fillStyle = "#fafaf8";
  context.fillRect(left, top, plotWidth, plotHeight);
  for (let tick = 0; tick <= 4; tick += 1) {
    const value = (maximum * tick) / 4;
    const x = xFor(value);
    const y = yFor(value);
    line(context, x, top, x, top + plotHeight, "#e9e8e2");
    line(context, left, y, width - right, y, "#e9e8e2");
    context.fillStyle = MUTED;
    context.font = `11px ${FONT}`;
    context.textAlign = "center";
    context.fillText(value.toFixed(0), x, top + plotHeight + 17);
    context.textAlign = "right";
    context.fillText(value.toFixed(0), left - 8, y + 4);
  }

  context.save();
  context.setLineDash([6, 6]);
  line(context, xFor(0), yFor(0), xFor(maximum), yFor(maximum), "#3d3c38", 1.3);
  context.restore();

  for (const entry of currentPayload.dimensions) {
    const colour = COLOURS[entry.dimension];
    context.strokeStyle = colour;
    context.lineWidth = 1.5;
    context.beginPath();
    entry.scaling.forEach((point, index) => {
      const x = xFor(Math.sqrt(point.n_steps));
      const y = yFor(point.rms_displacement / currentPayload.parameters.step_size);
      if (index === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.stroke();

    for (const point of entry.scaling) {
      const x = xFor(Math.sqrt(point.n_steps));
      const normalizedRms = point.rms_displacement / currentPayload.parameters.step_size;
      const error = (1.96 * point.rms_standard_error) / currentPayload.parameters.step_size;
      const yTop = yFor(normalizedRms + error);
      const yBottom = yFor(normalizedRms - error);
      line(context, x, yTop, x, yBottom, colour, 1);
      line(context, x - 3, yTop, x + 3, yTop, colour, 1);
      line(context, x - 3, yBottom, x + 3, yBottom, colour, 1);
      context.fillStyle = "#ffffff";
      context.strokeStyle = colour;
      context.lineWidth = 1.5;
      context.beginPath();
      context.arc(x, yFor(normalizedRms), 3.3, 0, Math.PI * 2);
      context.fill();
      context.stroke();
    }
  }

  line(context, left, top + plotHeight, width - right, top + plotHeight, "#88867f");
  line(context, left, top, left, top + plotHeight, "#88867f");
  context.fillStyle = INK;
  context.font = `12px ${FONT}`;
  context.textAlign = "center";
  context.fillText("√N", left + plotWidth / 2, height - 13);
  context.save();
  context.translate(16, top + plotHeight / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("rRMS / s", 0, 0);
  context.restore();

  let legendX = left;
  context.font = `11px ${FONT}`;
  for (const dimension of [1, 2, 3]) {
    context.fillStyle = COLOURS[dimension];
    context.fillRect(legendX, 15, 13, 2);
    context.fillStyle = INK;
    context.textAlign = "left";
    context.fillText(`${dimension}D`, legendX + 18, 19);
    legendX += 55;
  }
  context.save();
  context.setLineDash([5, 4]);
  line(context, legendX, 16, legendX + 15, 16, "#3d3c38", 1.2);
  context.restore();
  context.fillStyle = INK;
  context.fillText("theory", legendX + 20, 19);
}

function renderFits() {
  for (const entry of currentPayload.dimensions) {
    const card = document.querySelector(`[data-dimension-fit="${entry.dimension}"]`);
    const value = card.querySelector("dd");
    const detail = card.querySelector("span");
    value.textContent = `a = ${entry.fit.slope.toFixed(4)} ± ${entry.fit.slope_ci95_half_width.toFixed(4)}`;
    detail.textContent = `power α = ${entry.fit.exponent.toFixed(4)} ± ${entry.fit.exponent_ci95_half_width.toFixed(4)}`;
  }
}

function render() {
  if (!currentPayload) return;
  drawDistribution();
  drawScaling();
  renderFits();
}

function scheduleRender() {
  cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(render);
}

function updateStatus(text, progress = 1) {
  statusText.textContent = text;
  progressBar.style.width = `${Math.max(0, Math.min(1, progress)) * 100}%`;
}

function setResults(payload, status) {
  currentPayload = payload;
  laboratory.classList.remove("is-loading");
  errorMessage.hidden = true;
  runButton.disabled = false;
  downloadButton.disabled = false;
  exportButton.disabled = false;
  updateStatus(status, 1);
  render();
}

function failClosed(error) {
  laboratory.classList.remove("is-loading");
  laboratory.classList.add("has-error");
  errorMessage.hidden = false;
  runButton.disabled = true;
  downloadButton.disabled = true;
  exportButton.disabled = true;
  updateStatus("Validated comparison unavailable", 0);
  console.error(error);
}

function parametersFromForm() {
  const nWalks = Math.round(Number(controls.walks.value));
  const maxSteps = Math.round(Number(controls.maxSteps.value));
  const stepSize = Number(controls.stepSize.value);
  const seed = Math.round(Number(controls.seed.value));
  if (!Number.isFinite(nWalks) || nWalks < 500 || nWalks > 10000) {
    throw new Error("Walks per point must be between 500 and 10,000.");
  }
  if (![400, 800, 1600].includes(maxSteps)) {
    throw new Error("Choose a supported maximum step count.");
  }
  if (!Number.isFinite(stepSize) || stepSize <= 0 || stepSize > 100) {
    throw new Error("Step length must be greater than zero and at most 100.");
  }
  if (!Number.isFinite(seed) || seed < 0 || seed > 4294967295) {
    throw new Error("Seed must be an integer from 0 to 4,294,967,295.");
  }
  return { nWalks, maxSteps, stepSize, seed };
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    const parameters = parametersFromForm();
    if (worker) worker.terminate();
    worker = new Worker(
      new URL("./task-01-dimensions-worker.js", import.meta.url),
    );
    runButton.disabled = true;
    errorMessage.hidden = true;
    updateStatus("Running exact 1D ensemble", 0);
    worker.addEventListener("message", (workerEvent) => {
      const message = workerEvent.data;
      if (message.type === "progress") {
        const dimension = Math.min(3, Math.floor(message.progress * 3) + 1);
        updateStatus(`Running exact ${dimension}D ensemble`, message.progress);
      } else if (message.type === "complete") {
        setResults(message.payload, "Custom exact comparison complete");
        worker.terminate();
        worker = null;
      } else if (message.type === "error") {
        errorMessage.textContent = `The custom comparison failed: ${message.message}`;
        errorMessage.hidden = false;
        runButton.disabled = false;
        updateStatus("Custom comparison failed", 0);
        worker.terminate();
        worker = null;
      }
    });
    worker.addEventListener("error", (workerError) => {
      errorMessage.textContent = `The custom comparison failed: ${workerError.message}`;
      errorMessage.hidden = false;
      runButton.disabled = false;
      updateStatus("Custom comparison failed", 0);
    });
    worker.postMessage({ type: "run", parameters });
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
    runButton.disabled = false;
  }
});

function createCsv(payload) {
  const rows = [
    ["record", "dimension", "n_steps_or_q", "measured", "standard_error", "theory"],
  ];
  for (const entry of payload.dimensions) {
    for (const point of entry.scaling) {
      rows.push([
        "rms_scaling",
        entry.dimension,
        point.n_steps,
        point.rms_displacement,
        point.rms_standard_error,
        payload.parameters.step_size * Math.sqrt(point.n_steps),
      ]);
    }
    entry.distribution.bin_centres.forEach((q, index) => {
      rows.push([
        "endpoint_density",
        entry.dimension,
        q,
        entry.distribution.density[index],
        "",
        entry.distribution.theory_density[index],
      ]);
    });
  }
  return rows.map((row) => row.join(",")).join("\n");
}

function downloadBlob(blob, filename) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 0);
}

downloadButton.addEventListener("click", () => {
  if (!currentPayload) return;
  downloadBlob(
    new Blob([createCsv(currentPayload)], { type: "text/csv;charset=utf-8" }),
    "task-01-dimensional-extension.csv",
  );
});

exportButton.addEventListener("click", () => {
  if (!currentPayload) return;
  const output = document.createElement("canvas");
  output.width = 2200;
  output.height = 1240;
  const context = output.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, output.width, output.height);
  context.fillStyle = INK;
  context.font = `700 48px ${FONT}`;
  context.fillText("Task 1 extension: random walks in 1D, 2D and 3D", 80, 74);
  context.font = `26px ${FONT}`;
  context.fillStyle = MUTED;
  context.fillText("Exact ensembles compared with the universal rRMS = s√N law", 80, 116);
  context.drawImage(distributionCanvas, 60, 160, 1000, 900);
  context.drawImage(scalingCanvas, 1140, 160, 1000, 900);
  context.fillStyle = INK;
  context.font = `24px ${FONT}`;
  const fitSummary = currentPayload.dimensions
    .map((entry) => `${entry.dimension}D: a=${entry.fit.slope.toFixed(4)}, α=${entry.fit.exponent.toFixed(4)}`)
    .join("     ");
  context.fillText(fitSummary, 80, 1150);
  output.toBlob((blob) => {
    if (blob) downloadBlob(blob, "task-01-dimensional-extension.png");
  }, "image/png");
});

new ResizeObserver(scheduleRender).observe(laboratory);
window.addEventListener("pagehide", () => worker?.terminate());

fetch("../data/task-01-dimensions-validation.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) throw new Error(`Validation request failed (${response.status})`);
    return response.json();
  })
  .then(validatePayload)
  .then((payload) => {
    const date = new Date(payload.generated_at_utc).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
    setResults(payload, `Accepted reference ensemble · ${date}`);
  })
  .catch(failClosed);
