import { loadTask07Evidence } from "./task-07-evidence.js?v=20260731b";

const COLOURS = Object.freeze({
  psi: "#76a7ff",
  density: "#ff809f",
  accent: "#f4e341",
  blueDeep: "#245fb8",
  ink: "#171d31",
  muted: "#596477",
  grid: "#d7dbe3",
  paper: "#fbfaf5",
  states: ["#0072b2", "#d55e00", "#009e73", "#b9568e"],
});

const laboratory = document.querySelector("[data-state-laboratory]");
const stateCanvas = document.querySelector("#box-state-canvas");
const stateContext = stateCanvas.getContext("2d");
const spectrumCanvas = document.querySelector("#energy-spectrum-canvas");
const spectrumContext = spectrumCanvas.getContext("2d");
const densityCanvas = document.querySelector("#density-canvas");
const densityContext = densityCanvas.getContext("2d");
const uncertaintyCanvas = document.querySelector("#uncertainty-canvas");
const uncertaintyContext = uncertaintyCanvas.getContext("2d");
const quantumControl = document.querySelector("#quantum-number");
const controls = document.querySelector("[data-state-controls]");
const evidenceLock = document.querySelector("[data-evidence-lock]");
const spectrumTooltip = document.querySelector("[data-spectrum-tooltip]");

const outputs = {
  stateTitle: document.querySelector("[data-state-title]"),
  stateBadge: document.querySelector("[data-state-badge]"),
  quantum: document.querySelector("[data-quantum-output]"),
  energy: document.querySelector("[data-energy]"),
  relativeEnergy: document.querySelector("[data-relative-energy]"),
  nodes: document.querySelector("[data-node-count]"),
  product: document.querySelector("[data-uncertainty-product]"),
  spectrumSelected: document.querySelector("[data-spectrum-selected]"),
  spectrumStatus: document.querySelector("[data-spectrum-status]"),
  uncertaintySelected: document.querySelector("[data-uncertainty-selected]"),
  extensionResult: document.querySelector("[data-extension-result]"),
  lockTitle: document.querySelector("[data-lock-title]"),
  lockDetail: document.querySelector("[data-lock-detail]"),
  validationCount: document.querySelector("[data-validation-count]"),
  evidenceStatus: document.querySelector("[data-evidence-status]"),
};

const state = {
  evidence: null,
  n: 1,
  view: "both",
  densityStates: new Set([1, 2, 3, 4]),
  spectrumPoints: [],
};

function canvasSize(canvas, context) {
  const width = Math.max(1, canvas.clientWidth);
  const height = Math.max(1, canvas.clientHeight);
  const density = Math.min(window.devicePixelRatio || 1, 2);
  const pixelWidth = Math.round(width * density);
  const pixelHeight = Math.round(height * density);
  if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;
  }
  context.setTransform(density, 0, 0, density, 0, 0);
  return { width, height };
}

function line(context, x1, y1, x2, y2) {
  context.beginPath();
  context.moveTo(x1, y1);
  context.lineTo(x2, y2);
  context.stroke();
}

function currentEnergy() {
  return state.evidence.energies[state.n - 1];
}

function currentExpectation() {
  return state.evidence.expectations[state.n - 1];
}

function drawStateLaboratory() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(stateCanvas, stateContext);
  const compact = width < 590;
  const margins = {
    left: compact ? 42 : 68,
    right: compact ? 22 : 40,
    top: compact ? 74 : 82,
    bottom: compact ? 58 : 64,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const mid = plot.y + plot.height * 0.49;
  const amplitude = plot.height * (compact ? 0.28 : 0.3);
  const densityBaseline = plot.y + plot.height * 0.86;
  const densityScale = plot.height * (compact ? 0.17 : 0.19);
  const sampleCount = Math.max(500, Math.round(plot.width * 1.5));
  const viewPsi = state.view !== "density";
  const viewDensity = state.view !== "wavefunction";

  stateContext.clearRect(0, 0, width, height);
  stateContext.fillStyle = "#090c16";
  stateContext.fillRect(0, 0, width, height);

  const wellGradient = stateContext.createLinearGradient(
    plot.x,
    0,
    plot.x + plot.width,
    0,
  );
  wellGradient.addColorStop(0, "rgba(118,167,255,0.04)");
  wellGradient.addColorStop(0.5, "rgba(118,167,255,0.12)");
  wellGradient.addColorStop(1, "rgba(118,167,255,0.04)");
  stateContext.fillStyle = wellGradient;
  stateContext.fillRect(plot.x, plot.y, plot.width, plot.height);

  stateContext.fillStyle = "rgba(255,255,255,0.035)";
  stateContext.fillRect(0, plot.y, plot.x, plot.height);
  stateContext.fillRect(plot.x + plot.width, plot.y, margins.right, plot.height);

  stateContext.strokeStyle = "#7f8ba7";
  stateContext.lineWidth = 1;
  stateContext.setLineDash([3, 5]);
  line(stateContext, plot.x, mid, plot.x + plot.width, mid);
  line(
    stateContext,
    plot.x,
    densityBaseline,
    plot.x + plot.width,
    densityBaseline,
  );
  stateContext.setLineDash([]);

  stateContext.strokeStyle = "#f1f2ed";
  stateContext.lineWidth = compact ? 3 : 4;
  line(stateContext, plot.x, plot.y - 12, plot.x, plot.y + plot.height + 8);
  line(
    stateContext,
    plot.x + plot.width,
    plot.y - 12,
    plot.x + plot.width,
    plot.y + plot.height + 8,
  );

  if (viewDensity) {
    const densityGradient = stateContext.createLinearGradient(
      0,
      densityBaseline - densityScale,
      0,
      densityBaseline,
    );
    densityGradient.addColorStop(0, "rgba(255,128,159,0.5)");
    densityGradient.addColorStop(1, "rgba(255,128,159,0.04)");
    stateContext.beginPath();
    stateContext.moveTo(plot.x, densityBaseline);
    for (let index = 0; index <= sampleCount; index += 1) {
      const u = index / sampleCount;
      const density = 2 * Math.sin(state.n * Math.PI * u) ** 2;
      stateContext.lineTo(
        plot.x + u * plot.width,
        densityBaseline - (density / 2) * densityScale,
      );
    }
    stateContext.lineTo(plot.x + plot.width, densityBaseline);
    stateContext.closePath();
    stateContext.fillStyle = densityGradient;
    stateContext.fill();

    stateContext.beginPath();
    for (let index = 0; index <= sampleCount; index += 1) {
      const u = index / sampleCount;
      const density = 2 * Math.sin(state.n * Math.PI * u) ** 2;
      const x = plot.x + u * plot.width;
      const y = densityBaseline - (density / 2) * densityScale;
      if (index === 0) stateContext.moveTo(x, y);
      else stateContext.lineTo(x, y);
    }
    stateContext.strokeStyle = COLOURS.density;
    stateContext.lineWidth = compact ? 2.3 : 3;
    stateContext.shadowColor = COLOURS.density;
    stateContext.shadowBlur = 9;
    stateContext.stroke();
    stateContext.shadowBlur = 0;
  }

  if (viewPsi) {
    stateContext.beginPath();
    for (let index = 0; index <= sampleCount; index += 1) {
      const u = index / sampleCount;
      const psi = Math.sin(state.n * Math.PI * u);
      const x = plot.x + u * plot.width;
      const y = mid - psi * amplitude;
      if (index === 0) stateContext.moveTo(x, y);
      else stateContext.lineTo(x, y);
    }
    stateContext.strokeStyle = COLOURS.psi;
    stateContext.lineWidth = compact ? 2.5 : 3.2;
    stateContext.shadowColor = COLOURS.psi;
    stateContext.shadowBlur = 10;
    stateContext.stroke();
    stateContext.shadowBlur = 0;
  }

  stateContext.fillStyle = COLOURS.accent;
  for (let node = 1; node < state.n; node += 1) {
    const x = plot.x + (node / state.n) * plot.width;
    stateContext.beginPath();
    stateContext.arc(x, mid, compact ? 2.6 : 3.2, 0, Math.PI * 2);
    stateContext.fill();
  }

  stateContext.font = `${compact ? 10 : 12}px "Times New Roman"`;
  stateContext.fillStyle = "#edf0f5";
  stateContext.textAlign = "left";
  stateContext.fillText(
    `INFINITE WELL · n = ${state.n}`,
    compact ? 14 : 20,
    compact ? 27 : 30,
  );
  stateContext.fillStyle = "#a9b3c8";
  stateContext.textAlign = "right";
  stateContext.fillText(
    `${state.n - 1} INTERIOR NODE${state.n === 2 ? "" : "S"}`,
    width - (compact ? 14 : 20),
    compact ? 27 : 30,
  );
  stateContext.fillStyle = COLOURS.psi;
  stateContext.textAlign = "left";
  stateContext.fillText("SIGNED ψ", plot.x + 8, mid - amplitude - 15);
  stateContext.fillStyle = COLOURS.density;
  stateContext.fillText(
    "a|ψ|² ≥ 0",
    plot.x + 8,
    densityBaseline - densityScale - 14,
  );

  stateContext.fillStyle = "#dce0e9";
  stateContext.textAlign = "center";
  stateContext.fillText("0", plot.x, height - 24);
  stateContext.fillText("x / a", plot.x + plot.width / 2, height - 24);
  stateContext.fillText("1", plot.x + plot.width, height - 24);
  stateContext.fillStyle = "#9aa5bc";
  stateContext.fillText("V = ∞", plot.x - 20, plot.y - 23);
  stateContext.fillText("V = ∞", plot.x + plot.width + 18, plot.y - 23);

  stateCanvas.setAttribute(
    "aria-label",
    `State n equals ${state.n}: energy ${currentEnergy().energyEv.toFixed(6)} electronvolts, ${state.n - 1} interior nodes, uncertainty product ${currentExpectation().productOverHbar.toFixed(6)} h-bar.`,
  );
}

function drawSpectrum() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(spectrumCanvas, spectrumContext);
  const compact = width < 610;
  const margins = {
    left: compact ? 64 : 90,
    right: compact ? 23 : 42,
    top: compact ? 52 : 64,
    bottom: compact ? 69 : 82,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const xFor = (n) => plot.x + ((n - 0.5) / 10) * plot.width;
  const yFor = (energy) =>
    plot.y + plot.height - (energy / 40) * plot.height;

  spectrumContext.clearRect(0, 0, width, height);
  spectrumContext.fillStyle = COLOURS.paper;
  spectrumContext.fillRect(0, 0, width, height);
  spectrumContext.font = `${compact ? 10 : 14}px "Times New Roman"`;
  spectrumContext.fillStyle = COLOURS.muted;
  spectrumContext.strokeStyle = COLOURS.grid;
  spectrumContext.lineWidth = 1;

  for (const tick of [0, 10, 20, 30, 40]) {
    const y = yFor(tick);
    line(spectrumContext, plot.x, y, plot.x + plot.width, y);
    spectrumContext.textAlign = "right";
    spectrumContext.fillText(String(tick), plot.x - 12, y + 4);
  }
  for (let n = 1; n <= 10; n += 1) {
    const x = xFor(n);
    spectrumContext.textAlign = "center";
    spectrumContext.fillText(String(n), x, plot.y + plot.height + 25);
  }

  spectrumContext.strokeStyle = COLOURS.ink;
  spectrumContext.lineWidth = 1.35;
  line(spectrumContext, plot.x, plot.y, plot.x, plot.y + plot.height);
  line(
    spectrumContext,
    plot.x,
    plot.y + plot.height,
    plot.x + plot.width,
    plot.y + plot.height,
  );

  state.spectrumPoints = [];
  for (const energy of state.evidence.energies) {
    const x = xFor(energy.n);
    const y = yFor(energy.energyEv);
    const selected = energy.n === state.n;
    spectrumContext.strokeStyle = selected ? COLOURS.accent : "#5f91df";
    spectrumContext.lineWidth = selected ? 3.2 : 2;
    line(spectrumContext, x, yFor(0), x, y);
    spectrumContext.fillStyle = selected ? COLOURS.accent : COLOURS.blueDeep;
    spectrumContext.strokeStyle = COLOURS.ink;
    spectrumContext.lineWidth = selected ? 2 : 1;
    spectrumContext.beginPath();
    spectrumContext.arc(x, y, selected ? 9 : 6, 0, Math.PI * 2);
    spectrumContext.fill();
    spectrumContext.stroke();
    state.spectrumPoints.push({ x, y, energy });
  }

  spectrumContext.fillStyle = COLOURS.ink;
  spectrumContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
  spectrumContext.textAlign = "center";
  spectrumContext.fillText(
    "Quantum number, n (discrete)",
    plot.x + plot.width / 2,
    height - (compact ? 17 : 23),
  );
  spectrumContext.save();
  spectrumContext.translate(compact ? 19 : 27, plot.y + plot.height / 2);
  spectrumContext.rotate(-Math.PI / 2);
  spectrumContext.fillText("Energy, Eₙ / eV", 0, 0);
  spectrumContext.restore();

  spectrumContext.font = `italic ${compact ? 13 : 17}px "Times New Roman"`;
  spectrumContext.fillStyle = "#5a6476";
  spectrumContext.textAlign = "right";
  spectrumContext.fillText(
    "markers are allowed states · stems are guides",
    plot.x + plot.width,
    plot.y - 21,
  );
}

function drawDensity() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(densityCanvas, densityContext);
  const compact = width < 610;
  const margins = {
    left: compact ? 64 : 87,
    right: compact ? 22 : 38,
    top: compact ? 48 : 62,
    bottom: compact ? 68 : 78,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const xFor = (u) => plot.x + u * plot.width;
  const yFor = (density) =>
    plot.y + plot.height - (density / 2.1) * plot.height;

  densityContext.clearRect(0, 0, width, height);
  densityContext.fillStyle = COLOURS.paper;
  densityContext.fillRect(0, 0, width, height);
  densityContext.font = `${compact ? 10 : 14}px "Times New Roman"`;
  densityContext.fillStyle = COLOURS.muted;
  densityContext.strokeStyle = COLOURS.grid;
  densityContext.lineWidth = 1;

  for (const tick of [0, 0.5, 1, 1.5, 2]) {
    const y = yFor(tick);
    line(densityContext, plot.x, y, plot.x + plot.width, y);
    densityContext.textAlign = "right";
    densityContext.fillText(tick.toFixed(1), plot.x - 10, y + 4);
  }
  for (const tick of [0, 0.25, 0.5, 0.75, 1]) {
    const x = xFor(tick);
    densityContext.textAlign = "center";
    densityContext.fillText(tick.toFixed(2), x, plot.y + plot.height + 24);
  }

  densityContext.strokeStyle = COLOURS.ink;
  densityContext.lineWidth = 1.35;
  line(densityContext, plot.x, plot.y, plot.x, plot.y + plot.height);
  line(
    densityContext,
    plot.x,
    plot.y + plot.height,
    plot.x + plot.width,
    plot.y + plot.height,
  );

  for (let n = 1; n <= 4; n += 1) {
    if (!state.densityStates.has(n)) continue;
    const rows = state.evidence.states.get(n);
    densityContext.beginPath();
    rows.forEach((row, index) => {
      const x = xFor(row.u);
      const y = yFor(row.scaledDensity);
      if (index === 0) densityContext.moveTo(x, y);
      else densityContext.lineTo(x, y);
    });
    densityContext.strokeStyle = COLOURS.states[n - 1];
    densityContext.lineWidth = compact ? 2.2 : 3;
    densityContext.stroke();
  }

  densityContext.fillStyle = COLOURS.ink;
  densityContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
  densityContext.textAlign = "center";
  densityContext.fillText(
    "Normalized position, x / a",
    plot.x + plot.width / 2,
    height - (compact ? 17 : 22),
  );
  densityContext.save();
  densityContext.translate(compact ? 19 : 27, plot.y + plot.height / 2);
  densityContext.rotate(-Math.PI / 2);
  densityContext.fillText("Scaled density, a|ψₙ|²", 0, 0);
  densityContext.restore();
  densityContext.font = `italic ${compact ? 12 : 16}px "Times New Roman"`;
  densityContext.fillStyle = "#596477";
  densityContext.textAlign = "right";
  densityContext.fillText(
    "each visible curve integrates to 1",
    plot.x + plot.width,
    plot.y - 19,
  );
}

function drawUncertainty() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(uncertaintyCanvas, uncertaintyContext);
  const compact = width < 610;
  const margins = {
    left: compact ? 60 : 82,
    right: compact ? 22 : 38,
    top: compact ? 48 : 58,
    bottom: compact ? 67 : 76,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const xFor = (n) => plot.x + ((n - 1) / 9) * plot.width;
  const yFor = (product) =>
    plot.y + plot.height - (product / 9.5) * plot.height;

  uncertaintyContext.clearRect(0, 0, width, height);
  uncertaintyContext.fillStyle = COLOURS.paper;
  uncertaintyContext.fillRect(0, 0, width, height);
  uncertaintyContext.font = `${compact ? 10 : 13}px "Times New Roman"`;
  uncertaintyContext.fillStyle = COLOURS.muted;
  uncertaintyContext.strokeStyle = COLOURS.grid;
  uncertaintyContext.lineWidth = 1;

  for (const tick of [0, 2, 4, 6, 8]) {
    const y = yFor(tick);
    line(uncertaintyContext, plot.x, y, plot.x + plot.width, y);
    uncertaintyContext.textAlign = "right";
    uncertaintyContext.fillText(String(tick), plot.x - 10, y + 4);
  }
  for (let n = 1; n <= 10; n += 1) {
    uncertaintyContext.textAlign = "center";
    uncertaintyContext.fillText(
      String(n),
      xFor(n),
      plot.y + plot.height + 23,
    );
  }

  uncertaintyContext.strokeStyle = "#bf4b73";
  uncertaintyContext.lineWidth = 2;
  uncertaintyContext.setLineDash([9, 7]);
  line(
    uncertaintyContext,
    plot.x,
    yFor(0.5),
    plot.x + plot.width,
    yFor(0.5),
  );
  uncertaintyContext.setLineDash([]);
  uncertaintyContext.fillStyle = "#a63f62";
  uncertaintyContext.textAlign = "right";
  uncertaintyContext.fillText(
    "Heisenberg bound = 0.5",
    plot.x + plot.width,
    yFor(0.5) - 10,
  );

  uncertaintyContext.beginPath();
  state.evidence.expectations.forEach((record, index) => {
    const x = xFor(record.n);
    const y = yFor(record.productOverHbar);
    if (index === 0) uncertaintyContext.moveTo(x, y);
    else uncertaintyContext.lineTo(x, y);
  });
  uncertaintyContext.strokeStyle = "#246fbb";
  uncertaintyContext.lineWidth = compact ? 2.5 : 3.2;
  uncertaintyContext.stroke();

  for (const record of state.evidence.expectations) {
    const selected = record.n === state.n;
    uncertaintyContext.fillStyle = selected ? COLOURS.accent : "#246fbb";
    uncertaintyContext.strokeStyle = COLOURS.ink;
    uncertaintyContext.lineWidth = selected ? 2 : 1;
    uncertaintyContext.beginPath();
    uncertaintyContext.arc(
      xFor(record.n),
      yFor(record.productOverHbar),
      selected ? 8 : 5,
      0,
      Math.PI * 2,
    );
    uncertaintyContext.fill();
    uncertaintyContext.stroke();
  }

  uncertaintyContext.strokeStyle = COLOURS.ink;
  uncertaintyContext.lineWidth = 1.3;
  line(
    uncertaintyContext,
    plot.x,
    plot.y,
    plot.x,
    plot.y + plot.height,
  );
  line(
    uncertaintyContext,
    plot.x,
    plot.y + plot.height,
    plot.x + plot.width,
    plot.y + plot.height,
  );
  uncertaintyContext.fillStyle = COLOURS.ink;
  uncertaintyContext.font = `${compact ? 13 : 16}px "Times New Roman"`;
  uncertaintyContext.textAlign = "center";
  uncertaintyContext.fillText(
    "Quantum number, n",
    plot.x + plot.width / 2,
    height - (compact ? 17 : 21),
  );
  uncertaintyContext.save();
  uncertaintyContext.translate(compact ? 18 : 26, plot.y + plot.height / 2);
  uncertaintyContext.rotate(-Math.PI / 2);
  uncertaintyContext.fillText("ΔxΔp / ℏ", 0, 0);
  uncertaintyContext.restore();
}

function updateOutputs() {
  const energy = currentEnergy();
  const expectation = currentExpectation();
  outputs.stateTitle.textContent = `n = ${state.n} · exact eigenstate`;
  outputs.stateBadge.textContent = `${state.n - 1} node${state.n === 2 ? "" : "s"} · stationary`;
  outputs.quantum.value = `n = ${state.n}`;
  outputs.energy.textContent = `${energy.energyEv.toFixed(6)} eV`;
  outputs.relativeEnergy.textContent = `${energy.energyOverGround.toFixed(0)} E₁`;
  outputs.nodes.textContent = String(state.n - 1);
  outputs.product.textContent = `${expectation.productOverHbar.toFixed(6)} ℏ`;
  outputs.spectrumSelected.textContent =
    `n = ${state.n} · ${energy.energyEv.toFixed(6)} eV`;
  outputs.uncertaintySelected.textContent =
    `n = ${state.n} · ${expectation.productOverHbar.toFixed(6)}ℏ`;
  outputs.extensionResult.textContent =
    `n = ${state.n} · ${expectation.productOverHbar.toFixed(6)}ℏ > 0.5ℏ`;
  document.querySelectorAll("[data-state-preset]").forEach((button) => {
    button.classList.toggle(
      "is-current",
      Number(button.dataset.statePreset) === state.n,
    );
  });
}

function renderAll() {
  if (!state.evidence) return;
  updateOutputs();
  drawStateLaboratory();
  drawSpectrum();
  drawDensity();
  drawUncertainty();
}

function selectState(n, { focus = false } = {}) {
  if (!state.evidence) return;
  state.n = Math.max(1, Math.min(10, Math.round(n)));
  quantumControl.value = String(state.n);
  renderAll();
  if (focus) spectrumCanvas.focus({ preventScroll: true });
}

function nearestSpectrumPoint(event) {
  const bounds = spectrumCanvas.getBoundingClientRect();
  const x = event.clientX - bounds.left;
  const y = event.clientY - bounds.top;
  let nearest = null;
  let distance = 28;
  for (const point of state.spectrumPoints) {
    const candidate = Math.hypot(point.x - x, point.y - y);
    if (candidate < distance) {
      nearest = point;
      distance = candidate;
    }
  }
  return { point: nearest, x, y };
}

function setFailureState() {
  laboratory.classList.remove("is-loading");
  laboratory.classList.add("is-error");
  document.querySelector("[data-state-loading]").hidden = true;
  document.querySelector("[data-state-error]").hidden = false;
  document.querySelector("[data-spectrum-error]").hidden = false;
  document.querySelector("[data-density-error]").hidden = false;
  document.querySelector("[data-uncertainty-error]").hidden = false;
  outputs.stateTitle.textContent = "Evidence unavailable";
  outputs.stateBadge.textContent = "Interaction locked";
  outputs.spectrumStatus.textContent = "Validation unavailable";
  outputs.lockTitle.textContent = "Validation could not be confirmed";
  outputs.lockDetail.textContent =
    "One or more committed Task 7 artifacts failed to load or disagreed with the frozen analytical model. No interactive result is shown.";
  outputs.validationCount.textContent = "Not verified";
  outputs.evidenceStatus.textContent = "Locked";
  evidenceLock.classList.add("is-error");
}

function enableControls() {
  controls.querySelectorAll("button, input").forEach((control) => {
    control.disabled = false;
  });
  document.querySelectorAll("[data-density-state]").forEach((control) => {
    control.disabled = false;
  });
}

quantumControl.addEventListener("input", () => {
  selectState(Number(quantumControl.value));
});

document.querySelectorAll("[data-state-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    selectState(Number(button.dataset.statePreset));
  });
});

document.querySelectorAll('input[name="state-view"]').forEach((control) => {
  control.addEventListener("change", () => {
    if (!control.checked) return;
    state.view = control.value;
    drawStateLaboratory();
  });
});

document.querySelectorAll("[data-density-state]").forEach((control) => {
  control.addEventListener("change", () => {
    const n = Number(control.dataset.densityState);
    if (control.checked) state.densityStates.add(n);
    else if (state.densityStates.size === 1) {
      control.checked = true;
      return;
    } else state.densityStates.delete(n);
    drawDensity();
  });
});

for (const canvas of [stateCanvas, spectrumCanvas, uncertaintyCanvas]) {
  canvas.addEventListener("keydown", (event) => {
    if (!state.evidence) return;
    if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      event.preventDefault();
      selectState(state.n + 1);
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      event.preventDefault();
      selectState(state.n - 1);
    }
    if (event.key === "Home") {
      event.preventDefault();
      selectState(1);
    }
    if (event.key === "End") {
      event.preventDefault();
      selectState(10);
    }
  });
}

spectrumCanvas.addEventListener("pointermove", (event) => {
  if (!state.evidence) return;
  const { point, x, y } = nearestSpectrumPoint(event);
  if (!point) {
    spectrumTooltip.hidden = true;
    return;
  }
  spectrumTooltip.hidden = false;
  spectrumTooltip.textContent =
    `n = ${point.energy.n} · ${point.energy.energyEv.toFixed(6)} eV`;
  spectrumTooltip.style.left = `${Math.min(
    x + 14,
    spectrumCanvas.clientWidth - 170,
  )}px`;
  spectrumTooltip.style.top = `${Math.max(8, y - 48)}px`;
});

spectrumCanvas.addEventListener("pointerleave", () => {
  spectrumTooltip.hidden = true;
});

spectrumCanvas.addEventListener("click", (event) => {
  const { point } = nearestSpectrumPoint(event);
  if (point) selectState(point.energy.n, { focus: true });
});

const resizeObserver = new ResizeObserver(() => {
  if (!state.evidence) return;
  renderAll();
});
for (const canvas of [
  stateCanvas,
  spectrumCanvas,
  densityCanvas,
  uncertaintyCanvas,
]) {
  resizeObserver.observe(canvas);
}

try {
  state.evidence = await loadTask07Evidence();
  laboratory.classList.remove("is-loading");
  enableControls();
  outputs.spectrumStatus.textContent = "10 discrete levels locked";
  outputs.lockTitle.textContent = "Validated Task 7 evidence loaded";
  outputs.lockDetail.textContent =
    "All 37 checks pass. The analytical state catalogue, uncertainty values, 60-digit anchors, and independent five-grid eigensolver agree.";
  outputs.validationCount.textContent =
    `${state.evidence.validation.checks.length}/${state.evidence.validation.checks.length} pass`;
  outputs.evidenceStatus.textContent = "Evidence locked";
  evidenceLock.classList.add("is-verified");
  document.body.dataset.task07Status = "verified";
  renderAll();
  window.dispatchEvent(new CustomEvent("task07:ready"));
} catch (error) {
  console.error("Task 7 evidence validation failed", error);
  document.body.dataset.task07Status = "error";
  setFailureState();
}
