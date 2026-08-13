import { loadTask04Evidence } from "./task-04-evidence.js";

const chartCanvas = document.querySelector("#stopping-potential-chart");
const chartContext = chartCanvas.getContext("2d");

const comparisonLaboratory = document.querySelector(
  "[data-comparison-laboratory]",
);
const chartError = document.querySelector("[data-chart-error]");
const chartTooltip = document.querySelector("[data-chart-tooltip]");

const controls = {
  axisModes: [...document.querySelectorAll("[data-axis-mode]")],
  extrapolation: document.querySelector("[data-toggle-extrapolation]"),
};

const outputs = {
  chartStatus: document.querySelector("[data-chart-status]"),
  axisExplanation: document.querySelector("[data-axis-explanation]"),
  selectedMetal: document.querySelector("[data-selected-metal]"),
  selectedFrequency: document.querySelector("[data-selected-frequency]"),
  selectedWavelength: document.querySelector("[data-selected-wavelength]"),
  materialLedger: document.querySelector("[data-material-ledger]"),
};

const state = {
  evidence: null,
  selectedSymbol: "Cu",
  axisMode: "frequency",
  extrapolation: false,
  chartSize: { width: 1, height: 1 },
  chartFrame: null,
};

function canvasSize(canvas, context, minimumHeight) {
  const width = Math.max(300, canvas.clientWidth);
  const height = Math.max(minimumHeight, canvas.clientHeight);
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const bitmapWidth = Math.round(width * pixelRatio);
  const bitmapHeight = Math.round(height * pixelRatio);
  if (canvas.width !== bitmapWidth || canvas.height !== bitmapHeight) {
    canvas.width = bitmapWidth;
    canvas.height = bitmapHeight;
  }
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  return { width, height, pixelRatio };
}

function selectedMaterial() {
  return state.evidence?.materials.find(
    (material) => material.symbol === state.selectedSymbol,
  );
}

function formatThresholdFrequency(hz) {
  return `${(hz / 1e15).toFixed(4)} PHz`;
}

function formatWavelength(nm) {
  return `${nm.toFixed(1)} nm`;
}

function updateReadouts() {
  const material = selectedMaterial();
  if (!material) return;

  outputs.selectedMetal.textContent =
    `${material.name} (${material.symbol})`;
  outputs.selectedFrequency.textContent = formatThresholdFrequency(
    material.cutoffFrequencyHz,
  );
  outputs.selectedWavelength.textContent = formatWavelength(
    material.cutoffWavelengthNm,
  );

  document.querySelectorAll("[data-material-row]").forEach((row) => {
    const active = row.dataset.materialRow === state.selectedSymbol;
    row.classList.toggle("is-active", active);
    row.setAttribute("aria-pressed", String(active));
  });
}


function chartRange() {
  if (state.axisMode === "frequency") {
    return {
      xMin: 0.4,
      xMax: 2.4,
      yMin: state.extrapolation ? -4 : 0,
      yMax: 8.2,
      xTitle: "Photon frequency, f / PHz",
      yTitle: "Stopping potential, Vs / V",
      xTicks: [0.4, 0.8, 1.2, 1.6, 2.0, 2.4],
      yTicks: state.extrapolation
        ? [-4, -2, 0, 2, 4, 6, 8]
        : [0, 2, 4, 6, 8],
    };
  }
  return {
    xMin: 150,
    xMax: 700,
    yMin: state.extrapolation ? -4 : 0,
    yMax: 6.4,
    xTitle: "Vacuum wavelength, λ / nm",
    yTitle: "Stopping potential, Vs / V",
    xTicks: [150, 250, 350, 450, 550, 650],
    yTicks: state.extrapolation ? [-4, -2, 0, 2, 4, 6] : [0, 1, 2, 3, 4, 5, 6],
  };
}

function chartValue(material, xValue) {
  const constants = state.evidence.manifest.constants;
  if (state.axisMode === "frequency") {
    return (
      constants.planck_over_charge_v_s * xValue * 1e15 -
      material.workFunctionEv
    );
  }
  return constants.hc_over_charge_v_m / (xValue * 1e-9) - material.workFunctionEv;
}

function drawCurve(context, frame, range, material, index, selected) {
  const pointCount = 360;
  const dashPatterns = [[], [8, 5], [3, 5], [12, 5, 2, 5]];
  const mapX = (value) =>
    frame.left +
    ((value - range.xMin) / (range.xMax - range.xMin)) * frame.width;
  const mapY = (value) =>
    frame.bottom -
    ((value - range.yMin) / (range.yMax - range.yMin)) * frame.height;

  context.save();
  context.beginPath();
  context.rect(frame.left, frame.top, frame.width, frame.height);
  context.clip();

  if (state.extrapolation) {
    context.strokeStyle = selected
      ? "rgba(138, 100, 37, 0.48)"
      : "rgba(49, 46, 40, 0.12)";
    context.lineWidth = selected ? 1.4 : 0.8;
    context.setLineDash([4, 7]);
    context.beginPath();
    for (let point = 0; point <= pointCount; point += 1) {
      const xValue =
        range.xMin + (point / pointCount) * (range.xMax - range.xMin);
      const yValue = chartValue(material, xValue);
      const x = mapX(xValue);
      const y = mapY(yValue);
      if (point === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    }
    context.stroke();
  }

  context.strokeStyle = selected
    ? "#a8792d"
    : `rgba(47, 44, 38, ${0.2 + (index % 3) * 0.05})`;
  context.lineWidth = selected ? 3 : 1.05;
  context.setLineDash(selected ? [] : dashPatterns[index % dashPatterns.length]);
  context.lineCap = "round";
  context.lineJoin = "round";
  context.beginPath();
  let drawing = false;
  for (let point = 0; point <= pointCount; point += 1) {
    const xValue =
      range.xMin + (point / pointCount) * (range.xMax - range.xMin);
    const yValue = chartValue(material, xValue);
    const physical =
      state.axisMode === "frequency"
        ? xValue * 1e15 >= material.cutoffFrequencyHz
        : xValue <= material.cutoffWavelengthNm;
    if (!physical || yValue < -1e-10) {
      drawing = false;
      continue;
    }
    const x = mapX(xValue);
    const y = mapY(Math.max(0, yValue));
    if (!drawing) {
      context.moveTo(x, y);
      drawing = true;
    } else {
      context.lineTo(x, y);
    }
  }
  context.stroke();

  const thresholdX =
    state.axisMode === "frequency"
      ? material.cutoffFrequencyHz / 1e15
      : material.cutoffWavelengthNm;
  if (thresholdX >= range.xMin && thresholdX <= range.xMax) {
    context.fillStyle = selected ? "#a8792d" : "rgba(47, 44, 38, 0.34)";
    context.beginPath();
    context.arc(mapX(thresholdX), mapY(0), selected ? 5 : 2.5, 0, Math.PI * 2);
    context.fill();
  }

  context.restore();
}

function drawChart() {
  if (!state.evidence) return;
  const size = canvasSize(chartCanvas, chartContext, 470);
  state.chartSize = size;
  const { width, height } = size;
  const range = chartRange();
  const compact = width < 620;
  const frame = {
    left: compact ? 58 : 78,
    right: width - (compact ? 18 : 32),
    top: compact ? 30 : 38,
    bottom: height - (compact ? 62 : 70),
  };
  frame.width = frame.right - frame.left;
  frame.height = frame.bottom - frame.top;
  state.chartFrame = { ...frame, range };

  const mapX = (value) =>
    frame.left +
    ((value - range.xMin) / (range.xMax - range.xMin)) * frame.width;
  const mapY = (value) =>
    frame.bottom -
    ((value - range.yMin) / (range.yMax - range.yMin)) * frame.height;

  chartContext.clearRect(0, 0, width, height);
  chartContext.fillStyle = "#f8f4eb";
  chartContext.fillRect(0, 0, width, height);

  chartContext.font = `${compact ? 10 : 12}px "Times New Roman", Times, serif`;
  chartContext.textBaseline = "middle";
  chartContext.lineWidth = 1;

  range.yTicks.forEach((tick) => {
    const y = mapY(tick);
    chartContext.strokeStyle =
      Math.abs(tick) < 1e-9
        ? "rgba(48, 44, 37, 0.28)"
        : "rgba(48, 44, 37, 0.08)";
    chartContext.beginPath();
    chartContext.moveTo(frame.left, y);
    chartContext.lineTo(frame.right, y);
    chartContext.stroke();
    chartContext.fillStyle = "#6f675b";
    chartContext.textAlign = "right";
    chartContext.fillText(String(tick).replace("-", "−"), frame.left - 10, y);
  });

  range.xTicks.forEach((tick) => {
    const x = mapX(tick);
    chartContext.strokeStyle = "rgba(48, 44, 37, 0.07)";
    chartContext.beginPath();
    chartContext.moveTo(x, frame.top);
    chartContext.lineTo(x, frame.bottom);
    chartContext.stroke();
    chartContext.fillStyle = "#6f675b";
    chartContext.textAlign = "center";
    chartContext.fillText(
      state.axisMode === "frequency" ? tick.toFixed(1) : String(tick),
      x,
      frame.bottom + 21,
    );
  });

  chartContext.strokeStyle = "rgba(48, 44, 37, 0.28)";
  chartContext.beginPath();
  chartContext.moveTo(frame.left, frame.top);
  chartContext.lineTo(frame.left, frame.bottom);
  chartContext.lineTo(frame.right, frame.bottom);
  chartContext.stroke();

  const selected = selectedMaterial();
  state.evidence.materials
    .filter((material) => material.symbol !== selected.symbol)
    .forEach((material, index) =>
      drawCurve(chartContext, frame, range, material, index, false),
    );
  drawCurve(chartContext, frame, range, selected, 0, true);

  chartContext.fillStyle = "#3f3a32";
  chartContext.font = `italic ${compact ? 14 : 18}px "Times New Roman", Times, serif`;
  chartContext.textAlign = "center";
  chartContext.fillText(
    range.xTitle,
    frame.left + frame.width / 2,
    height - 20,
  );
  chartContext.save();
  chartContext.translate(compact ? 17 : 20, frame.top + frame.height / 2);
  chartContext.rotate(-Math.PI / 2);
  chartContext.fillText(range.yTitle, 0, 0);
  chartContext.restore();

  chartContext.fillStyle = "#a8792d";
  chartContext.font = `italic ${compact ? 16 : 20}px "Times New Roman", Times, serif`;
  chartContext.textAlign = "right";
  chartContext.fillText(
    `${selected.name} · ${selected.symbol}`,
    frame.right - 4,
    frame.top + 14,
  );
  chartContext.fillStyle = "#625a4f";
  chartContext.font = `${compact ? 9 : 11}px "Times New Roman", Times, serif`;
  chartContext.fillText(
    "Ag = Al = Pb exactly",
    frame.right - 4,
    frame.top + (compact ? 31 : 35),
  );

  chartCanvas.setAttribute(
    "aria-label",
    `Stopping potential versus ${state.axisMode} for nine metals; ${selected.name} is highlighted`,
  );
}

function updateChartCopy() {
  const selected = selectedMaterial();
  if (!selected) return;
  outputs.chartStatus.textContent =
    `${selected.name} highlighted · nine official metals`;
  outputs.axisExplanation.textContent =
    state.axisMode === "frequency"
      ? state.extrapolation
        ? "Solid lines are physical emission regions. Dashed negative segments are mathematical extrapolations only."
        : "Physical curves begin at each threshold frequency. Below threshold, stopping potential is undefined."
      : state.extrapolation
        ? "Solid curves end at each threshold wavelength. Dashed continuation is a non-physical extrapolation."
        : "Photoemission occurs only at wavelengths shorter than or equal to each metal’s threshold wavelength.";
}

function buildMaterialControls() {
  const materials = state.evidence.materials;
  outputs.materialLedger.replaceChildren();

  materials.forEach((material) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "material-row";
    button.dataset.materialRow = material.symbol;
    button.setAttribute("aria-pressed", "false");
    button.innerHTML = `
      <strong>${material.symbol}</strong>
      <div>
        <span>${material.name}</span>
        <small>f₀ ${(material.cutoffFrequencyHz / 1e15).toFixed(3)} PHz · λ₀ ${material.cutoffWavelengthNm.toFixed(1)} nm</small>
      </div>
      <em>${material.workFunctionEv.toFixed(1)} eV</em>
    `;
    button.addEventListener("click", () => {
      state.selectedSymbol = material.symbol;
      updateAll();
    });
    outputs.materialLedger.append(button);
  });

}

function updateAll() {
  updateReadouts();
  updateChartCopy();
  drawChart();
}

function setControlsEnabled(enabled) {
  [
    controls.extrapolation,
    ...controls.axisModes,
  ].filter(Boolean).forEach((control) => {
    control.disabled = !enabled;
  });
}

function handleAxisMode(event) {
  state.axisMode = event.currentTarget.dataset.axisMode;
  controls.axisModes.forEach((button) => {
    const active = button === event.currentTarget;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  chartTooltip.hidden = true;
  updateChartCopy();
  drawChart();
}

function handleChartPointer(event) {
  if (!state.evidence || !state.chartFrame) return;
  const rectangle = chartCanvas.getBoundingClientRect();
  const x = event.clientX - rectangle.left;
  const y = event.clientY - rectangle.top;
  const { range, left, right, top, bottom, width } = state.chartFrame;
  if (x < left || x > right || y < top || y > bottom) {
    chartTooltip.hidden = true;
    return;
  }

  const xValue =
    range.xMin + ((x - left) / width) * (range.xMax - range.xMin);
  const selected = selectedMaterial();
  const signedVoltage = chartValue(selected, xValue);
  const physical =
    state.axisMode === "frequency"
      ? xValue * 1e15 >= selected.cutoffFrequencyHz
      : xValue <= selected.cutoffWavelengthNm;
  const xLabel =
    state.axisMode === "frequency"
      ? `${xValue.toFixed(3)} PHz`
      : `${xValue.toFixed(1)} nm`;
  const voltageLabel = physical
    ? `${Math.max(0, signedVoltage).toFixed(3)} V`
    : state.extrapolation
      ? `${signedVoltage.toFixed(3)} V extrapolated`
      : "undefined below threshold";

  chartTooltip.innerHTML =
    `<strong>${selected.name} · ${selected.symbol}</strong><br>${xLabel}<br>V<sub>s</sub> ${voltageLabel}`;
  chartTooltip.hidden = false;
  const maxLeft = rectangle.width - chartTooltip.offsetWidth - 10;
  const maxTop = rectangle.height - chartTooltip.offsetHeight - 10;
  chartTooltip.style.left = `${Math.min(maxLeft, Math.max(10, x + 16))}px`;
  chartTooltip.style.top = `${Math.min(maxTop, Math.max(10, y - chartTooltip.offsetHeight - 12))}px`;
}

function attachListeners() {
  controls.axisModes.forEach((button) =>
    button.addEventListener("click", handleAxisMode),
  );
  controls.extrapolation.addEventListener("click", () => {
    state.extrapolation = !state.extrapolation;
    controls.extrapolation.setAttribute(
      "aria-pressed",
      String(state.extrapolation),
    );
    updateChartCopy();
    drawChart();
  });
  chartCanvas.addEventListener("pointermove", handleChartPointer, {
    passive: true,
  });
  chartCanvas.addEventListener("pointerleave", () => {
    chartTooltip.hidden = true;
  });
}

function handleFailure(error) {
  comparisonLaboratory.classList.remove("is-loading");
  chartError.hidden = false;
  chartError.textContent =
    error instanceof Error
      ? `Comparison data unavailable: ${error.message}`
      : "Task 4 comparison data is unavailable.";
  outputs.chartStatus.textContent = "Comparison unavailable";
  document.documentElement.dataset.task04Status = "error";
}

async function initialise() {
  setControlsEnabled(false);
  attachListeners();

  try {
    state.evidence = await loadTask04Evidence();
    buildMaterialControls();
    setControlsEnabled(true);
    comparisonLaboratory.classList.remove("is-loading");
    updateAll();
    document.documentElement.dataset.task04Status = "ready";
    window.dispatchEvent(new CustomEvent("task04:ready"));
  } catch (error) {
    handleFailure(error);
  }
}

const resizeObserver = new ResizeObserver(() => {
  drawChart();
});
resizeObserver.observe(document.querySelector(".comparison-chart-wrap"));

window.addEventListener(
  "pagehide",
  () => {
    resizeObserver.disconnect();
  },
  { once: true },
);

initialise();
