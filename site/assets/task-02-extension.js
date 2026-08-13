(() => {
  const laboratory = document.querySelector("[data-extension-laboratory]");
  const canvas = document.querySelector("#extension-bath-canvas");
  const pathCanvas = document.querySelector("#extension-path-canvas");
  if (!laboratory || !canvas || !pathCanvas) return;

  const context = canvas.getContext("2d");
  const pathContext = pathCanvas.getContext("2d");
  const modeInputs = Array.from(document.querySelectorAll('input[name="bath-mode"]'));
  const countInput = document.querySelector("#extension-particle-count");
  const playButton = document.querySelector("[data-extension-play]");
  const resetButton = document.querySelector("[data-extension-reset]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const outputs = {
    stageLabel: document.querySelector("[data-extension-stage-label]"),
    time: document.querySelector("[data-extension-time]"),
    eventLabel: document.querySelector("[data-extension-event-label]"),
    events: document.querySelector("[data-extension-events]"),
    tracerEvents: document.querySelector("[data-extension-tracer-events]"),
    energy: document.querySelector("[data-extension-energy]"),
  };

  const GAS_RADIUS = 0.014;
  const TRACER_RADIUS = 0.09;
  const GAS_MASS = 1;
  const TRACER_MASS = 10;
  const GAS_SPEED = 0.27;
  const RESET_INTERVAL = 0.8;
  const TIME_STEP = 1 / 180;
  const MAX_SUBSTEPS = 6;

  const state = {
    mode: "random-reset",
    particles: [],
    tracer: null,
    trail: [],
    seed: 2026,
    random: null,
    time: 0,
    events: 0,
    tracerEvents: 0,
    initialEnergy: 1,
    playing: false,
    visible: true,
    lastFrame: performance.now(),
    accumulator: 0,
    frameRequest: 0,
    evidence: null,
  };

  function mulberry32(seed) {
    let value = seed >>> 0;
    return () => {
      value += 0x6d2b79f5;
      let result = value;
      result = Math.imul(result ^ (result >>> 15), result | 1);
      result ^= result + Math.imul(result ^ (result >>> 7), result | 61);
      return ((result ^ (result >>> 14)) >>> 0) / 4294967296;
    };
  }

  function selectedMode() {
    return modeInputs.find((input) => input.checked)?.value || "random-reset";
  }

  function createParticle(random, particles) {
    for (let attempt = 0; attempt < 12000; attempt += 1) {
      const x = GAS_RADIUS + random() * (1 - 2 * GAS_RADIUS);
      const y = GAS_RADIUS + random() * (1 - 2 * GAS_RADIUS);
      if (Math.hypot(x - 0.5, y - 0.5) <= GAS_RADIUS + TRACER_RADIUS + 0.006) continue;
      if (
        particles.some(
          (particle) =>
            Math.hypot(x - particle.x, y - particle.y) <= 2 * GAS_RADIUS + 0.002,
        )
      ) {
        continue;
      }
      const angle = random() * Math.PI * 2;
      return {
        x,
        y,
        vx: GAS_SPEED * Math.cos(angle),
        vy: GAS_SPEED * Math.sin(angle),
        resetIn: random() * RESET_INTERVAL,
      };
    }
    throw new Error("The selected gas density could not be initialized");
  }

  function kineticEnergy() {
    let energy = 0;
    for (const particle of state.particles) {
      energy += 0.5 * GAS_MASS * (particle.vx ** 2 + particle.vy ** 2);
    }
    energy +=
      0.5 *
      TRACER_MASS *
      (state.tracer.vx ** 2 + state.tracer.vy ** 2);
    return energy;
  }

  function initialize() {
    state.mode = selectedMode();
    const random = mulberry32(state.seed + (state.mode === "hard-disc" ? 101 : 0));
    state.random = random;
    state.particles = [];
    const particleCount = Number(countInput.value);
    for (let index = 0; index < particleCount; index += 1) {
      state.particles.push(createParticle(random, state.particles));
    }
    state.tracer = { x: 0.5, y: 0.5, vx: 0, vy: 0 };
    state.trail = [{ x: 0.5, y: 0.5 }];
    state.time = 0;
    state.events = 0;
    state.tracerEvents = 0;
    state.accumulator = 0;
    state.lastFrame = performance.now();
    state.initialEnergy = kineticEnergy();
    updateLabels();
    drawBath();
  }

  function reflectBody(body, radius) {
    if (body.x < radius) {
      body.x = 2 * radius - body.x;
      body.vx = Math.abs(body.vx);
    } else if (body.x > 1 - radius) {
      body.x = 2 * (1 - radius) - body.x;
      body.vx = -Math.abs(body.vx);
    }
    if (body.y < radius) {
      body.y = 2 * radius - body.y;
      body.vy = Math.abs(body.vy);
    } else if (body.y > 1 - radius) {
      body.y = 2 * (1 - radius) - body.y;
      body.vy = -Math.abs(body.vy);
    }
  }

  function resolvePair(first, second) {
    const dx = second.x - first.x;
    const dy = second.y - first.y;
    const distance = Math.hypot(dx, dy);
    const contact = 2 * GAS_RADIUS;
    if (distance >= contact || distance === 0) return false;
    const nx = dx / distance;
    const ny = dy / distance;
    const correction = (contact - distance + 1e-7) / 2;
    first.x -= correction * nx;
    first.y -= correction * ny;
    second.x += correction * nx;
    second.y += correction * ny;
    const relativeNormal =
      (second.vx - first.vx) * nx + (second.vy - first.vy) * ny;
    if (relativeNormal >= 0) return false;
    const impulse = -relativeNormal;
    first.vx -= impulse * nx;
    first.vy -= impulse * ny;
    second.vx += impulse * nx;
    second.vy += impulse * ny;
    return true;
  }

  function resolveTracer(particle) {
    const dx = state.tracer.x - particle.x;
    const dy = state.tracer.y - particle.y;
    const distance = Math.hypot(dx, dy);
    const contact = GAS_RADIUS + TRACER_RADIUS;
    if (distance >= contact || distance === 0) return false;
    const nx = dx / distance;
    const ny = dy / distance;
    const penetration = contact - distance + 1e-7;
    const totalMass = GAS_MASS + TRACER_MASS;
    particle.x -= (TRACER_MASS / totalMass) * penetration * nx;
    particle.y -= (TRACER_MASS / totalMass) * penetration * ny;
    state.tracer.x += (GAS_MASS / totalMass) * penetration * nx;
    state.tracer.y += (GAS_MASS / totalMass) * penetration * ny;
    const relativeNormal =
      (state.tracer.vx - particle.vx) * nx +
      (state.tracer.vy - particle.vy) * ny;
    if (relativeNormal >= 0) return false;
    const impulse =
      (-(1 + 1) * relativeNormal) / (1 / GAS_MASS + 1 / TRACER_MASS);
    particle.vx -= (impulse / GAS_MASS) * nx;
    particle.vy -= (impulse / GAS_MASS) * ny;
    state.tracer.vx += (impulse / TRACER_MASS) * nx;
    state.tracer.vy += (impulse / TRACER_MASS) * ny;
    return true;
  }

  function advance() {
    for (const particle of state.particles) {
      if (state.mode === "random-reset") {
        particle.resetIn -= TIME_STEP;
        if (particle.resetIn <= 0) {
          const angle = state.random() * Math.PI * 2;
          particle.vx = GAS_SPEED * Math.cos(angle);
          particle.vy = GAS_SPEED * Math.sin(angle);
          particle.resetIn += RESET_INTERVAL;
          state.events += 1;
        }
      }
      particle.x += particle.vx * TIME_STEP;
      particle.y += particle.vy * TIME_STEP;
      reflectBody(particle, GAS_RADIUS);
    }
    state.tracer.x += state.tracer.vx * TIME_STEP;
    state.tracer.y += state.tracer.vy * TIME_STEP;
    reflectBody(state.tracer, TRACER_RADIUS);

    for (const particle of state.particles) {
      if (resolveTracer(particle)) state.tracerEvents += 1;
    }
    if (state.mode === "hard-disc") {
      for (let first = 0; first < state.particles.length; first += 1) {
        for (let second = first + 1; second < state.particles.length; second += 1) {
          if (resolvePair(state.particles[first], state.particles[second])) {
            state.events += 1;
          }
        }
      }
    }
    reflectBody(state.tracer, TRACER_RADIUS);
    state.time += TIME_STEP;
    if (state.trail.length === 0 || state.time % 0.025 < TIME_STEP) {
      state.trail.push({ x: state.tracer.x, y: state.tracer.y });
      if (state.trail.length > 900) state.trail.shift();
    }
  }

  function updateLabels() {
    const hardDisc = state.mode === "hard-disc";
    outputs.stageLabel.textContent = hardDisc
      ? "Explicit hard-disc bath"
      : "Random direction bath";
    outputs.eventLabel.textContent = hardDisc ? "Gas–gas impacts" : "Direction resets";
    outputs.time.textContent = `${state.time.toFixed(2)} ps`;
    outputs.events.textContent = state.events.toLocaleString();
    outputs.tracerEvents.textContent = state.tracerEvents.toLocaleString();
    const drift = (kineticEnergy() - state.initialEnergy) / state.initialEnergy;
    outputs.energy.textContent = drift.toExponential(2);
    playButton.textContent = state.playing ? "Pause model" : state.time > 0 ? "Continue" : "Run model";
  }

  function sizeCanvas(target, targetContext) {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(target.clientWidth * ratio));
    const height = Math.max(1, Math.round(target.clientHeight * ratio));
    if (target.width !== width || target.height !== height) {
      target.width = width;
      target.height = height;
    }
    targetContext.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { width: target.clientWidth, height: target.clientHeight };
  }

  function drawBath() {
    if (!state.tracer) return;
    const { width, height } = sizeCanvas(canvas, context);
    context.clearRect(0, 0, width, height);
    context.fillStyle = "#fbfaf6";
    context.fillRect(0, 0, width, height);
    const margin = 28;
    const scale = Math.min(width, height) - margin * 2;
    const left = (width - scale) / 2;
    const top = (height - scale) / 2;
    const screen = (x, y) => ({ x: left + x * scale, y: top + y * scale });

    context.strokeStyle = "#c8c3b9";
    context.lineWidth = 1;
    context.strokeRect(left, top, scale, scale);
    if (state.trail.length > 1) {
      context.beginPath();
      state.trail.forEach((point, index) => {
        const value = screen(point.x, point.y);
        if (index === 0) context.moveTo(value.x, value.y);
        else context.lineTo(value.x, value.y);
      });
      context.strokeStyle = "rgba(162, 79, 57, 0.68)";
      context.lineWidth = 1.5;
      context.stroke();
    }

    context.fillStyle = "#78969a";
    for (const particle of state.particles) {
      const point = screen(particle.x, particle.y);
      context.beginPath();
      context.arc(point.x, point.y, Math.max(2.2, GAS_RADIUS * scale), 0, Math.PI * 2);
      context.fill();
    }
    const tracer = screen(state.tracer.x, state.tracer.y);
    context.fillStyle = "#a24f39";
    context.beginPath();
    context.arc(tracer.x, tracer.y, TRACER_RADIUS * scale, 0, Math.PI * 2);
    context.fill();
    context.strokeStyle = "#7d3828";
    context.stroke();
  }

  function drawAcceptedPaths() {
    if (!state.evidence) return;
    const { width, height } = sizeCanvas(pathCanvas, pathContext);
    pathContext.clearRect(0, 0, width, height);
    pathContext.fillStyle = "#ffffff";
    pathContext.fillRect(0, 0, width, height);
    const paths = [
      { data: state.evidence.modes.random_reset.path, color: "#77726b", label: "Direction resets" },
      { data: state.evidence.modes.hard_disc.path, color: "#a24f39", label: "Hard discs" },
    ];
    const values = paths.flatMap(({ data }) => data.x_nm.concat(data.y_nm));
    const extent = Math.max(0.05, ...values.map((value) => Math.abs(value))) * 1.16;
    const margin = { left: 44, right: 20, top: 30, bottom: 38 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const mapX = (value) => margin.left + ((value + extent) / (2 * extent)) * plotWidth;
    const mapY = (value) => margin.top + ((extent - value) / (2 * extent)) * plotHeight;
    pathContext.strokeStyle = "#dedbd4";
    pathContext.lineWidth = 1;
    pathContext.beginPath();
    pathContext.moveTo(mapX(-extent), mapY(0));
    pathContext.lineTo(mapX(extent), mapY(0));
    pathContext.moveTo(mapX(0), mapY(-extent));
    pathContext.lineTo(mapX(0), mapY(extent));
    pathContext.stroke();
    for (const path of paths) {
      pathContext.beginPath();
      path.data.x_nm.forEach((x, index) => {
        const y = path.data.y_nm[index];
        if (index === 0) pathContext.moveTo(mapX(x), mapY(y));
        else pathContext.lineTo(mapX(x), mapY(y));
      });
      pathContext.strokeStyle = path.color;
      pathContext.lineWidth = 1.8;
      pathContext.stroke();
    }
    pathContext.fillStyle = "#5f5a53";
    pathContext.font = '12px "Times New Roman", Times, serif';
    pathContext.fillText("x displacement (nm)", width / 2 - 42, height - 10);
    pathContext.save();
    pathContext.translate(13, height / 2 + 42);
    pathContext.rotate(-Math.PI / 2);
    pathContext.fillText("y displacement (nm)", 0, 0);
    pathContext.restore();
    paths.forEach((path, index) => {
      const x = margin.left + index * 124;
      pathContext.strokeStyle = path.color;
      pathContext.lineWidth = 2;
      pathContext.beginPath();
      pathContext.moveTo(x, 14);
      pathContext.lineTo(x + 20, 14);
      pathContext.stroke();
      pathContext.fillStyle = "#4f4b45";
      pathContext.fillText(path.label, x + 26, 17);
    });
  }

  function frame(now) {
    state.frameRequest = 0;
    if (!state.playing || !state.visible) return;
    const elapsed = Math.min((now - state.lastFrame) / 1000, 0.06);
    state.lastFrame = now;
    state.accumulator += elapsed;
    let substeps = 0;
    while (state.accumulator >= TIME_STEP && substeps < MAX_SUBSTEPS) {
      advance();
      state.accumulator -= TIME_STEP;
      substeps += 1;
    }
    updateLabels();
    drawBath();
    state.frameRequest = requestAnimationFrame(frame);
  }

  function requestLoop() {
    if (!state.frameRequest && state.playing && state.visible) {
      state.lastFrame = performance.now();
      state.frameRequest = requestAnimationFrame(frame);
    }
  }

  playButton.addEventListener("click", () => {
    state.playing = !state.playing;
    updateLabels();
    requestLoop();
  });
  resetButton.addEventListener("click", () => {
    state.playing = false;
    initialize();
  });
  countInput.addEventListener("change", () => {
    state.playing = false;
    initialize();
  });
  modeInputs.forEach((input) => {
    input.addEventListener("change", () => {
      if (!input.checked) return;
      state.playing = false;
      initialize();
    });
  });

  new ResizeObserver(() => {
    drawBath();
    drawAcceptedPaths();
  }).observe(laboratory);
  new IntersectionObserver(
    ([entry]) => {
      state.visible = entry.isIntersecting;
      requestLoop();
    },
    { threshold: 0.05 },
  ).observe(laboratory);

  async function loadEvidence() {
    try {
      const response = await fetch("../data/task-02-extension-evidence.json", {
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`Evidence request failed: ${response.status}`);
      const evidence = await response.json();
      if (
        evidence.schema_version !== 1 ||
        evidence.accepted !== true ||
        !evidence.modes?.random_reset ||
        !evidence.modes?.hard_disc
      ) {
        throw new Error("Extension evidence failed schema validation");
      }
      state.evidence = evidence;
      laboratory.classList.remove("is-loading");
      laboratory.dataset.accepted = "true";
      drawAcceptedPaths();
    } catch (error) {
      console.error(error);
      laboratory.classList.remove("is-loading");
      laboratory.dataset.accepted = "false";
    }
  }

  initialize();
  loadEvidence();
  if (!reduceMotion.matches) {
    state.playing = true;
    updateLabels();
    requestLoop();
  }
  window.addEventListener("pagehide", () => {
    state.playing = false;
    if (state.frameRequest) cancelAnimationFrame(state.frameRequest);
  });
})();
