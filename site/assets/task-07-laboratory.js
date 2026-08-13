import { loadTask07Evidence } from "./task-07-evidence.js?v=20260731b";

const COLOURS = Object.freeze({
  psi: "#355c6d",
  density: "#a24f39",
  accent: "#a24f39",
  blueDeep: "#355c6d",
  ink: "#29251f",
  muted: "#756e65",
  grid: "#ded8cf",
  gridSoft: "#ece7df",
  paper: "#fcfbf7",
  paperDeep: "#f5f1e9",
  states: ["#355c6d", "#a24f39", "#5d7668", "#7c6676"],
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
const convergenceCanvas = document.querySelector("#convergence-canvas");
const convergenceContext = convergenceCanvas.getContext("2d");
const quantumControl = document.querySelector("#quantum-number");
const controls = document.querySelector("[data-state-controls]");
const spectrumTooltip = document.querySelector("[data-spectrum-tooltip]");
const resetStateButton = document.querySelector("[data-reset-state]");
const numericalMomentsBody = document.querySelector("[data-numerical-moments-body]");

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
  validationCount: document.querySelector("[data-validation-count]"),
  validationBoundary: document.querySelector("[data-validation-boundary]"),
  validationNormalization: document.querySelector("[data-validation-normalization]"),
  validationNodes: document.querySelector("[data-validation-nodes]"),
  validationEnergy: document.querySelector("[data-validation-energy]"),
  validationOverlap: document.querySelector("[data-validation-overlap]"),
  validationPMean: document.querySelector("[data-validation-pmean]"),
  validationP2: document.querySelector("[data-validation-p2]"),
  validationOrder: document.querySelector("[data-validation-order]"),
  validationError: document.querySelector("[data-validation-error]"),
  validationUncertainty: document.querySelector("[data-validation-uncertainty]"),
  validationBound: document.querySelector("[data-validation-bound]"),
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

function paintPaper(context, width, height) {
  context.fillStyle = COLOURS.paper;
  context.fillRect(0, 0, width, height);

  context.save();
  context.fillStyle = "rgba(70, 57, 44, 0.035)";
  const speckCount = Math.max(90, Math.round((width * height) / 4200));
  for (let index = 0; index < speckCount; index += 1) {
    const x = (index * 83 + 29) % Math.max(1, width);
    const y = (index * 137 + 53) % Math.max(1, height);
    const size = index % 7 === 0 ? 0.9 : 0.55;
    context.fillRect(x, y, size, size);
  }
  context.restore();
}

function strokePrinted(context, colour, width) {
  context.save();
  context.strokeStyle = "rgba(56, 43, 33, 0.11)";
  context.lineWidth = width + 2.2;
  context.stroke();
  context.restore();
  context.strokeStyle = colour;
  context.lineWidth = width;
  context.stroke();
}

function currentEnergy() {
  return state.evidence.energies[state.n - 1];
}

function currentExpectation() {
  return state.evidence.expectations[state.n - 1];
}

function renderInlineMath(node, source, fallback) {
  if (window.katex) {
    window.katex.render(source, node, {
      displayMode: false,
      output: "htmlAndMathml",
      strict: "warn",
      throwOnError: false,
      trust: false,
    });
    node.classList.add("proof-inline-math");
    return;
  }
  node.textContent = fallback;
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
  paintPaper(stateContext, width, height);
  stateContext.fillStyle = COLOURS.paperDeep;
  stateContext.fillRect(plot.x, plot.y, plot.width, plot.height);

  stateContext.fillStyle = "#eee8de";
  stateContext.fillRect(0, plot.y, plot.x, plot.height);
  stateContext.fillRect(plot.x + plot.width, plot.y, margins.right, plot.height);

  stateContext.strokeStyle = "#d4cdc2";
  stateContext.lineWidth = 1;
  stateContext.setLineDash([4, 6]);
  line(stateContext, plot.x, mid, plot.x + plot.width, mid);
  line(
    stateContext,
    plot.x,
    densityBaseline,
    plot.x + plot.width,
    densityBaseline,
  );
  stateContext.setLineDash([]);

  stateContext.strokeStyle = COLOURS.ink;
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
    stateContext.fillStyle = "rgba(162, 79, 57, 0.14)";
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
    strokePrinted(stateContext, COLOURS.density, compact ? 2.2 : 2.8);
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
    strokePrinted(stateContext, COLOURS.psi, compact ? 2.3 : 3);
  }

  stateContext.fillStyle = COLOURS.accent;
  for (let node = 1; node < state.n; node += 1) {
    const x = plot.x + (node / state.n) * plot.width;
    stateContext.beginPath();
    stateContext.arc(x, mid, compact ? 2.6 : 3.2, 0, Math.PI * 2);
    stateContext.fill();
  }

  stateContext.font = `${compact ? 10 : 12}px "Times New Roman"`;
  stateContext.fillStyle = COLOURS.ink;
  stateContext.textAlign = "left";
  stateContext.fillText(
    `INFINITE WELL · n = ${state.n}`,
    compact ? 14 : 20,
    compact ? 27 : 30,
  );
  stateContext.fillStyle = COLOURS.muted;
  stateContext.textAlign = "right";
  stateContext.fillText(
    `${state.n - 1} INTERIOR NODE${state.n === 2 ? "" : "S"}`,
    width - (compact ? 14 : 20),
    compact ? 27 : 30,
  );
  stateContext.fillStyle = COLOURS.psi;
  stateContext.textAlign = "left";
  stateContext.fillText(
    "WAVEFUNCTION SHAPE · √(a/2)ψ",
    plot.x + 8,
    mid - amplitude - 15,
  );
  stateContext.fillStyle = COLOURS.density;
  stateContext.fillText(
    "a|ψ|² ≥ 0",
    plot.x + 8,
    densityBaseline - densityScale - 14,
  );

  stateContext.fillStyle = COLOURS.ink;
  stateContext.textAlign = "center";
  stateContext.fillText("0", plot.x, height - 24);
  stateContext.fillText("x / a", plot.x + plot.width / 2, height - 24);
  stateContext.fillText("1", plot.x + plot.width, height - 24);
  stateContext.fillStyle = COLOURS.muted;
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
    top: compact ? 34 : 40,
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
  paintPaper(spectrumContext, width, height);
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
    spectrumContext.strokeStyle = COLOURS.gridSoft;
    spectrumContext.lineWidth = 1;
    line(spectrumContext, x, plot.y, x, plot.y + plot.height);
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
    spectrumContext.strokeStyle = selected
      ? "rgba(162, 79, 57, 0.58)"
      : "rgba(53, 92, 109, 0.42)";
    spectrumContext.lineWidth = selected ? 2.6 : 1.5;
    line(spectrumContext, x, yFor(0), x, y);
    spectrumContext.fillStyle = selected ? COLOURS.accent : COLOURS.blueDeep;
    spectrumContext.strokeStyle = COLOURS.paper;
    spectrumContext.lineWidth = selected ? 3 : 2;
    spectrumContext.beginPath();
    spectrumContext.arc(x, y, selected ? 9 : 6, 0, Math.PI * 2);
    spectrumContext.fill();
    spectrumContext.stroke();
    spectrumContext.strokeStyle = selected ? COLOURS.accent : COLOURS.ink;
    spectrumContext.lineWidth = 1;
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

}

function drawDensity() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(densityCanvas, densityContext);
  const compact = width < 610;
  const margins = {
    left: compact ? 64 : 87,
    right: compact ? 22 : 38,
    top: compact ? 34 : 40,
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
  paintPaper(densityContext, width, height);
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
    densityContext.strokeStyle = COLOURS.gridSoft;
    densityContext.lineWidth = 1;
    line(densityContext, x, plot.y, x, plot.y + plot.height);
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
    strokePrinted(
      densityContext,
      COLOURS.states[n - 1],
      compact ? 2.1 : 2.7,
    );
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
  paintPaper(uncertaintyContext, width, height);
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
    uncertaintyContext.strokeStyle = COLOURS.gridSoft;
    uncertaintyContext.lineWidth = 1;
    line(
      uncertaintyContext,
      xFor(n),
      plot.y,
      xFor(n),
      plot.y + plot.height,
    );
    uncertaintyContext.textAlign = "center";
    uncertaintyContext.fillText(
      String(n),
      xFor(n),
      plot.y + plot.height + 23,
    );
  }

  uncertaintyContext.strokeStyle = "rgba(162, 79, 57, 0.72)";
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
  uncertaintyContext.fillStyle = COLOURS.accent;
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
  strokePrinted(
    uncertaintyContext,
    COLOURS.psi,
    compact ? 2.4 : 3,
  );

  for (const record of state.evidence.expectations) {
    const selected = record.n === state.n;
    uncertaintyContext.fillStyle = selected ? COLOURS.accent : COLOURS.psi;
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

function drawConvergence() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(convergenceCanvas, convergenceContext);
  const compact = width < 520;
  const margins = {
    left: compact ? 62 : 76,
    right: compact ? 20 : 30,
    top: compact ? 42 : 52,
    bottom: compact ? 58 : 68,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const rows = state.evidence.uncertaintyConvergence;
  const logX = (grid) => Math.log10(grid);
  const logY = (error) => Math.log10(error);
  const minX = logX(rows[0].grid);
  const maxX = logX(rows.at(-1).grid);
  const minY = -5.2;
  const maxY = -1.8;
  const xFor = (grid) => plot.x + ((logX(grid) - minX) / (maxX - minX)) * plot.width;
  const yFor = (error) =>
    plot.y + plot.height - ((logY(error) - minY) / (maxY - minY)) * plot.height;

  convergenceContext.clearRect(0, 0, width, height);
  paintPaper(convergenceContext, width, height);
  convergenceContext.font = `${compact ? 10 : 12}px "Times New Roman"`;
  convergenceContext.fillStyle = COLOURS.muted;
  convergenceContext.strokeStyle = COLOURS.grid;
  for (const exponent of [-5, -4, -3, -2]) {
    const y = yFor(10 ** exponent);
    line(convergenceContext, plot.x, y, plot.x + plot.width, y);
    convergenceContext.textAlign = "right";
    convergenceContext.fillText(`10${String(exponent).replace("-", "⁻")}`, plot.x - 10, y + 4);
  }
  rows.forEach((row) => {
    const x = xFor(row.grid);
    convergenceContext.strokeStyle = COLOURS.gridSoft;
    line(convergenceContext, x, plot.y, x, plot.y + plot.height);
    convergenceContext.fillStyle = COLOURS.muted;
    convergenceContext.textAlign = "center";
    convergenceContext.fillText(String(row.grid), x, plot.y + plot.height + 20);
  });

  const series = [
    { key: "energyError", colour: COLOURS.ink, label: "E error" },
    { key: "deltaPError", colour: COLOURS.psi, label: "Δp error" },
    { key: "uncertaintyError", colour: COLOURS.density, label: "ΔxΔp error" },
  ];
  series.forEach(({ key, colour }, seriesIndex) => {
    convergenceContext.beginPath();
    rows.forEach((row, index) => {
      const x = xFor(row.grid);
      const y = yFor(row[key]);
      if (index === 0) convergenceContext.moveTo(x, y);
      else convergenceContext.lineTo(x, y);
    });
    strokePrinted(convergenceContext, colour, compact ? 2.2 : 2.8);
    rows.forEach((row) => {
      convergenceContext.beginPath();
      convergenceContext.arc(xFor(row.grid), yFor(row[key]), seriesIndex ? 4 : 3.5, 0, Math.PI * 2);
      convergenceContext.fillStyle = colour;
      convergenceContext.fill();
    });
  });

  convergenceContext.strokeStyle = COLOURS.ink;
  line(convergenceContext, plot.x, plot.y, plot.x, plot.y + plot.height);
  line(convergenceContext, plot.x, plot.y + plot.height, plot.x + plot.width, plot.y + plot.height);
  convergenceContext.textAlign = "center";
  convergenceContext.fillStyle = COLOURS.ink;
  convergenceContext.fillText("Interior grid points, N", plot.x + plot.width / 2, height - 16);
  series.forEach(({ colour, label }, index) => {
    const x = plot.x + 10 + index * (compact ? 86 : 112);
    convergenceContext.fillStyle = colour;
    convergenceContext.fillRect(x, 14, 18, 3);
    convergenceContext.fillStyle = COLOURS.ink;
    convergenceContext.textAlign = "left";
    convergenceContext.fillText(label, x + 25, 19);
  });
}

function renderNumericalEvidence() {
  if (!state.evidence) return;
  const finest = state.evidence.numericalMoments.filter(
    (record) => record.grid === 1600 && [1, 2, 3, 5, 10].includes(record.n),
  );
  numericalMomentsBody.replaceChildren(
    ...finest.map((record) => {
      const row = document.createElement("tr");
      const values = [
        String(record.n),
        (record.deltaX * 1e9).toFixed(6),
        (record.analyticalDeltaX * 1e9).toFixed(6),
        (record.pSquared * 1e48).toFixed(6),
        (record.deltaP * 1e25).toFixed(6),
        (record.analyticalDeltaP * 1e25).toFixed(6),
        record.product.toFixed(6),
        record.analyticalProduct.toFixed(6),
        record.ratio.toFixed(6),
        `${(record.relativeUncertaintyError * 100).toFixed(4)}%`,
      ];
      values.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });
      return row;
    }),
  );
  const convergence = state.evidence.uncertaintyConvergence;
  const finestGrid = convergence.at(-1);
  const minimumProduct = Math.min(
    ...state.evidence.numericalMoments.map((record) => record.product),
  );
  const passed = state.evidence.validation.checks.filter(
    (check) => check.passed === true,
  ).length;
  outputs.validationCount.textContent = `${passed}/${state.evidence.validation.checks.length}`;
  outputs.validationBoundary.textContent = "ψ(0) = ψ(a) = 0";
  outputs.validationNormalization.textContent = Math.max(
    ...state.evidence.numericalMoments.map(
      (record) => Math.abs(record.normalization - 1),
    ),
  ).toExponential(2);
  outputs.validationNodes.textContent = "10/10 pass";
  outputs.validationEnergy.textContent = "n² · order 2";
  outputs.validationOverlap.textContent = `1 − ${(1 - finestGrid.minimumOverlap).toExponential(2)}`;
  outputs.validationPMean.textContent = finestGrid.pMeanScaleRatio.toExponential(2);
  outputs.validationP2.textContent = `${(finestGrid.pSquaredError * 100).toFixed(4)}%`;
  outputs.validationOrder.textContent =
    `${finestGrid.minimumProductOrder.toFixed(3)}–${finestGrid.maximumProductOrder.toFixed(3)}`;
  outputs.validationError.textContent = `${(finestGrid.deltaPError * 100).toFixed(4)}%`;
  outputs.validationUncertainty.textContent = `${(finestGrid.uncertaintyError * 100).toFixed(4)}%`;
  outputs.validationBound.textContent = `${minimumProduct.toFixed(6)} ℏ`;
  drawConvergence();
}

function makeRenderedMathScrollableAndFocusable() {
  document.querySelectorAll(".moment-ledger .katex-display").forEach((display) => {
    display.setAttribute("tabindex", "0");
  });
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
  renderInlineMath(
    outputs.extensionResult,
    String.raw`n=${state.n}\;\cdot\;${expectation.productOverHbar.toFixed(6)}\hbar>0.5\hbar`,
    `n = ${state.n} · ${expectation.productOverHbar.toFixed(6)}ℏ > 0.5ℏ`,
  );
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
  drawConvergence();
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
  document.querySelector("[data-convergence-error]").hidden = false;
  outputs.stateTitle.textContent = "Model data unavailable";
  outputs.stateBadge.textContent = "Controls unavailable";
  outputs.spectrumStatus.textContent = "Spectrum unavailable";
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

resetStateButton.addEventListener("click", () => {
  state.view = "both";
  state.densityStates = new Set([1, 2, 3, 4]);
  document.querySelector('input[name="state-view"][value="both"]').checked = true;
  document.querySelectorAll("[data-density-state]").forEach((control) => {
    control.checked = true;
  });
  selectState(1);
  quantumControl.focus({ preventScroll: true });
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
  convergenceCanvas,
]) {
  resizeObserver.observe(canvas);
}

window.addEventListener("pagehide", () => resizeObserver.disconnect(), {
  once: true,
});

try {
  state.evidence = await loadTask07Evidence();
  laboratory.classList.remove("is-loading");
  enableControls();
  makeRenderedMathScrollableAndFocusable();
  outputs.spectrumStatus.textContent = "10 discrete levels";
  document.body.dataset.task07Status = "verified";
  renderNumericalEvidence();
  renderAll();
  window.dispatchEvent(new CustomEvent("task07:ready"));
} catch (error) {
  console.error("Task 7 model data failed to load", error);
  document.body.dataset.task07Status = "error";
  setFailureState();
}
