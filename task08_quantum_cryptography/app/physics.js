const DEG_TO_RAD = Math.PI / 180;
const POLARISATION_PERIOD_DEG = 180;
const PROBABILITY_TOLERANCE = 5e-15;

export const OFFICIAL_EXAMPLE = Object.freeze({ thetaDeg: -30, phiDeg: 30 });

function finiteNumber(value, name) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
  return value;
}

function probability(value, name) {
  const numeric = finiteNumber(value, name);
  if (
    numeric < -PROBABILITY_TOLERANCE ||
    numeric > 1 + PROBABILITY_TOLERANCE
  ) {
    throw new RangeError(`${name} fell outside [0, 1]`);
  }
  return Math.min(1, Math.max(0, numeric));
}

export function degreesToRadians(angleDeg) {
  return finiteNumber(angleDeg, "angleDeg") * DEG_TO_RAD;
}

export function normalizePolarisationAngleDeg(angleDeg) {
  const angle = finiteNumber(angleDeg, "angleDeg");
  return (
    ((angle + POLARISATION_PERIOD_DEG / 2) % POLARISATION_PERIOD_DEG +
      POLARISATION_PERIOD_DEG) %
      POLARISATION_PERIOD_DEG -
    POLARISATION_PERIOD_DEG / 2
  );
}

export function relativeDetectorAngleDeg(thetaDeg, phiDeg) {
  return normalizePolarisationAngleDeg(
    finiteNumber(phiDeg, "phiDeg") - finiteNumber(thetaDeg, "thetaDeg"),
  );
}

export function detectorProbabilities(angleDeg) {
  const angleRad = degreesToRadians(angleDeg);
  return Object.freeze({
    x: probability(Math.cos(angleRad) ** 2, "xProbability"),
    y: probability(Math.sin(angleRad) ** 2, "yProbability"),
  });
}

export function mismatchComparison(thetaDeg, phiDeg) {
  const theta = finiteNumber(thetaDeg, "thetaDeg");
  const phi = finiteNumber(phiDeg, "phiDeg");
  const detectorA = detectorProbabilities(theta);
  const detectorB = detectorProbabilities(phi);
  const classicalMatch = probability(
    detectorA.x * detectorB.x + detectorA.y * detectorB.y,
    "classicalMatch",
  );
  const classicalMismatch = probability(
    1 - classicalMatch,
    "classicalMismatch",
  );
  const relativeAngleDeg = relativeDetectorAngleDeg(theta, phi);
  const relativeAngleRad = degreesToRadians(relativeAngleDeg);
  const quantumMatch = probability(
    Math.cos(relativeAngleRad) ** 2,
    "quantumMatch",
  );
  const quantumMismatch = probability(
    Math.sin(relativeAngleRad) ** 2,
    "quantumMismatch",
  );

  return Object.freeze({
    thetaDeg: theta,
    phiDeg: phi,
    relativeAngleDeg,
    detectorA,
    detectorB,
    classicalMatch,
    classicalMismatch,
    quantumMatch,
    quantumMismatch,
    signedDifference: quantumMismatch - classicalMismatch,
  });
}

export function mismatchSweep(
  thetaDeg,
  phiMinimumDeg = -90,
  phiMaximumDeg = 90,
  stepDeg = 0.5,
) {
  const theta = finiteNumber(thetaDeg, "thetaDeg");
  const minimum = finiteNumber(phiMinimumDeg, "phiMinimumDeg");
  const maximum = finiteNumber(phiMaximumDeg, "phiMaximumDeg");
  const step = finiteNumber(stepDeg, "stepDeg");
  if (maximum <= minimum) {
    throw new RangeError("phiMaximumDeg must exceed phiMinimumDeg");
  }
  if (step <= 0) {
    throw new RangeError("stepDeg must be greater than zero");
  }

  const intervals = (maximum - minimum) / step;
  const roundedIntervals = Math.round(intervals);
  if (Math.abs(intervals - roundedIntervals) > 1e-10) {
    throw new RangeError("stepDeg must divide the phi range exactly");
  }
  if (roundedIntervals > 10_000) {
    throw new RangeError("mismatch sweep is limited to 10,001 points");
  }

  return Object.freeze(
    Array.from({ length: roundedIntervals + 1 }, (_, index) =>
      mismatchComparison(theta, minimum + index * step),
    ),
  );
}

export function clampDisplayAngle(angleDeg) {
  return Math.min(90, Math.max(-90, finiteNumber(angleDeg, "angleDeg")));
}
