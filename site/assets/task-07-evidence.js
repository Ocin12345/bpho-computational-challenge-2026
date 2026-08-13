const URLS = {
  energies: new URL("../../data/task07/energy_levels.csv", import.meta.url),
  states: new URL("../../data/task07/stationary_states.csv", import.meta.url),
  expectations: new URL(
    "../../data/task07/expectation_values.csv",
    import.meta.url,
  ),
  numerical: new URL(
    "../../data/task07/numerical_eigenvalues.csv",
    import.meta.url,
  ),
  numericalMoments: new URL(
    "../../data/task07/numerical_moments.csv",
    import.meta.url,
  ),
  uncertaintyConvergence: new URL(
    "../../data/task07/uncertainty_convergence.csv",
    import.meta.url,
  ),
  anchors: new URL("../../data/task07/reference_anchors.json", import.meta.url),
  validation: new URL(
    "../../data/task07/validation_report.json",
    import.meta.url,
  ),
  manifest: new URL("../../data/task07/manifest.json", import.meta.url),
};

function parseCsv(text, label) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) throw new Error(`${label} CSV is empty`);
  const headers = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const fields = line.split(",");
    if (fields.length !== headers.length) {
      throw new Error(`${label} CSV has a malformed row`);
    }
    return Object.fromEntries(
      headers.map((header, index) => [header, fields[index]]),
    );
  });
}

function finiteNumber(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error(`${label} is not finite`);
  return number;
}

function optionalFinite(value, label) {
  return value === "" ? null : finiteNumber(value, label);
}

function relativeError(observed, expected) {
  if (expected === 0) return Math.abs(observed);
  return Math.abs(observed - expected) / Math.abs(expected);
}

function validateManifest(manifest) {
  const config = manifest.configuration;
  const constants = manifest.constants;
  if (
    manifest.schema_version !== "task07-manifest-v1" ||
    manifest.output_schema_version !== "task07-data-v1" ||
    manifest.validation_passed !== true ||
    manifest.validation_check_count !== 50 ||
    manifest.model !== "one-dimensional non-relativistic infinite square well" ||
    manifest.figure_font_family !== "Times New Roman" ||
    !config ||
    config.schema_version !== "task07-v1" ||
    config.particle_identifier !== "electron" ||
    config.particle_mass_kg !== 9.1093837139e-31 ||
    config.box_width_m !== 1e-9 ||
    config.maximum_quantum_number !== 10 ||
    config.position_point_count !== 2001 ||
    JSON.stringify(config.density_quantum_numbers) !== "[1,2,3,4]" ||
    JSON.stringify(config.numerical_grid_sizes) !== "[100,200,400,800,1600]" ||
    !constants ||
    constants.planck_constant_j_s !== 6.62607015e-34 ||
    constants.elementary_charge_c !== 1.602176634e-19 ||
    constants.electron_mass_kg !== 9.1093837139e-31 ||
    !String(manifest.equations?.energy).includes("n^2") ||
    !String(manifest.equations?.uncertainty).includes("1/2")
  ) {
    throw new Error("Task 7 manifest is unsupported");
  }
}

function validateReport(report, manifest) {
  if (
    report.schema_version !== "task07-validation-v1" ||
    report.passed !== true ||
    report.study_digest !== manifest.study_digest ||
    !Array.isArray(report.checks) ||
    report.checks.length !== 50 ||
    !report.checks.every(
      (check) =>
        check.passed === true &&
        Number.isFinite(check.observed) &&
        Number.isFinite(check.expected) &&
        Number.isFinite(check.tolerance),
    )
  ) {
    throw new Error("The committed Task 7 validation report is not locked");
  }
}

function validateEnergies(rows, manifest) {
  if (rows.length !== 10) throw new Error("Task 7 requires ten energy levels");
  const { reduced_planck_constant_j_s: hbar } = manifest.constants;
  const { particle_mass_kg: mass, box_width_m: width } =
    manifest.configuration;
  const ground = (Math.PI ** 2 * hbar ** 2) / (2 * mass * width ** 2);

  return rows.map((row, index) => {
    const n = finiteNumber(row.quantum_number_n, "quantum number");
    const energyJ = finiteNumber(row.energy_j, "energy");
    const energyEv = finiteNumber(row.energy_ev, "energy in eV");
    const energyOverGround = finiteNumber(
      row.energy_over_ground,
      "scaled energy",
    );
    const gapToNextJ = optionalFinite(row.gap_to_next_j, "energy gap");
    const gapToNextEv = optionalFinite(row.gap_to_next_ev, "energy gap in eV");
    const expected = ground * n ** 2;

    if (
      n !== index + 1 ||
      relativeError(energyJ, expected) > 5e-12 ||
      relativeError(energyEv, energyJ / manifest.constants.elementary_charge_c) >
        5e-12 ||
      relativeError(energyOverGround, n ** 2) > 5e-12 ||
      (n < 10 &&
        (gapToNextJ === null ||
          relativeError(gapToNextJ, ground * (2 * n + 1)) > 5e-12 ||
          gapToNextEv === null)) ||
      (n === 10 && (gapToNextJ !== null || gapToNextEv !== null))
    ) {
      throw new Error(`Energy row n=${n} failed validation`);
    }
    return { n, energyJ, energyEv, energyOverGround, gapToNextJ, gapToNextEv };
  });
}

function validateStates(rows, manifest) {
  if (rows.length !== 2001 * 4) {
    throw new Error("Task 7 stationary-state grid is incomplete");
  }
  const width = manifest.configuration.box_width_m;
  const scale = Math.sqrt(2 / width);
  const states = new Map([1, 2, 3, 4].map((n) => [n, []]));

  rows.forEach((row, rowIndex) => {
    const positionIndex = finiteNumber(row.position_index, "position index");
    const n = finiteNumber(row.quantum_number_n, "state quantum number");
    const positionM = finiteNumber(row.position_m, "position");
    const positionNm = finiteNumber(row.position_nm, "position in nm");
    const u = finiteNumber(row.position_over_box_width, "normalized position");
    const psi = finiteNumber(row.wavefunction_m_neg_half, "wavefunction");
    const density = finiteNumber(
      row.probability_density_m_inv,
      "probability density",
    );
    const scaledDensity = finiteNumber(
      row.box_width_times_density,
      "scaled density",
    );
    const expectedIndex = Math.floor(rowIndex / 4);
    const expectedN = (rowIndex % 4) + 1;
    const expectedU = expectedIndex / 2000;
    const expectedPsi = scale * Math.sin(expectedN * Math.PI * expectedU);

    if (
      positionIndex !== expectedIndex ||
      n !== expectedN ||
      relativeError(positionM, expectedU * width) > 5e-12 ||
      relativeError(positionNm, expectedU) > 5e-12 ||
      Math.abs(u - expectedU) > 1e-14 ||
      Math.abs(psi / scale - expectedPsi / scale) > 2e-14 ||
      Math.abs(scaledDensity - 2 * Math.sin(n * Math.PI * u) ** 2) > 5e-13 ||
      relativeError(density, psi ** 2) > 5e-11
    ) {
      throw new Error(`Stationary-state row ${rowIndex} failed validation`);
    }
    states.get(n).push({ positionIndex, positionM, positionNm, u, psi, density, scaledDensity });
  });
  return states;
}

function validateExpectations(rows, manifest) {
  if (rows.length !== 10) {
    throw new Error("Task 7 expectation-value catalogue is incomplete");
  }
  const width = manifest.configuration.box_width_m;
  const hbar = manifest.constants.reduced_planck_constant_j_s;
  return rows.map((row, index) => {
    const n = finiteNumber(row.quantum_number_n, "expectation quantum number");
    const expectedX = finiteNumber(row.expected_x_m, "expected position");
    const expectedXSquared = finiteNumber(
      row.expected_x_squared_m2,
      "expected position squared",
    );
    const deltaX = finiteNumber(row.delta_x_m, "position uncertainty");
    const expectedP = finiteNumber(row.expected_p_kg_m_s, "expected momentum");
    const expectedPSquared = finiteNumber(
      row.expected_p_squared_kg2_m2_s2,
      "expected momentum squared",
    );
    const deltaP = finiteNumber(row.delta_p_kg_m_s, "momentum uncertainty");
    const product = finiteNumber(row.delta_x_delta_p_j_s, "uncertainty product");
    const productOverHbar = finiteNumber(
      row.delta_x_delta_p_over_hbar,
      "scaled uncertainty product",
    );
    const expectedProduct = Math.sqrt((n ** 2 * Math.PI ** 2) / 12 - 0.5);
    if (
      n !== index + 1 ||
      relativeError(expectedX, width / 2) > 5e-12 ||
      relativeError(
        expectedXSquared,
        width ** 2 * (1 / 3 - 1 / (2 * n ** 2 * Math.PI ** 2)),
      ) > 5e-12 ||
      relativeError(
        deltaX,
        width * Math.sqrt(1 / 12 - 1 / (2 * n ** 2 * Math.PI ** 2)),
      ) > 5e-12 ||
      expectedP !== 0 ||
      relativeError(expectedPSquared, (n * Math.PI * hbar / width) ** 2) >
        5e-12 ||
      relativeError(deltaP, n * Math.PI * hbar / width) > 5e-12 ||
      relativeError(product, deltaX * deltaP) > 5e-12 ||
      relativeError(productOverHbar, expectedProduct) > 5e-12 ||
      productOverHbar < 0.5
    ) {
      throw new Error(`Expectation row n=${n} failed validation`);
    }
    return {
      n,
      expectedX,
      expectedXSquared,
      deltaX,
      expectedP,
      expectedPSquared,
      deltaP,
      product,
      productOverHbar,
    };
  });
}

function validateNumerical(rows, energies) {
  if (rows.length !== 50) {
    throw new Error("Task 7 numerical convergence study is incomplete");
  }
  const grids = [100, 200, 400, 800, 1600];
  return rows.map((row, index) => {
    const grid = finiteNumber(row.interior_point_count, "numerical grid size");
    const n = finiteNumber(row.quantum_number_n, "numerical quantum number");
    const numericalEnergyEv = finiteNumber(
      row.numerical_energy_ev,
      "numerical energy",
    );
    const analyticalEnergyEv = finiteNumber(
      row.analytical_energy_ev,
      "analytical comparison energy",
    );
    const relativeEnergyError = finiteNumber(
      row.relative_energy_error,
      "relative numerical error",
    );
    const order = finiteNumber(
      row.observed_convergence_order,
      "convergence order",
    );
    const overlap = optionalFinite(
      row.finest_grid_absolute_overlap,
      "eigenfunction overlap",
    );
    const expectedGrid = grids[Math.floor(index / 10)];
    const expectedN = (index % 10) + 1;
    if (
      grid !== expectedGrid ||
      n !== expectedN ||
      relativeError(analyticalEnergyEv, energies[n - 1].energyEv) > 5e-12 ||
      relativeError(
        relativeEnergyError,
        Math.abs(numericalEnergyEv - analyticalEnergyEv) /
          analyticalEnergyEv,
      ) > 5e-9 ||
      order < 1.998 ||
      order > 2.001 ||
      (grid === 1600 ? overlap === null || overlap < 0.9999999999999 : overlap !== null)
    ) {
      throw new Error(`Numerical row ${index} failed validation`);
    }
    return {
      grid,
      n,
      numericalEnergyEv,
      analyticalEnergyEv,
      relativeEnergyError,
      order,
      overlap,
    };
  });
}

function validateNumericalMoments(rows, manifest) {
  if (rows.length !== 50) {
    throw new Error("Task 7 numerical moment catalogue is incomplete");
  }
  const grids = [100, 200, 400, 800, 1600];
  const width = manifest.configuration.box_width_m;
  const hbar = manifest.constants.reduced_planck_constant_j_s;
  return rows.map((row, index) => {
    const grid = finiteNumber(row.interior_point_count, "moment grid size");
    const n = finiteNumber(row.quantum_number_n, "moment quantum number");
    const expectedGrid = grids[Math.floor(index / 10)];
    const expectedN = (index % 10) + 1;
    const normalization = finiteNumber(row.normalization, "moment normalization");
    const expectedX = finiteNumber(row.expected_x_m_numeric, "numerical expected x");
    const expectedXSquared = finiteNumber(
      row.expected_x_squared_m2_numeric,
      "numerical expected x squared",
    );
    const pMeanReal = finiteNumber(
      row.p_mean_real_kg_m_s_numeric,
      "numerical p mean real part",
    );
    const pMeanImaginary = finiteNumber(
      row.p_mean_imaginary_kg_m_s_numeric,
      "numerical p mean imaginary part",
    );
    const pSquared = finiteNumber(
      row.p_squared_kg2_m2_s2_numeric,
      "numerical p squared",
    );
    const deltaX = finiteNumber(row.delta_x_m_numeric, "numerical delta x");
    const deltaP = finiteNumber(row.delta_p_kg_m_s_numeric, "numerical delta p");
    const product = finiteNumber(
      row.uncertainty_product_over_hbar_numeric,
      "numerical uncertainty product",
    );
    const ratio = finiteNumber(row.heisenberg_ratio_numeric, "numerical Heisenberg ratio");
    const analyticalDeltaX = width * Math.sqrt(1 / 12 - 1 / (2 * n ** 2 * Math.PI ** 2));
    const analyticalDeltaP = n * Math.PI * hbar / width;
    const analyticalProduct = Math.sqrt(n ** 2 * Math.PI ** 2 / 12 - 0.5);
    if (
      grid !== expectedGrid ||
      n !== expectedN ||
      Math.abs(normalization - 1) > 5e-12 ||
      Math.hypot(pMeanReal, pMeanImaginary) / analyticalDeltaP > 5e-12 ||
      relativeError(expectedX, width / 2) > 5e-7 ||
      relativeError(
        expectedXSquared,
        width ** 2 * (1 / 3 - 1 / (2 * n ** 2 * Math.PI ** 2)),
      ) > 2e-6 ||
      relativeError(deltaX, analyticalDeltaX) > 2e-2 ||
      relativeError(pSquared, analyticalDeltaP ** 2) > 5e-2 ||
      relativeError(deltaP, analyticalDeltaP) > 3e-2 ||
      relativeError(product, analyticalProduct) > 5e-2 ||
      Math.abs(ratio - 2 * product) > 5e-10 ||
      product < 0.5
    ) {
      throw new Error(`Numerical moment row ${index} failed validation`);
    }
    return {
      grid,
      n,
      normalization,
      expectedX,
      expectedXSquared,
      pMeanReal,
      pMeanImaginary,
      pSquared,
      deltaX,
      deltaP,
      product,
      ratio,
      analyticalDeltaX,
      analyticalDeltaP,
      analyticalProduct,
      relativeDeltaPError: finiteNumber(
        row.relative_delta_p_error,
        "relative delta p error",
      ),
      relativeP2Error: finiteNumber(
        row.relative_p_squared_error,
        "relative p squared error",
      ),
      relativeUncertaintyError: finiteNumber(
        row.relative_uncertainty_error,
        "relative uncertainty error",
      ),
      energyError: finiteNumber(row.relative_energy_error, "relative energy error"),
      overlap: finiteNumber(row.eigenvector_overlap, "eigenvector overlap"),
    };
  });
}

function validateUncertaintyConvergence(rows) {
  if (rows.length !== 5) {
    throw new Error("Task 7 uncertainty convergence catalogue is incomplete");
  }
  const grids = [100, 200, 400, 800, 1600];
  return rows.map((row, index) => {
    const grid = finiteNumber(row.interior_point_count, "convergence grid size");
    const energyError = finiteNumber(
      row.maximum_energy_relative_error,
      "maximum energy error",
    );
    const deltaXError = finiteNumber(
      row.maximum_delta_x_relative_error,
      "maximum delta x error",
    );
    const pSquaredError = finiteNumber(
      row.maximum_p_squared_relative_error,
      "maximum p squared error",
    );
    const deltaPError = finiteNumber(
      row.maximum_delta_p_relative_error,
      "maximum delta p error",
    );
    const uncertaintyError = finiteNumber(
      row.maximum_uncertainty_relative_error,
      "maximum uncertainty error",
    );
    const normalizationError = finiteNumber(
      row.maximum_normalization_error,
      "maximum normalization error",
    );
    const pMeanScaleRatio = finiteNumber(
      row.maximum_p_mean_scale_ratio,
      "maximum p mean scale ratio",
    );
    const minimumProduct = finiteNumber(
      row.minimum_uncertainty_product_over_hbar,
      "minimum uncertainty product",
    );
    const minimumOverlap = finiteNumber(
      row.minimum_eigenvector_overlap,
      "minimum eigenvector overlap",
    );
    const minimumDeltaPOrder = finiteNumber(
      row.minimum_delta_p_convergence_order,
      "minimum delta p order",
    );
    const maximumDeltaPOrder = finiteNumber(
      row.maximum_delta_p_convergence_order,
      "maximum delta p order",
    );
    const minimumProductOrder = finiteNumber(
      row.minimum_uncertainty_product_convergence_order,
      "minimum uncertainty product order",
    );
    const maximumProductOrder = finiteNumber(
      row.maximum_uncertainty_product_convergence_order,
      "maximum uncertainty product order",
    );
    if (
      grid !== grids[index] ||
      energyError < 0 ||
      deltaXError < 0 ||
      pSquaredError < 0 ||
      deltaPError < 0 ||
      uncertaintyError < 0 ||
      normalizationError > 5e-12 ||
      pMeanScaleRatio > 5e-12 ||
      minimumProduct < 0.5 ||
      minimumOverlap < 0.999999 ||
      minimumDeltaPOrder < 1.9 ||
      maximumDeltaPOrder > 2.05 ||
      minimumProductOrder < 1.9 ||
      maximumProductOrder > 2.05
    ) {
      throw new Error(`Uncertainty convergence row ${index} failed validation`);
    }
    return {
      grid,
      energyError,
      deltaXError,
      pSquaredError,
      deltaPError,
      uncertaintyError,
      normalizationError,
      pMeanScaleRatio,
      minimumOverlap,
      minimumDeltaPOrder,
      maximumDeltaPOrder,
      minimumProductOrder,
      maximumProductOrder,
    };
  });
}

function validateAnchors(anchors, expectations, manifest) {
  if (
    anchors.schema_version !== "task07-reference-v1" ||
    anchors.reference_precision_decimal_digits !== 60 ||
    anchors.box_width_m !== manifest.configuration.box_width_m ||
    anchors.particle_mass_kg !== manifest.configuration.particle_mass_kg ||
    !Array.isArray(anchors.anchors) ||
    anchors.anchors.length !== 4
  ) {
    throw new Error("Task 7 reference anchors are unsupported");
  }
  for (const anchor of anchors.anchors) {
    const record = expectations[anchor.quantum_number_n - 1];
    if (
      !record ||
      relativeError(
        anchor.delta_x_delta_p_over_hbar,
        record.productOverHbar,
      ) > 5e-12
    ) {
      throw new Error("Task 7 reference anchor failed validation");
    }
  }
}

export async function loadTask07Evidence() {
  const responses = await Promise.all(
    Object.values(URLS).map((url) => fetch(url, { cache: "no-store" })),
  );
  responses.forEach((response) => {
    if (!response.ok) {
      throw new Error(`Task 7 evidence request failed: ${response.status}`);
    }
  });
  const [
    energyText,
    stateText,
    expectationText,
    numericalText,
    numericalMomentsText,
    uncertaintyConvergenceText,
    anchors,
    validation,
    manifest,
  ] = await Promise.all([
    responses[0].text(),
    responses[1].text(),
    responses[2].text(),
    responses[3].text(),
    responses[4].text(),
    responses[5].text(),
    responses[6].json(),
    responses[7].json(),
    responses[8].json(),
  ]);

  validateManifest(manifest);
  validateReport(validation, manifest);
  const energies = validateEnergies(parseCsv(energyText, "energy"), manifest);
  const states = validateStates(parseCsv(stateText, "stationary state"), manifest);
  const expectations = validateExpectations(
    parseCsv(expectationText, "expectation value"),
    manifest,
  );
  const numerical = validateNumerical(
    parseCsv(numericalText, "numerical eigenvalue"),
    energies,
  );
  const numericalMoments = validateNumericalMoments(
    parseCsv(numericalMomentsText, "numerical moments"),
    manifest,
  );
  const uncertaintyConvergence = validateUncertaintyConvergence(
    parseCsv(uncertaintyConvergenceText, "uncertainty convergence"),
  );
  validateAnchors(anchors, expectations, manifest);

  return Object.freeze({
    manifest,
    validation,
    energies,
    states,
    expectations,
    numerical,
    numericalMoments,
    uncertaintyConvergence,
    anchors,
  });
}
