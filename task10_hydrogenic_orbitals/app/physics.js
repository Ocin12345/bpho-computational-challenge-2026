export const CONSTANTS = Object.freeze({
  electronMassKg: 9.1093837139e-31,
  atomicMassConstantKg: 1.66053906892e-27,
  bohrRadiusM: 5.29177210544e-11,
  hartreeEnergyEv: 27.211386245981,
  angstromM: 1e-10,
});

export const FAMILY_LABELS = Object.freeze(["S", "P", "D", "F", "G", "H", "I", "K"]);

function requireFinite(name, value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
  return value;
}

function requireInteger(name, value) {
  if (!Number.isInteger(value)) throw new TypeError(`${name} must be an integer`);
  return value;
}

function factorial(value) {
  requireInteger("factorial argument", value);
  if (value < 0) throw new RangeError("factorial argument must be non-negative");
  let result = 1;
  for (let index = 2; index <= value; index += 1) result *= index;
  return result;
}

export function defaultMassNumber(atomicNumber) {
  requireInteger("atomic number", atomicNumber);
  if (atomicNumber < 1 || atomicNumber > 20) throw new RangeError("Z must be in [1, 20]");
  return atomicNumber === 1 ? 1 : 2 * atomicNumber;
}

export function validateState(input) {
  if (!input || typeof input !== "object") throw new TypeError("state must be an object");
  const n = requireInteger("n", input.n);
  const l = requireInteger("l", input.l);
  const m = requireInteger("m", input.m);
  const Z = requireInteger("Z", input.Z ?? 1);
  const A = requireInteger("A", input.A ?? defaultMassNumber(Z));
  if (n < 1 || n > 8) throw new RangeError("n must be in [1, 8]");
  if (l < 0 || l >= n) throw new RangeError("l must satisfy 0 <= l < n");
  if (m < -l || m > l) throw new RangeError("m must satisfy -l <= m <= l");
  if (Z < 1 || Z > 20) throw new RangeError("Z must be in [1, 20]");
  if (A < Z || A > 3 * Z) throw new RangeError("A must satisfy Z <= A <= 3Z");
  return Object.freeze({ n, l, m, Z, A });
}

export function stateLabel(input) {
  const state = validateState(input);
  return `${state.n}${FAMILY_LABELS[state.l].toLowerCase()} (m=${state.m >= 0 ? "+" : ""}${state.m})`;
}

export function officialGalleryStates() {
  const states = [];
  for (let l = 0; l <= 4; l += 1) {
    for (let m = -l; m <= l; m += 1) states.push(validateState({ n: l + 1, l, m, Z: 1, A: 1 }));
  }
  return Object.freeze(states);
}

export function reducedMassRatio(input) {
  const state = validateState(input);
  const nuclearMass = state.A * CONSTANTS.atomicMassConstantKg;
  return nuclearMass / (CONSTANTS.electronMassKg + nuclearMass);
}

export function stateSummary(input) {
  const state = validateState(input);
  const muRatio = reducedMassRatio(state);
  const effectiveBohrRadiusM = CONSTANTS.bohrRadiusM / (muRatio * state.Z);
  return Object.freeze({
    state,
    reducedMassRatio: muRatio,
    effectiveBohrRadiusM,
    effectiveBohrRadiusAngstrom: effectiveBohrRadiusM / CONSTANTS.angstromM,
    energyEv: -0.5 * CONSTANTS.hartreeEnergyEv * muRatio * state.Z ** 2 / state.n ** 2,
    radialNodes: state.n - state.l - 1,
    angularNodes: state.l,
    degeneracy: 2 * state.l + 1,
    parity: state.l % 2 === 0 ? 1 : -1,
  });
}

export function associatedLaguerre(order, alpha, x) {
  requireInteger("order", order);
  requireInteger("alpha", alpha);
  requireFinite("x", x);
  if (order < 0 || alpha < 0) throw new RangeError("order and alpha must be non-negative");
  if (order === 0) return 1;
  let previous = 1;
  let current = 1 + alpha - x;
  if (order === 1) return current;
  for (let degree = 2; degree <= order; degree += 1) {
    const following = ((2 * degree - 1 + alpha - x) * current - (degree - 1 + alpha) * previous) / degree;
    previous = current;
    current = following;
  }
  return current;
}

export function associatedFerrers(l, m, x) {
  requireInteger("l", l);
  requireInteger("m", m);
  requireFinite("x", x);
  if (l < 0 || m < 0 || m > l) throw new RangeError("require 0 <= m <= l");
  if (x < -1 - 2e-15 || x > 1 + 2e-15) throw new RangeError("x must be in [-1, 1]");
  const bounded = Math.max(-1, Math.min(1, x));
  let pmm = 1;
  if (m > 0) {
    const root = Math.sqrt(Math.max(0, (1 - bounded) * (1 + bounded)));
    for (let index = 1; index <= m; index += 1) pmm *= (2 * index - 1) * root;
  }
  if (l === m) return pmm;
  let current = (2 * m + 1) * bounded * pmm;
  if (l === m + 1) return current;
  let previous = pmm;
  for (let degree = m + 2; degree <= l; degree += 1) {
    const following = ((2 * degree - 1) * bounded * current - (degree + m - 1) * previous) / (degree - m);
    previous = current;
    current = following;
  }
  return current;
}

export function realSphericalHarmonic(l, m, polar, azimuth) {
  requireInteger("l", l);
  requireInteger("m", m);
  requireFinite("polar", polar);
  requireFinite("azimuth", azimuth);
  if (l < 0 || Math.abs(m) > l) throw new RangeError("require |m| <= l");
  if (polar < -2e-15 || polar > Math.PI + 2e-15) throw new RangeError("polar must be in [0, pi]");
  const boundedPolar = Math.max(0, Math.min(Math.PI, polar));
  const mAbs = Math.abs(m);
  const normalization = Math.sqrt(((2 * l + 1) / (4 * Math.PI)) * factorial(l - mAbs) / factorial(l + mAbs));
  const ferrers = associatedFerrers(l, mAbs, Math.cos(boundedPolar));
  if (m < 0) return Math.SQRT2 * normalization * ferrers * Math.sin(mAbs * azimuth);
  if (m > 0) return Math.SQRT2 * normalization * ferrers * Math.cos(m * azimuth);
  return normalization * ferrers;
}

export function scaledRadialWavefunction(input, radiusOverA) {
  const state = validateState(input);
  requireFinite("radiusOverA", radiusOverA);
  if (radiusOverA < 0) throw new RangeError("radiusOverA must be non-negative");
  const order = state.n - state.l - 1;
  const alpha = 2 * state.l + 1;
  const rho = 2 * radiusOverA / state.n;
  const prefactor = Math.sqrt(factorial(order) / (2 * state.n * factorial(state.n + state.l))) * (2 / state.n) ** 1.5;
  return prefactor * Math.exp(-rho / 2) * rho ** state.l * associatedLaguerre(order, alpha, rho);
}

export function scaledDensityCartesian(input, xOverA, yOverA, zOverA) {
  const state = validateState(input);
  requireFinite("xOverA", xOverA);
  requireFinite("yOverA", yOverA);
  requireFinite("zOverA", zOverA);
  const radius = Math.hypot(xOverA, yOverA, zOverA);
  const polar = radius === 0 ? 0 : Math.acos(Math.max(-1, Math.min(1, zOverA / radius)));
  const azimuth = Math.atan2(yOverA, xOverA);
  const wavefunction = scaledRadialWavefunction(state, radius) * realSphericalHarmonic(state.l, state.m, polar, azimuth);
  return wavefunction ** 2;
}

export function densityAtScaledCoordinate(input, xScaled, yScaled, zScaled) {
  const state = validateState(input);
  const factor = state.n ** 2;
  return scaledDensityCartesian(state, factor * xScaled, factor * yScaled, factor * zScaled);
}

export function createScaledDensityEvaluator(input) {
  const state = validateState(input);
  const factor = state.n ** 2;
  const order = state.n - state.l - 1;
  const alpha = 2 * state.l + 1;
  const radialPrefactor = Math.sqrt(factorial(order) / (2 * state.n * factorial(state.n + state.l))) * (2 / state.n) ** 1.5;
  const mAbs = Math.abs(state.m);
  const angularNormalization = Math.sqrt(((2 * state.l + 1) / (4 * Math.PI)) * factorial(state.l - mAbs) / factorial(state.l + mAbs));
  return (xScaled, yScaled, zScaled) => {
    const x = factor * xScaled;
    const y = factor * yScaled;
    const z = factor * zScaled;
    const radius = Math.hypot(x, y, z);
    const rho = 2 * radius / state.n;
    const radial = radialPrefactor * Math.exp(-rho / 2) * rho ** state.l * associatedLaguerre(order, alpha, rho);
    const polarCosine = radius === 0 ? 1 : Math.max(-1, Math.min(1, z / radius));
    const ferrers = associatedFerrers(state.l, mAbs, polarCosine);
    const azimuth = Math.atan2(y, x);
    const angular = state.m < 0
      ? Math.SQRT2 * angularNormalization * ferrers * Math.sin(mAbs * azimuth)
      : state.m > 0
        ? Math.SQRT2 * angularNormalization * ferrers * Math.cos(state.m * azimuth)
        : angularNormalization * ferrers;
    return (radial * angular) ** 2;
  };
}

function requireSampling(extent, resolution) {
  requireFinite("extent", extent);
  requireInteger("resolution", resolution);
  if (extent <= 0 || extent > 8) throw new RangeError("extent must be in (0, 8]");
  if (resolution < 21 || resolution > 181 || resolution % 2 === 0) throw new RangeError("resolution must be odd in [21, 181]");
}

export function sampleSliceStack(input, { extent = 3.2, resolution = 61, sliceCount = 17 } = {}) {
  const state = validateState(input);
  requireSampling(extent, resolution);
  requireInteger("sliceCount", sliceCount);
  if (sliceCount < 5 || sliceCount > 31 || sliceCount % 2 === 0) throw new RangeError("sliceCount must be odd in [5, 31]");
  const evaluate = createScaledDensityEvaluator(state);
  const slices = [];
  let maximum = 0;
  for (let sliceIndex = 0; sliceIndex < sliceCount; sliceIndex += 1) {
    const z = -extent + (2 * extent * sliceIndex) / (sliceCount - 1);
    const values = new Float64Array(resolution * resolution);
    for (let row = 0; row < resolution; row += 1) {
      const y = -extent + (2 * extent * row) / (resolution - 1);
      for (let column = 0; column < resolution; column += 1) {
        const x = -extent + (2 * extent * column) / (resolution - 1);
        const value = evaluate(x, y, z);
        values[row * resolution + column] = value;
        if (value > maximum) maximum = value;
      }
    }
    slices.push(Object.freeze({ z, values }));
  }
  if (!(maximum > 0) || !Number.isFinite(maximum)) throw new Error("sampled density has no finite positive maximum");
  return Object.freeze({ state, extent, resolution, sliceCount, maximum, slices: Object.freeze(slices) });
}

export function sampleOrthogonalSlices(input, { extent = 3.2, resolution = 81 } = {}) {
  const state = validateState(input);
  requireSampling(extent, resolution);
  const evaluate = createScaledDensityEvaluator(state);
  const planes = [];
  let maximum = 0;
  for (const plane of ["xy", "xz", "yz"]) {
    const values = new Float64Array(resolution * resolution);
    for (let row = 0; row < resolution; row += 1) {
      const vertical = -extent + (2 * extent * row) / (resolution - 1);
      for (let column = 0; column < resolution; column += 1) {
        const horizontal = -extent + (2 * extent * column) / (resolution - 1);
        const coordinates = plane === "xy" ? [horizontal, vertical, 0] : plane === "xz" ? [horizontal, 0, vertical] : [0, horizontal, vertical];
        const value = evaluate(...coordinates);
        values[row * resolution + column] = value;
        if (value > maximum) maximum = value;
      }
    }
    planes.push(Object.freeze({ plane, values }));
  }
  return Object.freeze({ state, extent, resolution, maximum, planes: Object.freeze(planes) });
}

export function radialProfile(input, { extent = 6, samples = 401 } = {}) {
  const state = validateState(input);
  requireFinite("extent", extent);
  requireInteger("samples", samples);
  if (extent <= 0 || extent > 12 || samples < 51 || samples > 4001) throw new RangeError("invalid radial sampling");
  const result = [];
  for (let index = 0; index < samples; index += 1) {
    const scaledRadius = extent * index / (samples - 1);
    const radiusOverA = state.n ** 2 * scaledRadius;
    const radial = scaledRadialWavefunction(state, radiusOverA);
    result.push(Object.freeze({
      scaledRadius,
      probabilityPerScaledRadius: state.n ** 2 * radiusOverA ** 2 * radial ** 2,
    }));
  }
  return Object.freeze(result);
}
