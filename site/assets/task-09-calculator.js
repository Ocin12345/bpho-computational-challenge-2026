import { loadTask09Evidence } from "./task-09-evidence.js";
import {
  angleSweep,
  clampIncidentEnergyKev,
  clampScatteringAngleDeg,
  comptonKinematics,
} from "../../task09_compton_scattering/app/physics.js";
import {
  kleinNishinaState,
  kleinNishinaSweep,
} from "../../task09_compton_scattering/app/cross-section.js";

const OFFICIAL_ENERGIES = Object.freeze([50, 100, 200, 500, 1000]);
const ENERGY_COLOURS = new Map([
  [50, "#75bfff"],
  [100, "#67d7ac"],
  [200, "#ff7747"],
  [500, "#dc8bc4"],
  [1000, "#eebd59"],
]);
const ENERGY_DASHES = new Map([
  [50, []],
  [100, [10, 6]],
  [200, [3, 5]],
  [500, [15, 5, 3, 5]],
  [1000, [20, 7]],
]);

const laboratory = document.querySelector("[data-collision-laboratory]");
const controls = document.querySelector("[data-collision-controls]");
const energyControl = document.querySelector("#incident-energy");
const thetaControl = document.querySelector("#scattering-angle");
const collisionCanvas = document.querySelector("#collision-canvas");
const kinematicsCanvas = document.querySelector("#kinematics-canvas");
const crossCanvas = document.querySelector("#cross-section-canvas");

const collisionContext = collisionCanvas.getContext("2d");
const kinematicsContext = kinematicsCanvas.getContext("2d");
const crossContext = crossCanvas.getContext("2d");

const outputs = {
  collisionTitle: document.querySelector("[data-collision-title]"),
  laboratoryStatus: document.querySelector("[data-laboratory-status]"),
  energy: document.querySelector("[data-energy-output]"),
  theta: document.querySelector("[data-theta-output]"),
  shift: document.querySelector("[data-fractional-shift]"),
  absoluteShift: document.querySelector("[data-absolute-shift]"),
  beta: document.querySelector("[data-electron-beta]"),
  speed: document.querySelector("[data-electron-speed]"),
  recoilAngle: document.querySelector("[data-recoil-angle]"),
  recoilNote: document.querySelector("[data-recoil-note]"),
  scatteredEnergy: document.querySelector("[data-scattered-energy]"),
  kineticEnergy: document.querySelector("[data-kinetic-energy]"),
  retained: document.querySelector("[data-energy-retained]"),
  curveTitle: document.querySelector("[data-curve-title]"),
  kinematicsStatus: document.querySelector("[data-kinematics-status]"),
  crossSelected: document.querySelector("[data-cross-selected]"),
  totalCrossSection: document.querySelector("[data-total-cross-section]"),
  differentialCrossSection: document.querySelector(
    "[data-differential-cross-section]",
  ),
  relativeCrossSection: document.querySelector(
    "[data-relative-cross-section]",
  ),
  polarDensity: document.querySelector("[data-polar-density]"),
  forwardProbability: document.querySelector("[data-forward-probability]"),
  coreChecks: document.querySelector("[data-core-checks]"),
  extensionChecks: document.querySelector("[data-extension-checks]"),
  lockTitle: document.querySelector("[data-lock-title]"),
  lockDetail: document.querySelector("[data-lock-detail]"),
  evidenceStatus: document.querySelector("[data-evidence-status]"),
};

const state = {
  energyKev: 200,
  thetaDeg: 90,
  evidence: null,
  officialKinematics: new Map(),
  officialCrossSection: new Map(),
};

function resizeCanvas(canvas, context) {
  const width = Math.max(1, Math.round(canvas.clientWidth));
  const height = Math.max(1, Math.round(canvas.clientHeight));
  const density = Math.min(window.devicePixelRatio || 1, 2);
  const bitmapWidth = Math.round(width * density);
  const bitmapHeight = Math.round(height * density);
  if (canvas.width !== bitmapWidth || canvas.height !== bitmapHeight) {
    canvas.width = bitmapWidth;
    canvas.height = bitmapHeight;
  }
  context.setTransform(density, 0, 0, density, 0, 0);
  return { width, height, density };
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function degrees(value, digits = 1) {
  return `${Number(value).toLocaleString("en-GB", {
    maximumFractionDigits: digits,
  })}°`;
}

function formatFixed(value, digits) {
  return Number(value).toLocaleString("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatEnergy(value, digits = 0) {
  return `${Number(value).toLocaleString("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })} keV`;
}

function formatScientific(value) {
  if (value === 0) return "0";
  const exponent = Math.floor(Math.log10(Math.abs(value)));
  const coefficient = value / 10 ** exponent;
  const superscript = String(exponent)
    .replaceAll("-", "⁻")
    .replaceAll("0", "⁰")
    .replaceAll("1", "¹")
    .replaceAll("2", "²")
    .replaceAll("3", "³")
    .replaceAll("4", "⁴")
    .replaceAll("5", "⁵")
    .replaceAll("6", "⁶")
    .replaceAll("7", "⁷")
    .replaceAll("8", "⁸")
    .replaceAll("9", "⁹");
  return `${formatFixed(coefficient, 3)} × 10${superscript}`;
}

function clear(context, width, height, colour) {
  context.clearRect(0, 0, width, height);
  context.fillStyle = colour;
  context.fillRect(0, 0, width, height);
}

function line(context, x1, y1, x2, y2, colour, width = 1, dash = []) {
  context.save();
  context.beginPath();
  context.moveTo(x1, y1);
  context.lineTo(x2, y2);
  context.strokeStyle = colour;
  context.lineWidth = width;
  context.setLineDash(dash);
  context.stroke();
  context.restore();
}

function arrow(context, x1, y1, x2, y2, colour, width = 3) {
  line(context, x1, y1, x2, y2, colour, width);
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const head = 12 + width;
  context.save();
  context.beginPath();
  context.moveTo(x2, y2);
  context.lineTo(
    x2 - head * Math.cos(angle - Math.PI / 6),
    y2 - head * Math.sin(angle - Math.PI / 6),
  );
  context.lineTo(
    x2 - head * Math.cos(angle + Math.PI / 6),
    y2 - head * Math.sin(angle + Math.PI / 6),
  );
  context.closePath();
  context.fillStyle = colour;
  context.fill();
  context.restore();
}

function drawArc(context, x, y, radius, start, end, colour) {
  context.save();
  context.beginPath();
  context.arc(x, y, radius, start, end, end < start);
  context.strokeStyle = colour;
  context.lineWidth = 1.5;
  context.stroke();
  context.restore();
}

function drawCollision() {
  const { width, height } = resizeCanvas(collisionCanvas, collisionContext);
  clear(collisionContext, width, height, "#081620");
  const result = comptonKinematics(state.energyKev, state.thetaDeg);
  const compact = width < 600;
  const originX = compact ? width * 0.36 : width * 0.4;
  const originY = height * 0.5;
  const incomingLength = compact ? width * 0.28 : width * 0.34;
  const vectorScale = compact
    ? Math.min(width * 0.32, height * 0.28)
    : Math.min(width * 0.34, height * 0.33);
  const theta = (result.thetaDeg * Math.PI) / 180;
  const ratio = result.scatteredEnergyKev / result.incidentEnergyKev;
  const electronX = 1 - ratio * Math.cos(theta);
  const electronY =
    result.thetaDeg === 0 || result.thetaDeg === 180
      ? 0
      : ratio * Math.sin(theta);
  const photonEnd = {
    x: originX + vectorScale * ratio * Math.cos(theta),
    y: originY - vectorScale * ratio * Math.sin(theta),
  };
  const electronEnd = {
    x: originX + vectorScale * electronX,
    y: originY + vectorScale * electronY,
  };

  collisionContext.strokeStyle = "#183444";
  collisionContext.lineWidth = 1;
  for (let index = -4; index <= 5; index += 1) {
    line(
      collisionContext,
      0,
      originY + index * 52,
      width,
      originY + index * 52,
      "#122d3d",
    );
  }
  line(collisionContext, 0, originY, width, originY, "#375261", 1.2);
  arrow(
    collisionContext,
    originX - incomingLength,
    originY,
    originX - 9,
    originY,
    "#ff7747",
    4,
  );
  arrow(
    collisionContext,
    originX,
    originY,
    photonEnd.x,
    photonEnd.y,
    "#ff7747",
    4,
  );
  if (result.electronRecoilDirectionDefined) {
    arrow(
      collisionContext,
      originX,
      originY,
      electronEnd.x,
      electronEnd.y,
      "#62c5ee",
      4,
    );
  } else {
    collisionContext.beginPath();
    collisionContext.arc(originX, originY, 16, 0, Math.PI * 2);
    collisionContext.strokeStyle = "#62c5ee";
    collisionContext.lineWidth = 2;
    collisionContext.stroke();
  }

  collisionContext.beginPath();
  collisionContext.arc(originX, originY, 8, 0, Math.PI * 2);
  collisionContext.fillStyle = "#fff0d4";
  collisionContext.fill();
  collisionContext.beginPath();
  collisionContext.arc(originX, originY, 18, 0, Math.PI * 2);
  collisionContext.strokeStyle = "rgba(255,240,212,.3)";
  collisionContext.stroke();

  const thetaRadius = compact ? 42 : 60;
  if (result.thetaDeg > 0) {
    drawArc(
      collisionContext,
      originX,
      originY,
      thetaRadius,
      0,
      -theta,
      "#ff9b74",
    );
  }
  if (
    result.electronRecoilDirectionDefined &&
    result.electronRecoilAngleDeg > 0
  ) {
    drawArc(
      collisionContext,
      originX,
      originY,
      thetaRadius * 0.72,
      0,
      (result.electronRecoilAngleDeg * Math.PI) / 180,
      "#8ed8f5",
    );
  }

  collisionContext.font = `${compact ? 12 : 15}px "Times New Roman"`;
  collisionContext.fillStyle = "#a8bac3";
  collisionContext.textBaseline = "middle";
  collisionContext.textAlign = "center";
  collisionContext.fillText(
    `incident photon · ${formatEnergy(result.incidentEnergyKev)}`,
    originX - incomingLength * 0.53,
    originY - 25,
  );
  collisionContext.fillStyle = "#ff9b74";
  collisionContext.fillText(
    `E′ = ${formatFixed(result.scatteredEnergyKev, 3)} keV`,
    clamp(photonEnd.x, 90, width - 90),
    clamp(photonEnd.y - 26, 26, height - 26),
  );
  collisionContext.fillStyle = "#8ed8f5";
  collisionContext.fillText(
    result.electronRecoilDirectionDefined
      ? `electron · K = ${formatFixed(result.electronKineticEnergyKev, 3)} keV`
      : "electron · pₑ = 0",
    clamp(electronEnd.x, 90, width - 90),
    clamp(electronEnd.y + 28, 26, height - 26),
  );
  collisionContext.font = `italic ${compact ? 13 : 17}px "Times New Roman"`;
  collisionContext.fillStyle = "#ffb18e";
  collisionContext.fillText(
    `θ = ${degrees(result.thetaDeg)}`,
    originX + thetaRadius * 1.15,
    originY - thetaRadius * 0.45,
  );
  collisionContext.fillStyle = "#a8dff4";
  collisionContext.fillText(
    result.electronRecoilDirectionDefined
      ? `φ = ${degrees(result.electronRecoilAngleDeg)}`
      : "φ undefined",
    originX + thetaRadius,
    originY + thetaRadius * 0.68,
  );
}

function officialCurveValues(energy) {
  return state.officialKinematics.get(energy) || [];
}

function selectedSweep() {
  if (state.officialKinematics.has(state.energyKev)) {
    return state.officialKinematics.get(state.energyKev);
  }
  return angleSweep(state.energyKev, 0.5).map((item) => ({
    thetaDeg: item.thetaDeg,
    fractionalShift: item.fractionalWavelengthShift,
    beta: item.electronBeta,
    recoilAngleDeg: item.electronRecoilAngleDeg,
  }));
}

function chartPath(context, values, plot, extractor, maximum) {
  context.beginPath();
  values.forEach((value, index) => {
    const x = plot.x + (value.thetaDeg / 180) * plot.width;
    const y =
      plot.y +
      plot.height -
      (clamp(extractor(value), 0, maximum) / maximum) * plot.height;
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  });
}

function drawKinematics() {
  const { width, height } = resizeCanvas(
    kinematicsCanvas,
    kinematicsContext,
  );
  clear(kinematicsContext, width, height, "#07131d");
  const compact = width < 700;
  const left = compact ? 50 : 76;
  const right = compact ? 16 : 32;
  const top = compact ? 44 : 52;
  const bottom = compact ? 46 : 52;
  const panelGap = compact ? 54 : 68;
  const panelHeight =
    (height - top - bottom - panelGap * 2) / 3;
  const plots = [0, 1, 2].map((index) => ({
    x: left,
    y: top + index * (panelHeight + panelGap),
    width: width - left - right,
    height: panelHeight,
  }));
  const configurations = [
    {
      title: "A · Fractional wavelength shift, Δλ/λ",
      maximum: 4,
      extractor: (value) => value.fractionalShift,
      formatter: (value) => value.toFixed(value < 1 ? 2 : 1),
    },
    {
      title: "B · Relativistic electron recoil speed, v/c",
      maximum: 1,
      extractor: (value) => value.beta,
      formatter: (value) => value.toFixed(2),
    },
    {
      title: "C · Electron recoil angle, φ (degrees)",
      maximum: 90,
      extractor: (value) => value.recoilAngleDeg,
      formatter: (value) => `${Math.round(value)}°`,
    },
  ];
  const selected = comptonKinematics(state.energyKev, state.thetaDeg);
  const selectedValues = [
    selected.fractionalWavelengthShift,
    selected.electronBeta,
    selected.electronRecoilAngleDeg,
  ];

  plots.forEach((plot, panelIndex) => {
    const config = configurations[panelIndex];
    kinematicsContext.fillStyle = "#0b1b27";
    kinematicsContext.fillRect(
      plot.x - left + 8,
      plot.y - 30,
      plot.width + left + right - 16,
      plot.height + 56,
    );
    kinematicsContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
    kinematicsContext.fillStyle = "#f7ecd8";
    kinematicsContext.textAlign = "left";
    kinematicsContext.textBaseline = "alphabetic";
    kinematicsContext.fillText(
      config.title,
      plot.x,
      plot.y - (compact ? 12 : 15),
    );

    for (let tick = 0; tick <= 4; tick += 1) {
      const fraction = tick / 4;
      const y = plot.y + plot.height * (1 - fraction);
      line(
        kinematicsContext,
        plot.x,
        y,
        plot.x + plot.width,
        y,
        "#203a4a",
      );
      kinematicsContext.font = `${compact ? 10 : 12}px "Times New Roman"`;
      kinematicsContext.fillStyle = "#8fa5b0";
      kinematicsContext.textAlign = "right";
      kinematicsContext.textBaseline = "middle";
      kinematicsContext.fillText(
        config.formatter(config.maximum * fraction),
        plot.x - 9,
        y,
      );
    }
    for (const theta of [0, 45, 90, 135, 180]) {
      const x = plot.x + (theta / 180) * plot.width;
      line(
        kinematicsContext,
        x,
        plot.y,
        x,
        plot.y + plot.height,
        "#183342",
      );
      kinematicsContext.font = `${compact ? 10 : 12}px "Times New Roman"`;
      kinematicsContext.fillStyle = "#8fa5b0";
      kinematicsContext.textAlign = "center";
      kinematicsContext.textBaseline = "top";
      kinematicsContext.fillText(
        `${theta}°`,
        x,
        plot.y + plot.height + 8,
      );
    }

    for (const energy of OFFICIAL_ENERGIES) {
      const selectedOfficial = energy === state.energyKev;
      chartPath(
        kinematicsContext,
        officialCurveValues(energy),
        plot,
        config.extractor,
        config.maximum,
      );
      kinematicsContext.strokeStyle = ENERGY_COLOURS.get(energy);
      kinematicsContext.lineWidth = selectedOfficial ? 3.6 : 1.8;
      kinematicsContext.setLineDash(ENERGY_DASHES.get(energy));
      kinematicsContext.stroke();
    }
    if (!OFFICIAL_ENERGIES.includes(state.energyKev)) {
      chartPath(
        kinematicsContext,
        selectedSweep(),
        plot,
        config.extractor,
        config.maximum,
      );
      kinematicsContext.strokeStyle = "#fff0d4";
      kinematicsContext.lineWidth = 3.4;
      kinematicsContext.setLineDash([2, 6]);
      kinematicsContext.stroke();
    }
    kinematicsContext.setLineDash([]);

    const markerX = plot.x + (state.thetaDeg / 180) * plot.width;
    const markerY =
      plot.y +
      plot.height -
      (clamp(selectedValues[panelIndex], 0, config.maximum) /
        config.maximum) *
        plot.height;
    line(
      kinematicsContext,
      markerX,
      plot.y,
      markerX,
      plot.y + plot.height,
      "#dce8eb",
      1,
      [2, 5],
    );
    kinematicsContext.beginPath();
    kinematicsContext.arc(markerX, markerY, 5.3, 0, Math.PI * 2);
    kinematicsContext.fillStyle = "#fff0d4";
    kinematicsContext.fill();
    kinematicsContext.strokeStyle = "#07131d";
    kinematicsContext.lineWidth = 1.5;
    kinematicsContext.stroke();

    if (panelIndex === 2) {
      kinematicsContext.beginPath();
      kinematicsContext.arc(plot.x, plot.y, 5.2, 0, Math.PI * 2);
      kinematicsContext.fillStyle = "#0b1b27";
      kinematicsContext.fill();
      kinematicsContext.strokeStyle = "#ff7747";
      kinematicsContext.lineWidth = 2;
      kinematicsContext.stroke();
    }
  });
}

function crossSelectedSweep() {
  if (state.officialCrossSection.has(state.energyKev)) {
    return state.officialCrossSection.get(state.energyKev);
  }
  return kleinNishinaSweep(state.energyKev, 0.5).map((item) => ({
    thetaDeg: item.thetaDeg,
    relative: item.relativeDifferential,
    thetaPdf: item.thetaPdfRadInv,
  }));
}

function forwardProbability() {
  const summary = state.evidence?.crossSummaryByEnergy.get(state.energyKev);
  if (summary) return summary.forwardProbability;
  const sweep = kleinNishinaSweep(state.energyKev, 0.5);
  let integral = 0;
  const radiansPerStep = (0.5 * Math.PI) / 180;
  for (let index = 1; index <= 180; index += 1) {
    integral +=
      0.5 *
      (sweep[index - 1].thetaPdfRadInv + sweep[index].thetaPdfRadInv) *
      radiansPerStep;
  }
  return integral;
}

function drawCrossSection() {
  const { width, height } = resizeCanvas(crossCanvas, crossContext);
  clear(crossContext, width, height, "#fffaf0");
  const compact = width < 650;
  const left = compact ? 52 : 72;
  const right = compact ? 18 : 28;
  const top = compact ? 58 : 68;
  const gap = compact ? 72 : 86;
  const bottom = compact ? 42 : 52;
  const panelHeight = (height - top - gap - bottom) / 2;
  const plots = [
    { x: left, y: top, width: width - left - right, height: panelHeight },
    {
      x: left,
      y: top + panelHeight + gap,
      width: width - left - right,
      height: panelHeight,
    },
  ];
  const values = crossSelectedSweep();
  const densityMaximum = Math.max(
    0.9,
    ...values.map((value) => value.thetaPdf),
  );
  const configurations = [
    {
      title: "Relative differential strength · (dσ/dΩ) / rₑ²",
      maximum: 1,
      extractor: (value) => value.relative,
      colour: "#a83a18",
    },
    {
      title: "Normalized polar-angle density · p(θ) / rad⁻¹",
      maximum: Math.ceil(densityMaximum * 10) / 10,
      extractor: (value) => value.thetaPdf,
      colour: "#00648c",
    },
  ];
  const selectedCross = kleinNishinaState(state.energyKev, state.thetaDeg);
  const selectedValues = [
    selectedCross.relativeDifferential,
    selectedCross.thetaPdfRadInv,
  ];

  plots.forEach((plot, index) => {
    const config = configurations[index];
    crossContext.font = `${compact ? 13 : 17}px "Times New Roman"`;
    crossContext.fillStyle = "#18252c";
    crossContext.textAlign = "left";
    crossContext.fillText(config.title, plot.x, plot.y - 22);
    for (let tick = 0; tick <= 4; tick += 1) {
      const fraction = tick / 4;
      const y = plot.y + plot.height * (1 - fraction);
      line(crossContext, plot.x, y, plot.x + plot.width, y, "#d8d3c9");
      crossContext.font = `${compact ? 10 : 12}px "Times New Roman"`;
      crossContext.fillStyle = "#5c686e";
      crossContext.textAlign = "right";
      crossContext.fillText(
        (config.maximum * fraction).toFixed(2),
        plot.x - 9,
        y + 4,
      );
    }
    for (const theta of [0, 45, 90, 135, 180]) {
      const x = plot.x + (theta / 180) * plot.width;
      line(crossContext, x, plot.y, x, plot.y + plot.height, "#e2ddd4");
      crossContext.fillStyle = "#5c686e";
      crossContext.textAlign = "center";
      crossContext.fillText(`${theta}°`, x, plot.y + plot.height + 19);
    }
    chartPath(
      crossContext,
      values,
      plot,
      config.extractor,
      config.maximum,
    );
    crossContext.strokeStyle = config.colour;
    crossContext.lineWidth = 3;
    crossContext.setLineDash([]);
    crossContext.stroke();
    const markerX = plot.x + (state.thetaDeg / 180) * plot.width;
    const markerY =
      plot.y +
      plot.height -
      (selectedValues[index] / config.maximum) * plot.height;
    line(
      crossContext,
      markerX,
      plot.y,
      markerX,
      plot.y + plot.height,
      "#304c59",
      1,
      [2, 5],
    );
    crossContext.beginPath();
    crossContext.arc(markerX, markerY, 5, 0, Math.PI * 2);
    crossContext.fillStyle = config.colour;
    crossContext.fill();
    crossContext.strokeStyle = "#fffaf0";
    crossContext.lineWidth = 1.5;
    crossContext.stroke();
  });
}

function updateOutputs() {
  const result = comptonKinematics(state.energyKev, state.thetaDeg);
  const cross = kleinNishinaState(state.energyKev, state.thetaDeg);
  const energyRatio = result.scatteredEnergyKev / result.incidentEnergyKev;
  outputs.collisionTitle.textContent =
    `E = ${formatEnergy(state.energyKev)} · θ = ${degrees(state.thetaDeg)}`;
  outputs.energy.value = formatEnergy(state.energyKev);
  outputs.theta.value = degrees(state.thetaDeg);
  outputs.shift.value = formatFixed(result.fractionalWavelengthShift, 6);
  outputs.absoluteShift.textContent =
    `${formatFixed(result.wavelengthShiftM * 1e12, 3)} pm`;
  outputs.beta.value = `${formatFixed(result.electronBeta, 6)} c`;
  outputs.speed.textContent =
    `${formatScientific(result.electronSpeedMS)} m s⁻¹`;
  outputs.recoilAngle.value = result.electronRecoilDirectionDefined
    ? degrees(result.electronRecoilAngleDeg, 3)
    : "undefined";
  outputs.recoilNote.textContent = !result.electronRecoilDirectionDefined
    ? "zero electron momentum · 90° limit only"
    : state.thetaDeg === 180
      ? "defined · along incident axis"
      : "defined · below incident axis";
  outputs.scatteredEnergy.textContent = formatEnergy(
    result.scatteredEnergyKev,
    3,
  );
  outputs.kineticEnergy.textContent = formatEnergy(
    result.electronKineticEnergyKev,
    3,
  );
  outputs.retained.style.width = `${energyRatio * 100}%`;
  outputs.curveTitle.textContent =
    `${formatEnergy(state.energyKev)} selected · θ = ${degrees(state.thetaDeg)}`;
  outputs.crossSelected.textContent =
    `${formatEnergy(state.energyKev)} · ${degrees(state.thetaDeg)}`;
  outputs.totalCrossSection.textContent =
    `${formatFixed(cross.totalBarn, 6)} barn`;
  outputs.differentialCrossSection.textContent =
    `${formatFixed(cross.differentialBarnSr, 6)} barn sr⁻¹`;
  outputs.relativeCrossSection.textContent = formatFixed(
    cross.relativeDifferential,
    4,
  );
  outputs.polarDensity.textContent =
    `${formatFixed(cross.thetaPdfRadInv, 4)} rad⁻¹`;
  outputs.forwardProbability.textContent =
    `${formatFixed(forwardProbability() * 100, 2)}%`;

  energyControl.value = String(state.energyKev);
  thetaControl.value = String(state.thetaDeg);
  document.querySelectorAll("[data-energy-preset]").forEach((button) => {
    button.classList.toggle(
      "is-current",
      Number(button.dataset.energyPreset) === state.energyKev,
    );
  });
  document.querySelectorAll("[data-theta-preset]").forEach((button) => {
    button.classList.toggle(
      "is-current",
      Number(button.dataset.thetaPreset) === state.thetaDeg,
    );
  });
  document.querySelectorAll("[data-legend-energy]").forEach((item) => {
    item.classList.toggle(
      "is-selected",
      Number(item.dataset.legendEnergy) === state.energyKev,
    );
  });

  collisionCanvas.setAttribute(
    "aria-label",
    result.electronRecoilDirectionDefined
      ? `Momentum diagram for a ${formatEnergy(state.energyKev)} photon scattered through ${degrees(state.thetaDeg)}, with an electron recoil angle of ${degrees(result.electronRecoilAngleDeg)}`
      : `Forward scattering at ${formatEnergy(state.energyKev)} with zero electron momentum and undefined recoil direction`,
  );
}

function renderAll() {
  if (!state.evidence) return;
  updateOutputs();
  drawCollision();
  drawKinematics();
  drawCrossSection();
}

function setState(energyKev, thetaDeg) {
  if (!state.evidence) return;
  state.energyKev = Math.round(clampIncidentEnergyKev(energyKev));
  state.thetaDeg =
    Math.round(clampScatteringAngleDeg(thetaDeg) * 2) / 2;
  renderAll();
}

function enableControls() {
  controls.querySelectorAll("input").forEach((control) => {
    control.disabled = false;
  });
  document
    .querySelectorAll("[data-energy-preset],[data-theta-preset]")
    .forEach((button) => {
      button.disabled = false;
    });
}

function setFailureState() {
  laboratory.classList.remove("is-loading");
  document.querySelector("[data-collision-error]").hidden = false;
  document.querySelector("[data-kinematics-error]").hidden = false;
  document.querySelector("[data-cross-section-error]").hidden = false;
  outputs.laboratoryStatus.textContent = "Interaction locked";
  outputs.kinematicsStatus.textContent = "Validation unavailable";
  outputs.coreChecks.textContent = "Not verified";
  outputs.extensionChecks.textContent = "Not verified";
  outputs.lockTitle.textContent = "Validation could not be confirmed";
  outputs.lockDetail.textContent =
    "One or more committed Task 9 artifacts failed to load or disagreed with the frozen equations. No interactive result is shown.";
  outputs.evidenceStatus.textContent = "Locked";
  document.querySelector("[data-evidence-lock]").classList.add("is-error");
}

energyControl.addEventListener("input", () => {
  setState(Number(energyControl.value), state.thetaDeg);
});

thetaControl.addEventListener("input", () => {
  setState(state.energyKev, Number(thetaControl.value));
});

document.querySelectorAll("[data-energy-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    setState(Number(button.dataset.energyPreset), state.thetaDeg);
  });
});

document.querySelectorAll("[data-theta-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    setState(state.energyKev, Number(button.dataset.thetaPreset));
  });
});

function keyboardTheta(event) {
  if (!state.evidence) return;
  if (event.key === "ArrowRight" || event.key === "ArrowUp") {
    event.preventDefault();
    setState(state.energyKev, state.thetaDeg + 0.5);
  } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
    event.preventDefault();
    setState(state.energyKev, state.thetaDeg - 0.5);
  } else if (event.key === "Home") {
    event.preventDefault();
    setState(state.energyKev, 0);
  } else if (event.key === "End") {
    event.preventDefault();
    setState(state.energyKev, 180);
  }
}

collisionCanvas.addEventListener("keydown", keyboardTheta);
kinematicsCanvas.addEventListener("keydown", keyboardTheta);
crossCanvas.addEventListener("keydown", keyboardTheta);

function pointerTheta(event, canvas) {
  if (!state.evidence) return;
  const bounds = canvas.getBoundingClientRect();
  const leftPadding =
    canvas === collisionCanvas ? 0 : bounds.width < 700 ? 52 : 76;
  const rightPadding =
    canvas === collisionCanvas ? 0 : bounds.width < 700 ? 18 : 32;
  const fraction = clamp(
    (event.clientX - bounds.left - leftPadding) /
      (bounds.width - leftPadding - rightPadding),
    0,
    1,
  );
  setState(state.energyKev, Math.round(fraction * 360) / 2);
}

kinematicsCanvas.addEventListener("pointerdown", (event) => {
  pointerTheta(event, kinematicsCanvas);
});
crossCanvas.addEventListener("pointerdown", (event) => {
  pointerTheta(event, crossCanvas);
});

const resizeObserver = new ResizeObserver(() => {
  if (!state.evidence) return;
  drawCollision();
  drawKinematics();
  drawCrossSection();
});
resizeObserver.observe(collisionCanvas);
resizeObserver.observe(kinematicsCanvas);
resizeObserver.observe(crossCanvas);

loadTask09Evidence()
  .then((evidence) => {
    state.evidence = evidence;
    for (const energy of OFFICIAL_ENERGIES) {
      state.officialKinematics.set(
        energy,
        evidence.kinematics.filter((row) => row.energyKev === energy),
      );
      state.officialCrossSection.set(
        energy,
        evidence.crossSection.filter((row) => row.energyKev === energy),
      );
    }
    laboratory.classList.remove("is-loading");
    outputs.laboratoryStatus.textContent = "Exact state";
    outputs.kinematicsStatus.textContent = "3,605 points verified";
    outputs.coreChecks.textContent =
      `${evidence.validation.checks.length}/${evidence.validation.checks.length} pass`;
    outputs.extensionChecks.textContent =
      `${evidence.crossValidation.checks.length}/${evidence.crossValidation.checks.length} pass`;
    outputs.lockTitle.textContent = "Both validated evidence layers loaded";
    outputs.lockDetail.textContent =
      "Every interactive value is recomputed from the accepted relativistic equations; official curves remain tied to the committed data tables.";
    outputs.evidenceStatus.textContent = "Verified";
    enableControls();
    document.body.dataset.task09Status = "verified";
    renderAll();
  })
  .catch((error) => {
    console.error(error);
    document.body.dataset.task09Status = "error";
    setFailureState();
  });

window.addEventListener("pagehide", () => {
  resizeObserver.disconnect();
});
