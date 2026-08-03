import { loadTask05Evidence } from "./task-05-evidence.js";

const SERIES = Object.freeze({
  Lyman: { colour: "#0b7eb8", marker: "circle", symbol: "●" },
  Balmer: { colour: "#d85f02", marker: "square", symbol: "■" },
  Paschen: { colour: "#0a9f74", marker: "triangle", symbol: "▲" },
  Brackett: { colour: "#c978a4", marker: "diamond", symbol: "◆" },
  Pfund: { colour: "#df9f00", marker: "plus", symbol: "+" },
  "Higher series": { colour: "#607089", marker: "cross", symbol: "×" },
});

const SERIES_ORDER = Object.freeze([
  "Lyman",
  "Balmer",
  "Paschen",
  "Brackett",
  "Pfund",
  "Higher series",
]);

const SERIES_COUNTS = Object.freeze({
  Lyman: 9,
  Balmer: 8,
  Paschen: 7,
  Brackett: 6,
  Pfund: 5,
  "Higher series": 10,
});

const LINE_SUFFIXES = Object.freeze({
  alpha: "α",
  beta: "β",
  gamma: "γ",
  delta: "δ",
});

const instrument = document.querySelector("[data-transition-instrument]");
const stageCanvas = document.querySelector("#energy-level-stage");
const stageContext = stageCanvas.getContext("2d");
const atlas = document.querySelector("[data-emission-atlas]");
const chartCanvas = document.querySelector("#emission-energy-chart");
const chartContext = chartCanvas.getContext("2d");
const tooltip = document.querySelector("[data-atlas-tooltip]");
const transitionSelector = document.querySelector("#transition-selector");
const transitionControls = document.querySelector("[data-transition-controls]");
const visibleOnlyControl = document.querySelector("[data-visible-only]");
const photonRibbon = document.querySelector("[data-photon-ribbon]");
const evidenceLock = document.querySelector("[data-evidence-lock]");

const outputs = {
  transitionTitle: document.querySelector("[data-transition-title]"),
  regionBadge: document.querySelector("[data-region-badge]"),
  photonWavelength: document.querySelector("[data-photon-wavelength]"),
  photonEnergy: document.querySelector("[data-photon-energy]"),
  photonFrequency: document.querySelector("[data-photon-frequency]"),
  photonWavelengthReadout: document.querySelector(
    "[data-photon-wavelength-readout]",
  ),
  atlasStatus: document.querySelector("[data-atlas-status]"),
  atlasTransition: document.querySelector("[data-atlas-transition]"),
  atlasSeries: document.querySelector("[data-atlas-series]"),
  atlasEnergy: document.querySelector("[data-atlas-energy]"),
  atlasWavelength: document.querySelector("[data-atlas-wavelength]"),
  validationCount: document.querySelector("[data-validation-count]"),
  validationStatus: document.querySelector("[data-validation-status]"),
  transitionCount: document.querySelector("[data-transition-count]"),
  normalizedError: document.querySelector("[data-normalized-error]"),
  lockTitle: document.querySelector("[data-lock-title]"),
  lockDetail: document.querySelector("[data-lock-detail]"),
};

const state = {
  evidence: null,
  selectedIndex: 0,
  activeSeries: "All",
  visibleOnly: false,
  chartPoints: [],
  hoveredIndex: null,
};

function formatLineName(name) {
  if (!name) return "";
  const [series, suffix] = name.split("-");
  const symbol = LINE_SUFFIXES[suffix] || suffix;
  return series === "H" ? `H-${symbol}` : `${series}-${symbol}`;
}

function displaySeries(transition) {
  return transition.finalN <= 5 ? transition.seriesName : "Higher series";
}

function transitionLabel(transition) {
  const named = formatLineName(transition.lineName);
  return named
    ? `${named} · ${transition.initialN}→${transition.finalN}`
    : `${transition.initialN}→${transition.finalN}`;
}

function transitionOptionLabel(transition) {
  const named = formatLineName(transition.lineName);
  return `${transition.initialN}→${transition.finalN} · ${
    named || displaySeries(transition)
  } · ${formatWavelength(transition.wavelengthNm)}`;
}

function formatEnergy(value) {
  return `${value.toFixed(value >= 10 ? 4 : 6)} eV`;
}

function formatWavelength(value) {
  if (value >= 10000) return `${(value / 1000).toFixed(3)} µm`;
  if (value >= 1000) return `${value.toFixed(2)} nm`;
  return `${value.toFixed(3)} nm`;
}

function formatFrequency(value) {
  if (value >= 1e15) return `${(value / 1e15).toFixed(4)} PHz`;
  if (value >= 1e12) return `${(value / 1e12).toFixed(3)} THz`;
  return `${value.toExponential(4)} Hz`;
}

function wavelengthColour(wavelengthNm) {
  if (wavelengthNm < 380) return "#7652d8";
  if (wavelengthNm > 750) return "#ba5544";

  const stops = [
    [380, [120, 0, 168]],
    [430, [55, 28, 255]],
    [480, [0, 178, 255]],
    [510, [0, 222, 168]],
    [550, [75, 230, 68]],
    [590, [252, 232, 42]],
    [620, [255, 133, 34]],
    [680, [237, 42, 42]],
    [750, [150, 24, 37]],
  ];

  for (let index = 1; index < stops.length; index += 1) {
    if (wavelengthNm <= stops[index][0]) {
      const [x0, c0] = stops[index - 1];
      const [x1, c1] = stops[index];
      const t = (wavelengthNm - x0) / (x1 - x0);
      const colour = c0.map((channel, channelIndex) =>
        Math.round(channel + (c1[channelIndex] - channel) * t),
      );
      return `rgb(${colour.join(",")})`;
    }
  }
  return "#961825";
}

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
  return { width, height, density };
}

function roundedRect(context, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  context.beginPath();
  context.moveTo(x + r, y);
  context.lineTo(x + width - r, y);
  context.quadraticCurveTo(x + width, y, x + width, y + r);
  context.lineTo(x + width, y + height - r);
  context.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  context.lineTo(x + r, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - r);
  context.lineTo(x, y + r);
  context.quadraticCurveTo(x, y, x + r, y);
  context.closePath();
}

function drawEnergyStage() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(stageCanvas, stageContext);
  const transition = state.evidence.transitions[state.selectedIndex];
  const compact = width < 520;
  const left = compact ? 48 : 76;
  const right = compact ? 72 : 126;
  const top = compact ? 70 : 52;
  const bottom = compact ? 44 : 48;
  const plotHeight = height - top - bottom;
  const levelX0 = left;
  const levelX1 = width - right;
  const yForLevel = (n) => top + ((10 - n) / 9) * plotHeight;

  stageContext.clearRect(0, 0, width, height);
  stageContext.save();
  stageContext.lineCap = "round";
  stageContext.lineJoin = "round";

  stageContext.fillStyle = "#8e8390";
  stageContext.font = `${compact ? 9 : 11}px "Times New Roman"`;
  stageContext.textAlign = "left";
  if (compact) {
    stageContext.fillText("LEVEL SCHEMATIC · NOT TO SCALE", left, 21);
    stageContext.fillText("ENERGIES LABELLED IN eV", left, 35);
  } else {
    stageContext.fillText(
      "LEVEL-ORDERED SCHEMATIC · ENERGIES LABELLED · NOT TO SCALE",
      left,
      25,
    );
  }

  const ionizationY = compact ? 51 : Math.max(35, top - 18);
  stageContext.setLineDash([5, 5]);
  stageContext.strokeStyle = "rgba(244,236,242,0.30)";
  stageContext.lineWidth = 1;
  stageContext.beginPath();
  stageContext.moveTo(levelX0, ionizationY);
  stageContext.lineTo(levelX1, ionizationY);
  stageContext.stroke();
  stageContext.setLineDash([]);
  stageContext.fillStyle = "#968b97";
  stageContext.textAlign = "right";
  stageContext.fillText("ionization · 0 eV", width - 14, ionizationY + 4);

  for (const level of state.evidence.levels) {
    const y = yForLevel(level.n);
    const isInitial = level.n === transition.initialN;
    const isFinal = level.n === transition.finalN;

    stageContext.strokeStyle = isInitial
      ? "#e85d9f"
      : isFinal
        ? "#f7eff4"
        : "rgba(214,202,213,0.28)";
    stageContext.lineWidth = isInitial || isFinal ? 3 : 1.15;
    stageContext.beginPath();
    stageContext.moveTo(levelX0, y);
    stageContext.lineTo(levelX1, y);
    stageContext.stroke();

    stageContext.fillStyle = isInitial
      ? "#f3a5ca"
      : isFinal
        ? "#f7eff4"
        : "#968b97";
    stageContext.font = `${isInitial || isFinal ? "bold " : ""}${
      compact ? 12 : 14
    }px "Times New Roman"`;
    stageContext.textAlign = "right";
    stageContext.fillText(`n=${level.n}`, levelX0 - 10, y + 4);
    stageContext.textAlign = "left";
    stageContext.fillText(
      `${level.energyEv.toFixed(level.n <= 3 ? 3 : 4)} eV`,
      levelX1 + 10,
      y + 4,
    );
  }

  const arrowX = levelX0 + (levelX1 - levelX0) * (compact ? 0.72 : 0.76);
  const startY = yForLevel(transition.initialN) + 7;
  const endY = yForLevel(transition.finalN) - 8;
  stageContext.strokeStyle = wavelengthColour(transition.wavelengthNm);
  stageContext.fillStyle = wavelengthColour(transition.wavelengthNm);
  stageContext.shadowColor = wavelengthColour(transition.wavelengthNm);
  stageContext.shadowBlur = 12;
  stageContext.lineWidth = 3;
  stageContext.beginPath();
  stageContext.moveTo(arrowX, startY);
  stageContext.lineTo(arrowX, endY);
  stageContext.stroke();
  stageContext.beginPath();
  stageContext.moveTo(arrowX - 7, endY - 10);
  stageContext.lineTo(arrowX, endY);
  stageContext.lineTo(arrowX + 7, endY - 10);
  stageContext.stroke();
  stageContext.shadowBlur = 0;

  const label = `${transition.initialN} → ${transition.finalN}`;
  stageContext.font = `bold ${compact ? 13 : 15}px "Times New Roman"`;
  const labelWidth = stageContext.measureText(label).width + 20;
  const labelX = Math.max(levelX0, arrowX - labelWidth / 2);
  const labelY = (startY + endY) / 2 - 14;
  roundedRect(stageContext, labelX, labelY, labelWidth, 28, 2);
  stageContext.fillStyle = "rgba(22,17,29,0.94)";
  stageContext.fill();
  stageContext.strokeStyle = wavelengthColour(transition.wavelengthNm);
  stageContext.lineWidth = 1;
  stageContext.stroke();
  stageContext.fillStyle = "#f8f0f5";
  stageContext.textAlign = "center";
  stageContext.fillText(label, labelX + labelWidth / 2, labelY + 19);

  stageContext.restore();
}

function filteredTransitions() {
  if (!state.evidence) return [];
  return state.evidence.transitions.filter((transition) => {
    const seriesMatches =
      state.activeSeries === "All" ||
      displaySeries(transition) === state.activeSeries;
    const regionMatches =
      !state.visibleOnly || transition.spectralRegion === "visible";
    return seriesMatches && regionMatches;
  });
}

function drawMarker(context, marker, x, y, size, colour, selected = false) {
  context.save();
  context.translate(x, y);
  context.strokeStyle = selected ? "#211b27" : colour;
  context.fillStyle = colour;
  context.lineWidth = selected ? 2.4 : 1.6;
  context.beginPath();

  if (marker === "circle") {
    context.arc(0, 0, size, 0, Math.PI * 2);
    context.fill();
  } else if (marker === "square") {
    context.rect(-size, -size, size * 2, size * 2);
    context.fill();
  } else if (marker === "triangle") {
    context.moveTo(0, -size * 1.18);
    context.lineTo(size * 1.08, size * 0.85);
    context.lineTo(-size * 1.08, size * 0.85);
    context.closePath();
    context.fill();
  } else if (marker === "diamond") {
    context.moveTo(0, -size * 1.2);
    context.lineTo(size * 1.1, 0);
    context.lineTo(0, size * 1.2);
    context.lineTo(-size * 1.1, 0);
    context.closePath();
    context.fill();
  } else if (marker === "plus") {
    context.moveTo(-size, 0);
    context.lineTo(size, 0);
    context.moveTo(0, -size);
    context.lineTo(0, size);
    context.strokeStyle = colour;
    context.lineWidth = selected ? 4 : 3;
    context.stroke();
  } else {
    context.moveTo(-size * 0.8, -size * 0.8);
    context.lineTo(size * 0.8, size * 0.8);
    context.moveTo(size * 0.8, -size * 0.8);
    context.lineTo(-size * 0.8, size * 0.8);
    context.strokeStyle = colour;
    context.lineWidth = selected ? 3.4 : 2.5;
    context.stroke();
  }

  if (selected) {
    context.beginPath();
    context.arc(0, 0, size + 5, 0, Math.PI * 2);
    context.strokeStyle = "#211b27";
    context.lineWidth = 1.4;
    context.stroke();
  }
  context.restore();
}

function drawAtlasChart() {
  if (!state.evidence) return;
  const { width, height } = canvasSize(chartCanvas, chartContext);
  const compact = width < 620;
  const margins = {
    left: compact ? 64 : 92,
    right: compact ? 20 : 42,
    top: compact ? 54 : 64,
    bottom: compact ? 70 : 82,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const xMin = state.visibleOnly ? 380 : 80;
  const xMax = state.visibleOnly ? 750 : 50000;
  const yMin = state.visibleOnly ? 1.65 : 0;
  const yMax = state.visibleOnly ? 3.35 : 14.2;
  const logMin = Math.log10(xMin);
  const logMax = Math.log10(xMax);
  const xFor = (value) =>
    plot.x +
    (state.visibleOnly
      ? (value - xMin) / (xMax - xMin)
      : (Math.log10(value) - logMin) / (logMax - logMin)) *
      plot.width;
  const yFor = (value) =>
    plot.y + plot.height - ((value - yMin) / (yMax - yMin)) * plot.height;

  chartContext.clearRect(0, 0, width, height);
  chartContext.save();
  chartContext.fillStyle = "#fbf7f1";
  chartContext.fillRect(0, 0, width, height);

  const bandX0 = xFor(380);
  const bandX1 = xFor(750);
  chartContext.fillStyle = "rgba(239, 188, 81, 0.16)";
  chartContext.fillRect(
    Math.max(plot.x, bandX0),
    plot.y,
    Math.min(plot.x + plot.width, bandX1) - Math.max(plot.x, bandX0),
    plot.height,
  );

  const xTicks = state.visibleOnly
    ? [380, 450, 500, 550, 600, 650, 700, 750]
    : [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 40000];
  const yTicks = state.visibleOnly
    ? [1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2]
    : [0, 2, 4, 6, 8, 10, 12, 14];

  chartContext.font = `${compact ? 11 : 14}px "Times New Roman"`;
  chartContext.fillStyle = "#544a55";
  chartContext.strokeStyle = "#d7ccd4";
  chartContext.lineWidth = 1;

  for (const tick of yTicks) {
    const y = yFor(tick);
    chartContext.beginPath();
    chartContext.moveTo(plot.x, y);
    chartContext.lineTo(plot.x + plot.width, y);
    chartContext.stroke();
    chartContext.textAlign = "right";
    chartContext.fillText(
      Number.isInteger(tick) ? String(tick) : tick.toFixed(1),
      plot.x - 12,
      y + 4,
    );
  }

  for (const tick of xTicks) {
    if (tick < xMin || tick > xMax) continue;
    const x = xFor(tick);
    chartContext.beginPath();
    chartContext.moveTo(x, plot.y);
    chartContext.lineTo(x, plot.y + plot.height);
    chartContext.stroke();
    chartContext.textAlign = "center";
    const label =
      tick >= 1000 ? `${Number((tick / 1000).toPrecision(2))}k` : `${tick}`;
    chartContext.fillText(label, x, plot.y + plot.height + 23);
  }

  chartContext.strokeStyle = "#403642";
  chartContext.lineWidth = 1.4;
  chartContext.beginPath();
  chartContext.moveTo(plot.x, plot.y);
  chartContext.lineTo(plot.x, plot.y + plot.height);
  chartContext.lineTo(plot.x + plot.width, plot.y + plot.height);
  chartContext.stroke();

  chartContext.fillStyle = "#2b2230";
  chartContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
  chartContext.textAlign = "center";
  chartContext.fillText(
    "Emitted-photon vacuum wavelength, λ (nm)",
    plot.x + plot.width / 2,
    height - (compact ? 18 : 23),
  );
  chartContext.save();
  chartContext.translate(compact ? 19 : 29, plot.y + plot.height / 2);
  chartContext.rotate(-Math.PI / 2);
  chartContext.fillText("Emitted-photon energy, Eγ (eV)", 0, 0);
  chartContext.restore();

  chartContext.font = `bold ${compact ? 12 : 15}px "Times New Roman"`;
  chartContext.textAlign = "left";
  chartContext.fillStyle = "#8b6720";
  chartContext.fillText(
    state.visibleOnly ? "DECLARED VISIBLE WINDOW" : "VISIBLE 380–750 nm",
    Math.max(plot.x + 7, bandX0 + 7),
    plot.y + 22,
  );

  chartContext.save();
  chartContext.beginPath();
  chartContext.rect(plot.x, plot.y, plot.width, plot.height);
  chartContext.clip();

  chartContext.setLineDash([7, 6]);
  chartContext.strokeStyle = "#8c9bb0";
  chartContext.lineWidth = 2;
  chartContext.beginPath();
  const guideCount = 220;
  for (let index = 0; index <= guideCount; index += 1) {
    const fraction = index / guideCount;
    const wavelength = state.visibleOnly
      ? xMin + fraction * (xMax - xMin)
      : 10 ** (logMin + fraction * (logMax - logMin));
    const energy = state.evidence.manifest.constants.hc_ev_nm / wavelength;
    const x = xFor(wavelength);
    const y = yFor(energy);
    if (index === 0) chartContext.moveTo(x, y);
    else chartContext.lineTo(x, y);
  }
  chartContext.stroke();
  chartContext.setLineDash([]);

  if (!state.visibleOnly) {
    for (const limit of state.evidence.limits) {
      const x = xFor(limit.wavelengthNm);
      const y = yFor(limit.energyEv);
      const series = SERIES[limit.seriesName];
      chartContext.save();
      chartContext.translate(x, y);
      chartContext.rotate(Math.PI / 4);
      chartContext.strokeStyle = series.colour;
      chartContext.fillStyle = "#fbf7f1";
      chartContext.lineWidth = 2.2;
      chartContext.fillRect(-7, -7, 14, 14);
      chartContext.strokeRect(-7, -7, 14, 14);
      chartContext.restore();
    }
  }

  const points = [];
  for (const transition of state.evidence.transitions) {
    const visible =
      (!state.visibleOnly || transition.spectralRegion === "visible") &&
      (state.activeSeries === "All" ||
        displaySeries(transition) === state.activeSeries);
    if (!visible) continue;
    const x = xFor(transition.wavelengthNm);
    const y = yFor(transition.photonEnergyEv);
    if (
      x < plot.x ||
      x > plot.x + plot.width ||
      y < plot.y ||
      y > plot.y + plot.height
    ) {
      continue;
    }
    const seriesName = displaySeries(transition);
    const series = SERIES[seriesName];
    const selected = transition.index === state.selectedIndex;
    drawMarker(
      chartContext,
      series.marker,
      x,
      y,
      selected ? 7.2 : compact ? 4.2 : 5.1,
      series.colour,
      selected,
    );
    points.push({ x, y, transition });
  }
  state.chartPoints = points;
  chartContext.restore();

  chartContext.fillStyle = "#647186";
  chartContext.font = `italic ${compact ? 11 : 14}px "Times New Roman"`;
  chartContext.textAlign = "right";
  chartContext.fillText(
    "dashed guide: Eγ = hc/λ",
    plot.x + plot.width,
    plot.y - 18,
  );

  if (points.length === 0) {
    chartContext.fillStyle = "#6b5e69";
    chartContext.font = `${compact ? 15 : 18}px "Times New Roman"`;
    chartContext.textAlign = "center";
    chartContext.fillText(
      "No transitions match this series and wavelength window.",
      plot.x + plot.width / 2,
      plot.y + plot.height / 2,
    );
  }

  chartContext.restore();
}

function updateSelection(index, { syncFilter = false, announce = true } = {}) {
  if (!state.evidence) return;
  const count = state.evidence.transitions.length;
  state.selectedIndex = ((index % count) + count) % count;
  const transition = state.evidence.transitions[state.selectedIndex];
  const seriesName = displaySeries(transition);
  const named = formatLineName(transition.lineName);
  const colour = wavelengthColour(transition.wavelengthNm);

  if (syncFilter && state.activeSeries !== "All") {
    state.activeSeries = seriesName;
    syncSeriesControls();
  }

  transitionSelector.value = String(state.selectedIndex);
  outputs.transitionTitle.textContent = named
    ? `${named} · ${transition.initialN} → ${transition.finalN}`
    : `${seriesName} · ${transition.initialN} → ${transition.finalN}`;
  outputs.regionBadge.textContent = transition.spectralRegion;
  outputs.regionBadge.dataset.region = transition.spectralRegion;
  outputs.photonWavelength.textContent = formatWavelength(
    transition.wavelengthNm,
  );
  outputs.photonEnergy.textContent = formatEnergy(transition.photonEnergyEv);
  outputs.photonFrequency.textContent = formatFrequency(transition.frequencyHz);
  outputs.photonWavelengthReadout.textContent = formatWavelength(
    transition.wavelengthNm,
  );
  outputs.atlasTransition.textContent = `${transition.initialN}→${transition.finalN}`;
  outputs.atlasSeries.textContent = seriesName;
  outputs.atlasEnergy.textContent = formatEnergy(transition.photonEnergyEv);
  outputs.atlasWavelength.textContent = formatWavelength(
    transition.wavelengthNm,
  );

  photonRibbon.style.setProperty("--photon-colour", colour);
  photonRibbon.classList.remove("is-pulsing");
  requestAnimationFrame(() => photonRibbon.classList.add("is-pulsing"));

  stageCanvas.setAttribute(
    "aria-label",
    `${transitionLabel(transition)} hydrogen emission. Initial level ${
      transition.initialN
    } at ${transition.initialEnergyEv.toFixed(4)} electronvolts descends to level ${
      transition.finalN
    } at ${transition.finalEnergyEv.toFixed(4)} electronvolts, emitting ${formatEnergy(
      transition.photonEnergyEv,
    )} at ${formatWavelength(transition.wavelengthNm)}.`,
  );

  drawEnergyStage();
  drawAtlasChart();

  if (announce) {
    outputs.atlasStatus.textContent = `${transitionLabel(
      transition,
    )} selected · ${formatWavelength(transition.wavelengthNm)}`;
  }
}

function syncSeriesControls() {
  document.querySelectorAll("[data-series]").forEach((button) => {
    const active = button.dataset.series === state.activeSeries;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  document.querySelectorAll(".series-row").forEach((button) => {
    const active = button.dataset.ledgerSeries === state.activeSeries;
    button.classList.toggle("is-active", active);
  });
}

function chooseSeries(seriesName) {
  state.activeSeries = seriesName;
  syncSeriesControls();
  const candidates = filteredTransitions();
  if (
    candidates.length &&
    !candidates.some((transition) => transition.index === state.selectedIndex)
  ) {
    updateSelection(candidates[0].index, { announce: false });
  } else {
    drawAtlasChart();
  }
  outputs.atlasStatus.textContent = `${candidates.length} ${
    candidates.length === 1 ? "emission" : "emissions"
  } shown · ${state.visibleOnly ? "visible window" : "full catalogue"}`;
}

function populateTransitionSelector() {
  const fragment = document.createDocumentFragment();
  for (const transition of state.evidence.transitions) {
    const option = document.createElement("option");
    option.value = String(transition.index);
    option.textContent = transitionOptionLabel(transition);
    fragment.append(option);
  }
  transitionSelector.replaceChildren(fragment);
}

function populateSeriesLedger() {
  const ledger = document.querySelector("[data-series-ledger]");
  const fragment = document.createDocumentFragment();

  const allButton = document.createElement("button");
  allButton.type = "button";
  allButton.className = "series-row is-active";
  allButton.dataset.ledgerSeries = "All";
  allButton.style.setProperty("--series-colour", "#e85d9f");
  allButton.innerHTML = `
    <i class="series-marker" aria-hidden="true">∑</i>
    <div><span>All series</span><small>Every declared pair</small></div>
    <em>45 lines</em>
  `;
  fragment.append(allButton);

  for (const seriesName of SERIES_ORDER) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "series-row";
    button.dataset.ledgerSeries = seriesName;
    button.style.setProperty("--series-colour", SERIES[seriesName].colour);
    const finalLabel =
      seriesName === "Higher series" ? "n_f = 6–9" : `n_f = ${SERIES_ORDER.indexOf(seriesName) + 1}`;
    button.innerHTML = `
      <i class="series-marker" aria-hidden="true">${SERIES[seriesName].symbol}</i>
      <div><span>${seriesName}</span><small>${finalLabel}</small></div>
      <em>${SERIES_COUNTS[seriesName]} lines</em>
    `;
    fragment.append(button);
  }
  ledger.replaceChildren(fragment);
}

function populateLimitLedger() {
  const ledger = document.querySelector("[data-limit-ledger]");
  const fragment = document.createDocumentFragment();
  for (const limit of state.evidence.limits) {
    const row = document.createElement("div");
    row.className = "limit-row";
    row.style.setProperty("--series-colour", SERIES[limit.seriesName].colour);
    row.innerHTML = `
      <div>
        <span>n<sub>f</sub> = ${limit.finalN}</span>
        <strong>${limit.seriesName}</strong>
        <em>${limit.wavelengthNm.toFixed(3)} nm</em>
        <small>E<sub>∞</sub> = ${limit.energyEv.toFixed(6)} eV</small>
      </div>
    `;
    fragment.append(row);
  }
  ledger.replaceChildren(fragment);
}

function populateBalmerInstrument() {
  const visible = state.evidence.transitions
    .filter((transition) => transition.spectralRegion === "visible")
    .sort((a, b) => a.wavelengthNm - b.wavelengthNm);
  const lines = document.querySelector("[data-balmer-lines]");
  const list = document.querySelector("[data-visible-lines-list]");
  const lineFragment = document.createDocumentFragment();
  const cardFragment = document.createDocumentFragment();

  for (const transition of visible) {
    const line = document.createElement("i");
    const position = ((transition.wavelengthNm - 380) / (750 - 380)) * 100;
    line.className = "balmer-line";
    line.dataset.label =
      formatLineName(transition.lineName) ||
      `${transition.initialN}→${transition.finalN}`;
    line.style.setProperty("--x", `${position}%`);
    line.style.setProperty("--height", "238px");
    line.style.setProperty(
      "--line-colour",
      wavelengthColour(transition.wavelengthNm),
    );
    lineFragment.append(line);

    const card = document.createElement("div");
    card.className = "balmer-line-card";
    card.innerHTML = `
      <span>${formatLineName(transition.lineName) || "Balmer line"}</span>
      <strong>${transition.wavelengthNm.toFixed(3)} nm</strong>
      <small>${transition.initialN}→${transition.finalN} · ${transition.photonEnergyEv.toFixed(4)} eV</small>
    `;
    cardFragment.append(card);
  }
  lines.replaceChildren(lineFragment);
  list.replaceChildren(cardFragment);
}

function populateEvidenceMetrics() {
  const checkCount = state.evidence.validation.checks.length;
  outputs.validationCount.textContent = `${checkCount} / ${checkCount}`;
  outputs.validationStatus.textContent =
    "Independent Decimal and Rydberg paths pass";
  outputs.transitionCount.textContent = String(
    state.evidence.transitions.length,
  );
  outputs.normalizedError.textContent = `${state.evidence.maximumNormalizedError.toPrecision(
    3,
  )}×`;
}

function showTooltip(point, clientX, clientY) {
  const transition = point.transition;
  tooltip.innerHTML = `
    <strong>${transitionLabel(transition)}</strong><br>
    ${formatEnergy(transition.photonEnergyEv)}<br>
    ${formatWavelength(transition.wavelengthNm)}<br>
    ${transition.spectralRegion}
  `;
  tooltip.hidden = false;
  const bounds = atlas.querySelector(".atlas-chart-wrap").getBoundingClientRect();
  const tooltipWidth = 205;
  const left = Math.min(
    bounds.width - tooltipWidth - 12,
    Math.max(12, clientX - bounds.left + 16),
  );
  const top = Math.min(
    bounds.height - 116,
    Math.max(12, clientY - bounds.top + 16),
  );
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function nearestChartPoint(event) {
  const bounds = chartCanvas.getBoundingClientRect();
  const x = event.clientX - bounds.left;
  const y = event.clientY - bounds.top;
  let nearest = null;
  let nearestDistance = 18;
  for (const point of state.chartPoints) {
    const distance = Math.hypot(point.x - x, point.y - y);
    if (distance < nearestDistance) {
      nearest = point;
      nearestDistance = distance;
    }
  }
  return nearest;
}

function handleChartPointerMove(event) {
  const nearest = nearestChartPoint(event);
  if (!nearest) {
    state.hoveredIndex = null;
    tooltip.hidden = true;
    chartCanvas.style.cursor = "crosshair";
    return;
  }
  state.hoveredIndex = nearest.transition.index;
  chartCanvas.style.cursor = "pointer";
  showTooltip(nearest, event.clientX, event.clientY);
}

function handleChartClick(event) {
  const nearest = nearestChartPoint(event);
  if (!nearest) return;
  updateSelection(nearest.transition.index);
}

function stepWithinCurrentView(direction) {
  const candidates = filteredTransitions()
    .slice()
    .sort((a, b) => a.wavelengthNm - b.wavelengthNm);
  if (!candidates.length) return;
  const current = candidates.findIndex(
    (transition) => transition.index === state.selectedIndex,
  );
  const next =
    current < 0
      ? direction > 0
        ? 0
        : candidates.length - 1
      : (current + direction + candidates.length) % candidates.length;
  updateSelection(candidates[next].index);
}

function handleChartKeydown(event) {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const candidates = filteredTransitions()
    .slice()
    .sort((a, b) => a.wavelengthNm - b.wavelengthNm);
  if (!candidates.length) return;
  if (event.key === "Home") updateSelection(candidates[0].index);
  else if (event.key === "End") {
    updateSelection(candidates[candidates.length - 1].index);
  } else {
    stepWithinCurrentView(event.key === "ArrowRight" ? 1 : -1);
  }
}

function enableControls() {
  transitionControls
    .querySelectorAll("button, select")
    .forEach((control) => (control.disabled = false));
  atlas
    .querySelectorAll("button, input")
    .forEach((control) => (control.disabled = false));
}

function disableControls() {
  transitionControls
    .querySelectorAll("button, select")
    .forEach((control) => (control.disabled = true));
  atlas
    .querySelectorAll("button, input")
    .forEach((control) => (control.disabled = true));
}

function bindEvents() {
  transitionSelector.addEventListener("change", () => {
    updateSelection(Number(transitionSelector.value));
  });

  transitionControls
    .querySelectorAll("[data-step-transition]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        updateSelection(
          state.selectedIndex + Number(button.dataset.stepTransition),
        );
      });
    });

  document.querySelector("[data-series-filter]").addEventListener("click", (event) => {
    const button = event.target.closest("[data-series]");
    if (button) chooseSeries(button.dataset.series);
  });

  document.querySelector("[data-series-ledger]").addEventListener("click", (event) => {
    const button = event.target.closest("[data-ledger-series]");
    if (button) chooseSeries(button.dataset.ledgerSeries);
  });

  visibleOnlyControl.addEventListener("change", () => {
    state.visibleOnly = visibleOnlyControl.checked;
    const candidates = filteredTransitions();
    if (
      candidates.length &&
      !candidates.some((transition) => transition.index === state.selectedIndex)
    ) {
      updateSelection(candidates[0].index, { announce: false });
    } else {
      drawAtlasChart();
    }
    outputs.atlasStatus.textContent = `${candidates.length} ${
      candidates.length === 1 ? "emission" : "emissions"
    } shown · ${state.visibleOnly ? "visible window" : "full catalogue"}`;
  });

  chartCanvas.addEventListener("pointermove", handleChartPointerMove, {
    passive: true,
  });
  chartCanvas.addEventListener("pointerleave", () => {
    tooltip.hidden = true;
    state.hoveredIndex = null;
    chartCanvas.style.cursor = "crosshair";
  });
  chartCanvas.addEventListener("click", handleChartClick);
  chartCanvas.addEventListener("keydown", handleChartKeydown);
  stageCanvas.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    updateSelection(
      state.selectedIndex + (event.key === "ArrowRight" ? 1 : -1),
    );
  });

  const resizeObserver = new ResizeObserver(() => {
    drawEnergyStage();
    drawAtlasChart();
  });
  resizeObserver.observe(stageCanvas);
  resizeObserver.observe(chartCanvas);

  window.addEventListener(
    "pagehide",
    () => {
      resizeObserver.disconnect();
    },
    { once: true },
  );
}

function lockEvidence() {
  evidenceLock.dataset.locked = "true";
  outputs.lockTitle.textContent = "Task 5 evidence locked";
  outputs.lockDetail.textContent =
    "30/30 checks, 10 levels, 45 transitions and five analytical limits agree.";
}

function showFailure(error) {
  document.documentElement.dataset.task05Status = "error";
  instrument.classList.remove("is-loading");
  atlas.classList.remove("is-loading");
  document.querySelector("[data-instrument-loading]").hidden = true;
  document.querySelector("[data-instrument-error]").hidden = false;
  document.querySelector("[data-atlas-error]").hidden = false;
  outputs.regionBadge.textContent = "Evidence unavailable";
  outputs.validationStatus.textContent = "Validation could not be confirmed";
  outputs.atlasStatus.textContent = "Catalogue unavailable";
  evidenceLock.dataset.locked = "false";
  outputs.lockTitle.textContent = "Task 5 evidence not locked";
  outputs.lockDetail.textContent =
    "Interactive controls remain disabled because committed evidence could not be verified.";
  disableControls();
  console.error("Task 5 evidence load failed", error);
}

async function initialise() {
  try {
    state.evidence = await loadTask05Evidence();
    populateTransitionSelector();
    populateSeriesLedger();
    populateLimitLedger();
    populateBalmerInstrument();
    populateEvidenceMetrics();
    bindEvents();
    enableControls();
    lockEvidence();

    const defaultTransition = state.evidence.transitions.find(
      (transition) => transition.initialN === 3 && transition.finalN === 2,
    );
    state.selectedIndex = defaultTransition?.index ?? 0;
    instrument.classList.remove("is-loading");
    atlas.classList.remove("is-loading");
    document.querySelector("[data-instrument-loading]").hidden = true;
    document.documentElement.dataset.task05Status = "ready";
    updateSelection(state.selectedIndex, { announce: false });
    outputs.atlasStatus.textContent = "45 emissions shown · full catalogue";
    window.dispatchEvent(new CustomEvent("task05:ready"));
  } catch (error) {
    showFailure(error);
  }
}

initialise();
