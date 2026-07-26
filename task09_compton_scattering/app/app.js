import {
  ELECTRON_REST_ENERGY_KEV,
  OFFICIAL_ENERGIES_KEV,
  angleSweep,
  clampIncidentEnergyKev,
  clampScatteringAngleDeg,
  comptonKinematics,
} from "./physics.js";
import { kleinNishinaState, kleinNishinaSweep } from "./cross-section.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const DEFAULT_ENERGY_KEV = 200;
const DEFAULT_THETA_DEG = 90;
const ENERGY_COLOURS = new Map([
  [50, "#0072b2"],
  [100, "#007a5e"],
  [200, "#c44e00"],
  [500, "#a64f83"],
  [1_000, "#332288"],
]);
const ENERGY_DASH_PATTERNS = new Map([
  [50, ""],
  [100, "10 5"],
  [200, "3 4"],
  [500, "14 5 3 5"],
  [1_000, "18 6"],
]);

const elements = Object.fromEntries(
  [
    "energy-range",
    "energy-number",
    "energy-output",
    "theta-range",
    "theta-number",
    "theta-output",
    "reset-button",
    "live-results",
    "collision-description",
    "scattered-photon",
    "electron-vector",
    "theta-arc",
    "phi-arc",
    "scattered-label",
    "electron-label",
    "theta-arc-label",
    "phi-arc-label",
    "fractional-shift",
    "absolute-shift",
    "electron-beta",
    "electron-speed",
    "recoil-angle",
    "recoil-direction-note",
    "scattered-energy",
    "kinetic-energy",
    "photon-energy-fill",
    "selected-energy-legend",
    "selected-energy-label",
    "total-cross-section",
    "differential-cross-section",
    "relative-cross-section",
    "polar-density",
    "forward-probability",
  ].map((id) => [id, document.getElementById(id)]),
);

const state = {
  incidentEnergyKev: DEFAULT_ENERGY_KEV,
  thetaDeg: DEFAULT_THETA_DEG,
};

const officialSweeps = new Map(
  OFFICIAL_ENERGIES_KEV.map((energy) => [energy, angleSweep(energy)]),
);

function svgElement(tag, attributes = {}, text = "") {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attributes)) {
    node.setAttribute(name, String(value));
  }
  if (text) node.textContent = text;
  return node;
}

function formatNumber(value, digits = 3) {
  return Number(value).toLocaleString("en-GB", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

function formatFixed(value, digits) {
  return Number(value).toLocaleString("en-GB", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatEnergy(value) {
  return `${formatNumber(value, value < 10 ? 1 : 0)} keV`;
}

function scientific(value, digits = 3) {
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
  return `${formatFixed(coefficient, digits - 1)} × 10${superscript}`;
}

function setLine(line, x1, y1, x2, y2) {
  line.setAttribute("x1", x1.toFixed(3));
  line.setAttribute("y1", y1.toFixed(3));
  line.setAttribute("x2", x2.toFixed(3));
  line.setAttribute("y2", y2.toFixed(3));
}

function polarPoint(originX, originY, radius, screenAngleDeg) {
  const angle = (screenAngleDeg * Math.PI) / 180;
  return {
    x: originX + radius * Math.cos(angle),
    y: originY + radius * Math.sin(angle),
  };
}

function arcPath(originX, originY, radius, endAngleDeg) {
  if (Math.abs(endAngleDeg) < 1e-12) return "";
  const start = polarPoint(originX, originY, radius, 0);
  const end = polarPoint(originX, originY, radius, endAngleDeg);
  const largeArc = Math.abs(endAngleDeg) > 180 ? 1 : 0;
  const sweep = endAngleDeg > 0 ? 1 : 0;
  return `M ${start.x.toFixed(3)} ${start.y.toFixed(3)} A ${radius} ${radius} 0 ${largeArc} ${sweep} ${end.x.toFixed(3)} ${end.y.toFixed(3)}`;
}

function positionText(node, point, anchor = "start") {
  node.setAttribute("x", point.x.toFixed(3));
  node.setAttribute("y", point.y.toFixed(3));
  node.setAttribute("text-anchor", anchor);
}

function renderGeometry(result) {
  const originX = 260;
  const originY = 190;
  const momentumScale = 160;
  const thetaRad = (result.thetaDeg * Math.PI) / 180;
  const cosine = Math.cos(thetaRad);
  const sine = result.thetaDeg === 0 || result.thetaDeg === 180 ? 0 : Math.sin(thetaRad);
  const energyRatio = result.scatteredEnergyKev / result.incidentEnergyKev;
  const electronPxRatio = 1 - energyRatio * cosine;
  const electronPyRatio = energyRatio * sine;
  const photonEnd = {
    x: originX + momentumScale * energyRatio * cosine,
    y: originY - momentumScale * energyRatio * sine,
  };
  const electronEnd = {
    x: originX + momentumScale * electronPxRatio,
    y: originY + momentumScale * electronPyRatio,
  };
  setLine(elements["scattered-photon"], originX, originY, photonEnd.x, photonEnd.y);
  setLine(elements["electron-vector"], originX, originY, electronEnd.x, electronEnd.y);
  elements["electron-vector"].setAttribute(
    "opacity",
    result.electronRecoilDirectionDefined ? "1" : "0.3",
  );

  elements["theta-arc"].setAttribute(
    "d",
    arcPath(originX, originY, 66, -result.thetaDeg),
  );
  elements["phi-arc"].setAttribute(
    "d",
    result.electronRecoilDirectionDefined
      ? arcPath(originX, originY, 52, result.electronRecoilAngleDeg)
      : "",
  );

  const scatteredLabelPoint = {
    x: photonEnd.x + (photonEnd.x < originX ? -12 : 12),
    y: photonEnd.y - 10,
  };
  positionText(
    elements["scattered-label"],
    scatteredLabelPoint,
    photonEnd.x < originX ? "end" : "start",
  );
  const electronLabelPoint = {
    x: electronEnd.x + 12,
    y: electronEnd.y + 19,
  };
  positionText(elements["electron-label"], electronLabelPoint);
  elements["electron-label"].textContent = result.electronRecoilDirectionDefined
    ? "recoil electron · pₑ"
    : "recoil electron · pₑ = 0";

  const thetaLabelPoint = polarPoint(originX, originY, 90, -result.thetaDeg / 2);
  positionText(elements["theta-arc-label"], thetaLabelPoint, "middle");
  elements["theta-arc-label"].textContent = `θ = ${formatNumber(result.thetaDeg, 1)}°`;
  const phiLabelPoint = polarPoint(
    originX,
    originY,
    78,
    result.electronRecoilAngleDeg / 2,
  );
  positionText(elements["phi-arc-label"], phiLabelPoint, "middle");
  elements["phi-arc-label"].textContent = result.electronRecoilDirectionDefined
    ? `φ = ${formatNumber(result.electronRecoilAngleDeg, 1)}°`
    : "φ undefined";
  elements["collision-description"].textContent = result.electronRecoilDirectionDefined
    ? `A ${formatNumber(result.incidentEnergyKev, 1)} kiloelectronvolt photon scatters through ${formatNumber(result.thetaDeg, 1)} degrees. The recoil electron travels ${formatNumber(result.electronRecoilAngleDeg, 1)} degrees below the incident axis.`
    : `A ${formatNumber(result.incidentEnergyKev, 1)} kiloelectronvolt photon continues forward. The electron momentum is zero, so its recoil direction is undefined.`;
}

const chartFrame = { x0: 82, x1: 1045, y0: 25, y1: 315 };

function clearRenderedChart(svg) {
  for (const node of svg.querySelectorAll(".chart-rendered")) node.remove();
}

function chartX(thetaDeg) {
  return chartFrame.x0 + (thetaDeg / 180) * (chartFrame.x1 - chartFrame.x0);
}

function chartY(value, yMaximum) {
  return chartFrame.y1 - (value / yMaximum) * (chartFrame.y1 - chartFrame.y0);
}

function addAxes(root, yMaximum, yFormatter, yTitle) {
  const grid = svgElement("g", { class: "chart-grid" });
  const axes = svgElement("g");
  for (let index = 0; index <= 4; index += 1) {
    const fraction = index / 4;
    const y = chartFrame.y1 - fraction * (chartFrame.y1 - chartFrame.y0);
    grid.append(svgElement("line", { x1: chartFrame.x0, y1: y, x2: chartFrame.x1, y2: y }));
    axes.append(
      svgElement(
        "text",
        { class: "chart-label", x: chartFrame.x0 - 13, y: y + 5, "text-anchor": "end" },
        yFormatter(fraction * yMaximum),
      ),
    );
  }
  for (const theta of [0, 45, 90, 135, 180]) {
    const x = chartX(theta);
    grid.append(svgElement("line", { x1: x, y1: chartFrame.y0, x2: x, y2: chartFrame.y1 }));
    axes.append(
      svgElement(
        "text",
        { class: "chart-label", x, y: chartFrame.y1 + 28, "text-anchor": "middle" },
        `${theta}°`,
      ),
    );
  }
  axes.append(
    svgElement("line", {
      class: "chart-axis",
      x1: chartFrame.x0,
      y1: chartFrame.y0,
      x2: chartFrame.x0,
      y2: chartFrame.y1,
    }),
    svgElement("line", {
      class: "chart-axis",
      x1: chartFrame.x0,
      y1: chartFrame.y1,
      x2: chartFrame.x1,
      y2: chartFrame.y1,
    }),
    svgElement(
      "text",
      {
        class: "chart-axis-title",
        x: (chartFrame.x0 + chartFrame.x1) / 2,
        y: 365,
        "text-anchor": "middle",
      },
      "Photon scattering angle, θ",
    ),
    svgElement(
      "text",
      {
        class: "chart-axis-title",
        transform: `translate(22 ${(chartFrame.y0 + chartFrame.y1) / 2}) rotate(-90)`,
        "text-anchor": "middle",
      },
      yTitle,
    ),
  );
  root.append(grid, axes);
}

function curvePath(values, extractor, yMaximum) {
  return values
    .map((value, index) => {
      const x = chartX(value.thetaDeg);
      const y = chartY(Math.min(yMaximum, Math.max(0, extractor(value))), yMaximum);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(3)} ${y.toFixed(3)}`;
    })
    .join(" ");
}

function renderMultiEnergyChart({
  svgId,
  extractor,
  selectedValue,
  yMaximum,
  yFormatter,
  yTitle,
  description,
}) {
  const svg = document.getElementById(svgId);
  clearRenderedChart(svg);
  const root = svgElement("g", { class: "chart-rendered" });
  addAxes(root, yMaximum, yFormatter, yTitle);
  const selectedOfficial = OFFICIAL_ENERGIES_KEV.find(
    (energy) => Math.abs(energy - state.incidentEnergyKev) < 1e-10,
  );
  for (const energy of OFFICIAL_ENERGIES_KEV) {
    const selected = energy === selectedOfficial;
    root.append(
      svgElement("path", {
        class: "curve",
        d: curvePath(officialSweeps.get(energy), extractor, yMaximum),
        stroke: ENERGY_COLOURS.get(energy),
        "stroke-width": selected ? 4.5 : 2.2,
        "stroke-dasharray": ENERGY_DASH_PATTERNS.get(energy),
      }),
    );
  }
  if (!selectedOfficial) {
    const customSweep = angleSweep(state.incidentEnergyKev);
    root.append(
      svgElement("path", {
        class: "curve",
        d: curvePath(customSweep, extractor, yMaximum),
        stroke: "#101f35",
        "stroke-width": 4,
        "stroke-dasharray": "2 7",
      }),
    );
  }
  const markerX = chartX(state.thetaDeg);
  const markerY = chartY(selectedValue, yMaximum);
  root.append(
    svgElement("line", {
      class: "selected-guide",
      x1: markerX,
      x2: markerX,
      y1: chartFrame.y0,
      y2: chartFrame.y1,
    }),
    svgElement("circle", {
      class: "selected-marker",
      cx: markerX,
      cy: markerY,
      r: 7,
    }),
  );
  svg.append(root);
  svg.querySelector("desc").textContent = description;
}

function renderSingleCurveChart({
  svgId,
  sweep,
  extractor,
  selectedValue,
  yMaximum,
  yFormatter,
  yTitle,
  description,
}) {
  const svg = document.getElementById(svgId);
  clearRenderedChart(svg);
  const root = svgElement("g", { class: "chart-rendered" });
  addAxes(root, yMaximum, yFormatter, yTitle);
  root.append(
    svgElement("path", {
      class: "curve",
      d: curvePath(sweep, extractor, yMaximum),
      stroke: "#15795f",
      "stroke-width": 4,
    }),
  );
  const markerX = chartX(state.thetaDeg);
  const markerY = chartY(selectedValue, yMaximum);
  root.append(
    svgElement("line", {
      class: "selected-guide",
      x1: markerX,
      x2: markerX,
      y1: chartFrame.y0,
      y2: chartFrame.y1,
    }),
    svgElement("circle", {
      class: "selected-marker",
      cx: markerX,
      cy: markerY,
      r: 7,
    }),
  );
  svg.append(root);
  svg.querySelector("desc").textContent = description;
}

function forwardHemisphereProbability(sweep) {
  const finalIndex = sweep.findIndex((point) => point.thetaDeg === 90);
  const stepRad = ((sweep[1].thetaDeg - sweep[0].thetaDeg) * Math.PI) / 180;
  let integral = 0;
  for (let index = 1; index <= finalIndex; index += 1) {
    integral +=
      0.5 *
      (sweep[index - 1].thetaPdfRadInv + sweep[index].thetaPdfRadInv) *
      stepRad;
  }
  return integral;
}

function renderCharts(result) {
  const maximumShift = Math.max(
    4,
    comptonKinematics(state.incidentEnergyKev, 180).fractionalWavelengthShift * 1.08,
  );
  const shiftYMaximum = Math.ceil(maximumShift * 2) / 2;
  renderMultiEnergyChart({
    svgId: "shift-chart",
    extractor: (point) => point.fractionalWavelengthShift,
    selectedValue: result.fractionalWavelengthShift,
    yMaximum: shiftYMaximum,
    yFormatter: (value) => formatNumber(value, 2),
    yTitle: "Fractional shift, Δλ/λ",
    description: `The five official fractional-shift curves and the selected ${formatNumber(state.incidentEnergyKev, 1)} kiloelectronvolt curve. The marker is at ${formatNumber(state.thetaDeg, 1)} degrees with value ${formatNumber(result.fractionalWavelengthShift, 4)}.`,
  });
  renderMultiEnergyChart({
    svgId: "beta-chart",
    extractor: (point) => point.electronBeta,
    selectedValue: result.electronBeta,
    yMaximum: 1,
    yFormatter: (value) => formatFixed(value, 2),
    yTitle: "Electron recoil speed, v/c",
    description: `Five exact relativistic recoil-speed curves on a zero-to-one scale. The selected marker is ${formatNumber(result.electronBeta, 4)} times the speed of light.`,
  });
  renderMultiEnergyChart({
    svgId: "phi-chart",
    extractor: (point) => point.electronRecoilAngleDeg,
    selectedValue: result.electronRecoilAngleDeg,
    yMaximum: 90,
    yFormatter: (value) => `${formatNumber(value, 0)}°`,
    yTitle: "Electron recoil angle, φ",
    description: result.electronRecoilDirectionDefined
      ? `Five recoil-angle curves. The selected marker is ${formatNumber(result.electronRecoilAngleDeg, 2)} degrees.`
      : "Five recoil-angle curves. At the selected zero-degree photon angle the electron has zero momentum, so the plotted 90-degree value is only the continuous limit.",
  });
}

function renderExtension() {
  const selected = kleinNishinaState(state.incidentEnergyKev, state.thetaDeg);
  const sweep = kleinNishinaSweep(state.incidentEnergyKev);
  const forwardProbability = forwardHemisphereProbability(sweep);
  elements["total-cross-section"].textContent = `${formatFixed(selected.totalBarn, 4)} barn`;
  elements["differential-cross-section"].textContent = `${formatFixed(selected.differentialBarnSr, 4)} barn sr⁻¹`;
  elements["relative-cross-section"].textContent = formatFixed(
    selected.relativeDifferential,
    3,
  );
  elements["polar-density"].textContent = `${formatFixed(selected.thetaPdfRadInv, 3)} rad⁻¹`;
  elements["forward-probability"].textContent = `${formatFixed(100 * forwardProbability, 1)}%`;

  renderSingleCurveChart({
    svgId: "differential-chart",
    sweep,
    extractor: (point) => point.relativeDifferential,
    selectedValue: selected.relativeDifferential,
    yMaximum: 1,
    yFormatter: (value) => formatFixed(value, 2),
    yTitle: "Relative dσ/dΩ",
    description: `At ${formatNumber(state.incidentEnergyKev, 1)} kiloelectronvolts, the differential cross-section is shown relative to the common forward value.`,
  });
  const densityMaximum = Math.max(...sweep.map((point) => point.thetaPdfRadInv));
  const densityYMaximum = Math.max(0.1, Math.ceil(densityMaximum * 11) / 10);
  renderSingleCurveChart({
    svgId: "density-chart",
    sweep,
    extractor: (point) => point.thetaPdfRadInv,
    selectedValue: selected.thetaPdfRadInv,
    yMaximum: densityYMaximum,
    yFormatter: (value) => formatFixed(value, 2),
    yTitle: "Probability density / rad",
    description: `The ${formatNumber(state.incidentEnergyKev, 1)} kiloelectronvolt polar-angle density includes the solid-angle factor and integrates to one.`,
  });
}

function updatePresetStates() {
  for (const button of document.querySelectorAll("[data-energy]")) {
    const active = Number(button.dataset.energy) === state.incidentEnergyKev;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  }
  for (const button of document.querySelectorAll("[data-theta]")) {
    const active = Number(button.dataset.theta) === state.thetaDeg;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  }
}

function render() {
  const result = comptonKinematics(state.incidentEnergyKev, state.thetaDeg);
  elements["energy-output"].textContent = formatEnergy(state.incidentEnergyKev);
  elements["theta-output"].textContent = `${formatNumber(state.thetaDeg, 1)}°`;
  elements["fractional-shift"].textContent = formatNumber(
    result.fractionalWavelengthShift,
    5,
  );
  elements["absolute-shift"].textContent = `${formatNumber(result.wavelengthShiftM * 1e12, 4)} pm`;
  elements["electron-beta"].textContent = `${formatNumber(result.electronBeta, 5)} c`;
  elements["electron-speed"].textContent = `${scientific(result.electronSpeedMS)} m s⁻¹`;
  elements["recoil-angle"].textContent = result.electronRecoilDirectionDefined
    ? `${formatFixed(result.electronRecoilAngleDeg, 2)}°`
    : "undefined";
  elements["recoil-direction-note"].textContent = result.electronRecoilDirectionDefined
    ? "defined · below the incident axis"
    : "pₑ = 0 · graph shows the 90° limiting value";
  elements["scattered-energy"].textContent = `${formatFixed(result.scatteredEnergyKev, 3)} keV`;
  elements["kinetic-energy"].textContent = `${formatFixed(result.electronKineticEnergyKev, 3)} keV`;
  const retainedEnergyPercentage = Math.max(
    0,
    Math.min(100, (100 * result.scatteredEnergyKev) / result.incidentEnergyKev),
  );
  elements["photon-energy-fill"].value = retainedEnergyPercentage;
  elements["photon-energy-fill"].textContent = `${formatNumber(retainedEnergyPercentage, 2)}%`;
  elements["selected-energy-label"].textContent = `selected: ${formatEnergy(state.incidentEnergyKev)}`;

  renderGeometry(result);
  renderCharts(result);
  renderExtension();
  updatePresetStates();
  elements["live-results"].textContent = result.electronRecoilDirectionDefined
    ? `At ${formatNumber(state.incidentEnergyKev, 1)} kiloelectronvolts and ${formatNumber(state.thetaDeg, 1)} degrees: fractional shift ${formatNumber(result.fractionalWavelengthShift, 4)}, electron speed ${formatNumber(result.electronBeta, 4)} c, recoil angle ${formatNumber(result.electronRecoilAngleDeg, 2)} degrees.`
    : `At ${formatNumber(state.incidentEnergyKev, 1)} kiloelectronvolts and zero degrees: no wavelength shift, zero electron recoil speed, and no defined electron direction.`;
}

let pendingFrame = 0;
function scheduleRender() {
  if (pendingFrame) cancelAnimationFrame(pendingFrame);
  pendingFrame = requestAnimationFrame(() => {
    pendingFrame = 0;
    render();
  });
}

function setEnergy(value) {
  state.incidentEnergyKev = clampIncidentEnergyKev(Number(value));
  elements["energy-range"].value = String(state.incidentEnergyKev);
  elements["energy-number"].value = String(state.incidentEnergyKev);
  scheduleRender();
}

function setTheta(value) {
  state.thetaDeg = clampScatteringAngleDeg(Number(value));
  elements["theta-range"].value = String(state.thetaDeg);
  elements["theta-number"].value = String(state.thetaDeg);
  scheduleRender();
}

elements["energy-range"].addEventListener("input", (event) => setEnergy(event.target.value));
elements["energy-number"].addEventListener("change", (event) => setEnergy(event.target.value));
elements["theta-range"].addEventListener("input", (event) => setTheta(event.target.value));
elements["theta-number"].addEventListener("change", (event) => setTheta(event.target.value));

for (const button of document.querySelectorAll("[data-energy]")) {
  button.addEventListener("click", () => setEnergy(button.dataset.energy));
}
for (const button of document.querySelectorAll("[data-theta]")) {
  button.addEventListener("click", () => setTheta(button.dataset.theta));
}

elements["reset-button"].addEventListener("click", () => {
  state.incidentEnergyKev = DEFAULT_ENERGY_KEV;
  state.thetaDeg = DEFAULT_THETA_DEG;
  elements["energy-range"].value = String(DEFAULT_ENERGY_KEV);
  elements["energy-number"].value = String(DEFAULT_ENERGY_KEV);
  elements["theta-range"].value = String(DEFAULT_THETA_DEG);
  elements["theta-number"].value = String(DEFAULT_THETA_DEG);
  scheduleRender();
});

render();
