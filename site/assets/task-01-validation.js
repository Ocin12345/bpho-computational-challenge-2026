const DATA_URL = new URL("../data/task-01-validation.json", import.meta.url);

const canvases = {
  msd: document.querySelector("#validation-msd-canvas"),
  angle: document.querySelector("#validation-angle-canvas"),
  radial: document.querySelector("#validation-radial-canvas"),
};

const contexts = {
  msd: canvases.msd.getContext("2d"),
  angle: canvases.angle.getContext("2d"),
  radial: canvases.radial.getContext("2d"),
};

const outputs = {
  provenance: document.querySelector("[data-validation-provenance]"),
  slope: document.querySelector("[data-validation-slope]"),
  angle: document.querySelector("[data-validation-angle]"),
  r50: document.querySelector("[data-validation-r50]"),
  r95: document.querySelector("[data-validation-r95]"),
  lock: document.querySelector("[data-validation-lock]"),
  lockContainer: document.querySelector(".validation-lock"),
};
const laboratory = document.querySelector("[data-validation-laboratory]");
const errorOutput = document.querySelector("[data-validation-error]");

const NATURAL_PALETTE = [
  [67, 56, 134],
  [47, 103, 178],
  [28, 150, 143],
  [112, 167, 73],
  [226, 163, 54],
  [220, 91, 72],
  [181, 55, 118],
];

let validationData = null;
let resizeFrame = 0;

function canvasSize(canvas, context) {
  const width = Math.max(300, canvas.clientWidth);
  const height = Math.max(320, canvas.clientHeight);
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * pixelRatio);
  canvas.height = Math.round(height * pixelRatio);
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  return { width, height };
}

function colourAt(progress, alpha = 1) {
  const value = Math.min(1, Math.max(0, progress));
  const scaled = value * (NATURAL_PALETTE.length - 1);
  const lowerIndex = Math.floor(scaled);
  const upperIndex = Math.min(
    NATURAL_PALETTE.length - 1,
    lowerIndex + 1,
  );
  const blend = scaled - lowerIndex;
  const lower = NATURAL_PALETTE[lowerIndex];
  const upper = NATURAL_PALETTE[upperIndex];
  const channels = lower.map((channel, index) =>
    Math.round(channel + (upper[index] - channel) * blend),
  );
  return `rgba(${channels[0]}, ${channels[1]}, ${channels[2]}, ${alpha})`;
}

function drawBackground(context, width, height) {
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#f6f2ea";
  context.fillRect(0, 0, width, height);
  const wash = context.createRadialGradient(
    width * 0.54,
    height * 0.48,
    0,
    width * 0.54,
    height * 0.48,
    Math.max(width, height) * 0.72,
  );
  wash.addColorStop(0, "rgba(182, 152, 93, 0.05)");
  wash.addColorStop(1, "rgba(255, 255, 255, 0)");
  context.fillStyle = wash;
  context.fillRect(0, 0, width, height);
}

function drawAxes(context, frame) {
  context.strokeStyle = "rgba(55, 50, 42, 0.19)";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(frame.left, frame.top);
  context.lineTo(frame.left, frame.bottom);
  context.lineTo(frame.right, frame.bottom);
  context.stroke();
}

function labelStyle(context, align = "center") {
  context.fillStyle = "#756e62";
  context.font = '10px "Times New Roman", Times, serif';
  context.textAlign = align;
  context.textBaseline = "middle";
}

function chartFrame(width, height, options = {}) {
  const left = options.left ?? 62;
  const right = width - (options.right ?? 24);
  const top = options.top ?? 24;
  const bottom = height - (options.bottom ?? 48);
  return {
    left,
    right,
    top,
    bottom,
    width: right - left,
    height: bottom - top,
  };
}

function drawMsdChart(payload) {
  const context = contexts.msd;
  const { width, height } = canvasSize(canvases.msd, context);
  drawBackground(context, width, height);
  const frame = chartFrame(width, height, {
    left: width < 600 ? 58 : 74,
    bottom: 54,
  });
  drawAxes(context, frame);

  const rows = payload.msd.rows;
  const xValues = rows.map((row) => Math.log10(row.n_steps));
  const yLowValues = rows.map((row) =>
    Math.log10(
      Math.max(
        Number.EPSILON,
        row.mean_squared_displacement - row.ci95_half_width_msd,
      ),
    ),
  );
  const yHighValues = rows.map((row) =>
    Math.log10(row.mean_squared_displacement + row.ci95_half_width_msd),
  );
  const minimumX = Math.min(...xValues);
  const maximumX = Math.max(...xValues);
  const minimumY = Math.floor(Math.min(...yLowValues));
  const maximumY = Math.ceil(Math.max(...yHighValues));

  const xMap = (value) =>
    frame.left +
    ((Math.log10(value) - minimumX) / (maximumX - minimumX)) * frame.width;
  const yMap = (value) =>
    frame.bottom -
    ((Math.log10(value) - minimumY) / (maximumY - minimumY)) * frame.height;

  rows.forEach((row, index) => {
    if (width >= 620 || index % 2 === 0 || index === rows.length - 1) {
      const x = xMap(row.n_steps);
      context.strokeStyle = "rgba(55, 50, 42, 0.07)";
      context.beginPath();
      context.moveTo(x, frame.top);
      context.lineTo(x, frame.bottom);
      context.stroke();
      labelStyle(context);
      context.fillText(
        row.n_steps.toLocaleString(),
        x,
        frame.bottom + 20,
      );
    }
  });

  for (let exponent = minimumY; exponent <= maximumY; exponent += 1) {
    const value = 10 ** exponent;
    const y = yMap(value);
    context.strokeStyle = "rgba(55, 50, 42, 0.07)";
    context.beginPath();
    context.moveTo(frame.left, y);
    context.lineTo(frame.right, y);
    context.stroke();
    labelStyle(context, "right");
    context.fillText(
      exponent >= 0 ? value.toLocaleString() : value.toExponential(0),
      frame.left - 9,
      y,
    );
  }

  context.save();
  context.beginPath();
  context.rect(frame.left, frame.top, frame.width, frame.height);
  context.clip();

  context.strokeStyle = "#3f64b2";
  context.lineWidth = 2;
  context.beginPath();
  rows.forEach((row, index) => {
    const x = xMap(row.n_steps);
    const y = yMap(row.theoretical_msd);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.stroke();

  rows.forEach((row, index) => {
    const x = xMap(row.n_steps);
    const y = yMap(row.mean_squared_displacement);
    const yLow = yMap(
      Math.max(
        Number.EPSILON,
        row.mean_squared_displacement - row.ci95_half_width_msd,
      ),
    );
    const yHigh = yMap(
      row.mean_squared_displacement + row.ci95_half_width_msd,
    );
    context.strokeStyle = "rgba(21, 112, 109, 0.7)";
    context.lineWidth = 1.1;
    context.beginPath();
    context.moveTo(x, yLow);
    context.lineTo(x, yHigh);
    context.moveTo(x - 4, yLow);
    context.lineTo(x + 4, yLow);
    context.moveTo(x - 4, yHigh);
    context.lineTo(x + 4, yHigh);
    context.stroke();
    context.fillStyle = colourAt(index / (rows.length - 1));
    context.beginPath();
    context.arc(x, y, 4.4, 0, Math.PI * 2);
    context.fill();
    context.strokeStyle = "#f6f2ea";
    context.lineWidth = 1.4;
    context.stroke();
  });
  context.restore();

  context.fillStyle = "#514b42";
  context.font = 'italic 17px "Times New Roman", Times, serif';
  context.textAlign = "center";
  context.fillText("Number of steps, N", frame.left + frame.width / 2, height - 16);
  context.save();
  context.translate(18, frame.top + frame.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("Mean squared displacement, ⟨r²⟩", 0, 0);
  context.restore();

  const boxWidth = width < 600 ? 200 : 270;
  context.fillStyle = "rgba(246, 242, 234, 0.92)";
  context.strokeStyle = "rgba(55, 50, 42, 0.14)";
  context.lineWidth = 1;
  context.beginPath();
  context.roundRect(frame.left + 12, frame.top + 12, boxWidth, 54, 8);
  context.fill();
  context.stroke();
  context.fillStyle = "#38342d";
  context.font = '11px "Times New Roman", Times, serif';
  context.textAlign = "left";
  context.fillText(
    `Measured coefficient: ${payload.msd.weighted_coefficient.toFixed(4)} ± ${payload.msd.weighted_coefficient_ci95.toFixed(4)}`,
    frame.left + 23,
    frame.top + 32,
  );
  context.fillStyle = "#a4432f";
  context.fillText("Theory: 1.0000", frame.left + 23, frame.top + 51);
}

function drawAngularChart(payload) {
  const context = contexts.angle;
  const { width, height } = canvasSize(canvases.angle, context);
  drawBackground(context, width, height);
  const frame = chartFrame(width, height, { left: 58, bottom: 50 });
  drawAxes(context, frame);

  const evidence = payload.angular;
  const counts = evidence.bins.map((bin) => bin.count);
  const maximum = Math.max(...counts, evidence.expected_per_bin) * 1.08;
  const yMap = (value) =>
    frame.bottom - (value / maximum) * frame.height;
  const barWidth = frame.width / counts.length;

  [0, evidence.expected_per_bin, maximum].forEach((value) => {
    const y = yMap(value);
    context.strokeStyle = "rgba(55, 50, 42, 0.07)";
    context.beginPath();
    context.moveTo(frame.left, y);
    context.lineTo(frame.right, y);
    context.stroke();
    labelStyle(context, "right");
    context.fillText(Math.round(value).toLocaleString(), frame.left - 8, y);
  });

  counts.forEach((count, index) => {
    const x = frame.left + index * barWidth + 1;
    const y = yMap(count);
    context.fillStyle = colourAt(index / (counts.length - 1), 0.76);
    context.fillRect(
      x,
      y,
      Math.max(1, barWidth - 2),
      frame.bottom - y,
    );
  });

  context.save();
  context.setLineDash([7, 6]);
  context.strokeStyle = "#3f64b2";
  context.lineWidth = 1.3;
  const expectedY = yMap(evidence.expected_per_bin);
  context.beginPath();
  context.moveTo(frame.left, expectedY);
  context.lineTo(frame.right, expectedY);
  context.stroke();
  context.restore();

  const angleLabels = [
    [0, "0"],
    [0.25, "π/2"],
    [0.5, "π"],
    [0.75, "3π/2"],
    [1, "2π"],
  ];
  labelStyle(context);
  angleLabels.forEach(([position, label]) => {
    context.fillText(
      label,
      frame.left + position * frame.width,
      frame.bottom + 20,
    );
  });

  context.fillStyle = "#514b42";
  context.font = 'italic 17px "Times New Roman", Times, serif';
  context.textAlign = "center";
  context.fillText("Direction, θ", frame.left + frame.width / 2, height - 16);
  context.save();
  context.translate(17, frame.top + frame.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("Sample count", 0, 0);
  context.restore();

  context.fillStyle = "#38342d";
  context.font = '10px "Times New Roman", Times, serif';
  context.textAlign = "right";
  context.fillText(
    "uniform expectation",
    frame.right - 5,
    expectedY - 9,
  );
}

function drawRadialChart(payload) {
  const context = contexts.radial;
  const { width, height } = canvasSize(canvases.radial, context);
  drawBackground(context, width, height);
  const frame = chartFrame(width, height, { left: 58, bottom: 50 });
  drawAxes(context, frame);

  const evidence = payload.radial;
  const bins = evidence.bins;
  const maximumRadius = bins.at(-1).end_radius;
  const maximumCount =
    Math.max(
      ...bins.map((bin) =>
        Math.max(bin.count, bin.rayleigh_expected_count),
      ),
    ) * 1.08;
  const xMap = (value) =>
    frame.left + (value / maximumRadius) * frame.width;
  const yMap = (value) =>
    frame.bottom - (value / maximumCount) * frame.height;
  const barWidth = frame.width / bins.length;

  [0, maximumCount / 2, maximumCount].forEach((value) => {
    const y = yMap(value);
    context.strokeStyle = "rgba(55, 50, 42, 0.07)";
    context.beginPath();
    context.moveTo(frame.left, y);
    context.lineTo(frame.right, y);
    context.stroke();
    labelStyle(context, "right");
    context.fillText(Math.round(value).toLocaleString(), frame.left - 8, y);
  });

  bins.forEach((bin, index) => {
    const x = frame.left + index * barWidth + 1;
    const y = yMap(bin.count);
    context.fillStyle = "rgba(28, 150, 143, 0.34)";
    context.fillRect(
      x,
      y,
      Math.max(1, barWidth - 2),
      frame.bottom - y,
    );
  });

  context.strokeStyle = "#c94f70";
  context.lineWidth = 2;
  context.lineJoin = "round";
  context.beginPath();
  bins.forEach((bin, index) => {
    const radius = (bin.start_radius + bin.end_radius) / 2;
    const x = xMap(radius);
    const y = yMap(bin.rayleigh_expected_count);
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
  context.stroke();

  [
    [evidence.radius_50, "r₅₀", "#d68e25", [5, 6]],
    [evidence.radius_95, "r₉₅", "#43578f", [2, 6]],
  ].forEach(([radius, label, colour, dash]) => {
    const x = xMap(radius);
    context.save();
    context.setLineDash(dash);
    context.strokeStyle = colour;
    context.beginPath();
    context.moveTo(x, frame.top);
    context.lineTo(x, frame.bottom);
    context.stroke();
    context.restore();
    context.fillStyle = colour;
    context.font = '10px "Times New Roman", Times, serif';
    context.textAlign = "center";
    context.fillText(label, x, frame.top + 11);
  });

  labelStyle(context);
  [0, evidence.radius_50, evidence.radius_95, maximumRadius].forEach(
    (value) => {
      context.fillText(value.toFixed(1), xMap(value), frame.bottom + 20);
    },
  );

  context.fillStyle = "#514b42";
  context.font = 'italic 17px "Times New Roman", Times, serif';
  context.textAlign = "center";
  context.fillText("Endpoint distance, r", frame.left + frame.width / 2, height - 16);
  context.save();
  context.translate(17, frame.top + frame.height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("Endpoint count", 0, 0);
  context.restore();

  context.fillStyle = "#a4432f";
  context.font = '10px "Times New Roman", Times, serif';
  context.textAlign = "right";
  context.fillText("Rayleigh theory", frame.right - 6, frame.top + 14);
}

function validatePayload(payload) {
  if (
    payload.schema_version !== 1 ||
    !Array.isArray(payload.angular?.bins) ||
    !Array.isArray(payload.msd?.rows) ||
    !Array.isArray(payload.radial?.bins)
  ) {
    throw new Error("Task 1 validation data has an unsupported schema");
  }

  const checks = {
    angle: payload.angular.maximum_relative_deviation <= 0.04,
    msd:
      Math.abs(
        payload.msd.weighted_coefficient -
          payload.msd.theoretical_coefficient,
      ) <= payload.msd.weighted_coefficient_ci95 &&
      payload.msd.maximum_absolute_ratio_error <= 0.02,
    radial:
      Math.abs(payload.radial.observed_fraction_50 - 0.5) <= 0.015 &&
      Math.abs(payload.radial.observed_fraction_95 - 0.95) <= 0.01,
  };
  return { checks, passed: Object.values(checks).every(Boolean) };
}

function updateValidationSummary(payload, validation) {
  outputs.slope.textContent =
    `${payload.msd.weighted_coefficient.toFixed(4)} ± ${payload.msd.weighted_coefficient_ci95.toFixed(4)}`;
  outputs.angle.textContent =
    `${(payload.angular.maximum_relative_deviation * 100).toFixed(2)}%`;
  outputs.r50.textContent =
    `${(payload.radial.observed_fraction_50 * 100).toFixed(2)}%`;
  outputs.r95.textContent =
    `${(payload.radial.observed_fraction_95 * 100).toFixed(2)}%`;
  outputs.provenance.textContent =
    `${payload.angular.sample_count.toLocaleString()} exact directions · ${payload.radial.n_walks.toLocaleString()} exact endpoints · seed ${payload.seed}`;

  if (validation.passed) {
    outputs.lock.textContent = "Task 1 validation complete";
    outputs.lockContainer.dataset.locked = "true";
  } else {
    outputs.lock.textContent = "Task 1 not locked";
    outputs.lockContainer.dataset.locked = "false";
  }
}

function drawAll() {
  if (!validationData) return;
  drawMsdChart(validationData);
  drawAngularChart(validationData);
  drawRadialChart(validationData);
}

function scheduleRedraw() {
  cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(drawAll);
}

async function loadValidation() {
  laboratory.classList.add("is-loading");
  laboratory.classList.remove("has-error");
  errorOutput.hidden = true;
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Validation data returned HTTP ${response.status}`);
    }
    const payload = await response.json();
    const validation = validatePayload(payload);
    validationData = payload;
    updateValidationSummary(payload, validation);
    drawAll();
    laboratory.classList.remove("is-loading");
  } catch (error) {
    laboratory.classList.remove("is-loading");
    laboratory.classList.add("has-error");
    errorOutput.hidden = false;
    errorOutput.textContent =
      error instanceof Error
        ? `Validation evidence could not be loaded: ${error.message}. This task remains unlocked.`
        : "Validation evidence could not be loaded. This task remains unlocked.";
    outputs.provenance.textContent =
      error instanceof Error ? error.message : "Unknown validation error";
    outputs.lock.textContent = "Task 1 not locked";
    outputs.lockContainer.dataset.locked = "false";
  }
}

new ResizeObserver(scheduleRedraw).observe(
  document.querySelector(".validation-charts"),
);
window.addEventListener("resize", scheduleRedraw);

loadValidation();

if (document.fonts) {
  document.fonts.ready.then(scheduleRedraw);
}
