const canvas = document.querySelector("#walk-canvas");
const context = canvas.getContext("2d");
const stepsInput = document.querySelector("#step-count");
const stepsNumberInput = document.querySelector("#step-count-number");
const sizeInput = document.querySelector("#step-size");
const sizeNumberInput = document.querySelector("#step-size-number");
const speedInput = document.querySelector("#walk-speed");
const speedNumberInput = document.querySelector("#walk-speed-number");
const seedInput = document.querySelector("#walk-seed");
const playButton = document.querySelector("[data-play]");
const playLabel = playButton.querySelector("span");
const playIcon = playButton.querySelector("path");
const resetButton = document.querySelector("[data-reset]");
const newSeedButton = document.querySelector("[data-new-seed]");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const MAX_EXACT_STEPS = 1_000_000;
const MAX_PLOT_POINTS = 10_000;
const PATH_PALETTE = [
  [0, 120, 48, 34],
  [0.22, 142, 55, 39],
  [0.46, 164, 67, 47],
  [0.7, 183, 91, 70],
  [1, 198, 122, 103],
];

const outputs = {
  modeWarning: document.querySelector("[data-mode-warning]"),
  currentStep: document.querySelector("[data-current-step]"),
  displacement: document.querySelector("[data-displacement]"),
  rms: document.querySelector("[data-rms]"),
  ratio: document.querySelector("[data-ratio]"),
  progress: document.querySelector("[data-progress-bar]"),
};

function magnitudeValue(input) {
  return 10 ** Number(input.value);
}

const state = {
  xPositions: new Float64Array(0),
  yPositions: new Float64Array(0),
  stepAtPoint: new Float64Array(0),
  minX: new Float64Array(0),
  maxX: new Float64Array(0),
  minY: new Float64Array(0),
  maxY: new Float64Array(0),
  nSteps: Number(stepsNumberInput.value),
  stepSize: Number(sizeNumberInput.value),
  speed: Number(speedNumberInput.value),
  seed: Number(seedInput.value),
  pointCount: 0,
  blockSize: 1,
  mode: "exact",
  currentStep: 0,
  playing: false,
  lastTime: performance.now(),
  stepAccumulator: 0,
  cameraX: 0,
  cameraY: 0,
  scale: 1,
  resetCamera: true,
};

function mulberry32(seed) {
  let value = seed >>> 0;
  return function random() {
    value += 0x6d2b79f5;
    let result = value;
    result = Math.imul(result ^ (result >>> 15), result | 1);
    result ^= result + Math.imul(result ^ (result >>> 7), result | 61);
    return ((result ^ (result >>> 14)) >>> 0) / 4294967296;
  };
}

function normalPair(random) {
  const u = Math.max(random(), Number.EPSILON);
  const v = random();
  const magnitude = Math.sqrt(-2 * Math.log(u));
  const phase = 2 * Math.PI * v;
  return [magnitude * Math.cos(phase), magnitude * Math.sin(phase)];
}

function validSeed(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return 2026;
  return Math.min(4294967295, Math.max(0, Math.trunc(parsed)));
}

function clampedNumber(input, fallback) {
  const value = Number(input.value);
  if (!Number.isFinite(value)) return fallback;
  return Math.min(Number(input.max), Math.max(Number(input.min), value));
}

function createStorage(pointCount) {
  return {
    x: new Float64Array(pointCount + 1),
    y: new Float64Array(pointCount + 1),
    steps: new Float64Array(pointCount + 1),
  };
}

function buildExactWalk(random) {
  const blockSize = Math.max(1, Math.ceil(state.nSteps / MAX_PLOT_POINTS));
  const pointCount = Math.ceil(state.nSteps / blockSize);
  const storage = createStorage(pointCount);
  let point = 0;
  let x = 0;
  let y = 0;

  for (let step = 1; step <= state.nSteps; step += 1) {
    const theta = random() * Math.PI * 2;
    x += state.stepSize * Math.cos(theta);
    y += state.stepSize * Math.sin(theta);

    if (step % blockSize === 0 || step === state.nSteps) {
      point += 1;
      storage.x[point] = x;
      storage.y[point] = y;
      storage.steps[point] = step;
    }
  }

  return { ...storage, pointCount: point, blockSize, mode: "exact" };
}

function buildMultiscaleWalk(random) {
  const blockSize = Math.ceil(state.nSteps / MAX_PLOT_POINTS);
  const pointCount = Math.ceil(state.nSteps / blockSize);
  const storage = createStorage(pointCount);
  let completedSteps = 0;
  let x = 0;
  let y = 0;

  for (let point = 1; point <= pointCount; point += 1) {
    const microscopicSteps = Math.min(blockSize, state.nSteps - completedSteps);
    const sigma = state.stepSize * Math.sqrt(microscopicSteps / 2);
    const [normalX, normalY] = normalPair(random);
    x += sigma * normalX;
    y += sigma * normalY;
    completedSteps += microscopicSteps;
    storage.x[point] = x;
    storage.y[point] = y;
    storage.steps[point] = completedSteps;
  }

  return { ...storage, pointCount, blockSize, mode: "multiscale" };
}

function buildPrefixBounds() {
  const length = state.pointCount + 1;
  state.minX = new Float64Array(length);
  state.maxX = new Float64Array(length);
  state.minY = new Float64Array(length);
  state.maxY = new Float64Array(length);

  for (let index = 1; index < length; index += 1) {
    state.minX[index] = Math.min(state.minX[index - 1], state.xPositions[index]);
    state.maxX[index] = Math.max(state.maxX[index - 1], state.xPositions[index]);
    state.minY[index] = Math.min(state.minY[index - 1], state.yPositions[index]);
    state.maxY[index] = Math.max(state.maxY[index - 1], state.yPositions[index]);
  }
}

function buildWalk() {
  state.nSteps = Math.round(clampedNumber(stepsNumberInput, 1_000_000));
  state.stepSize = clampedNumber(sizeNumberInput, 1);
  state.speed = Math.round(clampedNumber(speedNumberInput, 1_000_000));
  stepsNumberInput.value = String(state.nSteps);
  sizeNumberInput.value = String(state.stepSize);
  speedNumberInput.value = String(state.speed);
  state.seed = validSeed(seedInput.value);
  seedInput.value = String(state.seed);

  const random = mulberry32(state.seed);
  const result =
    state.nSteps <= MAX_EXACT_STEPS
      ? buildExactWalk(random)
      : buildMultiscaleWalk(random);

  state.xPositions = result.x;
  state.yPositions = result.y;
  state.stepAtPoint = result.steps;
  state.pointCount = result.pointCount;
  state.blockSize = result.blockSize;
  state.mode = result.mode;
  buildPrefixBounds();

  state.currentStep = 0;
  state.stepAccumulator = 0;
  state.playing = false;
  state.lastTime = performance.now();
  state.resetCamera = true;
  updateControlLabels();
  updatePlayButton();
  updateResults();
  draw();
}

function updateControlLabels() {
  outputs.modeWarning.hidden = state.mode === "exact";
  stepsInput.value = String(Math.log10(state.nSteps));
  sizeInput.value = String(Math.min(Number(sizeInput.max), state.stepSize));
  speedInput.value = String(Math.log10(state.speed));
  stepsInput.setAttribute(
    "aria-valuetext",
    `${state.nSteps.toLocaleString()} steps`,
  );
  speedInput.setAttribute(
    "aria-valuetext",
    `${state.speed.toLocaleString()} steps per second`,
  );
  updateRangeFill(stepsInput);
  updateRangeFill(sizeInput);
  updateRangeFill(speedInput);
}

function updateRangeFill(input) {
  const minimum = Number(input.min);
  const maximum = Number(input.max);
  const value = Number(input.value);
  const percentage = ((value - minimum) / (maximum - minimum)) * 100;
  input.style.setProperty("--range-fill", `${percentage}%`);
}

function updatePlayButton() {
  if (state.playing) {
    playLabel.textContent = "Pause";
    playIcon.setAttribute("d", "M7 5h4v14H7zM13 5h4v14h-4z");
  } else if (state.currentStep >= state.nSteps) {
    playLabel.textContent = "Run again";
    playIcon.setAttribute("d", "M8 5l11 7-11 7z");
  } else {
    playLabel.textContent = state.currentStep > 0 ? "Continue" : "Run walk";
    playIcon.setAttribute("d", "M8 5l11 7-11 7z");
  }
}

function pointIndexForStep(step) {
  if (step >= state.nSteps) return state.pointCount;
  return Math.min(state.pointCount, Math.floor(step / state.blockSize));
}

function updateResults() {
  const point = pointIndexForStep(state.currentStep);
  const displacement = Math.hypot(
    state.xPositions[point] || 0,
    state.yPositions[point] || 0,
  );
  const rms = state.stepSize * Math.sqrt(state.currentStep);
  const ratio = rms > 0 ? displacement / rms : null;
  outputs.currentStep.textContent =
    `${Math.round(state.currentStep).toLocaleString()} / ${state.nSteps.toLocaleString()}`;
  outputs.displacement.textContent = displacement.toFixed(2);
  outputs.rms.textContent = rms.toFixed(2);
  outputs.ratio.textContent = ratio === null ? "—" : ratio.toFixed(3);
  outputs.progress.style.width = `${(state.currentStep / state.nSteps) * 100}%`;
}

function resizeCanvas() {
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(canvas.clientWidth * pixelRatio));
  const height = Math.max(1, Math.round(canvas.clientHeight * pixelRatio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  state.resetCamera = true;
  draw();
}

function visibleBounds() {
  const padding = 68;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const point = pointIndexForStep(state.currentStep);
  const rms = state.stepSize * Math.sqrt(Math.max(state.currentStep, 1));
  const minimumSpan = state.stepSize * 16;
  const minX = Math.min(state.minX[point], -rms, -minimumSpan / 2);
  const maxX = Math.max(state.maxX[point], rms, minimumSpan / 2);
  const minY = Math.min(state.minY[point], -rms, -minimumSpan / 2);
  const maxY = Math.max(state.maxY[point], rms, minimumSpan / 2);
  const targetX = (minX + maxX) / 2;
  const targetY = (minY + maxY) / 2;
  const targetScale = Math.max(
    0.00001,
    Math.min(
      (width - padding * 2) / Math.max(maxX - minX, minimumSpan),
      (height - padding * 2) / Math.max(maxY - minY, minimumSpan),
    ),
  );

  state.cameraX = targetX;
  state.cameraY = targetY;
  state.scale = targetScale;
  state.resetCamera = false;

  return {
    width,
    height,
    cameraX: state.cameraX,
    cameraY: state.cameraY,
    scale: state.scale,
  };
}

function worldToScreen(x, y, bounds) {
  return {
    x: bounds.width / 2 + (x - bounds.cameraX) * bounds.scale,
    y: bounds.height / 2 - (y - bounds.cameraY) * bounds.scale,
  };
}

function niceGridStep(rawStep) {
  const exponent = 10 ** Math.floor(Math.log10(Math.max(rawStep, Number.EPSILON)));
  const fraction = rawStep / exponent;
  const niceFraction =
    fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
  return niceFraction * exponent;
}

function formatGridValue(value, step) {
  if (Math.abs(value) < step * 0.001) return "0";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(absolute >= 10_000_000 ? 0 : 1)}m`;
  }
  if (absolute >= 1_000) {
    return `${(value / 1_000).toFixed(absolute >= 10_000 ? 0 : 1)}k`;
  }
  const decimals = step < 1 ? Math.min(3, Math.ceil(-Math.log10(step))) : 0;
  return value.toFixed(decimals).replace("-", "−");
}

function drawGrid(bounds) {
  const worldLeft = bounds.cameraX - bounds.width / (2 * bounds.scale);
  const worldRight = bounds.cameraX + bounds.width / (2 * bounds.scale);
  const worldBottom = bounds.cameraY - bounds.height / (2 * bounds.scale);
  const worldTop = bounds.cameraY + bounds.height / (2 * bounds.scale);
  const gridStep = niceGridStep(86 / bounds.scale);
  const xStart = Math.ceil(worldLeft / gridStep) * gridStep;
  const yStart = Math.ceil(worldBottom / gridStep) * gridStep;

  context.save();
  context.lineWidth = 1;
  context.font = '10px "Times New Roman", Times, serif';
  context.textBaseline = "middle";

  for (let x = xStart; x <= worldRight; x += gridStep) {
    const screen = worldToScreen(x, 0, bounds);
    const isAxis = Math.abs(x) < gridStep * 0.001;
    context.strokeStyle = isAxis
      ? "rgba(55, 50, 42, 0.24)"
      : "rgba(55, 50, 42, 0.065)";
    context.beginPath();
    context.moveTo(screen.x, 0);
    context.lineTo(screen.x, bounds.height);
    context.stroke();
    context.fillStyle = "rgba(70, 64, 55, 0.68)";
    context.textAlign = "center";
    context.fillText(formatGridValue(x, gridStep), screen.x, bounds.height - 15);
  }

  for (let y = yStart; y <= worldTop; y += gridStep) {
    const screen = worldToScreen(0, y, bounds);
    const isAxis = Math.abs(y) < gridStep * 0.001;
    context.strokeStyle = isAxis
      ? "rgba(55, 50, 42, 0.24)"
      : "rgba(55, 50, 42, 0.065)";
    context.beginPath();
    context.moveTo(0, screen.y);
    context.lineTo(bounds.width, screen.y);
    context.stroke();
    context.fillStyle = "rgba(70, 64, 55, 0.68)";
    context.textAlign = "left";
    context.fillText(formatGridValue(y, gridStep), 10, screen.y);
  }

  context.fillStyle = "rgba(54, 49, 41, 0.76)";
  context.font = 'italic 17px "Times New Roman", Times, serif';
  context.textAlign = "right";
  context.fillText("x", bounds.width - 12, bounds.height - 34);
  context.textAlign = "left";
  context.fillText("y", 12, 18);
  context.restore();
}

function drawRmsCircle(bounds) {
  const rms = state.stepSize * Math.sqrt(Math.max(state.currentStep, 1));
  const origin = worldToScreen(0, 0, bounds);
  context.save();
  context.setLineDash([6, 9]);
  context.lineDashOffset = -(performance.now() * 0.012) % 15;
  context.lineWidth = 1.25;
  context.strokeStyle = "rgba(164, 67, 47, 0.68)";
  context.beginPath();
  context.arc(origin.x, origin.y, rms * bounds.scale, 0, Math.PI * 2);
  context.stroke();
  context.restore();
}

function screenPoint(index, bounds) {
  return worldToScreen(
    state.xPositions[index],
    state.yPositions[index],
    bounds,
  );
}

function smoothstep(value) {
  return value * value * (3 - 2 * value);
}

function pathColour(progress, alpha = 1) {
  const value = Math.min(1, Math.max(0, progress));
  let upperIndex = 1;

  while (
    upperIndex < PATH_PALETTE.length - 1 &&
    value > PATH_PALETTE[upperIndex][0]
  ) {
    upperIndex += 1;
  }

  const lower = PATH_PALETTE[upperIndex - 1];
  const upper = PATH_PALETTE[upperIndex];
  const span = Math.max(Number.EPSILON, upper[0] - lower[0]);
  const blend = smoothstep((value - lower[0]) / span);
  const red = Math.round(lower[1] + (upper[1] - lower[1]) * blend);
  const green = Math.round(lower[2] + (upper[2] - lower[2]) * blend);
  const blue = Math.round(lower[3] + (upper[3] - lower[3]) * blend);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function drawPath(bounds) {
  const currentPoint = pointIndexForStep(state.currentStep);
  if (currentPoint < 1) return;
  context.save();
  context.lineCap = "round";
  context.lineJoin = "round";
  const colourBands = Math.min(120, currentPoint);
  const pointsPerBand = Math.ceil(currentPoint / colourBands);

  for (let band = 0; band < colourBands; band += 1) {
    const startIndex = band * pointsPerBand;
    const endIndex = Math.min(currentPoint, (band + 1) * pointsPerBand);
    if (endIndex <= startIndex) continue;

    const path = new Path2D();
    const start = screenPoint(startIndex, bounds);
    path.moveTo(start.x, start.y);
    for (let index = startIndex + 1; index <= endIndex; index += 1) {
      const point = screenPoint(index, bounds);
      path.lineTo(point.x, point.y);
    }

    const midpoint = Math.floor((startIndex + endIndex) / 2);
    const progress = state.stepAtPoint[midpoint] / state.nSteps;
    context.strokeStyle = pathColour(progress, 0.12);
    context.lineWidth = 4.8;
    context.stroke(path);
    context.strokeStyle = pathColour(progress, 0.96);
    context.lineWidth = 1.6;
    context.stroke(path);
  }
  context.restore();
}

function drawMarkers(bounds) {
  const currentPoint = pointIndexForStep(state.currentStep);
  const start = worldToScreen(0, 0, bounds);
  const finish = screenPoint(currentPoint, bounds);

  context.save();
  context.fillStyle = "#1b1b18";
  context.beginPath();
  context.arc(start.x, start.y, 4.5, 0, Math.PI * 2);
  context.fill();

  if (currentPoint > 0) {
    const progress = state.currentStep / state.nSteps;
    const endpointColour = pathColour(progress);
    const pulse = 9 + Math.sin(performance.now() * 0.006) * 1.2;
    context.strokeStyle = pathColour(progress, 0.42);
    context.lineWidth = 1;
    context.beginPath();
    context.arc(finish.x, finish.y, pulse, 0, Math.PI * 2);
    context.stroke();
    context.fillStyle = endpointColour;
    context.beginPath();
    context.arc(finish.x, finish.y, 5.5, 0, Math.PI * 2);
    context.fill();
  }
  context.restore();
}

function draw() {
  if (!canvas.width || !canvas.height || state.xPositions.length === 0) return;
  const bounds = visibleBounds();
  context.clearRect(0, 0, bounds.width, bounds.height);

  const gradient = context.createRadialGradient(
    bounds.width / 2,
    bounds.height / 2,
    0,
    bounds.width / 2,
    bounds.height / 2,
    Math.max(bounds.width, bounds.height) * 0.72,
  );
  gradient.addColorStop(0, "rgba(182, 152, 93, 0.055)");
  gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, bounds.width, bounds.height);

  drawGrid(bounds);
  drawRmsCircle(bounds);
  drawPath(bounds);
  drawMarkers(bounds);
}

function animate(now) {
  const delta = Math.min((now - state.lastTime) / 1000, 0.5);
  state.lastTime = now;

  if (state.playing) {
    state.stepAccumulator += delta * state.speed;
    const advance = Math.max(1, Math.floor(state.stepAccumulator));
    if (state.stepAccumulator >= 1) state.stepAccumulator -= advance;
    state.currentStep = Math.min(state.nSteps, state.currentStep + advance);
    if (state.currentStep >= state.nSteps) {
      state.playing = false;
      updatePlayButton();
    }
    updateResults();
  }

  draw();
  requestAnimationFrame(animate);
}

function restartWithCurrentParameters({ autoplay = false } = {}) {
  buildWalk();
  if (autoplay && !reduceMotion.matches) {
    state.playing = true;
    updatePlayButton();
  }
}

playButton.addEventListener("click", () => {
  if (state.currentStep >= state.nSteps) {
    state.currentStep = 0;
    state.resetCamera = true;
  }
  state.playing = !state.playing;
  state.lastTime = performance.now();
  updatePlayButton();
  updateResults();
});

resetButton.addEventListener("click", () => {
  state.currentStep = 0;
  state.playing = false;
  state.stepAccumulator = 0;
  state.resetCamera = true;
  updatePlayButton();
  updateResults();
  draw();
});

newSeedButton.addEventListener("click", () => {
  const randomSeed = crypto.getRandomValues(new Uint32Array(1))[0];
  seedInput.value = String(randomSeed);
  restartWithCurrentParameters({ autoplay: true });
});

stepsInput.addEventListener("input", () => {
  const value = magnitudeValue(stepsInput);
  stepsNumberInput.value = String(Math.round(value));
  stepsInput.setAttribute("aria-valuetext", `${value.toLocaleString()} steps`);
  updateRangeFill(stepsInput);
});
stepsInput.addEventListener("change", () => restartWithCurrentParameters());
stepsNumberInput.addEventListener("change", () => {
  const value = Math.round(clampedNumber(stepsNumberInput, 1_000_000));
  stepsNumberInput.value = String(value);
  stepsInput.value = String(Math.log10(value));
  restartWithCurrentParameters();
});

sizeInput.addEventListener("input", () => {
  sizeNumberInput.value = Number(sizeInput.value).toFixed(2);
  updateRangeFill(sizeInput);
});
sizeInput.addEventListener("change", () => restartWithCurrentParameters());
sizeNumberInput.addEventListener("change", () => {
  const value = clampedNumber(sizeNumberInput, 1);
  sizeNumberInput.value = String(value);
  sizeInput.value = String(Math.min(Number(sizeInput.max), value));
  restartWithCurrentParameters();
});

speedInput.addEventListener("input", () => {
  state.speed = magnitudeValue(speedInput);
  speedNumberInput.value = String(Math.round(state.speed));
  speedInput.setAttribute(
    "aria-valuetext",
    `${state.speed.toLocaleString()} steps per second`,
  );
  updateRangeFill(speedInput);
});
speedNumberInput.addEventListener("change", () => {
  const value = Math.round(clampedNumber(speedNumberInput, 1_000_000));
  speedNumberInput.value = String(value);
  speedInput.value = String(Math.log10(value));
  state.speed = value;
  updateRangeFill(speedInput);
});

seedInput.addEventListener("change", () => restartWithCurrentParameters());
window.addEventListener("resize", resizeCanvas);
new ResizeObserver(resizeCanvas).observe(canvas);

buildWalk();
resizeCanvas();
requestAnimationFrame(animate);

if (document.fonts) {
  document.fonts.ready.then(resizeCanvas);
}
