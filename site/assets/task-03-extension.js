const laboratory = document.querySelector("[data-debye-laboratory]");
const materialSelect = document.querySelector("#debye-material");
const ratioInput = document.querySelector("#debye-temperature-ratio");
const ratioOutput = document.querySelector("[data-debye-ratio-output]");
const statusText = document.querySelector("[data-debye-status]");
const errorMessage = document.querySelector("[data-debye-error]");
const content = [...document.querySelectorAll("[data-debye-content]")];
const canvas = document.querySelector("#debye-comparison-chart");
const context = canvas.getContext("2d");
const tooltip = document.querySelector("[data-debye-tooltip]");
const downloadButton = document.querySelector("[data-download-debye]");
const exportButton = document.querySelector("[data-export-debye]");

const outputs = {
  material: document.querySelector("[data-debye-material-name]"),
  temperature: document.querySelector("[data-debye-temperature]"),
  theta: document.querySelector("[data-debye-theta]"),
  debye: document.querySelector("[data-debye-capacity]"),
  einstein: document.querySelector("[data-extension-einstein-capacity]"),
  comparison: document.querySelector("[data-debye-ratio]"),
  interpretation: document.querySelector("[data-debye-interpretation]"),
};

const FONT = '"Times New Roman", Times, serif';
const INK = "#25231f";
const MUTED = "#6d6961";
const LINE = "#dedbd4";
const EINSTEIN = "#a24f39";
const DEBYE = "#25231f";
const THREE_R = 3 * 8.31446261815324;

let payload = null;
let geometry = null;
let resizeFrame = 0;

function validatePayload(candidate) {
  if (
    !candidate ||
    candidate.schema_version !== 1 ||
    candidate.accepted !== true ||
    !Array.isArray(candidate.materials) ||
    candidate.materials.length !== 7 ||
    !Array.isArray(candidate.curve) ||
    candidate.curve.length < 200
  ) {
    throw new Error("The accepted Einstein--Debye evidence is invalid.");
  }
  if (
    !candidate.curve.every(
      (point) =>
        Number.isFinite(point.temperature_over_debye_temperature) &&
        Number.isFinite(point.debye_over_3r) &&
        Number.isFinite(point.einstein_over_3r),
    )
  ) {
    throw new Error("The accepted curve contains invalid values.");
  }
  return candidate;
}

function selectedMaterial() {
  return payload.materials.find(
    (material) => material.symbol === materialSelect.value,
  );
}

function interpolateCurve(ratio) {
  const curve = payload.curve;
  if (ratio <= curve[0].temperature_over_debye_temperature) return curve[0];
  const last = curve[curve.length - 1];
  if (ratio >= last.temperature_over_debye_temperature) return last;
  let lowerIndex = 0;
  let upperIndex = curve.length - 1;
  while (upperIndex - lowerIndex > 1) {
    const middle = Math.floor((lowerIndex + upperIndex) / 2);
    if (curve[middle].temperature_over_debye_temperature <= ratio) {
      lowerIndex = middle;
    } else {
      upperIndex = middle;
    }
  }
  const lower = curve[lowerIndex];
  const upper = curve[upperIndex];
  const fraction =
    (ratio - lower.temperature_over_debye_temperature) /
    (upper.temperature_over_debye_temperature -
      lower.temperature_over_debye_temperature);
  const blend = (key) => lower[key] + (upper[key] - lower[key]) * fraction;
  return {
    temperature_over_debye_temperature: ratio,
    debye_over_3r: blend("debye_over_3r"),
    einstein_over_3r: blend("einstein_over_3r"),
  };
}

function formatCapacity(value) {
  if (value < 0.001) return `${value.toExponential(2)} J mol⁻¹ K⁻¹`;
  return `${value.toFixed(3)} J mol⁻¹ K⁻¹`;
}

function formatModelRatio(value) {
  if (value >= 1e6) return `>${Math.floor(value / 1e6).toLocaleString()} million ×`;
  if (value >= 1000) return `${value.toExponential(2)}×`;
  if (value >= 100) return `${value.toFixed(0)}×`;
  return `${value.toFixed(2)}×`;
}

function updateReadouts() {
  if (!payload) return;
  const material = selectedMaterial();
  const ratio = Number(ratioInput.value);
  const point = interpolateCurve(ratio);
  const temperature = ratio * material.debye_temperature_k;
  const debyeCapacity = point.debye_over_3r * THREE_R;
  const einsteinCapacity = point.einstein_over_3r * THREE_R;
  const modelRatio = debyeCapacity / Math.max(einsteinCapacity, Number.MIN_VALUE);

  ratioOutput.textContent = ratio.toFixed(2);
  outputs.material.textContent = `${material.name} · ${material.symbol}`;
  outputs.temperature.textContent = `${temperature.toFixed(1)} K`;
  outputs.theta.textContent = `${material.debye_temperature_k.toFixed(1)} K`;
  outputs.debye.textContent = formatCapacity(debyeCapacity);
  outputs.einstein.textContent = formatCapacity(einsteinCapacity);
  outputs.comparison.textContent = formatModelRatio(modelRatio);

  if (ratio <= 0.08) {
    outputs.interpretation.textContent =
      "The Einstein oscillator is exponentially frozen out. Debye's low-frequency acoustic modes still contribute with the T³ law.";
  } else if (ratio <= 0.3) {
    outputs.interpretation.textContent =
      "This is the transition region: Debye still predicts more heat capacity, but the two models are beginning to converge.";
  } else {
    outputs.interpretation.textContent =
      "At higher temperature both models approach the same classical Dulong–Petit limit, 3R.";
  }
  canvas.setAttribute(
    "aria-label",
    `Einstein and Debye heat-capacity comparison for ${material.name} at ${temperature.toFixed(1)} kelvin, or T over theta D equals ${ratio.toFixed(2)}`,
  );
  drawChart();
}

function setCanvasSize() {
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(canvas.clientWidth * pixelRatio));
  const height = Math.max(1, Math.round(canvas.clientHeight * pixelRatio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  return { width: canvas.clientWidth, height: canvas.clientHeight };
}

function drawLine(points, xFor, yFor, key, colour, width, dash = []) {
  context.save();
  context.strokeStyle = colour;
  context.lineWidth = width;
  context.setLineDash(dash);
  context.lineJoin = "round";
  context.beginPath();
  let started = false;
  for (const point of points) {
    const yValue = point[key];
    if (!Number.isFinite(yValue)) continue;
    const x = xFor(point.temperature_over_debye_temperature);
    const y = yFor(yValue);
    if (!started) {
      context.moveTo(x, y);
      started = true;
    } else {
      context.lineTo(x, y);
    }
  }
  context.stroke();
  context.restore();
}

function drawChart() {
  if (!payload || canvas.clientWidth === 0) return;
  const { width, height } = setCanvasSize();
  const compact = width < 620;
  const left = compact ? 48 : 62;
  const right = compact ? 14 : 22;
  const top = 24;
  const bottom = compact ? 47 : 54;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const xMaximum = 2.0;
  const yMaximum = 1.05;
  const xFor = (value) => left + (value / xMaximum) * plotWidth;
  const yFor = (value) => top + plotHeight - (value / yMaximum) * plotHeight;

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);
  context.fillStyle = "#fbfaf6";
  context.fillRect(left, top, plotWidth, plotHeight);

  context.font = `${compact ? 10 : 11}px ${FONT}`;
  context.fillStyle = MUTED;
  context.textBaseline = "middle";
  for (let index = 0; index <= 5; index += 1) {
    const yValue = index / 5;
    const y = yFor(yValue);
    context.strokeStyle = "#e6e3dc";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(left, y);
    context.lineTo(left + plotWidth, y);
    context.stroke();
    context.textAlign = "right";
    context.fillText(yValue.toFixed(1), left - 8, y);
  }
  const xTicks = compact ? [0, 0.5, 1, 1.5, 2] : [0, 0.25, 0.5, 1, 1.5, 2];
  context.textBaseline = "top";
  for (const xValue of xTicks) {
    const x = xFor(xValue);
    context.strokeStyle = "#ece9e3";
    context.beginPath();
    context.moveTo(x, top);
    context.lineTo(x, top + plotHeight);
    context.stroke();
    context.fillStyle = MUTED;
    context.textAlign = "center";
    context.fillText(xValue.toFixed(xValue % 1 === 0 ? 0 : 2), x, top + plotHeight + 9);
  }

  const displayedCurve = payload.curve.filter(
    (point) => point.temperature_over_debye_temperature <= xMaximum,
  );
  drawLine(displayedCurve, xFor, yFor, "debye_over_3r", DEBYE, 2.4);
  drawLine(displayedCurve, xFor, yFor, "einstein_over_3r", EINSTEIN, 2);
  drawLine(
    displayedCurve,
    xFor,
    yFor,
    "low_temperature_cubic_over_3r",
    "#77736b",
    1.2,
    [4, 4],
  );

  context.save();
  context.strokeStyle = "#8d8980";
  context.lineWidth = 1;
  context.setLineDash([7, 6]);
  context.beginPath();
  context.moveTo(left, yFor(1));
  context.lineTo(left + plotWidth, yFor(1));
  context.stroke();
  context.restore();

  const selectedRatio = Number(ratioInput.value);
  const selected = interpolateCurve(selectedRatio);
  const selectedX = xFor(selectedRatio);
  context.strokeStyle = "rgba(37, 35, 31, 0.35)";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(selectedX, top);
  context.lineTo(selectedX, top + plotHeight);
  context.stroke();
  for (const [key, colour] of [
    ["debye_over_3r", DEBYE],
    ["einstein_over_3r", EINSTEIN],
  ]) {
    context.fillStyle = "#ffffff";
    context.strokeStyle = colour;
    context.lineWidth = 2;
    context.beginPath();
    context.arc(selectedX, yFor(selected[key]), 4.5, 0, Math.PI * 2);
    context.fill();
    context.stroke();
  }

  context.strokeStyle = "#918d84";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(left, top);
  context.lineTo(left, top + plotHeight);
  context.lineTo(left + plotWidth, top + plotHeight);
  context.stroke();

  context.fillStyle = MUTED;
  context.font = `${compact ? 11 : 12}px ${FONT}`;
  context.textAlign = "center";
  context.textBaseline = "bottom";
  context.fillText("T / θD", left + plotWidth / 2, height - 2);
  context.save();
  context.translate(13, top + plotHeight / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("CV / 3R", 0, 0);
  context.restore();

  geometry = { left, top, plotWidth, plotHeight, xMaximum, xFor, yFor };
}

function tooltipAt(event) {
  if (!geometry || !payload) return;
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left) * (canvas.clientWidth / rect.width);
  const y = (event.clientY - rect.top) * (canvas.clientHeight / rect.height);
  if (
    x < geometry.left ||
    x > geometry.left + geometry.plotWidth ||
    y < geometry.top ||
    y > geometry.top + geometry.plotHeight
  ) {
    tooltip.hidden = true;
    return;
  }
  const ratio =
    ((x - geometry.left) / geometry.plotWidth) * geometry.xMaximum;
  const point = interpolateCurve(ratio);
  tooltip.innerHTML = `<strong>T / θ<sub>D</sub> = ${ratio.toFixed(2)}</strong><br>Debye ${(point.debye_over_3r * THREE_R).toFixed(3)} J mol⁻¹ K⁻¹<br>Einstein ${(point.einstein_over_3r * THREE_R).toFixed(3)} J mol⁻¹ K⁻¹`;
  tooltip.style.left = `${Math.min(canvas.clientWidth - 190, Math.max(8, x + 10))}px`;
  tooltip.style.top = `${Math.min(canvas.clientHeight - 76, Math.max(8, y - 22))}px`;
  tooltip.hidden = false;
}

function createCsv() {
  const rows = [
    ["temperature_over_debye_temperature", "debye_over_3R", "einstein_over_3R", "low_temperature_cubic_over_3R"],
    ...payload.curve.map((point) => [
      point.temperature_over_debye_temperature,
      point.debye_over_3r,
      point.einstein_over_3r,
      point.low_temperature_cubic_over_3r ?? "",
    ]),
  ];
  return rows.map((row) => row.join(",")).join("\n");
}

function downloadBlob(blob, filename) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 0);
}

materialSelect.addEventListener("change", updateReadouts);
ratioInput.addEventListener("input", updateReadouts);
canvas.addEventListener("pointermove", tooltipAt);
canvas.addEventListener("pointerleave", () => {
  tooltip.hidden = true;
});
canvas.addEventListener("keydown", (event) => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  event.preventDefault();
  const direction = event.key === "ArrowRight" ? 1 : -1;
  ratioInput.value = String(
    Math.min(2, Math.max(0.02, Number(ratioInput.value) + direction * 0.01)),
  );
  updateReadouts();
});

downloadButton.addEventListener("click", () => {
  if (!payload) return;
  downloadBlob(
    new Blob([createCsv()], { type: "text/csv;charset=utf-8" }),
    "task-03-einstein-debye-extension.csv",
  );
});

exportButton.addEventListener("click", () => {
  if (!payload) return;
  const material = selectedMaterial();
  const ratio = Number(ratioInput.value);
  const exportCanvas = document.createElement("canvas");
  exportCanvas.width = 2000;
  exportCanvas.height = 1200;
  const exportContext = exportCanvas.getContext("2d");
  exportContext.fillStyle = "#ffffff";
  exportContext.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
  exportContext.fillStyle = INK;
  exportContext.font = `700 62px ${FONT}`;
  exportContext.fillText("Task 3 extension: Einstein and Debye", 90, 94);
  exportContext.fillStyle = MUTED;
  exportContext.font = `30px ${FONT}`;
  exportContext.fillText(
    `${material.name} · θD = ${material.debye_temperature_k.toFixed(1)} K · selected T/θD = ${ratio.toFixed(2)}`,
    90,
    148,
  );
  exportContext.drawImage(canvas, 70, 200, 1860, 820);
  exportContext.fillStyle = INK;
  exportContext.font = `italic 29px ${FONT}`;
  exportContext.fillText(
    "Debye recovers CV ∝ T³ at low temperature; both models approach 3R at high temperature.",
    90,
    1100,
  );
  exportCanvas.toBlob((blob) => {
    if (blob) downloadBlob(blob, "task-03-einstein-debye-extension.png");
  }, "image/png");
});

function scheduleResize() {
  cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(drawChart);
}
new ResizeObserver(scheduleResize).observe(laboratory);

fetch("../data/task-03-debye-validation.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) throw new Error(`Debye evidence request failed (${response.status})`);
    return response.json();
  })
  .then(validatePayload)
  .then((acceptedPayload) => {
    payload = acceptedPayload;
    laboratory.classList.remove("is-loading");
    materialSelect.disabled = false;
    ratioInput.disabled = false;
    content.forEach((element) => {
      element.hidden = false;
    });
    const date = new Date(payload.generated_at_utc).toLocaleDateString("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
    statusText.textContent = `Accepted numerical comparison · ${date}`;
    updateReadouts();
  })
  .catch((error) => {
    laboratory.classList.remove("is-loading");
    laboratory.classList.add("has-error");
    errorMessage.hidden = false;
    statusText.textContent = "Validated comparison unavailable";
    console.error(error);
  });
