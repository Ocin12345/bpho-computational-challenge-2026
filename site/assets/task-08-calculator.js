import { loadTask08Evidence } from "./task-08-evidence.js?v=20260731";
import {
  clampDisplayAngle,
  mismatchComparison,
  mismatchSweep,
} from "../../task08_quantum_cryptography/app/physics.js";
import {
  advanceSeed,
  simulateFinitePhotonExperiment,
} from "../../task08_quantum_cryptography/app/statistics.js";

const PRESETS = Object.freeze({
  official: { thetaDeg: -30, phiDeg: 30 },
  zero: { thetaDeg: 0, phiDeg: 0 },
  aligned: { thetaDeg: 45, phiDeg: 45 },
  contrast: { thetaDeg: -45, phiDeg: 45 },
  perpendicular: { thetaDeg: 0, phiDeg: 90 },
});

const COLOURS = Object.freeze({
  orange: "#b65f45",
  orangeDeep: "#8d432f",
  teal: "#568b84",
  tealDeep: "#356d67",
  ochre: "#b79552",
  cream: "#f8f4eb",
  ink: "#2d2923",
  muted: "#766f65",
  grid: "#ded8cf",
  gridSoft: "#ebe6de",
  paper: "#fcfbf7",
  paperDeep: "#f5f1e9",
});

const laboratory = document.querySelector("[data-detector-laboratory]");
const detectorCanvas = document.querySelector("#detector-canvas");
const detectorContext = detectorCanvas.getContext("2d");
const sweepCanvas = document.querySelector("#sweep-canvas");
const sweepContext = sweepCanvas.getContext("2d");
const landscapeCanvas = document.querySelector("#landscape-canvas");
const landscapeContext = landscapeCanvas.getContext("2d");
const thetaControl = document.querySelector("#theta-angle");
const phiControl = document.querySelector("#phi-angle");
const angleControls = document.querySelector("[data-angle-controls]");
const samplingControls = document.querySelector("[data-sampling-controls]");
const photonPairsControl = document.querySelector("#photon-pairs");
const seedControl = document.querySelector("#sample-seed");
const sweepTooltip = document.querySelector("[data-sweep-tooltip]");

const outputs = {
  angleTitle: document.querySelector("[data-angle-title]"),
  badge: document.querySelector("[data-laboratory-badge]"),
  theta: document.querySelector("[data-theta-output]"),
  phi: document.querySelector("[data-phi-output]"),
  classicalPercent: document.querySelector("[data-classical-percent]"),
  classicalDecimal: document.querySelector("[data-classical-decimal]"),
  classicalFill: document.querySelector("[data-classical-fill]"),
  quantumPercent: document.querySelector("[data-quantum-percent]"),
  quantumDecimal: document.querySelector("[data-quantum-decimal]"),
  quantumFill: document.querySelector("[data-quantum-fill]"),
  difference: document.querySelector("[data-difference]"),
  differenceSummary: document.querySelector("[data-difference-summary]"),
  officialLock: document.querySelector("[data-official-lock]"),
  relativeAngle: document.querySelector("[data-relative-angle]"),
  sweepTitle: document.querySelector("[data-sweep-title]"),
  sweepStatus: document.querySelector("[data-sweep-status]"),
  landscapeSelected: document.querySelector("[data-landscape-selected]"),
  landscapeDifference: document.querySelector("[data-landscape-difference]"),
  sampleContext: document.querySelector("[data-sample-context]"),
};

const sampleOutputs = {
  classical: {
    theory: document.querySelector("[data-classical-theory]"),
    observed: document.querySelector("[data-classical-observed]"),
    count: document.querySelector("[data-classical-count]"),
    total: document.querySelector("[data-classical-total]"),
    interval: document.querySelector("[data-classical-interval]"),
    theoryMarker: document.querySelector("[data-classical-theory-marker]"),
    observedMarker: document.querySelector("[data-classical-observed-marker]"),
    expected: document.querySelector("[data-classical-expected]"),
    wilson: document.querySelector("[data-classical-wilson]"),
    residual: document.querySelector("[data-classical-residual]"),
  },
  quantum: {
    theory: document.querySelector("[data-quantum-theory]"),
    observed: document.querySelector("[data-quantum-observed]"),
    count: document.querySelector("[data-quantum-count]"),
    total: document.querySelector("[data-quantum-total]"),
    interval: document.querySelector("[data-quantum-interval]"),
    theoryMarker: document.querySelector("[data-quantum-theory-marker]"),
    observedMarker: document.querySelector("[data-quantum-observed-marker]"),
    expected: document.querySelector("[data-quantum-expected]"),
    wilson: document.querySelector("[data-quantum-wilson]"),
    residual: document.querySelector("[data-quantum-residual]"),
  },
};

const state = {
  evidence: null,
  thetaDeg: -30,
  phiDeg: 30,
  photonPairs: 1000,
  seed: 2026,
  sweepPlot: null,
  landscapePlot: null,
  landscapeRaster: null,
};

const countFormatter = new Intl.NumberFormat("en-US");

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

  const flecks = Math.min(280, Math.max(90, Math.round((width * height) / 3200)));
  context.save();
  context.fillStyle = "rgba(74, 64, 52, 0.035)";
  for (let index = 0; index < flecks; index += 1) {
    const x = (index * 83 + (index % 7) * 19) % width;
    const y = (index * 47 + (index % 11) * 23) % height;
    const radius = index % 5 === 0 ? 0.7 : 0.42;
    context.beginPath();
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fill();
  }
  context.restore();
}

function signedAngle(value) {
  if (Math.abs(value) < 0.0005) return "0°";
  return `${value > 0 ? "+" : "−"}${Math.abs(value).toFixed(0)}°`;
}

function percent(value) {
  return `${(100 * value).toFixed(1)}%`;
}

function signedPoints(value) {
  const points = 100 * value;
  if (Math.abs(points) < 0.05) return "0.0 pp";
  return `${points > 0 ? "+" : "−"}${Math.abs(points).toFixed(1)} pp`;
}

function intervalPercent(interval) {
  return `${(100 * interval.lower).toFixed(1)}–${(
    100 * interval.upper
  ).toFixed(1)}%`;
}

function residualText(value) {
  if (value === null) return "deterministic";
  if (Math.abs(value) < 0.005) return "0.00σ";
  return `${value > 0 ? "+" : "−"}${Math.abs(value).toFixed(2)}σ`;
}

function detectorAxis(angleDeg, radius) {
  const angle = (angleDeg * Math.PI) / 180;
  return {
    x: radius * Math.cos(angle),
    y: -radius * Math.sin(angle),
  };
}

function drawDetectorDial(context, centerX, centerY, radius, angleDeg, label, colour) {
  context.save();
  context.fillStyle = "rgba(255, 255, 255, 0.68)";
  context.strokeStyle = COLOURS.grid;
  context.lineWidth = 1;
  context.beginPath();
  context.arc(centerX, centerY, radius, 0, Math.PI * 2);
  context.fill();
  context.stroke();

  context.strokeStyle = COLOURS.gridSoft;
  context.beginPath();
  context.arc(centerX, centerY, radius * 0.64, 0, Math.PI * 2);
  context.stroke();

  context.strokeStyle = "rgba(45, 41, 35, 0.17)";
  context.lineWidth = 1;
  for (let angle = 0; angle < 360; angle += 15) {
    const radians = (angle * Math.PI) / 180;
    const major = angle % 45 === 0;
    const inner = radius * (major ? 0.86 : 0.91);
    const outer = radius * 0.98;
    line(
      context,
      centerX + inner * Math.cos(radians),
      centerY + inner * Math.sin(radians),
      centerX + outer * Math.cos(radians),
      centerY + outer * Math.sin(radians),
    );
  }

  context.strokeStyle = "rgba(45, 41, 35, 0.14)";
  context.setLineDash([3, 5]);
  line(context, centerX - radius * 0.76, centerY, centerX + radius * 0.76, centerY);
  line(context, centerX, centerY - radius * 0.76, centerX, centerY + radius * 0.76);
  context.setLineDash([]);

  const angleRadians = (-angleDeg * Math.PI) / 180;
  context.strokeStyle = colour;
  context.lineWidth = 1.4;
  context.beginPath();
  context.arc(
    centerX,
    centerY,
    radius * 0.36,
    0,
    angleRadians,
    angleRadians < 0,
  );
  context.stroke();

  const primary = detectorAxis(angleDeg, radius * 0.73);
  const secondary = detectorAxis(angleDeg + 90, radius * 0.73);
  context.strokeStyle = "rgba(255, 255, 255, 0.94)";
  context.lineWidth = 7;
  line(
    context,
    centerX - primary.x,
    centerY - primary.y,
    centerX + primary.x,
    centerY + primary.y,
  );
  context.strokeStyle = colour;
  context.lineWidth = 3.4;
  line(
    context,
    centerX - primary.x,
    centerY - primary.y,
    centerX + primary.x,
    centerY + primary.y,
  );
  context.setLineDash([6, 6]);
  context.globalAlpha = 0.5;
  context.lineWidth = 1.6;
  line(
    context,
    centerX - secondary.x,
    centerY - secondary.y,
    centerX + secondary.x,
    centerY + secondary.y,
  );
  context.globalAlpha = 1;
  context.setLineDash([]);
  context.strokeStyle = COLOURS.paper;
  context.lineWidth = 2;
  context.fillStyle = colour;
  context.beginPath();
  context.arc(centerX, centerY, 6, 0, Math.PI * 2);
  context.fill();
  context.stroke();

  context.fillStyle = COLOURS.muted;
  context.font = `600 ${Math.max(11, radius * 0.085)}px Arial`;
  context.textAlign = "center";
  context.fillText(label, centerX, centerY - radius - 23);
  context.fillStyle = colour;
  context.font = `${Math.max(19, radius * 0.15)}px "Times New Roman"`;
  context.fillText(signedAngle(angleDeg), centerX, centerY + 6);
  context.restore();
}

function drawDetectors() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(detectorCanvas, detectorContext);
  const compact = width < 620;
  detectorContext.clearRect(0, 0, width, height);
  paintPaper(detectorContext, width, height);

  const centerY = compact ? height * 0.47 : height * 0.5;
  const leftX = compact ? width * 0.26 : width * 0.25;
  const rightX = compact ? width * 0.74 : width * 0.75;
  const radius = Math.min(
    compact ? width * 0.2 : width * 0.17,
    height * 0.29,
  );

  detectorContext.strokeStyle = "rgba(89, 78, 66, 0.36)";
  detectorContext.lineWidth = 1.25;
  detectorContext.setLineDash([5, 6]);
  line(detectorContext, leftX + radius, centerY, rightX - radius, centerY);
  detectorContext.setLineDash([]);

  const arrowOffset = Math.min(45, Math.max(22, (rightX - leftX - 2 * radius) * 0.28));
  detectorContext.fillStyle = COLOURS.muted;
  for (const direction of [-1, 1]) {
    const tipX = width / 2 + direction * arrowOffset;
    detectorContext.beginPath();
    detectorContext.moveTo(tipX, centerY);
    detectorContext.lineTo(tipX - direction * 7, centerY - 4);
    detectorContext.lineTo(tipX - direction * 7, centerY + 4);
    detectorContext.closePath();
    detectorContext.fill();
  }

  const sourceX = width / 2;
  detectorContext.fillStyle = COLOURS.ochre;
  detectorContext.strokeStyle = COLOURS.paper;
  detectorContext.lineWidth = 3;
  detectorContext.beginPath();
  detectorContext.arc(sourceX, centerY, 7, 0, Math.PI * 2);
  detectorContext.fill();
  detectorContext.stroke();
  if (!compact) {
    detectorContext.font = `600 11px "Times New Roman"`;
    detectorContext.textAlign = "center";
    detectorContext.fillStyle = COLOURS.muted;
    detectorContext.fillText("PHOTON PAIR", sourceX, centerY + 29);
  }

  drawDetectorDial(
    detectorContext,
    leftX,
    centerY,
    radius,
    state.thetaDeg,
    "DETECTOR A · θ",
    COLOURS.orange,
  );
  drawDetectorDial(
    detectorContext,
    rightX,
    centerY,
    radius,
    state.phiDeg,
    "DETECTOR B · φ",
    COLOURS.teal,
  );

  const comparison = mismatchComparison(state.thetaDeg, state.phiDeg);
  detectorContext.fillStyle = COLOURS.ink;
  detectorContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
  detectorContext.fillText(
    `relative angle δ = ${signedAngle(comparison.relativeAngleDeg)}`,
    width / 2,
    height - 31,
  );
  detectorCanvas.setAttribute(
    "aria-label",
    `Detector A is ${signedAngle(state.thetaDeg)} and detector B is ${signedAngle(state.phiDeg)}. Relative angle ${signedAngle(comparison.relativeAngleDeg)}. Classical mismatch ${percent(comparison.classicalMismatch)} and quantum mismatch ${percent(comparison.quantumMismatch)}.`,
  );
}

function drawSweep() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(sweepCanvas, sweepContext);
  const compact = width < 610;
  const margins = {
    left: compact ? 64 : 88,
    right: compact ? 23 : 40,
    top: compact ? 58 : 68,
    bottom: compact ? 72 : 82,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const xFor = (phi) => plot.x + ((phi + 90) / 180) * plot.width;
  const yFor = (probability) =>
    plot.y + plot.height - probability * plot.height;
  state.sweepPlot = { plot, xFor, yFor };

  sweepContext.clearRect(0, 0, width, height);
  paintPaper(sweepContext, width, height);
  sweepContext.font = `${compact ? 10 : 14}px "Times New Roman"`;
  sweepContext.fillStyle = COLOURS.muted;
  sweepContext.strokeStyle = COLOURS.grid;
  sweepContext.lineWidth = 1;

  for (const tick of [0, 0.25, 0.5, 0.75, 1]) {
    const y = yFor(tick);
    line(sweepContext, plot.x, y, plot.x + plot.width, y);
    sweepContext.textAlign = "right";
    sweepContext.fillText(`${Math.round(tick * 100)}%`, plot.x - 11, y + 4);
  }
  for (const tick of [-90, -45, 0, 45, 90]) {
    const x = xFor(tick);
    line(sweepContext, x, plot.y, x, plot.y + plot.height);
    sweepContext.textAlign = "center";
    sweepContext.fillText(signedAngle(tick), x, plot.y + plot.height + 24);
  }

  const sweep = mismatchSweep(state.thetaDeg, -90, 90, 0.5);
  const traces = [
    ["classicalMismatch", COLOURS.orangeDeep, false],
    ["quantumMismatch", COLOURS.tealDeep, true],
  ];
  const trace = (key) => {
    sweepContext.beginPath();
    sweep.forEach((record, index) => {
      const x = xFor(record.phiDeg);
      const y = yFor(record[key]);
      if (index === 0) sweepContext.moveTo(x, y);
      else sweepContext.lineTo(x, y);
    });
  };
  for (const [key, colour, dashed] of traces) {
    trace(key);
    sweepContext.strokeStyle = "rgba(255, 255, 255, 0.9)";
    sweepContext.lineWidth = compact ? 5 : 6.5;
    sweepContext.setLineDash(dashed ? [10, 7] : []);
    sweepContext.stroke();

    trace(key);
    sweepContext.strokeStyle = colour;
    sweepContext.lineWidth = compact ? 2.2 : 3;
    sweepContext.setLineDash(dashed ? [10, 7] : []);
    sweepContext.stroke();
    sweepContext.setLineDash([]);
  }

  const comparison = mismatchComparison(state.thetaDeg, state.phiDeg);
  const selectedX = xFor(state.phiDeg);
  sweepContext.strokeStyle = "#8f867b";
  sweepContext.lineWidth = 1.4;
  sweepContext.setLineDash([4, 5]);
  line(sweepContext, selectedX, plot.y, selectedX, plot.y + plot.height);
  sweepContext.setLineDash([]);
  for (const [value, colour] of [
    [comparison.classicalMismatch, COLOURS.orangeDeep],
    [comparison.quantumMismatch, COLOURS.tealDeep],
  ]) {
    sweepContext.fillStyle = colour;
    sweepContext.strokeStyle = COLOURS.paper;
    sweepContext.lineWidth = 2;
    sweepContext.beginPath();
    sweepContext.arc(selectedX, yFor(value), compact ? 6 : 8, 0, Math.PI * 2);
    sweepContext.fill();
    sweepContext.stroke();
  }

  sweepContext.strokeStyle = COLOURS.ink;
  sweepContext.lineWidth = 1.3;
  line(sweepContext, plot.x, plot.y, plot.x, plot.y + plot.height);
  line(
    sweepContext,
    plot.x,
    plot.y + plot.height,
    plot.x + plot.width,
    plot.y + plot.height,
  );
  sweepContext.fillStyle = COLOURS.ink;
  sweepContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
  sweepContext.textAlign = "center";
  sweepContext.fillText(
    "Detector B angle, φ",
    plot.x + plot.width / 2,
    height - (compact ? 18 : 23),
  );
  sweepContext.save();
  sweepContext.translate(compact ? 19 : 27, plot.y + plot.height / 2);
  sweepContext.rotate(-Math.PI / 2);
  sweepContext.fillText("Mismatch probability", 0, 0);
  sweepContext.restore();
  sweepContext.font = `italic ${compact ? 12 : 16}px "Times New Roman"`;
  sweepContext.fillStyle = COLOURS.muted;
  sweepContext.textAlign = "right";
  sweepContext.fillText(
    `θ = ${signedAngle(state.thetaDeg)} · shared physical scale`,
    plot.x + plot.width,
    plot.y - 22,
  );
}

function mixChannel(a, b, amount) {
  return Math.round(a + (b - a) * amount);
}

function contrastColour(value) {
  const white = [255, 250, 244];
  const negative = [255, 120, 77];
  const positive = [79, 225, 209];
  const amount = Math.min(1, Math.abs(value) / 0.5);
  const target = value < 0 ? negative : positive;
  return [
    mixChannel(white[0], target[0], amount),
    mixChannel(white[1], target[1], amount),
    mixChannel(white[2], target[2], amount),
    255,
  ];
}

function createLandscapeRaster() {
  const raster = document.createElement("canvas");
  raster.width = 181;
  raster.height = 181;
  const context = raster.getContext("2d");
  const image = context.createImageData(181, 181);
  for (const record of state.evidence.grid) {
    const rowFromTop = 180 - record.thetaIndex;
    const offset = (rowFromTop * 181 + record.phiIndex) * 4;
    const colour = contrastColour(record.difference);
    image.data[offset] = colour[0];
    image.data[offset + 1] = colour[1];
    image.data[offset + 2] = colour[2];
    image.data[offset + 3] = 255;
  }
  context.putImageData(image, 0, 0);
  state.landscapeRaster = raster;
}

function drawLandscape() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(landscapeCanvas, landscapeContext);
  const compact = width < 600;
  const size = Math.min(
    width - (compact ? 84 : 120),
    height - (compact ? 105 : 130),
  );
  const plot = {
    x: compact ? 61 : 86,
    y: compact ? 48 : 62,
    width: size,
    height: size,
  };
  state.landscapePlot = plot;
  if (!state.landscapeRaster) createLandscapeRaster();

  landscapeContext.clearRect(0, 0, width, height);
  landscapeContext.fillStyle = COLOURS.paper;
  landscapeContext.fillRect(0, 0, width, height);
  landscapeContext.imageSmoothingEnabled = true;
  landscapeContext.drawImage(
    state.landscapeRaster,
    plot.x,
    plot.y,
    plot.width,
    plot.height,
  );

  landscapeContext.strokeStyle = "rgba(34,23,36,0.27)";
  landscapeContext.lineWidth = 1;
  for (const angle of [-90, -45, 0, 45, 90]) {
    const position = ((angle + 90) / 180) * plot.width;
    line(
      landscapeContext,
      plot.x + position,
      plot.y,
      plot.x + position,
      plot.y + plot.height,
    );
    const y = plot.y + plot.height - position;
    line(landscapeContext, plot.x, y, plot.x + plot.width, y);
  }

  const x = plot.x + ((state.phiDeg + 90) / 180) * plot.width;
  const y =
    plot.y + plot.height - ((state.thetaDeg + 90) / 180) * plot.height;
  landscapeContext.strokeStyle = COLOURS.ink;
  landscapeContext.lineWidth = 1.8;
  landscapeContext.beginPath();
  landscapeContext.arc(x, y, compact ? 6 : 8, 0, Math.PI * 2);
  landscapeContext.stroke();
  line(landscapeContext, x - 13, y, x + 13, y);
  line(landscapeContext, x, y - 13, x, y + 13);

  landscapeContext.fillStyle = COLOURS.ink;
  landscapeContext.font = `${compact ? 10 : 14}px "Times New Roman"`;
  landscapeContext.textAlign = "center";
  for (const angle of [-90, -45, 0, 45, 90]) {
    const px = plot.x + ((angle + 90) / 180) * plot.width;
    landscapeContext.fillText(
      signedAngle(angle),
      px,
      plot.y + plot.height + 24,
    );
    const py =
      plot.y + plot.height - ((angle + 90) / 180) * plot.height;
    landscapeContext.textAlign = "right";
    landscapeContext.fillText(signedAngle(angle), plot.x - 10, py + 4);
    landscapeContext.textAlign = "center";
  }
  landscapeContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
  landscapeContext.fillText(
    "Detector B angle, φ",
    plot.x + plot.width / 2,
    height - (compact ? 17 : 23),
  );
  landscapeContext.save();
  landscapeContext.translate(compact ? 17 : 25, plot.y + plot.height / 2);
  landscapeContext.rotate(-Math.PI / 2);
  landscapeContext.fillText("Detector A angle, θ", 0, 0);
  landscapeContext.restore();
}

function renderSampleCard(model, sample) {
  const output = sampleOutputs[model];
  output.theory.textContent = `theory ${percent(sample.theoreticalProbability)}`;
  output.observed.textContent = percent(sample.observedProbability);
  output.count.textContent = countFormatter.format(sample.mismatches);
  output.total.textContent = countFormatter.format(sample.photonPairs);
  output.expected.textContent = sample.expectedMismatches.toFixed(1);
  output.wilson.textContent = intervalPercent(sample.wilsonInterval);
  output.residual.textContent = residualText(sample.standardizedResidual);
  output.interval.style.left = `${sample.wilsonInterval.lower * 100}%`;
  output.interval.style.width =
    `${(sample.wilsonInterval.upper - sample.wilsonInterval.lower) * 100}%`;
  output.theoryMarker.style.left =
    `${sample.theoreticalProbability * 100}%`;
  output.observedMarker.style.left = `${sample.observedProbability * 100}%`;
}

function renderSampling() {
  if (!state.evidence) return;
  const experiment = simulateFinitePhotonExperiment(
    state.thetaDeg,
    state.phiDeg,
    state.photonPairs,
    state.seed,
  );
  renderSampleCard("classical", experiment.classical);
  renderSampleCard("quantum", experiment.quantum);
  outputs.sampleContext.textContent =
    `θ = ${signedAngle(state.thetaDeg)} · φ = ${signedAngle(state.phiDeg)} · N = ${countFormatter.format(state.photonPairs)} · seed ${countFormatter.format(state.seed)}`;
  photonPairsControl.value = String(state.photonPairs);
  seedControl.value = String(state.seed);
  document.querySelectorAll("[data-photon-preset]").forEach((button) => {
    button.classList.toggle(
      "is-current",
      Number(button.dataset.photonPreset) === state.photonPairs,
    );
  });
}

function updateOutputs() {
  const comparison = mismatchComparison(state.thetaDeg, state.phiDeg);
  outputs.angleTitle.textContent =
    `θ = ${signedAngle(state.thetaDeg)} · φ = ${signedAngle(state.phiDeg)}`;
  outputs.badge.textContent =
    `δ = ${signedAngle(comparison.relativeAngleDeg)}`;
  outputs.theta.value = signedAngle(state.thetaDeg);
  outputs.phi.value = signedAngle(state.phiDeg);
  outputs.classicalPercent.value = percent(comparison.classicalMismatch);
  outputs.classicalDecimal.textContent =
    `P = ${comparison.classicalMismatch.toFixed(3)}`;
  outputs.classicalFill.style.width =
    `${comparison.classicalMismatch * 100}%`;
  outputs.quantumPercent.value = percent(comparison.quantumMismatch);
  outputs.quantumDecimal.textContent =
    `P = ${comparison.quantumMismatch.toFixed(3)}`;
  outputs.quantumFill.style.width = `${comparison.quantumMismatch * 100}%`;
  outputs.difference.value = signedPoints(comparison.signedDifference);
  const direction =
    Math.abs(comparison.signedDifference) < 0.0005
      ? "The two models agree at this setting."
      : `Quantum predicts ${Math.abs(comparison.signedDifference * 100).toFixed(1)} percentage points ${comparison.signedDifference > 0 ? "more" : "fewer"} mismatches.`;
  outputs.differenceSummary.textContent = direction;
  outputs.relativeAngle.textContent =
    `relative angle δ = ${signedAngle(comparison.relativeAngleDeg)}`;
  outputs.officialLock.textContent =
    state.thetaDeg === -30 && state.phiDeg === 30
      ? "3/8 versus 3/4"
      : "Required example available";
  outputs.sweepTitle.textContent =
    `θ = ${signedAngle(state.thetaDeg)} · φ = ${signedAngle(state.phiDeg)}`;
  outputs.landscapeSelected.textContent =
    `${signedAngle(state.thetaDeg)} / ${signedAngle(state.phiDeg)}`;
  outputs.landscapeDifference.textContent =
    `ΔP = ${comparison.signedDifference >= 0 ? "+" : "−"}${Math.abs(comparison.signedDifference).toFixed(3)}`;
  document.querySelectorAll("[data-angle-preset]").forEach((button) => {
    const preset = PRESETS[button.dataset.anglePreset];
    button.classList.toggle(
      "is-current",
      preset.thetaDeg === state.thetaDeg && preset.phiDeg === state.phiDeg,
    );
  });
}

function renderAll() {
  if (!state.evidence) return;
  updateOutputs();
  drawDetectors();
  drawSweep();
  drawLandscape();
  renderSampling();
}

function setAngles(thetaDeg, phiDeg) {
  if (!state.evidence) return;
  state.thetaDeg = Math.round(clampDisplayAngle(thetaDeg));
  state.phiDeg = Math.round(clampDisplayAngle(phiDeg));
  thetaControl.value = String(state.thetaDeg);
  phiControl.value = String(state.phiDeg);
  renderAll();
}

function clampPhotonPairs(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 1000;
  return Math.max(10, Math.min(100000, Math.round(number)));
}

function clampSeed(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 2026;
  return Math.max(0, Math.min(0xffffffff, Math.round(number))) >>> 0;
}

function enableControls() {
  angleControls.querySelectorAll("input").forEach((control) => {
    control.disabled = false;
  });
  document.querySelectorAll("[data-angle-preset]").forEach((button) => {
    button.disabled = false;
  });
  samplingControls.querySelectorAll("button, input").forEach((control) => {
    control.disabled = false;
  });
}

function setFailureState() {
  laboratory.classList.remove("is-loading");
  document.querySelector("[data-detector-error]").hidden = false;
  document.querySelector("[data-sweep-error]").hidden = false;
  document.querySelector("[data-landscape-error]").hidden = false;
  outputs.badge.textContent = "Interaction locked";
  outputs.sweepStatus.textContent = "Sweep unavailable";
}

thetaControl.addEventListener("input", () => {
  setAngles(Number(thetaControl.value), state.phiDeg);
});

phiControl.addEventListener("input", () => {
  setAngles(state.thetaDeg, Number(phiControl.value));
});

document.querySelectorAll("[data-angle-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    const preset = PRESETS[button.dataset.anglePreset];
    setAngles(preset.thetaDeg, preset.phiDeg);
  });
});

for (const canvas of [detectorCanvas, sweepCanvas, landscapeCanvas]) {
  canvas.addEventListener("keydown", (event) => {
    if (!state.evidence) return;
    if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      event.preventDefault();
      setAngles(state.thetaDeg, state.phiDeg + 1);
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      event.preventDefault();
      setAngles(state.thetaDeg, state.phiDeg - 1);
    }
    if (event.key === "Home") {
      event.preventDefault();
      setAngles(state.thetaDeg, -90);
    }
    if (event.key === "End") {
      event.preventDefault();
      setAngles(state.thetaDeg, 90);
    }
  });
}

sweepCanvas.addEventListener("pointermove", (event) => {
  if (!state.sweepPlot) return;
  const bounds = sweepCanvas.getBoundingClientRect();
  const localX = event.clientX - bounds.left;
  const { plot } = state.sweepPlot;
  if (localX < plot.x || localX > plot.x + plot.width) {
    sweepTooltip.hidden = true;
    return;
  }
  const phi = Math.max(
    -90,
    Math.min(90, -90 + ((localX - plot.x) / plot.width) * 180),
  );
  const comparison = mismatchComparison(state.thetaDeg, phi);
  sweepTooltip.hidden = false;
  sweepTooltip.textContent =
    `φ ${signedAngle(phi)} · C ${percent(comparison.classicalMismatch)} · Q ${percent(comparison.quantumMismatch)}`;
  sweepTooltip.style.left =
    `${Math.min(localX + 14, sweepCanvas.clientWidth - 180)}px`;
  sweepTooltip.style.top = "16px";
});

sweepCanvas.addEventListener("pointerleave", () => {
  sweepTooltip.hidden = true;
});

sweepCanvas.addEventListener("click", (event) => {
  if (!state.sweepPlot) return;
  const bounds = sweepCanvas.getBoundingClientRect();
  const localX = event.clientX - bounds.left;
  const { plot } = state.sweepPlot;
  if (localX < plot.x || localX > plot.x + plot.width) return;
  const phi = -90 + ((localX - plot.x) / plot.width) * 180;
  setAngles(state.thetaDeg, phi);
  sweepCanvas.focus({ preventScroll: true });
});

landscapeCanvas.addEventListener("click", (event) => {
  if (!state.landscapePlot) return;
  const bounds = landscapeCanvas.getBoundingClientRect();
  const x = event.clientX - bounds.left;
  const y = event.clientY - bounds.top;
  const plot = state.landscapePlot;
  if (
    x < plot.x ||
    x > plot.x + plot.width ||
    y < plot.y ||
    y > plot.y + plot.height
  ) {
    return;
  }
  const phi = -90 + ((x - plot.x) / plot.width) * 180;
  const theta = -90 + ((plot.y + plot.height - y) / plot.height) * 180;
  setAngles(theta, phi);
  landscapeCanvas.focus({ preventScroll: true });
});

photonPairsControl.addEventListener("change", () => {
  state.photonPairs = clampPhotonPairs(photonPairsControl.value);
  renderSampling();
});

seedControl.addEventListener("change", () => {
  state.seed = clampSeed(seedControl.value);
  renderSampling();
});

document.querySelectorAll("[data-photon-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    state.photonPairs = Number(button.dataset.photonPreset);
    renderSampling();
  });
});

document.querySelector("[data-next-sample]").addEventListener("click", () => {
  state.seed = advanceSeed(state.seed);
  renderSampling();
});

const resizeObserver = new ResizeObserver(() => {
  if (!state.evidence) return;
  drawDetectors();
  drawSweep();
  drawLandscape();
});

window.addEventListener("pagehide", () => resizeObserver.disconnect(), {
  once: true,
});
for (const canvas of [detectorCanvas, sweepCanvas, landscapeCanvas]) {
  resizeObserver.observe(canvas);
}

try {
  state.evidence = await loadTask08Evidence();
  laboratory.classList.remove("is-loading");
  enableControls();
  outputs.sweepStatus.textContent = "361-angle sweep";
  state.landscapeRaster = null;
  document.body.dataset.task08Status = "verified";
  renderAll();
  window.dispatchEvent(new CustomEvent("task08:ready"));
} catch (error) {
  console.error("Task 8 evidence validation failed", error);
  document.body.dataset.task08Status = "error";
  setFailureState();
}
