import {
  OFFICIAL_EXAMPLE,
  clampDisplayAngle,
  mismatchComparison,
  mismatchSweep,
} from "./physics.js";
import {
  SIMULATION_DEFAULT_PHOTON_PAIRS,
  SIMULATION_DEFAULT_SEED,
  SIMULATION_MAXIMUM_PHOTON_PAIRS,
  SIMULATION_MINIMUM_PHOTON_PAIRS,
  UINT32_MAXIMUM,
  advanceSeed,
  simulateFinitePhotonExperiment,
} from "./statistics.js";

const PRESETS = Object.freeze({
  official: OFFICIAL_EXAMPLE,
  zero: Object.freeze({ thetaDeg: 0, phiDeg: 0 }),
  aligned: Object.freeze({ thetaDeg: 45, phiDeg: 45 }),
  contrast: Object.freeze({ thetaDeg: -45, phiDeg: 45 }),
  perpendicular: Object.freeze({ thetaDeg: 0, phiDeg: 90 }),
});

const elements = {};
let state = { ...OFFICIAL_EXAMPLE };
let simulationState = {
  photonPairs: SIMULATION_DEFAULT_PHOTON_PAIRS,
  seed: SIMULATION_DEFAULT_SEED,
};
let renderedChartTheta = null;
const countFormatter = new Intl.NumberFormat("en-US");

const CHART = Object.freeze({
  left: 88,
  right: 1048,
  top: 30,
  bottom: 366,
  phiMinimum: -90,
  phiMaximum: 90,
  curveStep: 0.5,
});

function requiredElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing required calculator element: ${id}`);
  }
  return element;
}

function signedAngle(angleDeg) {
  if (Math.abs(angleDeg) < 0.0005) return "0°";
  const sign = angleDeg > 0 ? "+" : "−";
  return `${sign}${Math.abs(angleDeg).toFixed(0)}°`;
}

function decimal(value) {
  return value.toFixed(3);
}

function percent(value) {
  return `${(100 * value).toFixed(1)}%`;
}

function signedPoints(value) {
  const points = 100 * value;
  if (Math.abs(points) < 0.05) return "0.0 pp";
  return `${points > 0 ? "+" : "−"}${Math.abs(points).toFixed(1)} pp`;
}

function count(value) {
  return countFormatter.format(value);
}

function sampleResidual(value) {
  if (value === null) return "deterministic";
  if (Math.abs(value) < 0.005) return "0.00σ";
  return `${value > 0 ? "+" : "−"}${Math.abs(value).toFixed(2)}σ`;
}

function intervalPercent(interval) {
  return `${(100 * interval.lower).toFixed(1)}–${(
    100 * interval.upper
  ).toFixed(1)}%`;
}

function setPercentPosition(element, property, value) {
  const normalized = Math.min(100, Math.max(0, 100 * value));
  element.style[property] = `${normalized}%`;
}

function spokenAngle(angleDeg) {
  if (Math.abs(angleDeg) < 0.0005) return "zero degrees";
  return `${angleDeg > 0 ? "plus" : "minus"} ${Math.abs(angleDeg).toFixed(0)} degrees`;
}

function chartX(phiDeg) {
  return (
    CHART.left +
    ((phiDeg - CHART.phiMinimum) /
      (CHART.phiMaximum - CHART.phiMinimum)) *
      (CHART.right - CHART.left)
  );
}

function chartY(probability) {
  return CHART.top + (1 - probability) * (CHART.bottom - CHART.top);
}

function curvePath(points, probabilityKey) {
  return points
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command}${chartX(point.phiDeg).toFixed(2)},${chartY(
        point[probabilityKey],
      ).toFixed(2)}`;
    })
    .join(" ");
}

function keepChartMarkerVisible(currentX) {
  const frameWidth = elements.chartFrame.clientWidth;
  const chartWidth = elements.comparisonChart.getBoundingClientRect().width;
  if (chartWidth <= frameWidth) return;
  const markerPosition = (currentX / 1080) * chartWidth;
  const target = markerPosition - frameWidth / 2;
  elements.chartFrame.scrollLeft = Math.min(
    chartWidth - frameWidth,
    Math.max(0, target),
  );
}

function setLine(line, centerX, centerY, dx, dy) {
  line.setAttribute("x1", String(centerX - dx));
  line.setAttribute("y1", String(centerY - dy));
  line.setAttribute("x2", String(centerX + dx));
  line.setAttribute("y2", String(centerY + dy));
}

function setLabel(label, centerX, centerY, dx, dy) {
  label.setAttribute("x", String(centerX + 1.18 * dx));
  label.setAttribute("y", String(centerY + 1.18 * dy + 5));
  label.setAttribute("text-anchor", dx >= 0 ? "start" : "end");
}

function renderDetector(prefix, angleDeg) {
  const angleRad = (angleDeg * Math.PI) / 180;
  const radius = 63;
  const xDx = radius * Math.cos(angleRad);
  const xDy = -radius * Math.sin(angleRad);
  const yDx = -radius * Math.sin(angleRad);
  const yDy = -radius * Math.cos(angleRad);
  setLine(elements[`${prefix}XAxis`], 110, 110, xDx, xDy);
  setLine(elements[`${prefix}YAxis`], 110, 110, yDx, yDy);
  setLabel(elements[`${prefix}XLabel`], 110, 110, xDx, xDy);
  setLabel(elements[`${prefix}YLabel`], 110, 110, yDx, yDy);
  elements[`${prefix}DialAngle`].textContent = signedAngle(angleDeg);
  elements[`${prefix}Description`].textContent =
    `Orthogonal X and Y detector axes rotated to ${spokenAngle(angleDeg)}.`;
}

function renderComparisonChart(result) {
  if (renderedChartTheta !== state.thetaDeg) {
    const sweep = mismatchSweep(
      state.thetaDeg,
      CHART.phiMinimum,
      CHART.phiMaximum,
      CHART.curveStep,
    );
    elements.classicalCurve.setAttribute(
      "d",
      curvePath(sweep, "classicalMismatch"),
    );
    elements.quantumCurve.setAttribute(
      "d",
      curvePath(sweep, "quantumMismatch"),
    );
    renderedChartTheta = state.thetaDeg;
  }

  const currentX = chartX(state.phiDeg);
  elements.chartCurrentLine.setAttribute("x1", currentX.toFixed(2));
  elements.chartCurrentLine.setAttribute("x2", currentX.toFixed(2));
  elements.classicalMarker.setAttribute("cx", currentX.toFixed(2));
  elements.classicalMarker.setAttribute(
    "cy",
    chartY(result.classicalMismatch).toFixed(2),
  );
  elements.quantumMarker.setAttribute("cx", currentX.toFixed(2));
  elements.quantumMarker.setAttribute(
    "cy",
    chartY(result.quantumMismatch).toFixed(2),
  );
  keepChartMarkerVisible(currentX);
  elements.chartTheta.textContent = signedAngle(state.thetaDeg);
  elements.chartPhi.textContent = signedAngle(state.phiDeg);
  elements.chartDescription.textContent =
    `For detector A at ${spokenAngle(state.thetaDeg)}, the graph compares ` +
    `classical and quantum mismatch from minus 90 to plus 90 degrees for ` +
    `detector B. At the selected detector B angle of ${spokenAngle(state.phiDeg)}, ` +
    `the classical mismatch is ${percent(result.classicalMismatch)} and the ` +
    `quantum mismatch is ${percent(result.quantumMismatch)}.`;
}

function updatePhotonCountPresetState() {
  for (const button of elements.photonCountButtons) {
    const active = Number(button.dataset.photonPairs) === simulationState.photonPairs;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  }
}

function renderFiniteSample(prefix, sample) {
  elements[`${prefix}SampleTheory`].textContent = percent(
    sample.theoreticalProbability,
  );
  elements[`${prefix}SamplePercent`].textContent = percent(
    sample.observedProbability,
  );
  elements[`${prefix}SampleCount`].textContent = count(sample.mismatches);
  elements[`${prefix}SampleTotal`].textContent = count(sample.photonPairs);
  elements[`${prefix}ExpectedCount`].textContent =
    sample.expectedMismatches.toFixed(1);
  elements[`${prefix}CountSigma`].textContent =
    sample.standardDeviationCount.toFixed(2);
  elements[`${prefix}WilsonInterval`].textContent = intervalPercent(
    sample.wilsonInterval,
  );
  elements[`${prefix}SampleResidual`].textContent = sampleResidual(
    sample.standardizedResidual,
  );
  setPercentPosition(
    elements[`${prefix}IntervalBand`],
    "left",
    sample.wilsonInterval.lower,
  );
  setPercentPosition(
    elements[`${prefix}IntervalBand`],
    "width",
    sample.wilsonInterval.upper - sample.wilsonInterval.lower,
  );
  setPercentPosition(
    elements[`${prefix}TheoryMarker`],
    "left",
    sample.theoreticalProbability,
  );
  setPercentPosition(
    elements[`${prefix}ObservedMarker`],
    "left",
    sample.observedProbability,
  );
}

function renderFinitePhotonExperiment() {
  const experiment = simulateFinitePhotonExperiment(
    state.thetaDeg,
    state.phiDeg,
    simulationState.photonPairs,
    simulationState.seed,
  );
  elements.photonCount.value = String(simulationState.photonPairs);
  elements.simulationSeed.value = String(simulationState.seed);
  elements.simulationTheta.textContent = signedAngle(state.thetaDeg);
  elements.simulationPhi.textContent = signedAngle(state.phiDeg);
  elements.simulationPairs.textContent = count(simulationState.photonPairs);
  elements.simulationSeedOutput.textContent = count(simulationState.seed);
  renderFiniteSample("classical", experiment.classical);
  renderFiniteSample("quantum", experiment.quantum);

  const observedDifference =
    experiment.quantum.observedProbability -
    experiment.classical.observedProbability;
  const theoreticalDifference =
    experiment.quantum.theoreticalProbability -
    experiment.classical.theoreticalProbability;
  elements.observedSampleDifference.textContent = signedPoints(observedDifference);
  if (Math.abs(observedDifference - theoreticalDifference) < 0.0005) {
    elements.samplingSummaryText.textContent =
      `This sample matches the theoretical ${signedPoints(
        theoreticalDifference,
      )} difference to the displayed precision.`;
  } else {
    elements.samplingSummaryText.textContent =
      `This sample differs from the theoretical ${signedPoints(
        theoreticalDifference,
      )} because finite counts fluctuate.`;
  }
  updatePhotonCountPresetState();
  return experiment;
}

function announceFinitePhotonExperiment(experiment) {
  elements.simulationLive.textContent =
    `${count(experiment.photonPairs)} photon pairs, seed ${count(
      experiment.seed,
    )}. Classical sample: ${count(
      experiment.classical.mismatches,
    )} mismatches, ${percent(
      experiment.classical.observedProbability,
    )}. Quantum sample: ${count(
      experiment.quantum.mismatches,
    )} mismatches, ${percent(experiment.quantum.observedProbability)}.`;
}

function updatePresetState() {
  for (const button of elements.presetButtons) {
    const preset = PRESETS[button.dataset.preset];
    const active =
      preset.thetaDeg === state.thetaDeg && preset.phiDeg === state.phiDeg;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  }
}

function updateResults({ announceTheory = true, announceSimulation = false } = {}) {
  const result = mismatchComparison(state.thetaDeg, state.phiDeg);
  const classicalPercent = 100 * result.classicalMismatch;
  const quantumPercent = 100 * result.quantumMismatch;
  const differencePoints = 100 * result.signedDifference;

  elements.thetaRange.value = String(state.thetaDeg);
  elements.thetaNumber.value = String(state.thetaDeg);
  elements.phiRange.value = String(state.phiDeg);
  elements.phiNumber.value = String(state.phiDeg);
  elements.thetaValue.textContent = signedAngle(state.thetaDeg);
  elements.phiValue.textContent = signedAngle(state.phiDeg);
  elements.deltaValue.textContent = signedAngle(result.relativeAngleDeg);

  renderDetector("a", state.thetaDeg);
  renderDetector("b", state.phiDeg);

  elements.classicalPercent.textContent = percent(result.classicalMismatch);
  elements.classicalDecimal.textContent = `P = ${decimal(result.classicalMismatch)}`;
  elements.classicalFill.style.width = `${classicalPercent}%`;
  elements.classicalMeter.setAttribute("aria-valuenow", classicalPercent.toFixed(3));
  elements.classicalMeter.setAttribute(
    "aria-valuetext",
    `${classicalPercent.toFixed(1)} percent`,
  );
  elements.quantumPercent.textContent = percent(result.quantumMismatch);
  elements.quantumDecimal.textContent = `P = ${decimal(result.quantumMismatch)}`;
  elements.quantumFill.style.width = `${quantumPercent}%`;
  elements.quantumMeter.setAttribute("aria-valuenow", quantumPercent.toFixed(3));
  elements.quantumMeter.setAttribute(
    "aria-valuetext",
    `${quantumPercent.toFixed(1)} percent`,
  );
  elements.differenceValue.textContent = signedPoints(result.signedDifference);

  if (Math.abs(differencePoints) < 0.05) {
    elements.differenceSummary.textContent =
      "The two models predict the same mismatch probability at this setting.";
  } else {
    const direction = differencePoints > 0 ? "more" : "less";
    elements.differenceSummary.textContent = `The quantum model predicts ${Math.abs(
      differencePoints,
    ).toFixed(1)} percentage points ${direction} mismatch.`;
  }

  elements.classicalSubstitution.innerHTML =
    `θ = ${signedAngle(state.thetaDeg)}, φ = ${signedAngle(state.phiDeg)} ` +
    `→ P<sub>C</sub> = ${decimal(result.classicalMismatch)}`;
  elements.quantumSubstitution.innerHTML =
    `sin²(${signedAngle(state.phiDeg)} − (${signedAngle(state.thetaDeg)})) ` +
    `= sin²(${signedAngle(result.relativeAngleDeg)}) = ${decimal(
      result.quantumMismatch,
    )}`;

  renderComparisonChart(result);
  const finiteExperiment = renderFinitePhotonExperiment();
  if (announceTheory) {
    elements.liveResults.textContent =
      `Detector A ${spokenAngle(state.thetaDeg)}; detector B ${spokenAngle(
        state.phiDeg,
      )}. Classical mismatch ${percent(result.classicalMismatch)}; ` +
      `quantum mismatch ${percent(result.quantumMismatch)}. ` +
      elements.differenceSummary.textContent;
  }
  if (announceSimulation) announceFinitePhotonExperiment(finiteExperiment);

  updatePresetState();
}

function setAngles(thetaDeg, phiDeg) {
  state = {
    thetaDeg: clampDisplayAngle(thetaDeg),
    phiDeg: clampDisplayAngle(phiDeg),
  };
  updateResults();
}

function setSimulation(photonPairs, seed) {
  if (
    !Number.isInteger(photonPairs) ||
    photonPairs < SIMULATION_MINIMUM_PHOTON_PAIRS ||
    photonPairs > SIMULATION_MAXIMUM_PHOTON_PAIRS
  ) {
    throw new RangeError("photonPairs lies outside the approved simulation range");
  }
  if (!Number.isInteger(seed) || seed < 0 || seed > UINT32_MAXIMUM) {
    throw new RangeError("seed must be an unsigned 32-bit integer");
  }
  simulationState = { photonPairs, seed };
  updateResults({ announceTheory: false, announceSimulation: true });
}

function bindAngle(rangeElement, numberElement, key) {
  rangeElement.addEventListener("input", () => {
    setAngles(
      key === "thetaDeg" ? Number(rangeElement.value) : state.thetaDeg,
      key === "phiDeg" ? Number(rangeElement.value) : state.phiDeg,
    );
  });
  numberElement.addEventListener("input", () => {
    if (numberElement.value.trim() === "") return;
    const value = Number(numberElement.value);
    if (!Number.isFinite(value)) return;
    setAngles(
      key === "thetaDeg" ? value : state.thetaDeg,
      key === "phiDeg" ? value : state.phiDeg,
    );
  });
  numberElement.addEventListener("change", () => {
    if (numberElement.value.trim() === "") {
      numberElement.value = String(state[key]);
      return;
    }
    setAngles(state.thetaDeg, state.phiDeg);
  });
}

function bindSimulationNumber(element, key, minimum, maximum) {
  element.addEventListener("input", () => {
    if (element.value.trim() === "") return;
    const value = Number(element.value);
    if (!Number.isInteger(value) || value < minimum || value > maximum) return;
    setSimulation(
      key === "photonPairs" ? value : simulationState.photonPairs,
      key === "seed" ? value : simulationState.seed,
    );
  });
  element.addEventListener("change", () => {
    const value = Number(element.value);
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      element.value = String(simulationState[key]);
    }
  });
}

export function initializeCalculator() {
  Object.assign(elements, {
    thetaRange: requiredElement("theta-range"),
    thetaNumber: requiredElement("theta-number"),
    phiRange: requiredElement("phi-range"),
    phiNumber: requiredElement("phi-number"),
    thetaValue: requiredElement("theta-value"),
    phiValue: requiredElement("phi-value"),
    deltaValue: requiredElement("delta-value"),
    classicalPercent: requiredElement("classical-percent"),
    classicalDecimal: requiredElement("classical-decimal"),
    classicalFill: requiredElement("classical-fill"),
    classicalMeter: requiredElement("classical-meter"),
    quantumPercent: requiredElement("quantum-percent"),
    quantumDecimal: requiredElement("quantum-decimal"),
    quantumFill: requiredElement("quantum-fill"),
    quantumMeter: requiredElement("quantum-meter"),
    differenceValue: requiredElement("difference-value"),
    differenceSummary: requiredElement("difference-summary"),
    classicalSubstitution: requiredElement("classical-substitution"),
    quantumSubstitution: requiredElement("quantum-substitution"),
    liveResults: requiredElement("live-results"),
    chartTheta: requiredElement("chart-theta"),
    chartPhi: requiredElement("chart-phi"),
    chartDescription: requiredElement("comparison-chart-description"),
    comparisonChart: requiredElement("comparison-chart"),
    chartFrame: document.querySelector(".chart-frame"),
    classicalCurve: requiredElement("classical-curve"),
    quantumCurve: requiredElement("quantum-curve"),
    chartCurrentLine: requiredElement("chart-current-line"),
    classicalMarker: requiredElement("classical-marker"),
    quantumMarker: requiredElement("quantum-marker"),
    aXAxis: requiredElement("a-x-axis"),
    aYAxis: requiredElement("a-y-axis"),
    aXLabel: requiredElement("a-x-label"),
    aYLabel: requiredElement("a-y-label"),
    aDialAngle: requiredElement("a-dial-angle"),
    aDescription: requiredElement("detector-a-svg-description"),
    bXAxis: requiredElement("b-x-axis"),
    bYAxis: requiredElement("b-y-axis"),
    bXLabel: requiredElement("b-x-label"),
    bYLabel: requiredElement("b-y-label"),
    bDialAngle: requiredElement("b-dial-angle"),
    bDescription: requiredElement("detector-b-svg-description"),
    resetButton: requiredElement("reset-button"),
    presetButtons: [...document.querySelectorAll("[data-preset]")],
    photonCount: requiredElement("photon-count"),
    simulationSeed: requiredElement("simulation-seed"),
    simulationTheta: requiredElement("simulation-theta"),
    simulationPhi: requiredElement("simulation-phi"),
    simulationPairs: requiredElement("simulation-pairs"),
    simulationSeedOutput: requiredElement("simulation-seed-output"),
    observedSampleDifference: requiredElement("observed-sample-difference"),
    samplingSummaryText: requiredElement("sampling-summary-text"),
    simulationLive: requiredElement("simulation-live"),
    nextSampleButton: requiredElement("next-sample-button"),
    resetSimulationButton: requiredElement("reset-simulation-button"),
    photonCountButtons: [...document.querySelectorAll("[data-photon-pairs]")],
  });

  for (const prefix of ["classical", "quantum"]) {
    Object.assign(elements, {
      [`${prefix}SampleTheory`]: requiredElement(`${prefix}-sample-theory`),
      [`${prefix}SamplePercent`]: requiredElement(`${prefix}-sample-percent`),
      [`${prefix}SampleCount`]: requiredElement(`${prefix}-sample-count`),
      [`${prefix}SampleTotal`]: requiredElement(`${prefix}-sample-total`),
      [`${prefix}ExpectedCount`]: requiredElement(`${prefix}-expected-count`),
      [`${prefix}CountSigma`]: requiredElement(`${prefix}-count-sigma`),
      [`${prefix}WilsonInterval`]: requiredElement(`${prefix}-wilson-interval`),
      [`${prefix}SampleResidual`]: requiredElement(`${prefix}-sample-residual`),
      [`${prefix}IntervalBand`]: requiredElement(`${prefix}-interval-band`),
      [`${prefix}TheoryMarker`]: requiredElement(`${prefix}-theory-marker`),
      [`${prefix}ObservedMarker`]: requiredElement(`${prefix}-observed-marker`),
    });
  }

  if (!elements.chartFrame) {
    throw new Error("Missing required calculator element: .chart-frame");
  }

  bindAngle(elements.thetaRange, elements.thetaNumber, "thetaDeg");
  bindAngle(elements.phiRange, elements.phiNumber, "phiDeg");
  bindSimulationNumber(
    elements.photonCount,
    "photonPairs",
    SIMULATION_MINIMUM_PHOTON_PAIRS,
    SIMULATION_MAXIMUM_PHOTON_PAIRS,
  );
  bindSimulationNumber(elements.simulationSeed, "seed", 0, UINT32_MAXIMUM);
  elements.resetButton.addEventListener("click", () =>
    setAngles(OFFICIAL_EXAMPLE.thetaDeg, OFFICIAL_EXAMPLE.phiDeg),
  );
  for (const button of elements.presetButtons) {
    button.addEventListener("click", () => {
      const preset = PRESETS[button.dataset.preset];
      if (!preset) throw new Error(`Unknown preset: ${button.dataset.preset}`);
      setAngles(preset.thetaDeg, preset.phiDeg);
    });
  }
  for (const button of elements.photonCountButtons) {
    button.addEventListener("click", () =>
      setSimulation(Number(button.dataset.photonPairs), simulationState.seed),
    );
  }
  elements.nextSampleButton.addEventListener("click", () =>
    setSimulation(
      simulationState.photonPairs,
      advanceSeed(simulationState.seed),
    ),
  );
  elements.resetSimulationButton.addEventListener("click", () =>
    setSimulation(SIMULATION_DEFAULT_PHOTON_PAIRS, SIMULATION_DEFAULT_SEED),
  );
  updateResults();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeCalculator, { once: true });
} else {
  initializeCalculator();
}
