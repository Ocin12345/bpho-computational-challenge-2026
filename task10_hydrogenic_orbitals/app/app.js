import {
  FAMILY_LABELS,
  defaultMassNumber,
  officialGalleryStates,
  radialProfile,
  sampleOrthogonalSlices,
  sampleSliceStack,
  scaledRadialWavefunction,
  stateLabel,
  stateSummary,
  validateState,
} from "./physics.js";

const elements = Object.fromEntries(
  [
    "z-select", "n-select", "l-select", "m-select", "gallery-preset",
    "extent-range", "slice-range", "threshold-range", "opacity-range",
    "extent-output", "slice-output", "threshold-output", "opacity-output",
    "reset-all", "live-status", "glass-canvas", "glass-canvas-title",
    "glass-canvas-description", "orbit-left", "orbit-right", "zoom-out",
    "zoom-in", "reset-camera", "state-label", "isotope-label", "energy-value",
    "bohr-value", "physical-extent", "node-value", "symmetry-value",
    "slice-xy", "slice-xz", "slice-yz", "radial-chart", "radial-description",
  ].map((id) => [id, document.getElementById(id)]),
);

const ELEMENT_SYMBOLS = ["H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca"];
const SVG_NS = "http://www.w3.org/2000/svg";
const VIEW_SCALE = 0.4;
const camera = { yaw: -0.82, pitch: 0.43, zoom: 1 };
let stackCache = null;
let orthogonalCache = null;
let renderFrame = 0;
let dragging = false;
let pointer = { x: 0, y: 0 };

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

function populateStaticControls() {
  addOptions(elements["z-select"], ELEMENT_SYMBOLS.map((symbol, index) => [index + 1, `${index + 1} · ${symbol}`]), 1);
  addOptions(elements["n-select"], Array.from({ length: 8 }, (_, index) => [index + 1, String(index + 1)]), 3);
  const presets = [["", "Custom validated state"]];
  for (const state of officialGalleryStates()) presets.push([`${state.n},${state.l},${state.m}`, stateLabel(state)]);
  addOptions(elements["gallery-preset"], presets, "3,2,0");
  updateAngularControls(2, 0);
}

function updateAngularControls(preferredL = Number(elements["l-select"].value || 0), preferredM = Number(elements["m-select"].value || 0)) {
  const n = Number(elements["n-select"].value);
  const l = Math.max(0, Math.min(n - 1, preferredL));
  addOptions(elements["l-select"], Array.from({ length: n }, (_, index) => [index, `${index} · ${FAMILY_LABELS[index]}`]), l);
  const m = Math.max(-l, Math.min(l, preferredM));
  addOptions(elements["m-select"], Array.from({ length: 2 * l + 1 }, (_, index) => {
    const value = index - l;
    return [value, value >= 0 ? `+${value}` : String(value)];
  }), m);
}

function currentState() {
  const Z = Number(elements["z-select"].value);
  return validateState({
    n: Number(elements["n-select"].value),
    l: Number(elements["l-select"].value),
    m: Number(elements["m-select"].value),
    Z,
    A: defaultMassNumber(Z),
  });
}

function currentDisplay() {
  return {
    extent: Number(elements["extent-range"].value),
    sliceCount: Number(elements["slice-range"].value),
    threshold: Number(elements["threshold-range"].value),
    opacity: Number(elements["opacity-range"].value),
  };
}

function syncPreset(state) {
  const key = state.Z === 1 && state.A === 1 && state.n === state.l + 1 && state.l <= 4
    ? `${state.n},${state.l},${state.m}`
    : "";
  elements["gallery-preset"].value = key;
}

function formatSigned(value, digits = 6) {
  const magnitude = Math.abs(value).toFixed(digits);
  return `${value < 0 ? "−" : "+"}${magnitude}`;
}

function updateOutputs(state, display) {
  const summary = stateSummary(state);
  const symbol = ELEMENT_SYMBOLS[state.Z - 1];
  elements["extent-output"].textContent = `${display.extent.toFixed(1)} n²a`;
  elements["slice-output"].textContent = String(display.sliceCount);
  elements["threshold-output"].textContent = display.threshold.toFixed(2);
  elements["opacity-output"].textContent = `${Math.round(100 * display.opacity)}%`;
  elements["state-label"].textContent = stateLabel(state);
  elements["isotope-label"].textContent = `${symbol}-${state.A} · Z=${state.Z} · A=${state.A}`;
  elements["energy-value"].textContent = `${formatSigned(summary.energyEv)} eV`;
  elements["bohr-value"].textContent = `${summary.effectiveBohrRadiusAngstrom.toFixed(6)} Å`;
  const halfExtentAngstrom = display.extent * state.n ** 2 * summary.effectiveBohrRadiusAngstrom;
  elements["physical-extent"].textContent = `display half-extent ${halfExtentAngstrom.toFixed(2)} Å`;
  elements["node-value"].textContent = `${summary.radialNodes} radial · ${summary.angularNodes} angular`;
  elements["symmetry-value"].textContent = `${summary.parity > 0 ? "even" : "odd"} parity · ${summary.degeneracy}-fold m degeneracy`;
  const readableState = `${symbol}-${state.A} ${stateLabel(state)}`;
  elements["glass-canvas-title"].textContent = `${readableState} probability-density slice stack.`;
  elements["glass-canvas-description"].textContent = `${display.sliceCount} x-y planes are projected in three dimensions. Colour and opacity encode relative probability density above the ${display.threshold.toFixed(2)} display cutoff. The displayed camera rotation is not electron motion.`;
  elements["radial-description"].textContent = `${readableState} radial probability per unit r divided by n squared a. It has ${summary.radialNodes} radial nodes.`;
}

const MAGMA_STOPS = [
  [0, [0, 0, 4]], [0.2, [47, 15, 82]], [0.4, [113, 31, 129]],
  [0.6, [181, 54, 122]], [0.8, [246, 112, 92]], [1, [252, 253, 191]],
];

function magma(value) {
  const bounded = Math.max(0, Math.min(1, value));
  let lower = MAGMA_STOPS[0];
  let upper = MAGMA_STOPS.at(-1);
  for (let index = 1; index < MAGMA_STOPS.length; index += 1) {
    if (bounded <= MAGMA_STOPS[index][0]) {
      upper = MAGMA_STOPS[index];
      lower = MAGMA_STOPS[index - 1];
      break;
    }
  }
  const t = (bounded - lower[0]) / Math.max(1e-12, upper[0] - lower[0]);
  return lower[1].map((component, index) => Math.round(component + t * (upper[1][index] - component)));
}

function densityTexture(values, resolution, maximum, threshold, opacity, transparent, contour = false) {
  const canvas = document.createElement("canvas");
  canvas.width = resolution;
  canvas.height = resolution;
  const context = canvas.getContext("2d", { alpha: true });
  const image = context.createImageData(resolution, resolution);
  for (let displayRow = 0; displayRow < resolution; displayRow += 1) {
    const sourceRow = resolution - 1 - displayRow;
    for (let column = 0; column < resolution; column += 1) {
      const sourceIndex = sourceRow * resolution + column;
      const relative = values[sourceIndex] / maximum;
      const colour = magma(relative ** 0.55);
      const imageIndex = 4 * (displayRow * resolution + column);
      let boundary = false;
      if (contour && relative >= threshold) {
        for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          const neighbourColumn = column + dx;
          const neighbourRow = sourceRow + dy;
          if (neighbourColumn >= 0 && neighbourColumn < resolution && neighbourRow >= 0 && neighbourRow < resolution) {
            if (values[neighbourRow * resolution + neighbourColumn] / maximum < threshold) boundary = true;
          }
        }
      }
      image.data[imageIndex] = boundary ? 255 : colour[0];
      image.data[imageIndex + 1] = boundary ? 255 : colour[1];
      image.data[imageIndex + 2] = boundary ? 255 : colour[2];
      image.data[imageIndex + 3] = transparent
        ? relative < threshold ? 0 : Math.round(255 * opacity * (0.16 + 0.84 * relative ** 0.68))
        : 255;
    }
  }
  context.putImageData(image, 0, 0);
  return canvas;
}

function projectPoint(x, y, z, width, height) {
  const cosineYaw = Math.cos(camera.yaw);
  const sineYaw = Math.sin(camera.yaw);
  const sinePitch = Math.sin(camera.pitch);
  const cosinePitch = Math.cos(camera.pitch);
  const scale = Math.min(width, height) * VIEW_SCALE * camera.zoom;
  return {
    x: width / 2 + scale * (cosineYaw * x - sineYaw * y),
    y: height / 2 + scale * (sinePitch * (sineYaw * x + cosineYaw * y) - cosinePitch * z),
  };
}

function drawAxis(context, width, height, x, y, z, colour, label) {
  const origin = projectPoint(0, 0, 0, width, height);
  const end = projectPoint(x, y, z, width, height);
  context.strokeStyle = colour;
  context.fillStyle = colour;
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(origin.x, origin.y);
  context.lineTo(end.x, end.y);
  context.stroke();
  context.font = "700 16px 'Times New Roman', Times, serif";
  context.fillText(label, end.x + 6, end.y - 4);
}

function renderGlass(stack, display, state) {
  const canvas = elements["glass-canvas"];
  const context = canvas.getContext("2d");
  const { width, height } = canvas;
  const background = context.createRadialGradient(width * 0.5, height * 0.45, 30, width * 0.5, height * 0.5, width * 0.65);
  background.addColorStop(0, "#18304a");
  background.addColorStop(1, "#06101c");
  context.fillStyle = background;
  context.fillRect(0, 0, width, height);

  const resolution = stack.resolution;
  const textures = stack.slices.map((slice) => densityTexture(slice.values, resolution, stack.maximum, display.threshold, display.opacity, true));
  const ordered = stack.slices.map((slice, index) => ({ slice, texture: textures[index] }))
    .sort((first, second) => Math.sin(camera.pitch) * (first.slice.z - second.slice.z));
  const cosineYaw = Math.cos(camera.yaw);
  const sineYaw = Math.sin(camera.yaw);
  const sinePitch = Math.sin(camera.pitch);
  const cosinePitch = Math.cos(camera.pitch);
  const scale = Math.min(width, height) * VIEW_SCALE * camera.zoom;
  const basisX = [cosineYaw, sinePitch * sineYaw];
  const basisY = [-sineYaw, sinePitch * cosineYaw];
  const basisZ = [0, -cosinePitch];
  for (const { slice, texture } of ordered) {
    const z = slice.z / display.extent;
    context.save();
    context.setTransform(
      2 * scale * basisX[0] / resolution,
      2 * scale * basisX[1] / resolution,
      2 * scale * basisY[0] / resolution,
      2 * scale * basisY[1] / resolution,
      width / 2 - scale * basisX[0] - scale * basisY[0] + scale * basisZ[0] * z,
      height / 2 - scale * basisX[1] - scale * basisY[1] + scale * basisZ[1] * z,
    );
    context.drawImage(texture, 0, 0);
    context.restore();
  }
  drawAxis(context, width, height, 1.18, 0, 0, "#7da5ff", "x");
  drawAxis(context, width, height, 0, 1.18, 0, "#65d2c7", "y");
  drawAxis(context, width, height, 0, 0, 1.18, "#ffad74", "z");
  context.fillStyle = "rgba(255,255,255,.92)";
  context.font = "800 22px 'Times New Roman', Times, serif";
  context.fillText(stateLabel(state), 24, 36);
  context.fillStyle = "rgba(220,232,245,.8)";
  context.font = "500 15px 'Times New Roman', Times, serif";
  context.fillText(`${display.sliceCount} planes · cutoff ${display.threshold.toFixed(2)} · axes in n²a`, 24, 60);
}

function renderOrthogonal(data, display) {
  for (const planeData of data.planes) {
    const canvas = elements[`slice-${planeData.plane}`];
    const context = canvas.getContext("2d");
    const texture = densityTexture(planeData.values, data.resolution, data.maximum, display.threshold, 1, false, true);
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(texture, 0, 0, canvas.width, canvas.height);
    context.strokeStyle = "rgba(255,255,255,.72)";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(canvas.width / 2, 0);
    context.lineTo(canvas.width / 2, canvas.height);
    context.moveTo(0, canvas.height / 2);
    context.lineTo(canvas.width, canvas.height / 2);
    context.stroke();
  }
}

function svgElement(name, attributes = {}, text = "") {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  if (text) element.textContent = text;
  return element;
}

function renderRadial(state) {
  const svg = elements["radial-chart"];
  const width = 760;
  const height = 420;
  const margin = { left: 70, right: 24, top: 25, bottom: 58 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const extent = 6.2;
  const profile = radialProfile(state, { extent, samples: 501 });
  const maximum = Math.max(...profile.map((point) => point.probabilityPerScaledRadius));
  const x = (value) => margin.left + plotWidth * value / extent;
  const y = (value) => margin.top + plotHeight * (1 - value / (1.08 * maximum));
  const retainedTitle = svg.querySelector("title")?.cloneNode(true);
  const retainedDescription = svg.querySelector("desc")?.cloneNode(true);
  svg.replaceChildren();
  if (retainedTitle) svg.append(retainedTitle);
  if (retainedDescription) svg.append(retainedDescription);
  const grid = svgElement("g", { class: "chart-grid", "aria-hidden": "true" });
  for (let index = 0; index <= 5; index += 1) {
    const xValue = extent * index / 5;
    grid.append(svgElement("line", { x1: x(xValue), y1: margin.top, x2: x(xValue), y2: height - margin.bottom }));
  }
  for (let index = 0; index <= 4; index += 1) {
    const yValue = 1.08 * maximum * index / 4;
    grid.append(svgElement("line", { x1: margin.left, y1: y(yValue), x2: width - margin.right, y2: y(yValue) }));
  }
  svg.append(grid);
  const axes = svgElement("g", { class: "chart-axis", "aria-hidden": "true" });
  axes.append(svgElement("line", { x1: margin.left, y1: margin.top, x2: margin.left, y2: height - margin.bottom }));
  axes.append(svgElement("line", { x1: margin.left, y1: height - margin.bottom, x2: width - margin.right, y2: height - margin.bottom }));
  for (let index = 0; index <= 5; index += 1) {
    const value = extent * index / 5;
    axes.append(svgElement("text", { x: x(value), y: height - margin.bottom + 25, "text-anchor": "middle" }, value.toFixed(1)));
  }
  for (let index = 0; index <= 4; index += 1) {
    const value = 1.08 * maximum * index / 4;
    axes.append(svgElement("text", { x: margin.left - 12, y: y(value) + 5, "text-anchor": "end" }, value.toFixed(2)));
  }
  axes.append(svgElement("text", { x: margin.left + plotWidth / 2, y: height - 12, "text-anchor": "middle" }, "scaled radius, r/(n²a)"));
  axes.append(svgElement("text", { transform: `translate(18 ${margin.top + plotHeight / 2}) rotate(-90)`, "text-anchor": "middle" }, "probability per d[r/(n²a)]"));
  svg.append(axes);
  const path = profile.map((point, index) => `${index === 0 ? "M" : "L"} ${x(point.scaledRadius).toFixed(2)} ${y(point.probabilityPerScaledRadius).toFixed(2)}`).join(" ");
  svg.append(svgElement("path", { class: "radial-curve", d: path }));

  const nodePositions = [];
  let previousRadius = 0.001;
  let previous = scaledRadialWavefunction(state, state.n ** 2 * previousRadius);
  for (let index = 1; index <= 3000 && nodePositions.length < state.n - state.l - 1; index += 1) {
    const radius = extent * index / 3000;
    const current = scaledRadialWavefunction(state, state.n ** 2 * radius);
    if (previous * current < 0) nodePositions.push((previousRadius + radius) / 2);
    previousRadius = radius;
    previous = current;
  }
  for (const position of nodePositions) {
    svg.append(svgElement("line", { class: "node-line", x1: x(position), y1: margin.top, x2: x(position), y2: height - margin.bottom }));
  }
  const peak = profile.reduce((best, point) => point.probabilityPerScaledRadius > best.probabilityPerScaledRadius ? point : best);
  svg.append(svgElement("circle", { class: "chart-marker", cx: x(peak.scaledRadius), cy: y(peak.probabilityPerScaledRadius), r: 6 }));
}

function renderEverything() {
  renderFrame = 0;
  const state = currentState();
  const display = currentDisplay();
  syncPreset(state);
  updateOutputs(state, display);
  const stackKey = `${state.n}/${state.l}/${state.m}/${state.Z}/${state.A}/${display.extent}/${display.sliceCount}`;
  if (!stackCache || stackCache.key !== stackKey) {
    stackCache = { key: stackKey, data: sampleSliceStack(state, { extent: display.extent, resolution: 61, sliceCount: display.sliceCount }) };
  }
  const orthogonalKey = `${state.n}/${state.l}/${state.m}/${state.Z}/${state.A}/${display.extent}`;
  if (!orthogonalCache || orthogonalCache.key !== orthogonalKey) {
    orthogonalCache = { key: orthogonalKey, data: sampleOrthogonalSlices(state, { extent: display.extent, resolution: 81 }) };
  }
  renderGlass(stackCache.data, display, state);
  renderOrthogonal(orthogonalCache.data, display);
  renderRadial(state);
  elements["live-status"].textContent = `${stateLabel(state)} selected. Energy ${stateSummary(state).energyEv.toFixed(6)} electronvolts. ${display.sliceCount} slices at cutoff ${display.threshold.toFixed(2)}.`;
}

function scheduleRender() {
  if (renderFrame) cancelAnimationFrame(renderFrame);
  renderFrame = requestAnimationFrame(renderEverything);
}

function rerenderCamera() {
  if (stackCache) renderGlass(stackCache.data, currentDisplay(), currentState());
}

function resetAll() {
  elements["z-select"].value = "1";
  elements["n-select"].value = "3";
  updateAngularControls(2, 0);
  elements["extent-range"].value = "3.2";
  elements["slice-range"].value = "17";
  elements["threshold-range"].value = "0.15";
  elements["opacity-range"].value = "0.72";
  camera.yaw = -0.82;
  camera.pitch = 0.43;
  camera.zoom = 1;
  stackCache = null;
  orthogonalCache = null;
  scheduleRender();
}

function wireEvents() {
  elements["n-select"].addEventListener("change", () => { updateAngularControls(); stackCache = null; orthogonalCache = null; scheduleRender(); });
  elements["l-select"].addEventListener("change", () => { updateAngularControls(Number(elements["l-select"].value), 0); stackCache = null; orthogonalCache = null; scheduleRender(); });
  for (const id of ["z-select", "m-select"]) elements[id].addEventListener("change", () => { stackCache = null; orthogonalCache = null; scheduleRender(); });
  elements["gallery-preset"].addEventListener("change", () => {
    if (!elements["gallery-preset"].value) return;
    const [n, l, m] = elements["gallery-preset"].value.split(",").map(Number);
    elements["z-select"].value = "1";
    elements["n-select"].value = String(n);
    updateAngularControls(l, m);
    stackCache = null;
    orthogonalCache = null;
    scheduleRender();
  });
  for (const id of ["extent-range", "slice-range"]) elements[id].addEventListener("input", () => { stackCache = null; orthogonalCache = null; scheduleRender(); });
  for (const id of ["threshold-range", "opacity-range"]) elements[id].addEventListener("input", scheduleRender);
  elements["reset-all"].addEventListener("click", resetAll);

  const orbit = (delta) => { camera.yaw += delta; rerenderCamera(); };
  const zoom = (factor) => { camera.zoom = Math.max(0.62, Math.min(1.65, camera.zoom * factor)); rerenderCamera(); };
  elements["orbit-left"].addEventListener("click", () => orbit(-0.16));
  elements["orbit-right"].addEventListener("click", () => orbit(0.16));
  elements["zoom-out"].addEventListener("click", () => zoom(0.88));
  elements["zoom-in"].addEventListener("click", () => zoom(1.14));
  elements["reset-camera"].addEventListener("click", () => { camera.yaw = -0.82; camera.pitch = 0.43; camera.zoom = 1; rerenderCamera(); });

  const canvas = elements["glass-canvas"];
  canvas.addEventListener("pointerdown", (event) => { dragging = true; pointer = { x: event.clientX, y: event.clientY }; canvas.setPointerCapture(event.pointerId); });
  canvas.addEventListener("pointermove", (event) => {
    if (!dragging) return;
    camera.yaw += (event.clientX - pointer.x) * 0.008;
    camera.pitch = Math.max(-1.05, Math.min(1.05, camera.pitch + (event.clientY - pointer.y) * 0.006));
    pointer = { x: event.clientX, y: event.clientY };
    rerenderCamera();
  });
  canvas.addEventListener("pointerup", (event) => { dragging = false; canvas.releasePointerCapture(event.pointerId); });
  canvas.addEventListener("pointercancel", () => { dragging = false; });
  canvas.addEventListener("wheel", (event) => { event.preventDefault(); zoom(event.deltaY > 0 ? 0.92 : 1.08); }, { passive: false });
  canvas.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); orbit(event.key === "ArrowLeft" ? -0.12 : 0.12); }
    if (event.key === "ArrowUp" || event.key === "ArrowDown") { event.preventDefault(); camera.pitch = Math.max(-1.05, Math.min(1.05, camera.pitch + (event.key === "ArrowUp" ? -0.1 : 0.1))); rerenderCamera(); }
    if (event.key === "+" || event.key === "=") { event.preventDefault(); zoom(1.1); }
    if (event.key === "-") { event.preventDefault(); zoom(0.9); }
  });
}

populateStaticControls();
wireEvents();
renderEverything();
