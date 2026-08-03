const tasks = [
  {
    id: "01",
    title: "Random walk",
    kicker: "Stochastic motion",
    summary:
      "Follow independent fixed-length steps and watch ensemble statistics emerge from individual uncertainty.",
    equation: "xₙ = Σ s cos θᵢ,   yₙ = Σ s sin θᵢ",
    parameter: "N = 240",
    stageLabel: "Ensemble trajectories / endpoint spread",
    instruction: "Move across the field to bias the viewing origin; the steps remain random.",
    docs: "../task01_random_walk/README.md",
    accent: "#41ecff",
    accentRgb: "65, 236, 255",
  },
  {
    id: "02",
    title: "Brownian motion",
    kicker: "Emergent statistics",
    summary:
      "Resolve a visible tracer buffeted by many smaller thermal particles inside a bounded two-dimensional chamber.",
    equation: "⟨r²(t)⟩ = 4Dt",
    parameter: "D = 0.42",
    stageLabel: "Thermal bath / tracer displacement",
    instruction: "Move near the tracer to disturb the local thermal bath.",
    docs: "../task02_brownian_motion/README.md",
    accent: "#ff4f91",
    accentRgb: "255, 79, 145",
  },
  {
    id: "03",
    title: "Thermal radiation",
    kicker: "Planck–Einstein",
    summary:
      "Compare black-body spectra as temperature shifts the peak and changes the total emitted power.",
    equation: "Bλ(T) = 2hc² / [λ⁵(eʰᶜ⁄λᵏᵀ − 1)]",
    parameter: "T = 5800 K",
    stageLabel: "Spectral radiance / wavelength",
    instruction: "Move horizontally to sweep the highlighted wavelength across the spectrum.",
    docs: "../task03_thermal_radiation/README.md",
    accent: "#ffb938",
    accentRgb: "255, 185, 56",
  },
  {
    id: "04",
    title: "Photoelectric effect",
    kicker: "Photon energy",
    summary:
      "Visualise photons striking a metal surface and electrons escaping only above the threshold frequency.",
    equation: "Kₘₐₓ = hf − φ",
    parameter: "f/f₀ = 1.35",
    stageLabel: "Photon incidence / electron emission",
    instruction: "Move vertically to vary the photon frequency relative to the threshold.",
    docs: "../task04_photoelectric_effect/README.md",
    accent: "#8b6cff",
    accentRgb: "139, 108, 255",
  },
  {
    id: "05",
    title: "Hydrogen spectrum",
    kicker: "Quantised transitions",
    summary:
      "Connect discrete hydrogen energy levels to emitted photons and their visible spectral lines.",
    equation: "1/λ = R∞(1/n₁² − 1/n₂²)",
    parameter: "n₂ → n₁",
    stageLabel: "Energy levels / spectral emission",
    instruction: "Move vertically to select the upper state and trigger a new transition.",
    docs: "../task05_hydrogen_spectrum/README.md",
    accent: "#35e6a3",
    accentRgb: "53, 230, 163",
  },
  {
    id: "06",
    title: "Electron diffraction",
    kicker: "Matter waves",
    summary:
      "Observe concentric diffraction rings and the inverse relationship between electron wavelength and accelerating voltage.",
    equation: "λ = h / √(2mₑeV)",
    parameter: "V = 4.5 kV",
    stageLabel: "Reciprocal lattice / ring intensity",
    instruction: "Move horizontally to change the accelerating voltage and contract the rings.",
    docs: "../task06_electron_diffraction/README.md",
    accent: "#ff695e",
    accentRgb: "255, 105, 94",
  },
  {
    id: "07",
    title: "Particle in a box",
    kicker: "Wave mechanics",
    summary:
      "Explore stationary states and a time-dependent mixture inside an infinite one-dimensional potential well.",
    equation: "ψₙ(x,t) = √(2/L) sin(nπx/L)e⁻ⁱᴱⁿᵗ/ℏ",
    parameter: "n = 3",
    stageLabel: "Probability density / ψ*ψ",
    instruction: "Move across the field to mix neighbouring eigenstates.",
    docs: "../task07_particle_in_box/README.md",
    accent: "#56a4ff",
    accentRgb: "86, 164, 255",
  },
  {
    id: "08",
    title: "Quantum cryptography",
    kicker: "Measurement",
    summary:
      "Track encoded photon states through incompatible measurement bases and reveal interception through the error rate.",
    equation: "QBER = Nₘᵢₛₘₐₜcₕ / Nₛᵢfₜₑd",
    parameter: "QBER = 0.0%",
    stageLabel: "BB84 channel / basis comparison",
    instruction: "Move vertically to introduce an intercept-resend disturbance.",
    docs: "../task08_quantum_cryptography/README.md",
    accent: "#e95dff",
    accentRgb: "233, 93, 255",
  },
  {
    id: "09",
    title: "Compton scattering",
    kicker: "Relativistic quanta",
    summary:
      "Resolve photon–electron momentum exchange as the scattering angle changes the outgoing wavelength.",
    equation: "Δλ = h/(mₑc)(1 − cos θ)",
    parameter: "θ = 90°",
    stageLabel: "Collision geometry / wavelength shift",
    instruction: "Move around the target to control the photon scattering angle.",
    docs: "../task09_compton_scattering/README.md",
    accent: "#f9e95e",
    accentRgb: "249, 233, 94",
  },
  {
    id: "10",
    title: "Hydrogenic orbitals",
    kicker: "Probability density",
    summary:
      "Rotate through nodal surfaces and probability lobes for hydrogen-like atomic states.",
    equation: "ψₙₗₘ(r,θ,φ) = Rₙₗ(r)Yₗᵐ(θ,φ)",
    parameter: "3d / m = 1",
    stageLabel: "Orbital density / nodal structure",
    instruction: "Move across the field to rotate the projected orbital.",
    docs: "../task10_hydrogenic_orbitals/README.md",
    accent: "#22d8ff",
    accentRgb: "34, 216, 255",
  },
];

const root = document.documentElement;
const body = document.body;
const canvas = document.querySelector("#simulation-canvas");
const context = canvas.getContext("2d", { alpha: false });
const taskNumber = document.querySelector("[data-task-number]");
const taskKicker = document.querySelector("[data-task-kicker]");
const taskTitle = document.querySelector("[data-task-title]");
const taskSummary = document.querySelector("[data-task-summary]");
const taskEquation = document.querySelector("[data-task-equation]");
const taskCaveat = document.querySelector("[data-task-caveat]");
const documentation = document.querySelector("[data-documentation]");
const stageLabel = document.querySelector("[data-stage-label]");
const instruction = document.querySelector("[data-instruction]");
const parameter = document.querySelector("[data-parameter]");
const timeReadout = document.querySelector("[data-time]");
const frameReadout = document.querySelector("[data-frame]");
const playToggle = document.querySelector("[data-play-toggle]");
const playLabel = document.querySelector("[data-play-label]");
const resetButton = document.querySelector("[data-reset]");
const speedInput = document.querySelector("[data-speed]");
const speedOutput = document.querySelector("[data-speed-output]");
const previousButton = document.querySelector("[data-previous]");
const nextButton = document.querySelector("[data-next]");
const drawer = document.querySelector("[data-task-drawer]");
const drawerList = document.querySelector("[data-task-list]");
const drawerToggle = document.querySelector("[data-drawer-toggle]");
const drawerClose = document.querySelector("[data-drawer-close]");
const drawerBackdrop = document.querySelector("[data-drawer-backdrop]");
const transition = document.querySelector("[data-lab-transition]");
const transitionNumber = document.querySelector("[data-lab-transition-number]");
const cursor = document.querySelector("[data-cursor]");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const coarsePointer = window.matchMedia("(pointer: coarse)");

const queryTask = Number.parseInt(new URLSearchParams(window.location.search).get("task"), 10);

const state = {
  taskIndex: Number.isFinite(queryTask)
    ? Math.min(Math.max(queryTask - 1, 0), tasks.length - 1)
    : 6,
  running: !reduceMotion.matches,
  speed: 1,
  elapsed: 0,
  frame: 0,
  lastFrame: performance.now(),
  pointer: { x: 0.5, y: 0.5 },
  pointerTarget: { x: 0.5, y: 0.5 },
  width: 0,
  height: 0,
  dpr: 1,
  walkers: [],
  particles: [],
  orbitalPoints: [],
  randomSeed: 173,
  lastStep: 0,
};

function seededRandom() {
  state.randomSeed = (state.randomSeed * 1664525 + 1013904223) >>> 0;
  return state.randomSeed / 4294967296;
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  state.dpr = Math.min(window.devicePixelRatio || 1, coarsePointer.matches ? 1 : 1.5);
  state.width = Math.max(rect.width, 1);
  state.height = Math.max(rect.height, 1);
  canvas.width = Math.round(state.width * state.dpr);
  canvas.height = Math.round(state.height * state.dpr);
  context.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
}

function background(accent, glow = 0.22) {
  const { width, height, pointer } = state;
  context.fillStyle = "#080a17";
  context.fillRect(0, 0, width, height);

  const radial = context.createRadialGradient(
    pointer.x * width,
    pointer.y * height,
    0,
    pointer.x * width,
    pointer.y * height,
    Math.max(width, height) * 0.75,
  );
  radial.addColorStop(0, `${accent}${Math.round(glow * 255).toString(16).padStart(2, "0")}`);
  radial.addColorStop(0.36, `${accent}18`);
  radial.addColorStop(1, "rgba(8,10,23,0)");
  context.fillStyle = radial;
  context.fillRect(0, 0, width, height);
}

function line(points, color, width = 1, alpha = 1) {
  if (!points.length) return;
  context.save();
  context.globalAlpha = alpha;
  context.strokeStyle = color;
  context.lineWidth = width;
  context.beginPath();
  context.moveTo(points[0][0], points[0][1]);
  for (let index = 1; index < points.length; index += 1) {
    context.lineTo(points[index][0], points[index][1]);
  }
  context.stroke();
  context.restore();
}

function glowCircle(x, y, radius, color, alpha = 1) {
  context.save();
  context.globalAlpha = alpha;
  context.shadowColor = color;
  context.shadowBlur = radius * 1.8;
  context.fillStyle = color;
  context.beginPath();
  context.arc(x, y, radius, 0, Math.PI * 2);
  context.fill();
  context.restore();
}

function wavePath(x1, y1, x2, y2, amplitude, cycles, phase, color, width = 2) {
  const points = [];
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.hypot(dx, dy);
  const normalX = length ? -dy / length : 0;
  const normalY = length ? dx / length : 1;
  for (let step = 0; step <= 100; step += 1) {
    const ratio = step / 100;
    const envelope = Math.sin(Math.PI * ratio);
    const offset = Math.sin(ratio * Math.PI * 2 * cycles + phase) * amplitude * envelope;
    points.push([
      x1 + dx * ratio + normalX * offset,
      y1 + dy * ratio + normalY * offset,
    ]);
  }
  line(points, color, width, 0.92);
}

function resetSimulation() {
  state.elapsed = 0;
  state.frame = 0;
  state.lastStep = 0;
  state.randomSeed = 173 + state.taskIndex * 991;
  state.walkers = Array.from({ length: 16 }, (_, index) => ({
    x: state.width * 0.52,
    y: state.height * 0.52,
    color: `hsl(${185 + index * 13} 95% 64%)`,
    path: [],
  }));
  state.particles = Array.from({ length: 76 }, (_, index) => ({
    x: seededRandom() * state.width,
    y: seededRandom() * state.height,
    vx: (seededRandom() - 0.5) * (index === 0 ? 22 : 80),
    vy: (seededRandom() - 0.5) * (index === 0 ? 22 : 80),
    radius: index === 0 ? 14 : 2 + seededRandom() * 2,
  }));
  state.orbitalPoints = Array.from({ length: coarsePointer.matches ? 340 : 780 }, (_, index) => {
    const angle = seededRandom() * Math.PI * 2;
    const sign = seededRandom() > 0.5 ? 1 : -1;
    const radius = Math.pow(seededRandom(), 0.55);
    const lobe = Math.abs(Math.cos(angle * 2));
    return {
      angle,
      sign,
      radius,
      lobe,
      depth: seededRandom(),
      phase: index * 0.17,
    };
  });
}

function drawRandomWalk(delta) {
  const task = tasks[0];
  background(task.accent, 0.19);
  const stepInterval = 0.032;
  state.lastStep += delta;
  while (state.lastStep > stepInterval && state.walkers[0]?.path.length < 240) {
    state.lastStep -= stepInterval;
    for (const walker of state.walkers) {
      const angle = seededRandom() * Math.PI * 2;
      walker.x += Math.cos(angle) * 7;
      walker.y += Math.sin(angle) * 7;
      walker.path.push([walker.x, walker.y]);
    }
  }

  const driftX = (state.pointer.x - 0.5) * 75;
  const driftY = (state.pointer.y - 0.5) * 75;
  context.save();
  context.translate(driftX, driftY);
  for (const walker of state.walkers) {
    line(walker.path, walker.color, 1.3, 0.46);
    glowCircle(walker.x, walker.y, 2.6, walker.color, 0.9);
  }
  context.restore();

  context.strokeStyle = "rgba(255,255,255,.28)";
  context.beginPath();
  context.arc(
    state.width * 0.52 + driftX,
    state.height * 0.52 + driftY,
    Math.sqrt(Math.max(state.walkers[0]?.path.length || 0, 1)) * 7,
    0,
    Math.PI * 2,
  );
  context.stroke();
}

function drawBrownian(delta) {
  const task = tasks[1];
  background(task.accent, 0.15);
  const { width, height } = state;
  const tracer = state.particles[0];
  const pointerX = state.pointer.x * width;
  const pointerY = state.pointer.y * height;

  for (let index = 0; index < state.particles.length; index += 1) {
    const particle = state.particles[index];
    particle.vx += (seededRandom() - 0.5) * (index === 0 ? 18 : 210) * delta;
    particle.vy += (seededRandom() - 0.5) * (index === 0 ? 18 : 210) * delta;
    const dx = particle.x - pointerX;
    const dy = particle.y - pointerY;
    const distance = Math.max(Math.hypot(dx, dy), 1);
    if (distance < 100) {
      particle.vx += (dx / distance) * (100 - distance) * delta * 2;
      particle.vy += (dy / distance) * (100 - distance) * delta * 2;
    }
    particle.vx *= 0.995;
    particle.vy *= 0.995;
    particle.x += particle.vx * delta;
    particle.y += particle.vy * delta;
    if (particle.x < particle.radius || particle.x > width - particle.radius) particle.vx *= -1;
    if (particle.y < particle.radius || particle.y > height - particle.radius) particle.vy *= -1;
    particle.x = Math.min(Math.max(particle.x, particle.radius), width - particle.radius);
    particle.y = Math.min(Math.max(particle.y, particle.radius), height - particle.radius);

    if (index > 0 && Math.hypot(particle.x - tracer.x, particle.y - tracer.y) < tracer.radius + 8) {
      tracer.vx += (tracer.x - particle.x) * delta * 2;
      tracer.vy += (tracer.y - particle.y) * delta * 2;
    }
  }

  for (let index = 1; index < state.particles.length; index += 1) {
    const particle = state.particles[index];
    glowCircle(particle.x, particle.y, particle.radius, index % 3 ? "#5cecff" : "#ff4f91", 0.58);
  }
  glowCircle(tracer.x, tracer.y, tracer.radius, "#fff4dc", 0.95);
  context.strokeStyle = task.accent;
  context.lineWidth = 1;
  context.beginPath();
  context.arc(tracer.x, tracer.y, tracer.radius + 10 + Math.sin(state.elapsed * 4) * 3, 0, Math.PI * 2);
  context.stroke();
}

function planckShape(x, temperature) {
  const scaled = Math.max(x * 8.5 / temperature, 0.02);
  return Math.pow(scaled, 3) / Math.max(Math.exp(scaled) - 1, 0.001);
}

function drawThermalRadiation() {
  const task = tasks[2];
  background(task.accent, 0.14);
  const { width, height } = state;
  const left = width * 0.09;
  const right = width * 0.92;
  const bottom = height * 0.78;
  const top = height * 0.18;
  const temperatures = [0.85, 1.05, 1.35];
  const colors = ["#ff4a8e", "#ffb938", "#f7f0d8"];

  context.strokeStyle = "rgba(255,255,255,.32)";
  context.beginPath();
  context.moveTo(left, top);
  context.lineTo(left, bottom);
  context.lineTo(right, bottom);
  context.stroke();

  temperatures.forEach((temperature, curveIndex) => {
    const raw = [];
    let maxValue = 0;
    for (let step = 0; step <= 180; step += 1) {
      const x = step / 180;
      const value = planckShape(x + 0.035, temperature);
      raw.push(value);
      maxValue = Math.max(maxValue, value);
    }
    const points = raw.map((value, step) => [
      left + (right - left) * (step / 180),
      bottom - ((value / maxValue) * (bottom - top) * (0.52 + curveIndex * 0.18)),
    ]);
    line(points, colors[curveIndex], 2.2, 0.88);
  });

  const markerX = left + (right - left) * state.pointer.x;
  context.strokeStyle = "rgba(255,255,255,.75)";
  context.setLineDash([4, 7]);
  context.beginPath();
  context.moveTo(markerX, top);
  context.lineTo(markerX, bottom);
  context.stroke();
  context.setLineDash([]);

  const spectral = context.createLinearGradient(left, 0, right, 0);
  spectral.addColorStop(0, "#682cff");
  spectral.addColorStop(0.25, "#147cff");
  spectral.addColorStop(0.48, "#24e5b5");
  spectral.addColorStop(0.68, "#ffe14f");
  spectral.addColorStop(0.84, "#ff7a32");
  spectral.addColorStop(1, "#ff315f");
  context.fillStyle = spectral;
  context.fillRect(left, bottom + 18, right - left, 5);
}

function drawPhotoelectric() {
  const task = tasks[3];
  background(task.accent, 0.17);
  const { width, height } = state;
  const plateX = width * 0.58;
  const frequencyRatio = 0.7 + (1 - state.pointer.y) * 1.25;
  const thresholdMet = frequencyRatio >= 1;
  parameter.textContent = `f/f₀ = ${frequencyRatio.toFixed(2)}`;

  const metalGradient = context.createLinearGradient(plateX, 0, plateX + 100, 0);
  metalGradient.addColorStop(0, "rgba(255,255,255,.72)");
  metalGradient.addColorStop(1, "rgba(99,108,150,.22)");
  context.fillStyle = metalGradient;
  context.fillRect(plateX, height * 0.12, 62, height * 0.76);

  for (let index = 0; index < 7; index += 1) {
    const y = height * (0.2 + index * 0.1);
    const travel = (state.elapsed * (90 + frequencyRatio * 50) + index * 93) % (plateX - 45);
    wavePath(20 + travel - 140, y, 20 + travel, y, 7, 4 + frequencyRatio * 2, state.elapsed * 3, task.accent, 1.5);
    glowCircle(20 + travel, y, 3, "#f2e9ff", 0.9);

    if (thresholdMet) {
      const electronProgress = Math.max(0, Math.min((travel - (plateX - 80)) / 90, 1));
      const eX = plateX + electronProgress * (width - plateX - 90);
      const eY = y - electronProgress * (35 + index * 7);
      if (electronProgress > 0) glowCircle(eX, eY, 4, "#41ecff", 0.9);
    }
  }

  context.fillStyle = thresholdMet ? "#35e6a3" : "#ff695e";
  context.font = '10px "DM Mono"';
  context.fillText(thresholdMet ? "EMISSION ALLOWED" : "BELOW THRESHOLD", plateX + 82, height * 0.16);
}

function drawHydrogenSpectrum() {
  const task = tasks[4];
  background(task.accent, 0.14);
  const { width, height } = state;
  const left = width * 0.08;
  const centre = width * 0.48;
  const top = height * 0.16;
  const bottom = height * 0.82;
  const upperN = Math.max(3, Math.min(6, Math.round(3 + (1 - state.pointer.y) * 3)));
  const lowerN = 2;
  parameter.textContent = `n = ${upperN} → ${lowerN}`;

  const levelY = (n) => bottom - (1 - 1 / (n * n)) * (bottom - top);
  for (let n = 1; n <= 6; n += 1) {
    const y = levelY(n);
    context.strokeStyle = n === upperN || n === lowerN ? task.accent : "rgba(255,255,255,.2)";
    context.lineWidth = n === upperN || n === lowerN ? 2 : 1;
    context.beginPath();
    context.moveTo(left, y);
    context.lineTo(centre, y);
    context.stroke();
    context.fillStyle = "rgba(255,255,255,.55)";
    context.font = '9px "DM Mono"';
    context.fillText(`n=${n}`, left, y - 8);
  }

  const progress = (state.elapsed * 0.45) % 1;
  const startY = levelY(upperN);
  const endY = levelY(lowerN);
  const electronY = startY + (endY - startY) * Math.min(progress * 1.8, 1);
  glowCircle(centre - 35, electronY, 5, "#f7f2df", 1);

  if (progress > 0.54) {
    wavePath(centre + 5, endY, width * 0.88, endY - 80, 9, 8, state.elapsed * 6, task.accent, 2);
  }

  const spectrumX = width * 0.68;
  const spectralLines = [
    ["#e947ff", 0.08],
    ["#556dff", 0.24],
    ["#35d6ff", 0.43],
    ["#ff4d62", 0.82],
  ];
  spectralLines.forEach(([color, position]) => {
    context.strokeStyle = color;
    context.shadowColor = color;
    context.shadowBlur = 12;
    context.beginPath();
    context.moveTo(spectrumX + position * width * 0.24, height * 0.58);
    context.lineTo(spectrumX + position * width * 0.24, height * 0.79);
    context.stroke();
    context.shadowBlur = 0;
  });
}

function drawElectronDiffraction() {
  const task = tasks[5];
  background(task.accent, 0.15);
  const { width, height } = state;
  const centreX = width * 0.57;
  const centreY = height * 0.49;
  const voltage = 2 + state.pointer.x * 6;
  parameter.textContent = `V = ${voltage.toFixed(1)} kV`;
  const contraction = 1 / Math.sqrt(voltage / 2);

  for (let ring = 1; ring <= 7; ring += 1) {
    const radius = ring * Math.min(width, height) * 0.075 * contraction;
    context.strokeStyle = ring % 2 ? "rgba(255,105,94,.82)" : "rgba(65,236,255,.66)";
    context.lineWidth = 1.2 + Math.sin(state.elapsed * 2 + ring) * 0.35;
    context.shadowColor = task.accent;
    context.shadowBlur = 12;
    context.beginPath();
    context.arc(centreX, centreY, radius, 0, Math.PI * 2);
    context.stroke();
  }
  context.shadowBlur = 0;

  context.fillStyle = "rgba(255,255,255,.18)";
  context.fillRect(width * 0.12, centreY - 2, centreX - width * 0.12, 4);
  for (let index = 0; index < 12; index += 1) {
    const progress = (state.elapsed * 0.36 + index / 12) % 1;
    glowCircle(width * 0.12 + progress * (centreX - width * 0.12), centreY, 2.2, "#f7f2df", 0.72);
  }
  glowCircle(centreX, centreY, 5, "#ffffff", 1);
}

function drawParticleInBox() {
  const task = tasks[6];
  background(task.accent, 0.19);
  const { width, height } = state;
  const left = width * 0.1;
  const right = width * 0.9;
  const mid = height * 0.52;
  const amplitude = height * 0.22;
  const mix = state.pointer.x;
  const n = 2 + Math.round(mix * 3);
  parameter.textContent = `n = ${n}`;

  context.strokeStyle = "rgba(255,255,255,.55)";
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(left, height * 0.18);
  context.lineTo(left, height * 0.82);
  context.moveTo(right, height * 0.18);
  context.lineTo(right, height * 0.82);
  context.stroke();

  const wave = [];
  const density = [];
  for (let step = 0; step <= 260; step += 1) {
    const xNorm = step / 260;
    const x = left + (right - left) * xNorm;
    const psi1 = Math.sin(n * Math.PI * xNorm) * Math.cos(state.elapsed * (0.8 + n * 0.16));
    const psi2 = Math.sin((n + 1) * Math.PI * xNorm) * Math.cos(state.elapsed * (1.0 + n * 0.19));
    const psi = psi1 * (1 - mix * 0.36) + psi2 * mix * 0.36;
    wave.push([x, mid - psi * amplitude]);
    density.push([x, mid + 85 - psi * psi * amplitude * 0.75]);
  }

  const fill = context.createLinearGradient(0, mid, 0, mid + 120);
  fill.addColorStop(0, "rgba(86,164,255,.58)");
  fill.addColorStop(1, "rgba(86,164,255,0)");
  context.beginPath();
  context.moveTo(density[0][0], mid + 85);
  density.forEach(([x, y]) => context.lineTo(x, y));
  context.lineTo(density[density.length - 1][0], mid + 85);
  context.closePath();
  context.fillStyle = fill;
  context.fill();
  line(density, "#41ecff", 1.5, 0.75);
  line(wave, "#f7f2df", 2.4, 0.95);
}

function drawQuantumCrypto() {
  const task = tasks[7];
  background(task.accent, 0.15);
  const { width, height } = state;
  const aliceX = width * 0.14;
  const bobX = width * 0.86;
  const centreY = height * 0.5;
  const disturbance = Math.max(0, (0.48 - state.pointer.y) * 1.8);
  parameter.textContent = `QBER = ${(disturbance * 25).toFixed(1)}%`;

  context.strokeStyle = "rgba(255,255,255,.22)";
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(aliceX, centreY);
  context.lineTo(bobX, centreY);
  context.stroke();

  for (const [label, x] of [["ALICE", aliceX], ["BOB", bobX]]) {
    context.strokeStyle = task.accent;
    context.strokeRect(x - 33, centreY - 48, 66, 96);
    context.fillStyle = "rgba(255,255,255,.75)";
    context.font = '9px "DM Mono"';
    context.textAlign = "center";
    context.fillText(label, x, centreY + 70);
  }
  context.textAlign = "start";

  for (let photon = 0; photon < 10; photon += 1) {
    const progress = (state.elapsed * 0.24 + photon / 10) % 1;
    const x = aliceX + (bobX - aliceX) * progress;
    const basis = photon % 4;
    const y = centreY + Math.sin(progress * Math.PI * 2 + basis) * 8;
    glowCircle(x, y, 4, basis % 2 ? "#41ecff" : "#e95dff", 0.95);
    context.strokeStyle = "rgba(255,255,255,.58)";
    context.save();
    context.translate(x, y);
    context.rotate((basis * Math.PI) / 4);
    context.beginPath();
    context.moveTo(-9, 0);
    context.lineTo(9, 0);
    context.stroke();
    context.restore();
  }

  if (disturbance > 0.03) {
    const eveX = width * 0.52;
    context.setLineDash([5, 6]);
    context.strokeStyle = "#ff695e";
    context.beginPath();
    context.arc(eveX, centreY, 38 + disturbance * 20, 0, Math.PI * 2);
    context.stroke();
    context.setLineDash([]);
    context.fillStyle = "#ff695e";
    context.font = '9px "DM Mono"';
    context.fillText("INTERCEPT", eveX - 25, centreY - 52);
  }
}

function drawCompton() {
  const task = tasks[8];
  background(task.accent, 0.17);
  const { width, height } = state;
  const targetX = width * 0.52;
  const targetY = height * 0.52;
  const angle = Math.atan2(
    state.pointer.y * height - targetY,
    state.pointer.x * width - targetX,
  );
  const degrees = Math.round(Math.abs((angle * 180) / Math.PI));
  parameter.textContent = `θ = ${degrees}°`;

  wavePath(
    width * 0.08,
    targetY,
    targetX - 12,
    targetY,
    7,
    9,
    state.elapsed * 5,
    "#41ecff",
    2,
  );
  glowCircle(targetX, targetY, 11, "#f7f2df", 1);

  const rayLength = Math.min(width, height) * 0.42;
  const outX = targetX + Math.cos(angle) * rayLength;
  const outY = targetY + Math.sin(angle) * rayLength;
  const wavelengthStretch = 1 + Math.abs(1 - Math.cos(angle)) * 0.8;
  wavePath(
    targetX + Math.cos(angle) * 13,
    targetY + Math.sin(angle) * 13,
    outX,
    outY,
    8,
    8 / wavelengthStretch,
    state.elapsed * 3,
    task.accent,
    2.2,
  );

  const electronAngle = angle + Math.PI * 0.62;
  const eProgress = Math.min((state.elapsed * 0.34) % 1.25, 1);
  const electronX = targetX + Math.cos(electronAngle) * rayLength * 0.65 * eProgress;
  const electronY = targetY + Math.sin(electronAngle) * rayLength * 0.65 * eProgress;
  line([[targetX, targetY], [electronX, electronY]], "rgba(255,255,255,.28)", 1, 1);
  glowCircle(electronX, electronY, 5, "#ff695e", 0.95);

  context.strokeStyle = "rgba(249,233,94,.55)";
  context.beginPath();
  context.arc(targetX, targetY, 50, 0, angle, angle < 0);
  context.stroke();
}

function drawOrbitals() {
  const task = tasks[9];
  background(task.accent, 0.18);
  const { width, height } = state;
  const centreX = width * 0.53;
  const centreY = height * 0.5;
  const rotation = (state.pointer.x - 0.5) * Math.PI * 1.6 + state.elapsed * 0.08;
  const tilt = (state.pointer.y - 0.5) * 1.2;
  const scale = Math.min(width, height) * 0.38;

  context.save();
  context.globalCompositeOperation = "lighter";
  for (const point of state.orbitalPoints) {
    const orbitalRadius = point.radius * point.lobe;
    const localX = Math.cos(point.angle) * orbitalRadius * point.sign;
    const localY = Math.sin(point.angle) * orbitalRadius;
    const localZ = (point.depth - 0.5) * 0.8 * (1 - point.lobe);
    const rotX = localX * Math.cos(rotation) - localZ * Math.sin(rotation);
    const rotZ = localX * Math.sin(rotation) + localZ * Math.cos(rotation);
    const projectedY = localY * Math.cos(tilt) - rotZ * Math.sin(tilt);
    const x = centreX + rotX * scale;
    const y = centreY + projectedY * scale;
    const alpha = 0.18 + point.depth * 0.42;
    const color = point.sign > 0 ? "#22d8ff" : "#ff4f91";
    context.globalAlpha = alpha;
    context.fillStyle = color;
    context.fillRect(x, y, 1.2 + point.depth * 1.8, 1.2 + point.depth * 1.8);
  }
  context.restore();
  glowCircle(centreX, centreY, 5, "#f7f2df", 1);

  context.strokeStyle = "rgba(255,255,255,.18)";
  context.beginPath();
  context.ellipse(centreX, centreY, scale * 0.82, scale * 0.31, rotation, 0, Math.PI * 2);
  context.stroke();
}

const renderers = [
  drawRandomWalk,
  drawBrownian,
  drawThermalRadiation,
  drawPhotoelectric,
  drawHydrogenSpectrum,
  drawElectronDiffraction,
  drawParticleInBox,
  drawQuantumCrypto,
  drawCompton,
  drawOrbitals,
];

function applyTask(index, updateHistory = true) {
  state.taskIndex = (index + tasks.length) % tasks.length;
  const task = tasks[state.taskIndex];
  root.style.setProperty("--accent", task.accent);
  root.style.setProperty("--accent-rgb", task.accentRgb);
  taskNumber.textContent = task.id;
  taskKicker.textContent = task.kicker;
  taskTitle.textContent = task.title;
  taskSummary.textContent = task.summary;
  taskEquation.textContent = task.equation;
  taskCaveat.textContent =
    "Concept animation. Validated numerical results remain in the task report.";
  documentation.href = task.docs;
  stageLabel.textContent = task.stageLabel;
  instruction.textContent = task.instruction;
  parameter.textContent = task.parameter;
  transitionNumber.textContent = task.id;
  document.title = `${task.title} | BPhO Laboratory`;
  if (updateHistory) {
    history.replaceState(null, "", `?task=${task.id}`);
  }
  resetSimulation();
  renderDrawer();
}

function switchTask(index) {
  if ((index + tasks.length) % tasks.length === state.taskIndex) {
    closeDrawer();
    return;
  }
  const targetIndex = (index + tasks.length) % tasks.length;
  transitionNumber.textContent = tasks[targetIndex].id;
  transition.style.background = tasks[targetIndex].accent;
  body.classList.add("content-changing");
  transition.classList.remove("is-ready");
  transition.classList.add("is-switching");
  closeDrawer();

  window.setTimeout(
    () => {
      applyTask(targetIndex);
      transition.classList.remove("is-switching");
      transition.classList.add("is-ready");
      window.setTimeout(() => body.classList.remove("content-changing"), 130);
    },
    reduceMotion.matches ? 0 : 460,
  );
}

function renderDrawer() {
  drawerList.innerHTML = tasks
    .map(
      (task, index) => `
        <button
          type="button"
          class="drawer-task${index === state.taskIndex ? " is-current" : ""}"
          data-drawer-task="${index}"
          style="--drawer-accent:${task.accent}"
        >
          <span>${task.id}</span>
          <strong>${task.title}</strong>
          <span>↗</span>
        </button>
      `,
    )
    .join("");
  drawerList.querySelectorAll("[data-drawer-task]").forEach((button) => {
    button.addEventListener("click", () => switchTask(Number(button.dataset.drawerTask)));
  });
}

function openDrawer() {
  drawer.classList.add("is-open");
  drawerBackdrop.classList.add("is-visible");
  drawer.setAttribute("aria-hidden", "false");
  drawerToggle.setAttribute("aria-expanded", "true");
  drawer.querySelector(".is-current")?.focus({ preventScroll: false });
}

function closeDrawer() {
  drawer.classList.remove("is-open");
  drawerBackdrop.classList.remove("is-visible");
  drawer.setAttribute("aria-hidden", "true");
  drawerToggle.setAttribute("aria-expanded", "false");
}

function updateControls() {
  playToggle.setAttribute("aria-pressed", String(state.running));
  playLabel.textContent = state.running ? "Pause" : "Play";
  speedOutput.textContent = `${state.speed.toFixed(2)}×`;
}

function animate(now) {
  const rawDelta = Math.min((now - state.lastFrame) / 1000, 0.05);
  state.lastFrame = now;
  const delta = state.running ? rawDelta * state.speed : 0;
  state.elapsed += delta;
  state.frame += state.running ? 1 : 0;
  state.pointer.x += (state.pointerTarget.x - state.pointer.x) * 0.08;
  state.pointer.y += (state.pointerTarget.y - state.pointer.y) * 0.08;

  renderers[state.taskIndex](delta);
  timeReadout.textContent = `${state.elapsed.toFixed(2)} s`;
  frameReadout.textContent = String(state.frame).padStart(4, "0").slice(-4);
  requestAnimationFrame(animate);
}

function updatePointer(event) {
  const rect = canvas.getBoundingClientRect();
  state.pointerTarget.x = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
  state.pointerTarget.y = Math.min(Math.max((event.clientY - rect.top) / rect.height, 0), 1);
  if (!coarsePointer.matches) {
    cursor.classList.add("is-visible");
    cursor.style.transform = `translate(${event.clientX}px, ${event.clientY}px) translate(-50%, -50%)`;
  }
}

function bindEvents() {
  window.addEventListener("resize", () => {
    resizeCanvas();
    resetSimulation();
  });
  window.addEventListener("pointermove", updatePointer, { passive: true });
  document.addEventListener("pointerover", (event) => {
    cursor.classList.toggle("is-link", Boolean(event.target.closest("a, button, input")));
  });

  playToggle.addEventListener("click", () => {
    state.running = !state.running;
    updateControls();
  });
  resetButton.addEventListener("click", resetSimulation);
  speedInput.addEventListener("input", () => {
    state.speed = Number(speedInput.value);
    updateControls();
  });
  previousButton.addEventListener("click", () => switchTask(state.taskIndex - 1));
  nextButton.addEventListener("click", () => switchTask(state.taskIndex + 1));
  drawerToggle.addEventListener("click", openDrawer);
  drawerClose.addEventListener("click", closeDrawer);
  drawerBackdrop.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target.matches("input, button, a")) {
      if (event.key === "Escape") closeDrawer();
      return;
    }
    if (event.key === "ArrowLeft") switchTask(state.taskIndex - 1);
    if (event.key === "ArrowRight") switchTask(state.taskIndex + 1);
    if (event.key === "Escape") closeDrawer();
    if (event.code === "Space") {
      event.preventDefault();
      state.running = !state.running;
      updateControls();
    }
  });
}

resizeCanvas();
applyTask(state.taskIndex, false);
bindEvents();
updateControls();
requestAnimationFrame(animate);
window.setTimeout(
  () => transition.classList.add("is-ready"),
  reduceMotion.matches ? 0 : 220,
);
