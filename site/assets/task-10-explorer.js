import { loadTask10Evidence } from "./task-10-evidence.js";
import {
  FAMILY_LABELS,
  defaultMassNumber,
  officialGalleryStates,
  radialProfile,
  sampleOrthogonalSlices,
  sampleSliceStack,
  stateLabel,
  stateSummary,
  validateState,
} from "../../task10_hydrogenic_orbitals/app/physics.js";

const elements = {
  laboratory: document.querySelector("[data-orbital-laboratory]"),
  laboratoryStatus: document.querySelector("[data-laboratory-status]"),
  stateTitle: document.querySelector("[data-state-title]"),
  stateLabel: document.querySelector("[data-state-label]"),
  energy: document.querySelector("[data-energy]"),
  bohrRadius: document.querySelector("[data-bohr-radius]"),
  nodeCounts: document.querySelector("[data-node-counts]"),
  symmetry: document.querySelector("[data-symmetry]"),
  atomicNumber: document.querySelector("#atomic-number"),
  principalNumber: document.querySelector("#principal-number"),
  angularNumber: document.querySelector("#angular-number"),
  magneticNumber: document.querySelector("#magnetic-number"),
  galleryPreset: document.querySelector("#gallery-preset"),
  extent: document.querySelector("#extent-range"),
  sliceCount: document.querySelector("#slice-count"),
  threshold: document.querySelector("#density-threshold"),
  opacity: document.querySelector("#density-opacity"),
  extentOutput: document.querySelector("[data-extent-output]"),
  sliceOutput: document.querySelector("[data-slice-output]"),
  thresholdOutput: document.querySelector("[data-threshold-output]"),
  opacityOutput: document.querySelector("[data-opacity-output]"),
  cameraActions: [...document.querySelectorAll("[data-camera-action]")],
  glassCanvas: document.querySelector("#glass-canvas"),
  sliceCanvas: document.querySelector("#slice-canvas"),
  radialCanvas: document.querySelector("#radial-canvas"),
  scalingCanvas: document.querySelector("#z-scaling-canvas"),
  glassLoading: document.querySelector("[data-glass-loading]"),
  glassError: document.querySelector("[data-glass-error]"),
  sliceError: document.querySelector("[data-slice-error]"),
  radialError: document.querySelector("[data-radial-error]"),
  scalingError: document.querySelector("[data-scaling-error]"),
  sliceTitle: document.querySelector("[data-slice-title]"),
  radialTitle: document.querySelector("[data-radial-title]"),
  radialNodes: document.querySelector("[data-radial-nodes]"),
  angularNodes: document.querySelector("[data-angular-nodes]"),
  parity: document.querySelector("[data-parity]"),
  scalingTitle: document.querySelector("[data-scaling-title]"),
  scalingState: document.querySelector("[data-scaling-state]"),
  ionRows: [...document.querySelectorAll("[data-ion-row]")],
};

const ELEMENT_SYMBOLS = Object.freeze([
  "H",
  "He",
  "Li",
  "Be",
  "B",
  "C",
  "N",
  "O",
  "F",
  "Ne",
  "Na",
  "Mg",
  "Al",
  "Si",
  "P",
  "S",
  "Cl",
  "Ar",
  "K",
  "Ca",
]);

const DENSITY_STOPS = Object.freeze([
  [0, [250, 247, 239]],
  [0.2, [229, 210, 181]],
  [0.42, [205, 157, 109]],
  [0.64, [178, 101, 69]],
  [0.84, [121, 67, 54]],
  [1, [54, 42, 38]],
]);

const FIGURE = Object.freeze({
  paper: "#fcfbf7",
  ink: "#302c27",
  muted: "#746e65",
  grid: "rgba(72, 65, 58, .11)",
  gridStrong: "rgba(72, 65, 58, .24)",
  rust: "#a4533e",
  teal: "#3f7771",
  tealSoft: "rgba(63, 119, 113, .18)",
  ochre: "#b79552",
});

const FIGURE_FONT = '"Times New Roman", Times, serif';
const SCALING_IONS = Object.freeze([
  Object.freeze({ Z: 1, A: 1, label: "H", colour: FIGURE.rust }),
  Object.freeze({ Z: 2, A: 4, label: "He⁺", colour: FIGURE.teal }),
  Object.freeze({ Z: 3, A: 6, label: "Li²⁺", colour: FIGURE.ochre }),
]);
const VIEW_SCALE = 0.37;
const camera = { yaw: -0.82, pitch: 0.43, zoom: 1 };

let evidence = null;
let stackCache = null;
let sliceCache = null;
let dragging = false;
let pointer = { x: 0, y: 0 };
let resizeTimer = 0;

function addOptions(select, options, selected) {
  select.replaceChildren();
  for (const [value, label] of options) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = label;
    option.selected = String(value) === String(selected);
    select.append(option);
  }
}

function populateControls() {
  addOptions(
    elements.atomicNumber,
    ELEMENT_SYMBOLS.map((symbol, index) => [
      index + 1,
      `${index + 1} · ${symbol}-${defaultMassNumber(index + 1)}`,
    ]),
    1,
  );
  addOptions(
    elements.principalNumber,
    Array.from({ length: 8 }, (_, index) => [index + 1, String(index + 1)]),
    3,
  );
  const presets = [["", "Custom state"]];
  for (const state of officialGalleryStates()) {
    presets.push([
      `${state.n},${state.l},${state.m}`,
      `${FAMILY_LABELS[state.l]} family · ${stateLabel(state)}`,
    ]);
  }
  addOptions(elements.galleryPreset, presets, "3,2,0");
  updateAngularControls(2, 0);
}

function updateAngularControls(
  preferredL = Number(elements.angularNumber.value || 0),
  preferredM = Number(elements.magneticNumber.value || 0),
) {
  const n = Number(elements.principalNumber.value);
  const l = Math.max(0, Math.min(n - 1, preferredL));
  addOptions(
    elements.angularNumber,
    Array.from({ length: n }, (_, index) => [
      index,
      `${index} · ${FAMILY_LABELS[index]}`,
    ]),
    l,
  );
  const m = Math.max(-l, Math.min(l, preferredM));
  addOptions(
    elements.magneticNumber,
    Array.from({ length: 2 * l + 1 }, (_, index) => {
      const value = index - l;
      return [value, value >= 0 ? `+${value}` : String(value)];
    }),
    m,
  );
}

function currentState() {
  const Z = Number(elements.atomicNumber.value);
  return validateState({
    n: Number(elements.principalNumber.value),
    l: Number(elements.angularNumber.value),
    m: Number(elements.magneticNumber.value),
    Z,
    A: defaultMassNumber(Z),
  });
}

function currentDisplay() {
  return Object.freeze({
    extent: Number(elements.extent.value),
    sliceCount: Number(elements.sliceCount.value),
    threshold: Number(elements.threshold.value),
    opacity: Number(elements.opacity.value),
  });
}

function syncPreset(state) {
  const key =
    state.Z === 1 &&
    state.A === 1 &&
    state.n === state.l + 1 &&
    state.l <= 4
      ? `${state.n},${state.l},${state.m}`
      : "";
  elements.galleryPreset.value = key;
}

function signed(value, digits = 6) {
  return `${value < 0 ? "−" : "+"}${Math.abs(value).toFixed(digits)}`;
}

function updateText(state, display) {
  const summary = stateSummary(state);
  const symbol = ELEMENT_SYMBOLS[state.Z - 1];
  const label = stateLabel(state);
  const isotope = `${symbol}-${state.A}`;
  const parityWord = summary.parity > 0 ? "even" : "odd";

  elements.extentOutput.textContent = `${display.extent.toFixed(1)} n²a`;
  elements.sliceOutput.textContent = String(display.sliceCount);
  elements.thresholdOutput.textContent = display.threshold.toFixed(2);
  elements.opacityOutput.textContent = `${Math.round(100 * display.opacity)}%`;
  elements.stateTitle.textContent = `${isotope} · ${label}`;
  elements.stateLabel.textContent = label;
  elements.energy.textContent = `${signed(summary.energyEv)} eV`;
  elements.bohrRadius.textContent =
    `${summary.effectiveBohrRadiusAngstrom.toFixed(6)} Å`;
  elements.nodeCounts.textContent =
    `${summary.radialNodes} radial · ${summary.angularNodes} angular`;
  elements.symmetry.textContent =
    `${parityWord} · ${summary.degeneracy}-fold m degeneracy`;
  elements.sliceTitle.textContent = `${label} · shared relative scale`;
  elements.radialTitle.textContent =
    `Pᵣ(r) · ${summary.radialNodes} radial ${summary.radialNodes === 1 ? "node" : "nodes"}`;
  elements.radialNodes.textContent =
    `n − l − 1 = ${summary.radialNodes}`;
  elements.angularNodes.textContent = `l = ${summary.angularNodes}`;
  elements.parity.innerHTML =
    `(−1)<sup>l</sup> = ${parityWord}`;
  elements.glassCanvas.setAttribute(
    "aria-label",
    `${display.sliceCount} semitransparent probability-density planes for ${isotope} ${label}; relative display cutoff ${display.threshold.toFixed(2)}.`,
  );
  elements.sliceCanvas.setAttribute(
    "aria-label",
    `Orthogonal x-y, x-z, and y-z relative probability-density slices for ${isotope} ${label}.`,
  );
  elements.radialCanvas.setAttribute(
    "aria-label",
    `Normalized radial probability for ${isotope} ${label}, with ${summary.radialNodes} radial nodes.`,
  );
}

function fitCanvas(canvas) {
  const bounds = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width));
  const height = Math.max(1, Math.round(bounds.height));
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const pixelWidth = Math.round(width * ratio);
  const pixelHeight = Math.round(height * ratio);
  if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;
  }
  const context = canvas.getContext("2d", { alpha: false });
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { context, width, height, ratio };
}

function densityColour(value) {
  const bounded = Math.max(0, Math.min(1, value));
  let lower = DENSITY_STOPS[0];
  let upper = DENSITY_STOPS[DENSITY_STOPS.length - 1];
  for (let index = 1; index < DENSITY_STOPS.length; index += 1) {
    if (bounded <= DENSITY_STOPS[index][0]) {
      lower = DENSITY_STOPS[index - 1];
      upper = DENSITY_STOPS[index];
      break;
    }
  }
  const amount =
    (bounded - lower[0]) / Math.max(1e-12, upper[0] - lower[0]);
  return lower[1].map((component, index) =>
    Math.round(component + amount * (upper[1][index] - component)),
  );
}

function densityTexture(
  values,
  resolution,
  maximum,
  threshold,
  opacity,
  transparent,
  contour = false,
) {
  const texture = document.createElement("canvas");
  texture.width = resolution;
  texture.height = resolution;
  const context = texture.getContext("2d", { alpha: true });
  const image = context.createImageData(resolution, resolution);
  for (let displayRow = 0; displayRow < resolution; displayRow += 1) {
    const sourceRow = resolution - 1 - displayRow;
    for (let column = 0; column < resolution; column += 1) {
      const sourceIndex = sourceRow * resolution + column;
      const relative = values[sourceIndex] / maximum;
      const colour = densityColour(relative ** 0.58);
      const imageIndex = 4 * (displayRow * resolution + column);
      let boundary = false;
      if (contour && relative >= threshold) {
        for (const [dx, dy] of [
          [-1, 0],
          [1, 0],
          [0, -1],
          [0, 1],
        ]) {
          const neighbourColumn = column + dx;
          const neighbourRow = sourceRow + dy;
          if (
            neighbourColumn >= 0 &&
            neighbourColumn < resolution &&
            neighbourRow >= 0 &&
            neighbourRow < resolution &&
            values[neighbourRow * resolution + neighbourColumn] / maximum <
              threshold
          ) {
            boundary = true;
          }
        }
      }
      image.data[imageIndex] = boundary ? 63 : colour[0];
      image.data[imageIndex + 1] = boundary ? 55 : colour[1];
      image.data[imageIndex + 2] = boundary ? 49 : colour[2];
      image.data[imageIndex + 3] = transparent
        ? relative < threshold
          ? 0
          : Math.round(
              255 * opacity * (0.12 + 0.88 * relative ** 0.62),
            )
        : 255;
    }
  }
  context.putImageData(image, 0, 0);
  return texture;
}

function projectPoint(x, y, z, width, height) {
  const cosineYaw = Math.cos(camera.yaw);
  const sineYaw = Math.sin(camera.yaw);
  const sinePitch = Math.sin(camera.pitch);
  const cosinePitch = Math.cos(camera.pitch);
  const scale = Math.min(width, height) * VIEW_SCALE * camera.zoom;
  return Object.freeze({
    x: width / 2 + scale * (cosineYaw * x - sineYaw * y),
    y:
      height / 2 +
      scale *
        (sinePitch * (sineYaw * x + cosineYaw * y) - cosinePitch * z),
  });
}

function drawAxis(context, width, height, x, y, z, colour, label) {
  const origin = projectPoint(0, 0, 0, width, height);
  const end = projectPoint(x, y, z, width, height);
  context.strokeStyle = colour;
  context.fillStyle = colour;
  context.lineWidth = 1.4;
  context.beginPath();
  context.moveTo(origin.x, origin.y);
  context.lineTo(end.x, end.y);
  context.stroke();
  context.font = `italic 16px ${FIGURE_FONT}`;
  context.fillText(label, end.x + 7, end.y - 5);
}

function drawPlaneOutline(context, z, width, height) {
  const corners = [
    projectPoint(-1, -1, z, width, height),
    projectPoint(1, -1, z, width, height),
    projectPoint(1, 1, z, width, height),
    projectPoint(-1, 1, z, width, height),
  ];
  context.beginPath();
  context.moveTo(corners[0].x, corners[0].y);
  corners.slice(1).forEach((point) => context.lineTo(point.x, point.y));
  context.closePath();
  context.stroke();
}

function drawColourScale(context, width, height, threshold) {
  const scaleWidth = Math.min(230, width * 0.35);
  const left = width - scaleWidth - 24;
  const top = height - 42;
  const gradient = context.createLinearGradient(left, 0, left + scaleWidth, 0);
  DENSITY_STOPS.forEach(([stop, colour]) => {
    gradient.addColorStop(stop, `rgb(${colour.join(",")})`);
  });
  context.fillStyle = gradient;
  context.fillRect(left, top, scaleWidth, 7);
  context.strokeStyle = FIGURE.gridStrong;
  context.strokeRect(left, top, scaleWidth, 7);
  context.fillStyle = FIGURE.muted;
  context.font = `12px ${FIGURE_FONT}`;
  context.textAlign = "left";
  context.fillText("0", left, top - 6);
  context.textAlign = "right";
  context.fillText("relative density 1", left + scaleWidth, top - 6);
  context.fillStyle = FIGURE.teal;
  context.textAlign = "center";
  context.fillText(
    `cutoff ${threshold.toFixed(2)}`,
    left + threshold * scaleWidth,
    top + 23,
  );
  context.textAlign = "left";
}

function renderGlass(stack, display, state) {
  const { context, width, height } = fitCanvas(elements.glassCanvas);
  context.fillStyle = FIGURE.paper;
  context.fillRect(0, 0, width, height);

  context.strokeStyle = FIGURE.grid;
  context.lineWidth = 1;
  for (let index = 1; index <= 4; index += 1) {
    context.beginPath();
    context.arc(
      width * 0.5,
      height * 0.5,
      (Math.min(width, height) * index) / 10,
      0,
      Math.PI * 2,
    );
    context.stroke();
  }

  const textures = stack.slices.map((slice) =>
    densityTexture(
      slice.values,
      stack.resolution,
      stack.maximum,
      display.threshold,
      display.opacity,
      true,
    ),
  );
  const ordered = stack.slices
    .map((slice, index) => ({ slice, texture: textures[index] }))
    .sort(
      (first, second) =>
        Math.sin(camera.pitch) * (first.slice.z - second.slice.z),
    );
  const cosineYaw = Math.cos(camera.yaw);
  const sineYaw = Math.sin(camera.yaw);
  const sinePitch = Math.sin(camera.pitch);
  const cosinePitch = Math.cos(camera.pitch);
  const scale = Math.min(width, height) * VIEW_SCALE * camera.zoom;
  const basisX = [cosineYaw, sinePitch * sineYaw];
  const basisY = [-sineYaw, sinePitch * cosineYaw];
  const basisZ = [0, -cosinePitch];

  context.strokeStyle = FIGURE.tealSoft;
  context.lineWidth = 0.8;
  for (const { slice, texture } of ordered) {
    const z = slice.z / display.extent;
    drawPlaneOutline(context, z, width, height);
    context.save();
    context.transform(
      (2 * scale * basisX[0]) / stack.resolution,
      (2 * scale * basisX[1]) / stack.resolution,
      (2 * scale * basisY[0]) / stack.resolution,
      (2 * scale * basisY[1]) / stack.resolution,
      width / 2 -
        scale * basisX[0] -
        scale * basisY[0] +
        scale * basisZ[0] * z,
      height / 2 -
        scale * basisX[1] -
        scale * basisY[1] +
        scale * basisZ[1] * z,
    );
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    context.drawImage(texture, 0, 0);
    context.restore();
  }

  drawAxis(context, width, height, 1.22, 0, 0, FIGURE.ink, "x");
  drawAxis(context, width, height, 0, 1.22, 0, FIGURE.teal, "y");
  drawAxis(context, width, height, 0, 0, 1.22, FIGURE.rust, "z");

  context.fillStyle = FIGURE.ink;
  context.font = `24px ${FIGURE_FONT}`;
  context.fillText(stateLabel(state), 24, 38);
  context.fillStyle = FIGURE.muted;
  context.font = `14px ${FIGURE_FONT}`;
  context.fillText(
    `${display.sliceCount} fixed xy planes · axes in n²a`,
    24,
    61,
  );
  drawColourScale(context, width, height, display.threshold);
}

function drawSlicePanel(
  context,
  planeData,
  data,
  display,
  x,
  y,
  size,
) {
  const texture = densityTexture(
    planeData.values,
    data.resolution,
    data.maximum,
    display.threshold,
    1,
    false,
    true,
  );
  context.fillStyle = FIGURE.paper;
  context.fillRect(x, y, size, size);
  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = "high";
  context.drawImage(texture, x, y, size, size);
  context.strokeStyle = FIGURE.gridStrong;
  context.lineWidth = 1;
  context.strokeRect(x + 0.5, y + 0.5, size - 1, size - 1);
  context.beginPath();
  context.moveTo(x + size / 2, y);
  context.lineTo(x + size / 2, y + size);
  context.moveTo(x, y + size / 2);
  context.lineTo(x + size, y + size / 2);
  context.stroke();

  const planeLabel = {
    xy: "xy · z = 0",
    xz: "xz · y = 0",
    yz: "yz · x = 0",
  }[planeData.plane];
  context.fillStyle = FIGURE.ink;
  context.font = `17px ${FIGURE_FONT}`;
  context.fillText(planeLabel, x, y - 13);
  context.fillStyle = FIGURE.muted;
  context.font = `12px ${FIGURE_FONT}`;
  context.fillText(`−${display.extent.toFixed(1)}`, x, y + size + 17);
  context.textAlign = "right";
  context.fillText(
    `+${display.extent.toFixed(1)} n²a`,
    x + size,
    y + size + 17,
  );
  context.textAlign = "left";
}

function renderSlices(data, display, state) {
  const { context, width, height } = fitCanvas(elements.sliceCanvas);
  context.fillStyle = FIGURE.paper;
  context.fillRect(0, 0, width, height);

  const vertical = width < 640;
  if (vertical) {
    const size = Math.max(76, Math.min(width - 90, (height - 116) / 3));
    const x = Math.max(52, (width - size) / 2);
    data.planes.forEach((plane, index) => {
      const y = 33 + index * (size + 45);
      drawSlicePanel(context, plane, data, display, x, y, size);
    });
  } else {
    const gap = 22;
    const size = Math.min(
      (width - 60 - 2 * gap) / 3,
      height - 122,
    );
    const total = 3 * size + 2 * gap;
    const left = (width - total) / 2;
    data.planes.forEach((plane, index) => {
      drawSlicePanel(
        context,
        plane,
        data,
        display,
        left + index * (size + gap),
        58,
        size,
      );
    });
  }

  context.fillStyle = FIGURE.muted;
  context.font = `13px ${FIGURE_FONT}`;
  context.fillText(
    `${stateLabel(state)} · shared scale · contour ${display.threshold.toFixed(2)}`,
    22,
    height - 23,
  );
}

function renderRadial(state) {
  const { context, width, height } = fitCanvas(elements.radialCanvas);
  const compact = width < 520;
  const margin = {
    left: compact ? 58 : 78,
    right: 22,
    top: 35,
    bottom: compact ? 74 : 80,
  };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const extent = 6.2;
  const profile = radialProfile(state, { extent, samples: 501 });
  const maximum = Math.max(
    ...profile.map((point) => point.probabilityPerScaledRadius),
  );
  const x = (value) => margin.left + (plotWidth * value) / extent;
  const y = (value) =>
    margin.top + plotHeight * (1 - value / (1.08 * maximum));

  context.fillStyle = FIGURE.paper;
  context.fillRect(0, 0, width, height);

  context.strokeStyle = FIGURE.grid;
  context.fillStyle = FIGURE.muted;
  context.font = `12px ${FIGURE_FONT}`;
  context.lineWidth = 1;
  for (let index = 0; index <= 5; index += 1) {
    const value = (extent * index) / 5;
    const position = x(value);
    context.beginPath();
    context.moveTo(position, margin.top);
    context.lineTo(position, height - margin.bottom);
    context.stroke();
    context.textAlign = "center";
    context.fillText(value.toFixed(1), position, height - margin.bottom + 24);
  }
  for (let index = 0; index <= 4; index += 1) {
    const value = (1.08 * maximum * index) / 4;
    const position = y(value);
    context.beginPath();
    context.moveTo(margin.left, position);
    context.lineTo(width - margin.right, position);
    context.stroke();
    context.textAlign = "right";
    context.fillText(value.toFixed(2), margin.left - 10, position + 4);
  }

  const area = context.createLinearGradient(0, margin.top, 0, height - margin.bottom);
  area.addColorStop(0, "rgba(164, 83, 62, .34)");
  area.addColorStop(1, "rgba(164, 83, 62, .025)");
  context.beginPath();
  context.moveTo(x(0), y(0));
  profile.forEach((point) =>
    context.lineTo(x(point.scaledRadius), y(point.probabilityPerScaledRadius)),
  );
  context.lineTo(x(extent), y(0));
  context.closePath();
  context.fillStyle = area;
  context.fill();

  context.beginPath();
  profile.forEach((point, index) => {
    const method = index === 0 ? "moveTo" : "lineTo";
    context[method](
      x(point.scaledRadius),
      y(point.probabilityPerScaledRadius),
    );
  });
  context.strokeStyle = FIGURE.rust;
  context.lineWidth = 2.4;
  context.stroke();

  const nodeRows = evidence.radialNodes.filter(
    (row) => Number(row.n) === state.n && Number(row.l) === state.l,
  );
  for (const row of nodeRows) {
    const position = Number(row.radius_over_n_squared_a);
    context.setLineDash([5, 5]);
    context.strokeStyle = FIGURE.teal;
    context.lineWidth = 1.2;
    context.beginPath();
    context.moveTo(x(position), margin.top);
    context.lineTo(x(position), height - margin.bottom);
    context.stroke();
    context.setLineDash([]);
    context.fillStyle = FIGURE.teal;
    context.textAlign = "center";
    context.font = `italic 11px ${FIGURE_FONT}`;
    context.fillText(`node ${row.node_index}`, x(position), margin.top + 14);
  }

  const peak = profile.reduce((best, point) =>
    point.probabilityPerScaledRadius > best.probabilityPerScaledRadius
      ? point
      : best,
  );
  context.fillStyle = FIGURE.ochre;
  context.beginPath();
  context.arc(
    x(peak.scaledRadius),
    y(peak.probabilityPerScaledRadius),
    4.5,
    0,
    Math.PI * 2,
  );
  context.fill();

  context.strokeStyle = FIGURE.gridStrong;
  context.lineWidth = 1.2;
  context.beginPath();
  context.moveTo(margin.left, margin.top);
  context.lineTo(margin.left, height - margin.bottom);
  context.lineTo(width - margin.right, height - margin.bottom);
  context.stroke();

  context.fillStyle = FIGURE.ink;
  context.font = `16px ${FIGURE_FONT}`;
  context.textAlign = "center";
  context.fillText(
    "scaled radius, r/(n²a)",
    margin.left + plotWidth / 2,
    height - 25,
  );
  context.save();
  context.translate(18, margin.top + plotHeight / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("probability per d[r/(n²a)]", 0, 0);
  context.restore();
  context.textAlign = "left";
  context.fillStyle = FIGURE.muted;
  context.font = `13px ${FIGURE_FONT}`;
  context.fillText(
    `${stateLabel(state)} · normalized radial distribution`,
    margin.left,
    21,
  );
}

function renderIonScaling(selectedState) {
  const { context, width, height } = fitCanvas(elements.scalingCanvas);
  const compact = width < 560;
  const margin = {
    left: compact ? 58 : 76,
    right: compact ? 18 : 30,
    top: compact ? 72 : 62,
    bottom: compact ? 72 : 78,
  };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const scaledExtent = 6.2;
  const series = SCALING_IONS.map((ion) => {
    const state = validateState({
      n: selectedState.n,
      l: selectedState.l,
      m: selectedState.m,
      Z: ion.Z,
      A: ion.A,
    });
    const summary = stateSummary(state);
    const radialScaleAngstrom =
      state.n ** 2 * summary.effectiveBohrRadiusAngstrom;
    const points = radialProfile(state, {
      extent: scaledExtent,
      samples: 701,
    }).map((point) => ({
      radiusAngstrom: point.scaledRadius * radialScaleAngstrom,
      probabilityPerAngstrom:
        point.probabilityPerScaledRadius / radialScaleAngstrom,
    }));
    return Object.freeze({ ion, state, summary, points });
  });

  const xMaximum =
    scaledExtent *
    selectedState.n ** 2 *
    series[0].summary.effectiveBohrRadiusAngstrom;
  const yMaximum =
    1.08 *
    Math.max(
      ...series.flatMap(({ points }) =>
        points.map((point) => point.probabilityPerAngstrom),
      ),
    );
  const x = (value) => margin.left + (plotWidth * value) / xMaximum;
  const y = (value) =>
    margin.top + plotHeight * (1 - value / Math.max(yMaximum, 1e-12));
  const tick = (value) => {
    if (value >= 10) return value.toFixed(0);
    if (value >= 1) return value.toFixed(1);
    return value.toFixed(2);
  };

  context.fillStyle = FIGURE.paper;
  context.fillRect(0, 0, width, height);
  context.strokeStyle = FIGURE.grid;
  context.fillStyle = FIGURE.muted;
  context.font = `12px ${FIGURE_FONT}`;
  context.lineWidth = 1;
  for (let index = 0; index <= 5; index += 1) {
    const value = (xMaximum * index) / 5;
    const position = x(value);
    context.beginPath();
    context.moveTo(position, margin.top);
    context.lineTo(position, height - margin.bottom);
    context.stroke();
    context.textAlign = "center";
    context.fillText(tick(value), position, height - margin.bottom + 23);
  }
  for (let index = 0; index <= 4; index += 1) {
    const value = (yMaximum * index) / 4;
    const position = y(value);
    context.beginPath();
    context.moveTo(margin.left, position);
    context.lineTo(width - margin.right, position);
    context.stroke();
    context.textAlign = "right";
    context.fillText(tick(value), margin.left - 9, position + 4);
  }

  for (const { ion, points } of series) {
    context.beginPath();
    points.forEach((point, index) => {
      context[index === 0 ? "moveTo" : "lineTo"](
        x(point.radiusAngstrom),
        y(point.probabilityPerAngstrom),
      );
    });
    context.strokeStyle = ion.colour;
    context.lineWidth = 2.5;
    context.lineJoin = "round";
    context.lineCap = "round";
    context.stroke();
  }

  context.strokeStyle = FIGURE.gridStrong;
  context.lineWidth = 1.2;
  context.beginPath();
  context.moveTo(margin.left, margin.top);
  context.lineTo(margin.left, height - margin.bottom);
  context.lineTo(width - margin.right, height - margin.bottom);
  context.stroke();

  const legendGap = compact ? Math.max(72, (width - 32) / 3) : 112;
  const legendLeft = compact ? 14 : margin.left;
  series.forEach(({ ion }, index) => {
    const legendX = legendLeft + index * legendGap;
    context.strokeStyle = ion.colour;
    context.lineWidth = 3;
    context.beginPath();
    context.moveTo(legendX, 25);
    context.lineTo(legendX + 24, 25);
    context.stroke();
    context.fillStyle = FIGURE.ink;
    context.textAlign = "left";
    context.font = `14px ${FIGURE_FONT}`;
    context.fillText(ion.label, legendX + 31, 30);
  });

  context.fillStyle = FIGURE.ink;
  context.font = `16px ${FIGURE_FONT}`;
  context.textAlign = "center";
  context.fillText(
    "physical radius, r (Å)",
    margin.left + plotWidth / 2,
    height - 25,
  );
  context.save();
  context.translate(18, margin.top + plotHeight / 2);
  context.rotate(-Math.PI / 2);
  context.fillText("radial probability per Å", 0, 0);
  context.restore();

  const label = stateLabel(selectedState);
  elements.scalingTitle.textContent = `${label} · H, He⁺, Li²⁺`;
  elements.scalingState.textContent = label;
  const hydrogenSummary = series[0].summary;
  series.forEach(({ ion, summary }, index) => {
    const row = elements.ionRows[index];
    const energyRatio = Math.abs(summary.energyEv / hydrogenSummary.energyEv);
    const radiusRatio =
      summary.effectiveBohrRadiusAngstrom /
      hydrogenSummary.effectiveBohrRadiusAngstrom;
    row.querySelector("[data-ion-energy]").textContent =
      `${signed(summary.energyEv)} eV · ${energyRatio.toFixed(3)}×`;
    row.querySelector("[data-ion-radius]").textContent =
      `a = ${summary.effectiveBohrRadiusAngstrom.toFixed(6)} Å · ${radiusRatio.toFixed(3)}×`;
    row.querySelector("dt").setAttribute(
      "aria-label",
      `${ion.label}, nuclear charge ${ion.Z}`,
    );
  });
  elements.scalingCanvas.setAttribute(
    "aria-label",
    `Physical radial probability for H, He plus, and Li two plus in the ${label} state. Increasing nuclear charge contracts the distribution.`,
  );
}

function renderEverything({ resample = false } = {}) {
  if (!evidence) return;
  const state = currentState();
  const display = currentDisplay();
  syncPreset(state);
  updateText(state, display);

  const stackKey = [
    state.n,
    state.l,
    state.m,
    state.Z,
    state.A,
    display.extent,
    display.sliceCount,
  ].join("/");
  if (resample || !stackCache || stackCache.key !== stackKey) {
    stackCache = {
      key: stackKey,
      data: sampleSliceStack(state, {
        extent: display.extent,
        resolution: 81,
        sliceCount: display.sliceCount,
      }),
    };
  }

  const sliceKey = [
    state.n,
    state.l,
    state.m,
    state.Z,
    state.A,
    display.extent,
  ].join("/");
  if (resample || !sliceCache || sliceCache.key !== sliceKey) {
    sliceCache = {
      key: sliceKey,
      data: sampleOrthogonalSlices(state, {
        extent: display.extent,
        resolution: 121,
      }),
    };
  }

  renderGlass(stackCache.data, display, state);
  renderSlices(sliceCache.data, display, state);
  renderRadial(state);
  renderIonScaling(state);
  elements.laboratoryStatus.textContent = "";
}

function invalidateSamples() {
  stackCache = null;
  sliceCache = null;
  renderEverything({ resample: true });
}

function rerenderCamera() {
  if (!stackCache || !evidence) return;
  renderGlass(stackCache.data, currentDisplay(), currentState());
}

function orbit(amount) {
  camera.yaw += amount;
  rerenderCamera();
}

function zoom(factor) {
  camera.zoom = Math.max(0.62, Math.min(1.65, camera.zoom * factor));
  rerenderCamera();
}

function resetCamera() {
  camera.yaw = -0.82;
  camera.pitch = 0.43;
  camera.zoom = 1;
  rerenderCamera();
}

function wireEvents() {
  elements.principalNumber.addEventListener("change", () => {
    updateAngularControls();
    invalidateSamples();
  });
  elements.angularNumber.addEventListener("change", () => {
    updateAngularControls(Number(elements.angularNumber.value), 0);
    invalidateSamples();
  });
  for (const select of [elements.atomicNumber, elements.magneticNumber]) {
    select.addEventListener("change", invalidateSamples);
  }
  elements.galleryPreset.addEventListener("change", () => {
    if (!elements.galleryPreset.value) return;
    const [n, l, m] = elements.galleryPreset.value.split(",").map(Number);
    elements.atomicNumber.value = "1";
    elements.principalNumber.value = String(n);
    updateAngularControls(l, m);
    invalidateSamples();
  });
  for (const control of [elements.extent, elements.sliceCount]) {
    control.addEventListener("input", invalidateSamples);
  }
  for (const control of [elements.threshold, elements.opacity]) {
    control.addEventListener("input", () => renderEverything());
  }

  for (const button of elements.cameraActions) {
    button.addEventListener("click", () => {
      const actions = {
        left: () => orbit(-0.16),
        right: () => orbit(0.16),
        out: () => zoom(0.88),
        in: () => zoom(1.14),
        reset: resetCamera,
      };
      actions[button.dataset.cameraAction]();
    });
  }

  const canvas = elements.glassCanvas;
  canvas.addEventListener("pointerdown", (event) => {
    dragging = true;
    pointer = { x: event.clientX, y: event.clientY };
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    camera.yaw += (event.clientX - pointer.x) * 0.008;
    camera.pitch = Math.max(
      -1.05,
      Math.min(1.05, camera.pitch + (event.clientY - pointer.y) * 0.006),
    );
    pointer = { x: event.clientX, y: event.clientY };
    rerenderCamera();
  });
  canvas.addEventListener("pointerup", (event) => {
    dragging = false;
    if (canvas.hasPointerCapture(event.pointerId)) {
      canvas.releasePointerCapture(event.pointerId);
    }
  });
  canvas.addEventListener("pointercancel", () => {
    dragging = false;
  });
  canvas.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      zoom(event.deltaY > 0 ? 0.92 : 1.08);
    },
    { passive: false },
  );
  canvas.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      orbit(event.key === "ArrowLeft" ? -0.12 : 0.12);
    }
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault();
      camera.pitch = Math.max(
        -1.05,
        Math.min(
          1.05,
          camera.pitch + (event.key === "ArrowUp" ? -0.1 : 0.1),
        ),
      );
      rerenderCamera();
    }
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      zoom(1.1);
    }
    if (event.key === "-") {
      event.preventDefault();
      zoom(0.9);
    }
  });

  const resizeObserver = new ResizeObserver(() => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => renderEverything(), 80);
  });
  [
    elements.glassCanvas,
    elements.sliceCanvas,
    elements.radialCanvas,
    elements.scalingCanvas,
  ].forEach((canvasElement) => resizeObserver.observe(canvasElement));
  window.addEventListener(
    "pagehide",
    () => {
      window.clearTimeout(resizeTimer);
      resizeObserver.disconnect();
    },
    { once: true },
  );
}

function setEnabled(enabled) {
  const controls = [
    elements.atomicNumber,
    elements.principalNumber,
    elements.angularNumber,
    elements.magneticNumber,
    elements.galleryPreset,
    elements.extent,
    elements.sliceCount,
    elements.threshold,
    elements.opacity,
    ...elements.cameraActions,
  ];
  controls.forEach((control) => {
    control.disabled = !enabled;
  });
}

function lockEvidence(result) {
  evidence = result;
  elements.laboratory.classList.remove("is-loading");
  elements.laboratoryStatus.textContent = "Rendering";
  document.body.dataset.task10Status = "verified";
  setEnabled(true);
  renderEverything({ resample: true });
}

function failClosed(error) {
  console.error("Task 10 evidence lock failed", error);
  evidence = null;
  setEnabled(false);
  elements.laboratory.classList.remove("is-loading");
  elements.laboratoryStatus.textContent = "Orbital data unavailable";
  [
    elements.glassError,
    elements.sliceError,
    elements.radialError,
    elements.scalingError,
  ].forEach((message) => {
    message.hidden = false;
  });
  document.body.dataset.task10Status = "error";
}

populateControls();
setEnabled(false);
wireEvents();
loadTask10Evidence().then(lockEvidence).catch(failClosed);
