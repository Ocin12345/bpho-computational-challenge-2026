const DIMENSION_LABELS = {
  1: "One dimension",
  2: "Two dimensions",
  3: "Three dimensions",
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

function checkpoints(maxSteps) {
  const values = new Set(
    [1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2, 3 / 4, 1].map((fraction) =>
      Math.max(4, Math.min(maxSteps, Math.round(maxSteps * fraction))),
    ),
  );
  values.add(maxSteps);
  return [...values].sort((a, b) => a - b);
}

function fitThroughOrigin(x, y) {
  let xy = 0;
  let xx = 0;
  for (let index = 0; index < x.length; index += 1) {
    xy += x[index] * y[index];
    xx += x[index] ** 2;
  }
  const slope = xy / xx;
  let residualSquares = 0;
  for (let index = 0; index < x.length; index += 1) {
    residualSquares += (y[index] - slope * x[index]) ** 2;
  }
  const variance = residualSquares / Math.max(1, x.length - 1);
  return { slope, standardError: Math.sqrt(variance / xx) };
}

function fitPowerLaw(stepCounts, values) {
  const x = stepCounts.map(Math.log);
  const y = values.map(Math.log);
  const xMean = x.reduce((sum, value) => sum + value, 0) / x.length;
  const yMean = y.reduce((sum, value) => sum + value, 0) / y.length;
  let numerator = 0;
  let denominator = 0;
  for (let index = 0; index < x.length; index += 1) {
    numerator += (x[index] - xMean) * (y[index] - yMean);
    denominator += (x[index] - xMean) ** 2;
  }
  const exponent = numerator / denominator;
  const intercept = yMean - exponent * xMean;
  let residualSquares = 0;
  for (let index = 0; index < x.length; index += 1) {
    residualSquares += (y[index] - intercept - exponent * x[index]) ** 2;
  }
  const residualVariance = residualSquares / Math.max(1, x.length - 2);
  return {
    exponent,
    standardError: Math.sqrt(residualVariance / denominator),
  };
}

function theoryDensity(q, dimension) {
  if (dimension === 1) return Math.sqrt(2 / Math.PI) * Math.exp(-0.5 * q ** 2);
  if (dimension === 2) return 2 * q * Math.exp(-(q ** 2));
  return (
    Math.sqrt(2 / Math.PI) *
    3 *
    Math.sqrt(3) *
    q ** 2 *
    Math.exp(-1.5 * q ** 2)
  );
}

function runDimension({ dimension, nWalks, maxSteps, stepSize, seed }) {
  const random = mulberry32(
    (seed + Math.imul(dimension, 0x9e3779b1)) >>> 0,
  );
  const x = new Float64Array(nWalks);
  const y = new Float64Array(nWalks);
  const z = new Float64Array(nWalks);
  const marks = checkpoints(maxSteps);
  const markSet = new Set(marks);
  const scaling = [];

  for (let step = 1; step <= maxSteps; step += 1) {
    for (let walk = 0; walk < nWalks; walk += 1) {
      if (dimension === 1) {
        x[walk] += (random() < 0.5 ? -1 : 1) * stepSize;
      } else if (dimension === 2) {
        const angle = random() * Math.PI * 2;
        x[walk] += stepSize * Math.cos(angle);
        y[walk] += stepSize * Math.sin(angle);
      } else {
        const azimuth = random() * Math.PI * 2;
        const cosinePolar = random() * 2 - 1;
        const radialXY = Math.sqrt(Math.max(0, 1 - cosinePolar ** 2));
        x[walk] += stepSize * radialXY * Math.cos(azimuth);
        y[walk] += stepSize * radialXY * Math.sin(azimuth);
        z[walk] += stepSize * cosinePolar;
      }
    }

    if (markSet.has(step)) {
      let sumR2 = 0;
      let sumR4 = 0;
      for (let walk = 0; walk < nWalks; walk += 1) {
        const radiusSquared = x[walk] ** 2 + y[walk] ** 2 + z[walk] ** 2;
        sumR2 += radiusSquared;
        sumR4 += radiusSquared ** 2;
      }
      const meanSquaredDisplacement = sumR2 / nWalks;
      const sampleVariance = Math.max(
        0,
        (sumR4 - nWalks * meanSquaredDisplacement ** 2) /
          Math.max(1, nWalks - 1),
      );
      const msdStandardError = Math.sqrt(sampleVariance / nWalks);
      const rmsDisplacement = Math.sqrt(meanSquaredDisplacement);
      scaling.push({
        n_steps: step,
        mean_squared_displacement: meanSquaredDisplacement,
        msd_standard_error: msdStandardError,
        rms_displacement: rmsDisplacement,
        rms_standard_error:
          msdStandardError / (2 * Math.max(rmsDisplacement, Number.MIN_VALUE)),
      });
    }

    if (step % 24 === 0 || step === maxSteps) {
      const overall = ((dimension - 1) + step / maxSteps) / 3;
      self.postMessage({ type: "progress", progress: overall });
    }
  }

  const binCount = 36;
  const maximumQ = 3.6;
  const binWidth = maximumQ / binCount;
  const counts = new Uint32Array(binCount);
  const normalizedRadii = new Float64Array(nWalks);
  let acceptedRadii = 0;
  let meanX = 0;
  let meanY = 0;
  let meanZ = 0;
  for (let walk = 0; walk < nWalks; walk += 1) {
    const q = Math.hypot(x[walk], y[walk], z[walk]) / (stepSize * Math.sqrt(maxSteps));
    normalizedRadii[walk] = q;
    const bin = Math.floor(q / binWidth);
    if (bin >= 0 && bin < binCount) {
      counts[bin] += 1;
      acceptedRadii += 1;
    }
    meanX += x[walk];
    meanY += y[walk];
    meanZ += z[walk];
  }

  const binEdges = Array.from({ length: binCount + 1 }, (_, index) => index * binWidth);
  const binCentres = Array.from({ length: binCount }, (_, index) => (index + 0.5) * binWidth);
  const density = [...counts].map((count) => count / (acceptedRadii * binWidth));
  const theory = binCentres.map((q) => theoryDensity(q, dimension));
  const stepCounts = scaling.map((point) => point.n_steps);
  const normalizedRms = scaling.map((point) => point.rms_displacement / stepSize);
  const slopeFit = fitThroughOrigin(stepCounts.map(Math.sqrt), normalizedRms);
  const powerFit = fitPowerLaw(stepCounts, normalizedRms);

  return {
    dimension,
    label: DIMENSION_LABELS[dimension],
    mean_endpoint: [meanX / nWalks, meanY / nWalks, meanZ / nWalks].slice(0, dimension),
    distribution: {
      variable: "q = |R| / (s sqrt(N))",
      bin_edges: binEdges,
      bin_centres: binCentres,
      density,
      theory_density: theory,
      sample_count: nWalks,
    },
    scaling,
    fit: {
      model: "r_RMS / s = a sqrt(N)",
      slope: slopeFit.slope,
      slope_standard_error: slopeFit.standardError,
      slope_ci95_half_width: 1.96 * slopeFit.standardError,
      power_model: "r_RMS / s = A N^alpha",
      exponent: powerFit.exponent,
      exponent_standard_error: powerFit.standardError,
      exponent_ci95_half_width: 1.96 * powerFit.standardError,
    },
  };
}

self.addEventListener("message", (event) => {
  if (event.data?.type !== "run") return;
  try {
    const parameters = event.data.parameters;
    const dimensions = [1, 2, 3].map((dimension) =>
      runDimension({ dimension, ...parameters }),
    );
    self.postMessage({
      type: "complete",
      payload: {
        schema_version: 1,
        accepted: null,
        source: "custom exact browser run",
        parameters: {
          n_walks: parameters.nWalks,
          max_steps: parameters.maxSteps,
          step_size: parameters.stepSize,
          master_seed: parameters.seed,
        },
        dimensions,
      },
    });
  } catch (error) {
    self.postMessage({
      type: "error",
      message: error instanceof Error ? error.message : "Unknown worker error",
    });
  }
});
