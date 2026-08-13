const evidenceUrl = new URL(
  "../../data/task07/superposition_validation.json",
  import.meta.url,
);

const lab = document.querySelector("[data-superposition-lab]");
const phaseControl = document.querySelector("#superposition-phase");
const canvas = document.querySelector("#superposition-canvas");
const context = canvas.getContext("2d");
const downloadButton = document.querySelector("[data-download-superposition]");

const PALETTE = Object.freeze({
  ink: "#29251f",
  muted: "#756e65",
  accent: "#a24f39",
  accentDark: "#7d3828",
  paper: "#fcfbf7",
  paperDeep: "#f5f1e9",
  grid: "#ded8cf",
  gridSoft: "#ece7df",
});

const outputs = {
  phase: document.querySelector("[data-superposition-phase-output]"),
  time: document.querySelector("[data-superposition-time]"),
  position: document.querySelector("[data-superposition-position]"),
  left: document.querySelector("[data-superposition-left]"),
  energy: document.querySelector("[data-superposition-energy]"),
  error: document.querySelector("[data-superposition-error]"),
};

const state = {
  evidence: null,
  phaseDegrees: 0,
};

function relativeError(observed, expected) {
  if (expected === 0) return Math.abs(observed);
  return Math.abs(observed - expected) / Math.abs(expected);
}

function validateEvidence(payload) {
  const anchors = payload?.phase_anchors;
  const checks = payload?.validation?.checks;
  const derived = payload?.derived;
  if (
    payload?.schema_version !== "task07-superposition-v1" ||
    payload?.status !== "accepted_optional_extension" ||
    payload?.baseline_model !==
      "stationary states in a one-dimensional infinite square well" ||
    payload?.configuration?.states?.join(",") !== "1,2" ||
    payload?.configuration?.probabilities?.join(",") !== "0.5,0.5" ||
    payload?.configuration?.box_width_nm !== 1 ||
    payload?.validation?.passed !== true ||
    payload?.validation?.check_count !== 14 ||
    !Array.isArray(checks) ||
    checks.length !== 14 ||
    !checks.every(
      (check) =>
        check.passed === true &&
        Number.isFinite(check.observed) &&
        Number.isFinite(check.expected) &&
        Number.isFinite(check.tolerance),
    ) ||
    !Array.isArray(anchors) ||
    anchors.length !== 17 ||
    !Number.isFinite(derived?.beat_period_fs) ||
    derived.beat_period_fs <= 0 ||
    relativeError(derived.energy_2_ev, 4 * derived.energy_1_ev) > 5e-14 ||
    relativeError(derived.mean_energy_ev, 2.5 * derived.energy_1_ev) > 5e-14 ||
    relativeError(derived.energy_uncertainty_ev, 1.5 * derived.energy_1_ev) >
      5e-14
  ) {
    throw new Error("Unsupported or unvalidated Task 7 extension evidence");
  }

  anchors.forEach((anchor, index) => {
    const phase = anchor.phase_rad;
    const expectedPosition = 0.5 - (16 * Math.cos(phase)) / (9 * Math.PI ** 2);
    const expectedLeft = 0.5 + (4 * Math.cos(phase)) / (3 * Math.PI);
    if (
      anchor.phase_index !== index ||
      relativeError(anchor.expected_position_over_width, expectedPosition) >
        5e-13 ||
      relativeError(anchor.left_half_probability, expectedLeft) > 5e-13 ||
      Math.abs(anchor.normalization - 1) > 5e-12
    ) {
      throw new Error(`Invalid superposition phase anchor ${index}`);
    }
  });
  return payload;
}

function densityAt(u, phase) {
  const first = Math.sin(Math.PI * u);
  const second = Math.sin(2 * Math.PI * u);
  return (
    first * first +
    second * second +
    2 * Math.cos(phase) * first * second
  );
}

function expectedPosition(phase) {
  return 0.5 - (16 * Math.cos(phase)) / (9 * Math.PI ** 2);
}

function leftProbability(phase) {
  return 0.5 + (4 * Math.cos(phase)) / (3 * Math.PI);
}

function fitCanvas() {
  const width = Math.max(canvas.clientWidth, 320);
  const height = Math.max(canvas.clientHeight, 330);
  const density = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * density);
  canvas.height = Math.round(height * density);
  context.setTransform(density, 0, 0, density, 0, 0);
  return { width, height };
}

function line(x1, y1, x2, y2) {
  context.beginPath();
  context.moveTo(x1, y1);
  context.lineTo(x2, y2);
  context.stroke();
}

function paintPaper(width, height) {
  context.fillStyle = PALETTE.paper;
  context.fillRect(0, 0, width, height);
  context.save();
  context.fillStyle = "rgba(70, 57, 44, 0.035)";
  const speckCount = Math.max(90, Math.round((width * height) / 4200));
  for (let index = 0; index < speckCount; index += 1) {
    const x = (index * 83 + 29) % Math.max(1, width);
    const y = (index * 137 + 53) % Math.max(1, height);
    const size = index % 7 === 0 ? 0.9 : 0.55;
    context.fillRect(x, y, size, size);
  }
  context.restore();
}

function strokePrinted(colour, width) {
  context.save();
  context.strokeStyle = "rgba(56, 43, 33, 0.11)";
  context.lineWidth = width + 2.2;
  context.stroke();
  context.restore();
  context.strokeStyle = colour;
  context.lineWidth = width;
  context.stroke();
}

function drawSuperposition() {
  if (!state.evidence) return;
  const { width, height } = fitCanvas();
  const compact = width < 560;
  const margins = {
    left: compact ? 48 : 70,
    right: compact ? 24 : 38,
    top: compact ? 66 : 72,
    bottom: compact ? 60 : 70,
  };
  const plot = {
    x: margins.left,
    y: margins.top,
    width: width - margins.left - margins.right,
    height: height - margins.top - margins.bottom,
  };
  const baseline = plot.y + plot.height;
  const phase = (state.phaseDegrees * Math.PI) / 180;
  const mean = expectedPosition(phase);
  const samples = Math.max(500, Math.round(plot.width * 1.5));
  let maximum = 0;
  for (let index = 0; index <= samples; index += 1) {
    maximum = Math.max(maximum, densityAt(index / samples, phase));
  }
  const yFor = (value) => baseline - (value / Math.max(maximum * 1.08, 1)) * plot.height;

  context.clearRect(0, 0, width, height);
  paintPaper(width, height);
  context.fillStyle = PALETTE.paperDeep;
  context.fillRect(plot.x, plot.y, plot.width, plot.height);
  context.fillStyle = PALETTE.ink;
  context.font = `600 ${compact ? 16 : 19}px "Times New Roman", Times, serif`;
  context.textAlign = "left";
  context.fillText("Equal n = 1 and n = 2 superposition", plot.x, 28);
  context.fillStyle = PALETTE.muted;
  context.font = `${compact ? 12 : 13}px "Times New Roman", Times, serif`;
  context.fillText(
    `relative phase θ = ${state.phaseDegrees}°`,
    plot.x,
    49,
  );

  context.strokeStyle = PALETTE.gridSoft;
  context.lineWidth = 1;
  for (const fraction of [0.25, 0.5, 0.75]) {
    line(
      plot.x + plot.width * fraction,
      plot.y,
      plot.x + plot.width * fraction,
      baseline,
    );
  }
  for (const fraction of [0.25, 0.5, 0.75]) {
    line(
      plot.x,
      plot.y + plot.height * fraction,
      plot.x + plot.width,
      plot.y + plot.height * fraction,
    );
  }
  context.strokeStyle = PALETTE.grid;
  context.setLineDash([5, 6]);
  line(plot.x + plot.width / 2, plot.y, plot.x + plot.width / 2, baseline);
  context.setLineDash([]);

  context.beginPath();
  context.moveTo(plot.x, baseline);
  for (let index = 0; index <= samples; index += 1) {
    const u = index / samples;
    context.lineTo(plot.x + u * plot.width, yFor(densityAt(u, phase)));
  }
  context.lineTo(plot.x + plot.width, baseline);
  context.closePath();
  context.fillStyle = "rgba(162, 79, 57, 0.15)";
  context.fill();

  context.beginPath();
  for (let index = 0; index <= samples; index += 1) {
    const u = index / samples;
    const x = plot.x + u * plot.width;
    const y = yFor(densityAt(u, phase));
    if (index === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  }
  strokePrinted(PALETTE.accent, compact ? 2.3 : 3);

  context.strokeStyle = PALETTE.ink;
  context.lineWidth = compact ? 3 : 4;
  line(plot.x, plot.y - 8, plot.x, baseline + 8);
  line(plot.x + plot.width, plot.y - 8, plot.x + plot.width, baseline + 8);
  context.lineWidth = 1;
  line(plot.x, baseline, plot.x + plot.width, baseline);

  const meanX = plot.x + mean * plot.width;
  context.strokeStyle = PALETTE.accentDark;
  context.lineWidth = 2;
  context.setLineDash([6, 5]);
  line(meanX, plot.y, meanX, baseline);
  context.setLineDash([]);
  context.fillStyle = PALETTE.accentDark;
  context.beginPath();
  context.arc(meanX, plot.y + 2, 4, 0, Math.PI * 2);
  context.fill();
  context.font = `600 ${compact ? 11 : 13}px "Times New Roman", Times, serif`;
  context.textAlign = mean < 0.55 ? "left" : "right";
  const meanLabel = `⟨x⟩ = ${mean.toFixed(4)}a`;
  const labelWidth = context.measureText(meanLabel).width + 14;
  const labelX = mean < 0.55 ? meanX + 7 : meanX - labelWidth - 7;
  context.fillStyle = "rgba(252, 251, 247, 0.94)";
  context.fillRect(labelX, plot.y + 7, labelWidth, 23);
  context.strokeStyle = PALETTE.grid;
  context.lineWidth = 1;
  context.strokeRect(labelX + 0.5, plot.y + 7.5, labelWidth - 1, 22);
  context.fillStyle = PALETTE.accentDark;
  context.textAlign = "left";
  context.fillText(meanLabel, labelX + 7, plot.y + 23);

  context.fillStyle = PALETTE.muted;
  context.font = `${compact ? 11 : 13}px "Times New Roman", Times, serif`;
  context.textAlign = "center";
  context.fillText("0", plot.x, height - 25);
  context.fillText("a/2", plot.x + plot.width / 2, height - 25);
  context.fillText("a", plot.x + plot.width, height - 25);
  context.fillText("position, x", plot.x + plot.width / 2, height - 7);
  context.textAlign = "left";
  context.fillText("a|Ψ|²", plot.x + 9, plot.y + 19);

  context.strokeStyle = PALETTE.ink;
  context.lineWidth = 1;
  for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
    const x = plot.x + plot.width * fraction;
    line(x, baseline, x, baseline + 6);
  }

  canvas.setAttribute(
    "aria-label",
    `Equal superposition of states one and two at relative phase ${state.phaseDegrees} degrees. Expected position ${mean.toFixed(
      4,
    )} times the box width; probability in the left half ${(
      leftProbability(phase) * 100
    ).toFixed(2)} percent.`,
  );
}

function updatePhase(value) {
  if (!state.evidence) return;
  state.phaseDegrees = Math.max(0, Math.min(360, Math.round(Number(value))));
  phaseControl.value = String(state.phaseDegrees);
  const phase = (state.phaseDegrees * Math.PI) / 180;
  const fraction = state.phaseDegrees / 360;
  const timeFs = state.evidence.derived.beat_period_fs * fraction;
  outputs.phase.textContent = `${state.phaseDegrees}°`;
  outputs.time.textContent = `${fraction.toFixed(3)}T · ${timeFs.toFixed(4)} fs`;
  outputs.position.textContent = `${expectedPosition(phase).toFixed(6)}a`;
  outputs.left.textContent = `${(leftProbability(phase) * 100).toFixed(3)}%`;
  outputs.energy.textContent = `${state.evidence.derived.mean_energy_ev.toFixed(6)} eV`;
  document.querySelectorAll("[data-phase-preset]").forEach((button) => {
    const active = Number(button.dataset.phasePreset) === state.phaseDegrees;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  drawSuperposition();
}

function downloadChart() {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `task07-superposition-${state.phaseDegrees}deg.png`;
    link.click();
    URL.revokeObjectURL(url);
  }, "image/png");
}

function showFailure(error) {
  lab.classList.remove("is-loading");
  phaseControl.disabled = true;
  document
    .querySelectorAll("[data-phase-preset]")
    .forEach((button) => (button.disabled = true));
  downloadButton.disabled = true;
  outputs.error.hidden = false;
  document.body.dataset.task07ExtensionStatus = "error";
  console.error("Task 7 superposition extension failed", error);
}

async function initialise() {
  try {
    const response = await fetch(evidenceUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(`Evidence request failed: ${response.status}`);
    state.evidence = validateEvidence(await response.json());
    document.body.dataset.task07ExtensionStatus = "ready";
    phaseControl.disabled = false;
    document.querySelectorAll("[data-phase-preset]").forEach((button) => {
      button.disabled = false;
      button.addEventListener("click", () => updatePhase(button.dataset.phasePreset));
    });
    downloadButton.disabled = false;
    lab.classList.remove("is-loading");
    phaseControl.addEventListener("input", () => updatePhase(phaseControl.value));
    downloadButton.addEventListener("click", downloadChart);
    const resizeObserver = new ResizeObserver(drawSuperposition);
    resizeObserver.observe(canvas);
    window.addEventListener("pagehide", () => resizeObserver.disconnect(), {
      once: true,
    });
    updatePhase(0);
    window.dispatchEvent(new CustomEvent("task07-extension:ready"));
  } catch (error) {
    showFailure(error);
  }
}

initialise();
