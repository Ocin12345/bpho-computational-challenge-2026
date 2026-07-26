import { mismatchComparison } from "./physics.js";

export const SIMULATION_MINIMUM_PHOTON_PAIRS = 10;
export const SIMULATION_MAXIMUM_PHOTON_PAIRS = 100_000;
export const SIMULATION_DEFAULT_PHOTON_PAIRS = 1_000;
export const SIMULATION_DEFAULT_SEED = 2_026;
export const UINT32_MAXIMUM = 0xffffffff;
export const WILSON_95_Z = 1.959963984540054;

const UINT32_MODULUS = 0x1_0000_0000;
const MULBERRY32_INCREMENT = 0x6d2b79f5;
const CLASSICAL_STREAM_SALT = 0x243f6a88;
const QUANTUM_STREAM_SALT = 0xb7e15162;

function integer(value, name, minimum = 0, maximum = Number.MAX_SAFE_INTEGER) {
  if (!Number.isInteger(value)) {
    throw new TypeError(`${name} must be an integer`);
  }
  if (value < minimum || value > maximum) {
    throw new RangeError(`${name} must lie within [${minimum}, ${maximum}]`);
  }
  return value;
}

function probability(value, name = "probability") {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
  if (value < 0 || value > 1) {
    throw new RangeError(`${name} must lie within [0, 1]`);
  }
  return value;
}

function uint32(value, name = "seed") {
  return integer(value, name, 0, UINT32_MAXIMUM) >>> 0;
}

function createMulberry32(seed) {
  let state = uint32(seed);
  return () => {
    state = (state + MULBERRY32_INCREMENT) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return (value ^ (value >>> 14)) >>> 0;
  };
}

export function mulberry32Uint32Sequence(seed, count) {
  const length = integer(count, "count");
  const next = createMulberry32(seed);
  return Object.freeze(Array.from({ length }, () => next()));
}

export function mulberry32UniformSequence(seed, count) {
  return Object.freeze(
    mulberry32Uint32Sequence(seed, count).map(
      (value) => value / UINT32_MODULUS,
    ),
  );
}

export function derivedStreamSeed(seed, model) {
  const normalized = uint32(seed);
  if (model === "classical") return (normalized ^ CLASSICAL_STREAM_SALT) >>> 0;
  if (model === "quantum") return (normalized ^ QUANTUM_STREAM_SALT) >>> 0;
  throw new RangeError("model must be 'classical' or 'quantum'");
}

export function advanceSeed(seed) {
  return (uint32(seed) + 1) >>> 0;
}

export function binomialMismatchCount(photonPairs, theoreticalProbability, seed) {
  const count = integer(photonPairs, "photonPairs", 1);
  const threshold = probability(theoreticalProbability, "theoreticalProbability");
  const next = createMulberry32(seed);
  let mismatches = 0;
  for (let index = 0; index < count; index += 1) {
    if (next() / UINT32_MODULUS < threshold) mismatches += 1;
  }
  return mismatches;
}

export function wilsonInterval(
  mismatches,
  photonPairs,
  zValue = WILSON_95_Z,
) {
  const count = integer(photonPairs, "photonPairs", 1);
  const observedCount = integer(mismatches, "mismatches", 0, count);
  if (typeof zValue !== "number" || !Number.isFinite(zValue)) {
    throw new TypeError("zValue must be a finite number");
  }
  if (zValue <= 0) throw new RangeError("zValue must be greater than zero");
  const observed = observedCount / count;
  const zSquared = zValue * zValue;
  const denominator = 1 + zSquared / count;
  const center = (observed + zSquared / (2 * count)) / denominator;
  const halfWidth =
    (zValue / denominator) *
    Math.sqrt(
      (observed * (1 - observed)) / count +
        zSquared / (4 * count * count),
    );
  let lower = Math.max(0, center - halfWidth);
  let upper = Math.min(1, center + halfWidth);
  if (Math.abs(lower) <= 1e-15) lower = 0;
  if (Math.abs(upper - 1) <= 1e-15) upper = 1;
  return Object.freeze({ lower, upper });
}

function modelSample(model, theoreticalProbability, photonPairs, displayedSeed) {
  const streamSeed = derivedStreamSeed(displayedSeed, model);
  const mismatches = binomialMismatchCount(
    photonPairs,
    theoreticalProbability,
    streamSeed,
  );
  const expectedMismatches = photonPairs * theoreticalProbability;
  const standardDeviationCount = Math.sqrt(
    photonPairs * theoreticalProbability * (1 - theoreticalProbability),
  );
  const standardizedResidual =
    standardDeviationCount === 0
      ? null
      : (mismatches - expectedMismatches) / standardDeviationCount;
  return Object.freeze({
    model,
    streamSeed,
    photonPairs,
    mismatches,
    matches: photonPairs - mismatches,
    theoreticalProbability,
    observedProbability: mismatches / photonPairs,
    expectedMismatches,
    standardDeviationCount,
    standardizedResidual,
    wilsonInterval: wilsonInterval(mismatches, photonPairs),
  });
}

export function simulateFinitePhotonExperiment(
  thetaDeg,
  phiDeg,
  photonPairs = SIMULATION_DEFAULT_PHOTON_PAIRS,
  seed = SIMULATION_DEFAULT_SEED,
) {
  const count = integer(
    photonPairs,
    "photonPairs",
    SIMULATION_MINIMUM_PHOTON_PAIRS,
    SIMULATION_MAXIMUM_PHOTON_PAIRS,
  );
  const displayedSeed = uint32(seed);
  const comparison = mismatchComparison(thetaDeg, phiDeg);
  return Object.freeze({
    thetaDeg,
    phiDeg,
    photonPairs: count,
    seed: displayedSeed,
    classical: modelSample(
      "classical",
      comparison.classicalMismatch,
      count,
      displayedSeed,
    ),
    quantum: modelSample(
      "quantum",
      comparison.quantumMismatch,
      count,
      displayedSeed,
    ),
  });
}
