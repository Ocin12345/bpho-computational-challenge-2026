(() => {
const DATA_URL = new URL("../data/task-02-evidence.json", window.location.href);

const canvases = {
  msd: document.querySelector("#msd-chart"),
  endpoints: document.querySelector("#endpoint-chart"),
  convergence: document.querySelector("#convergence-chart"),
};

const contexts = Object.fromEntries(
  Object.entries(canvases).map(([name, canvas]) => [
    name,
    canvas.getContext("2d"),
  ]),
);
const exportButtons = [
  ...document.querySelectorAll("[data-export-figure]"),
];
const exportSettings = {
  msd: {
    width: 1600,
    height: 900,
    filename: "task02-mean-squared-displacement-3200x1800.png",
  },
  endpoints: {
    width: 1200,
    height: 1200,
    filename: "task02-endpoint-distribution-2400x2400.png",
  },
  convergence: {
    width: 1200,
    height: 1200,
    filename: "task02-time-step-convergence-2400x2400.png",
  },
};

const outputs = {
  provenance: document.querySelector("[data-evidence-provenance]"),
  diffusion: document.querySelector("[data-diffusion]"),
  diffusionCi: document.querySelector("[data-diffusion-ci]"),
  rSquared: document.querySelector("[data-r-squared]"),
  runCount: document.querySelector("[data-run-count]"),
  collisionError: document.querySelector("[data-collision-error]"),
  content: document.querySelector("[data-evidence-content]"),
  error: document.querySelector("[data-evidence-error]"),
  empty: document.querySelector("[data-evidence-empty]"),
  section: document.querySelector(".evidence-section"),
};

let evidence = null;
let resizeFrame = 0;

function validateEvidence(payload) {
  if (payload?.schema_version !== 1 || payload?.passed !== true) return false;
  if (payload?.ensemble?.run_count !== 64) return false;
  if (!Array.isArray(payload?.ensemble?.series)) return false;
  if (payload.ensemble.series.length < 100) return false;
  if (!Array.isArray(payload?.ensemble?.endpoints)) return false;
  if (payload.ensemble.endpoints.length !== payload.ensemble.run_count) {
    return false;
  }
  if (!Array.isArray(payload?.validation?.controlled_convergence)) {
    return false;
  }
  return payload.validation.controlled_convergence.length >= 4;
}

function canvasSize(canvas, context, renderOptions = {}) {
  const width = renderOptions.width ??
    Math.max(280, canvas.clientWidth);
  const height = renderOptions.height ??
    Math.max(300, canvas.clientHeight);
  const pixelRatio = renderOptions.pixelRatio ??
    Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  return { width, height };
}

function chartFrame(width, height, options = {}) {
  const left = options.left ?? (width < 500 ? 52 : 68);
  const top = options.top ?? 28;
  const right = width - (options.right ?? 22);
  const bottom = height - (options.bottom ?? 51);
  return {
    left,
    top,
    right,
    bottom,
    width: right - left,
    height: bottom - top,
  };
}

function drawPaper(context, width, height) {
  context.clearRect(0, 0, width, height);
  const wash = context.createLinearGradient(0, 0, width, height);
  wash.addColorStop(0, "#f4f0e8");
  wash.addColorStop(1, "#efe9df");
  context.fillStyle = wash;
  context.fillRect(0, 0, width, height);
}

function drawAxisLines(context, frame) {
  context.strokeStyle = "rgba(45, 47, 43, 0.23)";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(frame.left, frame.top);
  context.lineTo(frame.left, frame.bottom);
  context.lineTo(frame.right, frame.bottom);
  context.stroke();
}

function drawGridLine(context, frame, orientation, position) {
  context.strokeStyle = "rgba(56, 54, 48, 0.075)";
  context.lineWidth = 1;
  context.beginPath();
  if (orientation === "horizontal") {
    context.moveTo(frame.left, position);
    context.lineTo(frame.right, position);
  } else {
    context.moveTo(position, frame.top);
    context.lineTo(position, frame.bottom);
  }
  context.stroke();
}

function axisLabel(context, alignment = "center", width = 700) {
  const fontSize = width < 500 ? 10.5 : width > 1200 ? 13 : 11.5;
  context.fillStyle = "#777168";
  context.font = `${fontSize}px "Times New Roman", Times, serif`;
  context.textAlign = alignment;
  context.textBaseline = "middle";
}

function axisTitle(context, width = 700) {
  const fontSize = width < 500 ? 15 : width > 1200 ? 19 : 17;
  context.fillStyle = "#55534d";
  context.font =
    `italic ${fontSize}px "Times New Roman", Times, serif`;
  context.textAlign = "center";
  context.textBaseline = "middle";
}

function drawMsdChart(payload, renderOptions = {}) {
  const canvas = renderOptions.canvas ?? canvases.msd;
  const context = renderOptions.context ?? contexts.msd;
  const { width, height } = canvasSize(canvas, context, renderOptions);
  drawPaper(context, width, height);
  const frame = chartFrame(width, height, {
    left: width < 580 ? 56 : 72,
    bottom: 54,
    top: 30,
  });
  drawAxisLines(context, frame);

  const rows = payload.ensemble.series;
  const maximumTime = Math.max(...rows.map((row) => row.time_ps));
  const maximumMsd =
    Math.max(...rows.map((row) => row.msd_ci_high_nm2)) * 1.08;
  const xMap = (value) =>
    frame.left + (value / maximumTime) * frame.width;
  const yMap = (value) =>
    frame.bottom - (value / maximumMsd) * frame.height;

  for (let time = 0; time <= maximumTime; time += 25) {
    const x = xMap(time);
    drawGridLine(context, frame, "vertical", x);
    axisLabel(context, "center", width);
    context.fillText(String(time), x, frame.bottom + 18);
  }

  const yStep = maximumMsd <= 2.5 ? 0.5 : maximumMsd / 5;
  for (let value = 0; value <= maximumMsd + yStep * 0.2; value += yStep) {
    const y = yMap(value);
    drawGridLine(context, frame, "horizontal", y);
    axisLabel(context, "right", width);
    context.fillText(value.toFixed(1), frame.left - 9, y);
  }

  context.save();
  context.beginPath();
  context.rect(frame.left, frame.top, frame.width, frame.height);
  context.clip();

  const [fitStart, fitEnd] = payload.ensemble.fit_window_ps;
  context.fillStyle = "rgba(240, 183, 91, 0.095)";
  context.fillRect(
    xMap(fitStart),
    frame.top,
    xMap(fitEnd) - xMap(fitStart),
    frame.height,
  );

  context.fillStyle = "rgba(78, 177, 187, 0.19)";
  context.beginPath();
  rows.forEach((row, index) => {
    const x = xMap(row.time_ps);
    const y = yMap(row.msd_ci_high_nm2);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  [...rows].reverse().forEach((row) => {
    context.lineTo(xMap(row.time_ps), yMap(row.msd_ci_low_nm2));
  });
  context.closePath();
  context.fill();

  context.strokeStyle = "#667b76";
  context.lineWidth = 2.4;
  context.lineJoin = "round";
  context.beginPath();
  rows.forEach((row, index) => {
    const x = xMap(row.time_ps);
    const y = yMap(row.msd_nm2);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.stroke();

  const fit = (time) =>
    payload.ensemble.msd_fit_intercept_nm2 +
    payload.ensemble.msd_fit_slope_nm2_per_ps * time;
  context.setLineDash([8, 6]);
  context.strokeStyle = "#c47658";
  context.lineWidth = 2.1;
  context.beginPath();
  context.moveTo(xMap(fitStart), yMap(fit(fitStart)));
  context.lineTo(xMap(fitEnd), yMap(fit(fitEnd)));
  context.stroke();
  context.restore();

  axisTitle(context, width);
  context.fillText(
    "time, t (ps)",
    frame.left + frame.width / 2,
    height - 16,
  );
  context.save();
  context.translate(17, frame.top + frame.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("mean-squared displacement (nm²)", 0, 0);
  context.restore();

  const legendFontSize =
    width < 540 ? 10.5 : width > 1200 ? 13 : 11.5;
  const legendWidth =
    width < 540 ? 194 : width > 1200 ? 276 : 244;
  context.fillStyle = "rgba(244, 240, 232, 0.92)";
  context.strokeStyle = "rgba(62, 59, 53, 0.14)";
  context.lineWidth = 1;
  context.beginPath();
  context.roundRect(
    frame.left + 12,
    frame.top + 12,
    legendWidth,
    67,
    3,
  );
  context.fill();
  context.stroke();
  context.font =
    `${legendFontSize}px "Times New Roman", Times, serif`;
  context.textAlign = "left";
  context.textBaseline = "middle";

  context.fillStyle = "rgba(78, 177, 187, 0.2)";
  context.fillRect(frame.left + 23, frame.top + 23, 25, 10);
  context.fillStyle = "#625e57";
  context.fillText("95% confidence band", frame.left + 57, frame.top + 28);

  context.strokeStyle = "#667b76";
  context.lineWidth = 2.2;
  context.beginPath();
  context.moveTo(frame.left + 23, frame.top + 47);
  context.lineTo(frame.left + 48, frame.top + 47);
  context.stroke();
  context.fillStyle = "#625e57";
  context.fillText("ensemble MSD", frame.left + 57, frame.top + 47);

  context.setLineDash([6, 4]);
  context.strokeStyle = "#c47658";
  context.beginPath();
  context.moveTo(frame.left + 23, frame.top + 65);
  context.lineTo(frame.left + 48, frame.top + 65);
  context.stroke();
  context.setLineDash([]);
  context.fillStyle = "#625e57";
  context.fillText("20–100 ps fit", frame.left + 57, frame.top + 65);
}

function drawEndpointChart(payload, renderOptions = {}) {
  const canvas = renderOptions.canvas ?? canvases.endpoints;
  const context = renderOptions.context ?? contexts.endpoints;
  const { width, height } = canvasSize(canvas, context, renderOptions);
  drawPaper(context, width, height);
  const frame = chartFrame(width, height, {
    left: 58,
    right: 25,
    bottom: 54,
    top: 28,
  });
  drawAxisLines(context, frame);

  const endpoints = payload.ensemble.endpoints;
  const maximumAbsolute = Math.max(
    ...endpoints.flatMap((point) => [Math.abs(point.x_nm), Math.abs(point.y_nm)]),
    2.5,
  );
  const domain = Math.ceil(maximumAbsolute * 2) / 2;
  const xMap = (value) =>
    frame.left + ((value + domain) / (2 * domain)) * frame.width;
  const yMap = (value) =>
    frame.bottom - ((value + domain) / (2 * domain)) * frame.height;

  for (let value = -Math.floor(domain); value <= domain; value += 1) {
    const x = xMap(value);
    const y = yMap(value);
    drawGridLine(context, frame, "vertical", x);
    drawGridLine(context, frame, "horizontal", y);
    axisLabel(context, "center", width);
    context.fillText(String(value), x, frame.bottom + 18);
    axisLabel(context, "right", width);
    context.fillText(String(value), frame.left - 8, y);
  }

  context.strokeStyle = "rgba(45, 72, 72, 0.46)";
  context.lineWidth = 1.1;
  context.beginPath();
  context.moveTo(xMap(0), frame.top);
  context.lineTo(xMap(0), frame.bottom);
  context.moveTo(frame.left, yMap(0));
  context.lineTo(frame.right, yMap(0));
  context.stroke();

  context.save();
  context.beginPath();
  context.rect(frame.left, frame.top, frame.width, frame.height);
  context.clip();
  endpoints.forEach((point, index) => {
    const alpha = 0.46 + (index % 6) * 0.035;
    context.fillStyle = `rgba(102, 123, 118, ${alpha})`;
    context.beginPath();
    context.arc(xMap(point.x_nm), yMap(point.y_nm), 4.3, 0, Math.PI * 2);
    context.fill();
  });

  const meanX = payload.ensemble.final_mean_x_nm;
  const meanY = payload.ensemble.final_mean_y_nm;
  const [xLow, xHigh] = payload.ensemble.final_mean_x_ci_nm;
  const [yLow, yHigh] = payload.ensemble.final_mean_y_ci_nm;
  const meanScreenX = xMap(meanX);
  const meanScreenY = yMap(meanY);

  context.strokeStyle = "#c47658";
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(xMap(xLow), meanScreenY);
  context.lineTo(xMap(xHigh), meanScreenY);
  context.moveTo(meanScreenX, yMap(yLow));
  context.lineTo(meanScreenX, yMap(yHigh));
  context.stroke();
  context.fillStyle = "#c47658";
  context.beginPath();
  context.arc(meanScreenX, meanScreenY, 6.2, 0, Math.PI * 2);
  context.fill();
  context.strokeStyle = "#f4f0e8";
  context.lineWidth = 1.5;
  context.stroke();
  context.restore();

  axisTitle(context, width);
  context.fillText(
    "final x displacement (nm)",
    frame.left + frame.width / 2,
    height - 16,
  );
  context.save();
  context.translate(17, frame.top + frame.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("final y displacement (nm)", 0, 0);
  context.restore();
}

function drawConvergenceChart(payload, renderOptions = {}) {
  const canvas = renderOptions.canvas ?? canvases.convergence;
  const context = renderOptions.context ?? contexts.convergence;
  const { width, height } = canvasSize(canvas, context, renderOptions);
  drawPaper(context, width, height);
  const frame = chartFrame(width, height, {
    left: width < 560 ? 61 : 82,
    bottom: 58,
    top: 31,
  });
  drawAxisLines(context, frame);

  const rows = payload.validation.controlled_convergence;
  const xValues = rows.map((row) => Math.log10(row.time_step_ps));
  const yValues = rows.map((row) => Math.log10(row.rms_endpoint_error_nm));
  const minimumX = Math.min(...xValues) - 0.04;
  const maximumX = Math.max(...xValues) + 0.04;
  const minimumY = Math.min(...yValues) - 0.08;
  const maximumY = Math.max(...yValues) + 0.08;
  const xMap = (value) =>
    frame.left +
    ((Math.log10(value) - minimumX) / (maximumX - minimumX)) * frame.width;
  const yMap = (value) =>
    frame.bottom -
    ((Math.log10(value) - minimumY) / (maximumY - minimumY)) * frame.height;

  rows.forEach((row) => {
    const x = xMap(row.time_step_ps);
    const y = yMap(row.rms_endpoint_error_nm);
    drawGridLine(context, frame, "vertical", x);
    drawGridLine(context, frame, "horizontal", y);
    axisLabel(context, "center", width);
    context.fillText(
      row.time_step_ps.toFixed(4),
      x,
      frame.bottom + 19,
    );
    axisLabel(context, "right", width);
    context.fillText(
      row.rms_endpoint_error_nm.toFixed(3),
      frame.left - 9,
      y,
    );
  });

  context.save();
  context.beginPath();
  context.rect(frame.left, frame.top, frame.width, frame.height);
  context.clip();

  const referenceCoefficient =
    rows[0].rms_endpoint_error_nm / rows[0].time_step_ps;
  context.setLineDash([8, 6]);
  context.strokeStyle = "#c47658";
  context.lineWidth = 2;
  context.beginPath();
  rows.forEach((row, index) => {
    const x = xMap(row.time_step_ps);
    const y = yMap(referenceCoefficient * row.time_step_ps);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.stroke();
  context.setLineDash([]);

  context.strokeStyle = "#667b76";
  context.lineWidth = 2.5;
  context.beginPath();
  rows.forEach((row, index) => {
    const x = xMap(row.time_step_ps);
    const y = yMap(row.rms_endpoint_error_nm);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.stroke();

  rows.forEach((row) => {
    context.fillStyle = "#667b76";
    context.beginPath();
    context.arc(
      xMap(row.time_step_ps),
      yMap(row.rms_endpoint_error_nm),
      5.2,
      0,
      Math.PI * 2,
    );
    context.fill();
    context.strokeStyle = "#f4f0e8";
    context.lineWidth = 1.5;
    context.stroke();
  });
  context.restore();

  axisTitle(context, width);
  context.fillText(
    "time step, Δt (ps) — finer to the left",
    frame.left + frame.width / 2,
    height - 17,
  );
  context.save();
  context.translate(19, frame.top + frame.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("RMS endpoint error (nm)", 0, 0);
  context.restore();

  context.fillStyle = "rgba(244, 240, 232, 0.9)";
  context.strokeStyle = "rgba(62, 59, 53, 0.14)";
  const noteWidth = Math.min(
    frame.width - 26,
    width > 1000 ? 330 : width < 560 ? 220 : 260,
  );
  const noteHeight = width > 1000 ? 62 : 52;
  context.beginPath();
  context.roundRect(
    frame.left + 13,
    frame.top + 12,
    noteWidth,
    noteHeight,
    3,
  );
  context.fill();
  context.stroke();
  context.fillStyle = "#58564f";
  context.font =
    `${width > 1000 ? 13 : 10.5}px "Times New Roman", Times, serif`;
  context.textAlign = "left";
  context.fillText(
    `minimum observed order = ${payload.validation.minimum_observed_order.toFixed(3)}`,
    frame.left + 25,
    frame.top + 31,
  );
  context.fillText(
    "measured error follows first-order reference",
    frame.left + 25,
    frame.top + 48,
  );
}

function renderAll() {
  if (!evidence) return;
  drawMsdChart(evidence);
  drawEndpointChart(evidence);
  drawConvergenceChart(evidence);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportFigure(button) {
  if (!evidence) return;
  const kind = button.dataset.exportFigure;
  const settings = exportSettings[kind];
  const renderer = {
    msd: drawMsdChart,
    endpoints: drawEndpointChart,
    convergence: drawConvergenceChart,
  }[kind];
  if (!settings || !renderer) return;

  const exportCanvas = document.createElement("canvas");
  const exportContext = exportCanvas.getContext("2d", { alpha: false });
  renderer(evidence, {
    canvas: exportCanvas,
    context: exportContext,
    width: settings.width,
    height: settings.height,
    pixelRatio: 2,
  });

  const label = button.querySelector("span");
  const originalLabel = label?.textContent;
  button.disabled = true;
  exportCanvas.toBlob((blob) => {
    if (blob) {
      downloadBlob(blob, settings.filename);
      button.classList.add("is-complete");
      if (label) label.textContent = "PNG saved";
    }
    button.disabled = false;
    window.setTimeout(() => {
      button.classList.remove("is-complete");
      if (label && originalLabel) label.textContent = originalLabel;
    }, 1800);
  }, "image/png");
}

function populateMetrics(payload) {
  const diffusion = payload.ensemble.diffusion_coefficient_nm2_per_ps;
  const [low, high] = payload.ensemble.diffusion_ci_nm2_per_ps;
  outputs.diffusion.textContent = `${diffusion.toExponential(2)} nm² ps⁻¹`;
  outputs.diffusionCi.textContent =
    `95% CI ${low.toExponential(2)}–${high.toExponential(2)}`;
  outputs.rSquared.textContent =
    `R² = ${payload.ensemble.msd_fit_r_squared.toFixed(3)}`;
  outputs.runCount.textContent = String(payload.ensemble.run_count);
  outputs.collisionError.textContent =
    payload.validation.worst_normalized_collision_error.toExponential(2);
  outputs.provenance.textContent =
    `Verified Python evidence · ${payload.ensemble.run_count} seeds · ` +
    `${payload.ensemble.source_series_points.toLocaleString()} recorded time points`;
}

async function loadEvidence() {
  try {
    let payload = window.TASK02_EVIDENCE;
    if (!payload) {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      payload = await response.json();
    }
    if (
      Array.isArray(payload?.ensemble?.series) &&
      payload.ensemble.series.length === 0
    ) {
      outputs.provenance.textContent = "No verified trajectories available";
      outputs.content.hidden = true;
      outputs.error.hidden = true;
      outputs.empty.hidden = false;
      outputs.section.classList.remove("is-loading");
      return;
    }
    if (!validateEvidence(payload)) {
      throw new Error("Task 2 evidence failed schema validation");
    }

    evidence = payload;
    populateMetrics(payload);
    outputs.content.hidden = false;
    outputs.error.hidden = true;
    outputs.empty.hidden = true;
    outputs.section.classList.remove("is-loading");
    requestAnimationFrame(renderAll);
  } catch (error) {
    console.error(error);
    outputs.provenance.textContent = "Verified evidence unavailable";
    outputs.content.hidden = true;
    outputs.error.hidden = false;
    outputs.empty.hidden = true;
    outputs.section.classList.remove("is-loading");
  }
}

new ResizeObserver(() => {
  cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(renderAll);
}).observe(outputs.content);

exportButtons.forEach((button) => {
  button.addEventListener("click", () => exportFigure(button));
});

loadEvidence();
})();
