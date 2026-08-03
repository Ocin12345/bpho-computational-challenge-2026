import { loadTask04Evidence } from "./task-04-evidence.js";

const stageCanvas = document.querySelector("#photoelectric-stage");
const stageContext = stageCanvas.getContext("2d");
const chartCanvas = document.querySelector("#stopping-potential-chart");
const chartContext = chartCanvas.getContext("2d");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const chamber = document.querySelector("[data-threshold-chamber]");
const chamberLoading = document.querySelector("[data-chamber-loading]");
const chamberError = document.querySelector("[data-chamber-error]");
const comparisonLaboratory = document.querySelector(
  "[data-comparison-laboratory]",
);
const chartError = document.querySelector("[data-chart-error]");
const chartTooltip = document.querySelector("[data-chart-tooltip]");
const extensionImage = document.querySelector("[data-extension-image]");
const extensionToggle = document.querySelector("[data-toggle-extension]");

const controls = {
  form: document.querySelector("[data-photoelectric-controls]"),
  material: document.querySelector("#target-material"),
  frequency: document.querySelector("#photon-frequency"),
  intensity: document.querySelector("#light-intensity"),
  reverse: document.querySelector("#reverse-potential"),
  toggle: document.querySelector("[data-toggle-chamber]"),
  presets: [...document.querySelectorAll("[data-threshold-preset]")],
  axisModes: [...document.querySelectorAll("[data-axis-mode]")],
  extrapolation: document.querySelector("[data-toggle-extrapolation]"),
};

const outputs = {
  material: document.querySelector("[data-chamber-material]"),
  emissionState: document.querySelector("[data-emission-state]"),
  photonEnergy: document.querySelector("[data-photon-energy]"),
  workFunction: document.querySelector("[data-work-function]"),
  kineticEnergy: document.querySelector("[data-kinetic-energy]"),
  stoppingPotential: document.querySelector("[data-stopping-potential]"),
  frequency: document.querySelector("[data-frequency-output]"),
  wavelength: document.querySelector("[data-wavelength-output]"),
  intensity: document.querySelector("[data-intensity-output]"),
  reverse: document.querySelector("[data-reverse-output]"),
  collectorState: document.querySelector("[data-collector-state]"),
  thresholdComparison: document.querySelector("[data-threshold-comparison]"),
  thresholdRatio: document.querySelector("[data-threshold-ratio]"),
  thresholdFill: document.querySelector("[data-threshold-fill]"),
  playLabel: document.querySelector("[data-play-label]"),
  playIcon: document.querySelector("[data-play-icon]"),
  chartStatus: document.querySelector("[data-chart-status]"),
  axisExplanation: document.querySelector("[data-axis-explanation]"),
  selectedMetal: document.querySelector("[data-selected-metal]"),
  selectedFrequency: document.querySelector("[data-selected-frequency]"),
  selectedWavelength: document.querySelector("[data-selected-wavelength]"),
  materialLedger: document.querySelector("[data-material-ledger]"),
  validationCount: document.querySelector("[data-validation-count]"),
  validationStatus: document.querySelector("[data-validation-status]"),
  materialCount: document.querySelector("[data-material-count]"),
  gradient: document.querySelector("[data-gradient]"),
  lock: document.querySelector("[data-evidence-lock]"),
  lockTitle: document.querySelector("[data-lock-title]"),
  lockDetail: document.querySelector("[data-lock-detail]"),
};

const state = {
  evidence: null,
  selectedSymbol: "Cu",
  frequencyPhz: Number(controls.frequency.value),
  intensity: Number(controls.intensity.value),
  reversePotential: Number(controls.reverse.value),
  running: !reduceMotion.matches,
  axisMode: "frequency",
  extrapolation: false,
  animationFrame: 0,
  lastTime: performance.now(),
  stageTime: 0,
  stageSize: { width: 1, height: 1 },
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

function currentPhysics() {
  const material = selectedMaterial();
  if (!material) return null;
  const constants = state.evidence.manifest.constants;
  const frequencyHz = state.frequencyPhz * 1e15;
  const photonEnergyEv = constants.planck_over_charge_v_s * frequencyHz;
  const wavelengthNm =
    (constants.speed_of_light_m_s / frequencyHz) * 1e9;
  const signedEnergyEv = photonEnergyEv - material.workFunctionEv;
  const tolerance = 1e-10;
  const emission = signedEnergyEv >= -tolerance;
  const stoppingPotential = emission ? Math.max(0, signedEnergyEv) : null;
  const atThreshold = emission && Math.abs(signedEnergyEv) <= 0.004;
  const stopped =
    emission &&
    !atThreshold &&
    state.reversePotential + 1e-9 >= stoppingPotential;

  return {
    material,
    frequencyHz,
    photonEnergyEv,
    wavelengthNm,
    signedEnergyEv,
    emission,
    atThreshold,
    stopped,
    collecting: emission && !atThreshold && !stopped,
    stoppingPotential,
    ratio: frequencyHz / material.cutoffFrequencyHz,
  };
}

function formatFrequency(hz) {
  return `${(hz / 1e15).toFixed(3)} PHz`;
}

function formatThresholdFrequency(hz) {
  return `${(hz / 1e15).toFixed(4)} PHz`;
}

function formatWavelength(nm) {
  return `${nm.toFixed(1)} nm`;
}

function updateReadouts() {
  const physics = currentPhysics();
  if (!physics) return;

  outputs.material.textContent =
    `${physics.material.name} · ${physics.material.symbol}`;
  outputs.photonEnergy.textContent = `${physics.photonEnergyEv.toFixed(3)} eV`;
  outputs.workFunction.textContent =
    `${physics.material.workFunctionEv.toFixed(1)} eV`;
  outputs.kineticEnergy.textContent = physics.emission
    ? `${Math.max(0, physics.signedEnergyEv).toFixed(3)} eV`
    : "Undefined";
  outputs.stoppingPotential.textContent = physics.emission
    ? `${physics.stoppingPotential.toFixed(3)} V`
    : "Undefined";
  outputs.frequency.textContent = formatFrequency(physics.frequencyHz);
  outputs.wavelength.textContent = formatWavelength(physics.wavelengthNm);
  outputs.intensity.textContent = `${state.intensity} / 10`;
  outputs.reverse.textContent = `${state.reversePotential.toFixed(2)} V`;
  outputs.thresholdComparison.innerHTML =
    `f / f<sub>0</sub> · ${physics.material.symbol}`;
  outputs.thresholdRatio.textContent = `${physics.ratio.toFixed(3)}×`;
  outputs.thresholdFill.style.transform =
    `scaleX(${Math.min(1, Math.max(0, physics.ratio / 2))})`;

  if (!physics.emission) {
    outputs.emissionState.textContent = "Below threshold";
    outputs.emissionState.dataset.state = "inactive";
    outputs.collectorState.textContent =
      "No photoelectron reaches the collector";
  } else if (physics.atThreshold) {
    outputs.emissionState.textContent = "Threshold state";
    outputs.emissionState.dataset.state = "stopped";
    outputs.collectorState.textContent =
      "Kmax is zero at the ideal threshold";
  } else if (physics.stopped) {
    outputs.emissionState.textContent = "Current suppressed";
    outputs.emissionState.dataset.state = "stopped";
    outputs.collectorState.textContent =
      `Reverse potential ≥ ${physics.stoppingPotential.toFixed(2)} V`;
  } else {
    outputs.emissionState.textContent = "Photoemission";
    outputs.emissionState.dataset.state = "active";
    outputs.collectorState.textContent =
      `Reverse potential < ${physics.stoppingPotential.toFixed(2)} V`;
  }

  outputs.selectedMetal.textContent =
    `${physics.material.name} (${physics.material.symbol})`;
  outputs.selectedFrequency.textContent = formatThresholdFrequency(
    physics.material.cutoffFrequencyHz,
  );
  outputs.selectedWavelength.textContent = formatWavelength(
    physics.material.cutoffWavelengthNm,
  );

  document.querySelectorAll("[data-material-row]").forEach((row) => {
    const active = row.dataset.materialRow === state.selectedSymbol;
    row.classList.toggle("is-active", active);
    row.setAttribute("aria-pressed", String(active));
  });
}

function drawStageBackground(context, width, height) {
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#191915";
  context.fillRect(0, 0, width, height);
  context.strokeStyle = "rgba(244, 237, 223, 0.055)";
  context.lineWidth = 1;
  const spacing = width < 500 ? 42 : 58;
  for (let x = spacing; x < width; x += spacing) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, height);
    context.stroke();
  }
  for (let y = spacing; y < height; y += spacing) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(width, y);
    context.stroke();
  }
}

function drawArrow(context, startX, startY, endX, endY, colour) {
  const angle = Math.atan2(endY - startY, endX - startX);
  context.save();
  context.strokeStyle = colour;
  context.fillStyle = colour;
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(startX, startY);
  context.lineTo(endX, endY);
  context.stroke();
  context.beginPath();
  context.moveTo(endX, endY);
  context.lineTo(
    endX - Math.cos(angle - Math.PI / 6) * 7,
    endY - Math.sin(angle - Math.PI / 6) * 7,
  );
  context.lineTo(
    endX - Math.cos(angle + Math.PI / 6) * 7,
    endY - Math.sin(angle + Math.PI / 6) * 7,
  );
  context.closePath();
  context.fill();
  context.restore();
}

function drawApparatus(context, width, height, physics) {
  const compact = width < 560;
  const centreY = height * (compact ? 0.54 : 0.52);
  const lampX = width * (compact ? 0.12 : 0.1);
  const plateX = width * (compact ? 0.48 : 0.46);
  const collectorX = width * (compact ? 0.84 : 0.86);
  const plateHeight = height * 0.5;

  context.save();
  context.font = '11px "Times New Roman", Times, serif';
  context.textBaseline = "middle";

  context.strokeStyle = "#6f6b60";
  context.lineWidth = 1.2;
  context.strokeRect(
    width * 0.055,
    height * 0.18,
    width * 0.89,
    height * 0.67,
  );

  context.fillStyle = "#d1a24f";
  context.beginPath();
  context.arc(lampX, centreY, compact ? 12 : 16, 0, Math.PI * 2);
  context.fill();
  context.strokeStyle = "#e8c986";
  context.lineWidth = 1;
  context.beginPath();
  context.arc(lampX, centreY, compact ? 20 : 27, 0, Math.PI * 2);
  context.stroke();

  context.fillStyle = "#f1ebdf";
  context.fillRect(plateX - 4, centreY - plateHeight / 2, 8, plateHeight);
  context.fillStyle = "#d1a24f";
  context.fillRect(
    collectorX - 4,
    centreY - plateHeight / 2,
    8,
    plateHeight,
  );

  context.fillStyle = "#aaa193";
  context.textAlign = "center";
  context.fillText("photon source", lampX, height * 0.12);
  context.fillText(
    `${physics.material.name} cathode`,
    plateX,
    height * 0.91,
  );
  context.fillText("collector", collectorX, height * 0.91);

  context.fillStyle = "#f4eddf";
  context.font = 'italic 15px "Times New Roman", Times, serif';
  context.fillText("−", plateX, height * 0.12);
  context.fillText("+", collectorX, height * 0.12);

  if (state.reversePotential > 0.01) {
    const arrowY = height * 0.15;
    drawArrow(
      context,
      collectorX - 10,
      arrowY,
      plateX + 10,
      arrowY,
      "rgba(209, 162, 79, 0.72)",
    );
    context.fillStyle = "#c7bdaf";
    context.font = '10px "Times New Roman", Times, serif';
    context.fillText(
      `${state.reversePotential.toFixed(2)} V reverse field`,
      (plateX + collectorX) / 2,
      arrowY - 13,
    );
  }

  const photonCount = Math.max(3, state.intensity + 2);
  for (let index = 0; index < photonCount; index += 1) {
    const progress =
      (state.stageTime * 0.00031 + index / photonCount) % 1;
    const x = lampX + (plateX - lampX) * progress;
    const wavelengthScale = Math.min(
      7,
      Math.max(2.5, 7 - state.frequencyPhz * 1.7),
    );
    const y =
      centreY +
      Math.sin(progress * Math.PI * wavelengthScale + index * 0.8) *
        (compact ? 17 : 26) +
      ((index % 3) - 1) * (compact ? 20 : 28);
    context.strokeStyle = "rgba(209, 162, 79, 0.36)";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(x - 12, y);
    context.lineTo(x - 4, y);
    context.stroke();
    context.fillStyle = "#d1a24f";
    context.beginPath();
    context.arc(x, y, compact ? 2.2 : 2.8, 0, Math.PI * 2);
    context.fill();
  }

  if (physics.emission && physics.atThreshold) {
    const electronCount = Math.max(2, Math.ceil(state.intensity / 2));
    for (let index = 0; index < electronCount; index += 1) {
      const y =
        centreY +
        (index - (electronCount - 1) / 2) * (compact ? 14 : 19);
      context.fillStyle = "#f1ebdf";
      context.beginPath();
      context.arc(plateX + 8, y, 2.7, 0, Math.PI * 2);
      context.fill();
    }
  }

  if (physics.emission && !physics.atThreshold) {
    const electronCount = Math.max(2, state.intensity);
    const speed = 0.00013 * Math.sqrt(0.45 + physics.stoppingPotential);
    for (let index = 0; index < electronCount; index += 1) {
      const cycle = (state.stageTime * speed + index / electronCount) % 1;
      let progress = cycle;
      if (physics.stopped) {
        progress =
          cycle < 0.5 ? cycle * 2 : (1 - cycle) * 2;
        const reach = Math.min(
          0.78,
          Math.max(
            0.13,
            physics.stoppingPotential /
              Math.max(state.reversePotential, physics.stoppingPotential) *
              0.72,
          ),
        );
        progress *= reach;
      }
      const x = plateX + (collectorX - plateX) * progress;
      const baseY =
        centreY +
        ((index % 5) - 2) * (compact ? 14 : 19);
      const y =
        baseY +
        Math.sin(progress * Math.PI + index * 1.4) *
          (compact ? 17 : 25);
      context.fillStyle = physics.collecting ? "#f4eddf" : "#b8afa1";
      context.beginPath();
      context.arc(x + 6, y, compact ? 2.2 : 2.7, 0, Math.PI * 2);
      context.fill();
      context.strokeStyle = "rgba(244, 237, 223, 0.24)";
      context.beginPath();
      context.moveTo(x - 8, y);
      context.lineTo(x + 1, y);
      context.stroke();
    }
  }

  context.fillStyle = "#a9a092";
  context.font = '10px "Times New Roman", Times, serif';
  context.textAlign = "left";
  context.fillText(
    `${formatFrequency(physics.frequencyHz)} · ${formatWavelength(physics.wavelengthNm)}`,
    width * 0.075,
    height * 0.96,
  );
  context.textAlign = "right";
  context.fillText(
    physics.emission
      ? `Kmax = ${Math.max(0, physics.signedEnergyEv).toFixed(3)} eV`
      : "Kmax undefined below threshold",
    width * 0.925,
    height * 0.96,
  );
  context.restore();
}

function drawStage() {
  if (!state.evidence) return;
  const size = canvasSize(stageCanvas, stageContext, 390);
  state.stageSize = size;
  const physics = currentPhysics();
  drawStageBackground(stageContext, size.width, size.height);
  drawApparatus(stageContext, size.width, size.height, physics);
}

function animationLoop(now) {
  const delta = Math.min(40, now - state.lastTime);
  state.lastTime = now;
  if (state.running && !document.hidden) {
    state.stageTime += delta;
    drawStage();
  }
  state.animationFrame = requestAnimationFrame(animationLoop);
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
  controls.material.replaceChildren();
  outputs.materialLedger.replaceChildren();

  materials.forEach((material) => {
    const option = document.createElement("option");
    option.value = material.symbol;
    option.textContent =
      `${material.name} (${material.symbol}) · ${material.workFunctionEv.toFixed(1)} eV`;
    controls.material.append(option);

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
      controls.material.value = material.symbol;
      updateAll();
    });
    outputs.materialLedger.append(button);
  });

  controls.material.value = state.selectedSymbol;
}

function updateEvidenceSummary() {
  const checks = state.evidence.validation.checks;
  outputs.validationCount.textContent = `${checks.length} / ${checks.length}`;
  outputs.validationStatus.textContent =
    "Every pre-declared check passes";
  outputs.materialCount.textContent = String(state.evidence.materials.length);
  outputs.gradient.textContent =
    `${state.evidence.manifest.constants.planck_over_charge_v_s.toExponential(4)} V s`;
  outputs.lock.dataset.locked = "true";
  outputs.lockTitle.textContent = "Task 4 evidence verified";
  outputs.lockDetail.textContent =
    "43/43 checks pass; the official table, constants, cut-offs, and physical masks agree.";
}

function updateAll() {
  updateReadouts();
  updateChartCopy();
  drawStage();
  drawChart();
}

function setControlsEnabled(enabled) {
  [
    controls.material,
    controls.frequency,
    controls.intensity,
    controls.reverse,
    controls.toggle,
    controls.extrapolation,
    ...controls.presets,
    ...controls.axisModes,
  ].forEach((control) => {
    control.disabled = !enabled;
  });
}

function updatePlayButton() {
  outputs.playLabel.textContent = state.running
    ? "Pause chamber"
    : "Run chamber";
  outputs.playIcon.setAttribute(
    "d",
    state.running ? "M7 5h4v14H7zm6 0h4v14h-4z" : "M8 5l11 7-11 7z",
  );
}

function handleFrequencyInput() {
  state.frequencyPhz = Number(controls.frequency.value);
  updateAll();
}

function handleMaterialChange() {
  state.selectedSymbol = controls.material.value;
  updateAll();
}

function handleIntensityInput() {
  state.intensity = Number(controls.intensity.value);
  updateReadouts();
  drawStage();
}

function handleReverseInput() {
  state.reversePotential = Number(controls.reverse.value);
  updateReadouts();
  drawStage();
}

function handleThresholdPreset(event) {
  const material = selectedMaterial();
  if (!material) return;
  const thresholdPhz = material.cutoffFrequencyHz / 1e15;
  const factors = { below: 0.88, at: 1, above: 1.24 };
  const factor = factors[event.currentTarget.dataset.thresholdPreset] ?? 1;
  state.frequencyPhz = Math.min(
    Number(controls.frequency.max),
    Math.max(Number(controls.frequency.min), thresholdPhz * factor),
  );
  controls.frequency.value = state.frequencyPhz.toFixed(6);
  updateAll();
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
  controls.material.addEventListener("change", handleMaterialChange);
  controls.frequency.addEventListener("input", handleFrequencyInput);
  controls.intensity.addEventListener("input", handleIntensityInput);
  controls.reverse.addEventListener("input", handleReverseInput);
  controls.toggle.addEventListener("click", () => {
    state.running = !state.running;
    updatePlayButton();
    drawStage();
  });
  controls.presets.forEach((button) =>
    button.addEventListener("click", handleThresholdPreset),
  );
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
  extensionToggle.addEventListener("click", () => {
    const playing = extensionToggle.getAttribute("aria-pressed") === "true";
    extensionToggle.setAttribute("aria-pressed", String(!playing));
    extensionImage.src = playing
      ? extensionImage.dataset.storyboardSrc
      : extensionImage.dataset.gifSrc;
    extensionImage.alt = playing
      ? "Validated four-panel storyboard of the photoelectric-effect extension"
      : "Validated six-second schematic animation of the photoelectric effect";
    extensionToggle.textContent = playing
      ? "Play 6-second loop"
      : "Show static storyboard";
  });
  document.addEventListener("visibilitychange", () => {
    state.lastTime = performance.now();
  });
}

function handleFailure(error) {
  chamber.classList.remove("is-loading");
  comparisonLaboratory.classList.remove("is-loading");
  chamberLoading.hidden = true;
  chamberError.hidden = false;
  chartError.hidden = false;
  chamberError.textContent =
    error instanceof Error
      ? `Validated evidence unavailable: ${error.message}`
      : "Validated Task 4 evidence is unavailable.";
  chartError.textContent = chamberError.textContent;
  outputs.emissionState.textContent = "Evidence unavailable";
  outputs.emissionState.dataset.state = "inactive";
  outputs.chartStatus.textContent = "Comparison unavailable";
  outputs.validationStatus.textContent = "Validation could not be confirmed";
  outputs.lock.dataset.locked = "false";
  outputs.lockTitle.textContent = "Task 4 evidence not locked";
  outputs.lockDetail.textContent =
    "The interactive page fails closed when committed evidence is unavailable.";
  document.documentElement.dataset.task04Status = "error";
}

async function initialise() {
  setControlsEnabled(false);
  attachListeners();
  updatePlayButton();

  try {
    state.evidence = await loadTask04Evidence();
    buildMaterialControls();
    updateEvidenceSummary();
    setControlsEnabled(true);
    chamber.classList.remove("is-loading");
    comparisonLaboratory.classList.remove("is-loading");
    chamberLoading.hidden = true;
    updateAll();
    document.documentElement.dataset.task04Status = "ready";
    window.dispatchEvent(new CustomEvent("task04:ready"));
    state.animationFrame = requestAnimationFrame(animationLoop);
  } catch (error) {
    handleFailure(error);
  }
}

const resizeObserver = new ResizeObserver(() => {
  drawStage();
  drawChart();
});
resizeObserver.observe(document.querySelector(".chamber-canvas-wrap"));
resizeObserver.observe(document.querySelector(".comparison-chart-wrap"));

window.addEventListener(
  "pagehide",
  () => {
    cancelAnimationFrame(state.animationFrame);
    resizeObserver.disconnect();
  },
  { once: true },
);

initialise();
