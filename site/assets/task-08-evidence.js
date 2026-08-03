const URLS = {
  sweep: new URL("../../data/task08/angle_sweep.csv", import.meta.url),
  grid: new URL("../../data/task08/mismatch_grid.csv", import.meta.url),
  references: new URL("../../data/task08/reference_cases.json", import.meta.url),
  validation: new URL(
    "../../data/task08/validation_report.json",
    import.meta.url,
  ),
  manifest: new URL("../../data/task08/manifest.json", import.meta.url),
  finite: new URL(
    "../../data/task08/finite_photon_reference.json",
    import.meta.url,
  ),
  statisticalValidation: new URL(
    "../../data/task08/statistical_validation_report.json",
    import.meta.url,
  ),
  statisticalManifest: new URL(
    "../../data/task08/statistics_manifest.json",
    import.meta.url,
  ),
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

function mismatchReference(thetaDeg, phiDeg) {
  const theta = (thetaDeg * Math.PI) / 180;
  const phi = (phiDeg * Math.PI) / 180;
  const delta = phi - theta;
  return {
    classical: (1 - Math.cos(2 * theta) * Math.cos(2 * phi)) / 2,
    quantum: (1 - Math.cos(2 * delta)) / 2,
    difference: -0.5 * Math.sin(2 * theta) * Math.sin(2 * phi),
  };
}

function close(observed, expected, tolerance = 5e-12) {
  return Math.abs(observed - expected) <= tolerance;
}

function validateManifest(manifest) {
  const config = manifest.configuration;
  if (
    manifest.schema_version !== "task08-manifest-v1" ||
    manifest.output_schema_version !== "task08-data-v1" ||
    manifest.validation_passed !== true ||
    manifest.validation_check_count !== 42 ||
    manifest.model !==
      "classical and quantum entangled-photon detector mismatch" ||
    !config ||
    config.schema_version !== "task08-v1" ||
    config.angle_minimum_deg !== -90 ||
    config.angle_maximum_deg !== 90 ||
    config.angle_step_deg !== 1 ||
    config.sweep_point_count !== 361 ||
    config.sweep_spacing_deg !== 0.5 ||
    config.heatmap_point_count !== 181 ||
    config.heatmap_spacing_deg !== 1 ||
    config.official_theta_deg !== -30 ||
    config.official_phi_deg !== 30 ||
    manifest.constants?.polarisation_period_deg !== 180 ||
    !String(manifest.equations?.classical_mismatch).includes("cos(theta)^2") ||
    !String(manifest.equations?.quantum_mismatch).includes("sin(phi - theta)^2")
  ) {
    throw new Error("Task 8 manifest is unsupported");
  }
}

function validateReport(report, manifest) {
  if (
    report.schema_version !== "task08-validation-v1" ||
    report.passed !== true ||
    report.study_digest !== manifest.study_digest ||
    !Array.isArray(report.checks) ||
    report.checks.length !== 42 ||
    !report.checks.every(
      (check) =>
        check.passed === true &&
        Number.isFinite(check.observed) &&
        Number.isFinite(check.expected) &&
        Number.isFinite(check.tolerance),
    )
  ) {
    throw new Error("The committed Task 8 validation report is not locked");
  }
}

function validateSweep(rows) {
  if (rows.length !== 361) {
    throw new Error("Task 8 fixed-angle sweep must contain 361 points");
  }
  return rows.map((row, index) => {
    const thetaDeg = finiteNumber(row.theta_deg, "sweep theta");
    const phiDeg = finiteNumber(row.phi_deg, "sweep phi");
    const classicalMismatch = finiteNumber(
      row.classical_mismatch_probability,
      "sweep classical mismatch",
    );
    const quantumMismatch = finiteNumber(
      row.quantum_mismatch_probability,
      "sweep quantum mismatch",
    );
    const difference = finiteNumber(
      row.quantum_minus_classical,
      "sweep difference",
    );
    const expectedPhi = -90 + index * 0.5;
    const reference = mismatchReference(thetaDeg, phiDeg);
    if (
      thetaDeg !== -30 ||
      phiDeg !== expectedPhi ||
      !close(classicalMismatch, reference.classical) ||
      !close(quantumMismatch, reference.quantum) ||
      !close(difference, reference.difference)
    ) {
      throw new Error(`Task 8 sweep row ${index} failed validation`);
    }
    return { thetaDeg, phiDeg, classicalMismatch, quantumMismatch, difference };
  });
}

function validateGrid(rows) {
  if (rows.length !== 181 * 181) {
    throw new Error("Task 8 mismatch grid must contain 32,761 points");
  }
  return rows.map((row, rowIndex) => {
    const thetaIndex = finiteNumber(row.theta_index, "theta index");
    const phiIndex = finiteNumber(row.phi_index, "phi index");
    const thetaDeg = finiteNumber(row.theta_deg, "grid theta");
    const phiDeg = finiteNumber(row.phi_deg, "grid phi");
    const classicalMismatch = finiteNumber(
      row.classical_mismatch_probability,
      "grid classical mismatch",
    );
    const quantumMismatch = finiteNumber(
      row.quantum_mismatch_probability,
      "grid quantum mismatch",
    );
    const difference = finiteNumber(
      row.quantum_minus_classical,
      "grid difference",
    );
    const expectedThetaIndex = Math.floor(rowIndex / 181);
    const expectedPhiIndex = rowIndex % 181;
    const reference = mismatchReference(thetaDeg, phiDeg);
    if (
      thetaIndex !== expectedThetaIndex ||
      phiIndex !== expectedPhiIndex ||
      thetaDeg !== -90 + expectedThetaIndex ||
      phiDeg !== -90 + expectedPhiIndex ||
      !close(classicalMismatch, reference.classical) ||
      !close(quantumMismatch, reference.quantum) ||
      !close(difference, reference.difference)
    ) {
      throw new Error(`Task 8 grid row ${rowIndex} failed validation`);
    }
    return {
      thetaIndex,
      phiIndex,
      thetaDeg,
      phiDeg,
      classicalMismatch,
      quantumMismatch,
      difference,
    };
  });
}

function validateReferences(references) {
  if (
    references.schema_version !== "task08-reference-v1" ||
    !Array.isArray(references.cases) ||
    references.cases.length !== 5
  ) {
    throw new Error("Task 8 reference cases are unsupported");
  }
  const cases = new Map();
  for (const item of references.cases) {
    const reference = mismatchReference(item.theta_deg, item.phi_deg);
    if (
      !close(item.classical_mismatch.decimal, reference.classical) ||
      !close(item.quantum_mismatch.decimal, reference.quantum) ||
      !close(item.signed_difference.decimal, reference.difference)
    ) {
      throw new Error(`Task 8 reference ${item.identifier} failed validation`);
    }
    cases.set(item.identifier, Object.freeze(item));
  }
  const official = cases.get("official_example");
  if (
    !official ||
    official.theta_deg !== -30 ||
    official.phi_deg !== 30 ||
    official.classical_mismatch.numerator !== 3 ||
    official.classical_mismatch.denominator !== 8 ||
    official.quantum_mismatch.numerator !== 3 ||
    official.quantum_mismatch.denominator !== 4
  ) {
    throw new Error("The official Task 8 anchor is missing");
  }
  return cases;
}

function validateStatistics(manifest, report, finite) {
  if (
    manifest.schema_version !== "task08-statistics-manifest-v1" ||
    manifest.output_schema_version !== "task08-statistics-data-v1" ||
    manifest.validation_passed !== true ||
    manifest.validation_check_count !== 24 ||
    !manifest.warning.includes("not cryptographically secure") ||
    report.schema_version !== "task08-statistical-validation-v1" ||
    report.passed !== true ||
    !Array.isArray(report.checks) ||
    report.checks.length !== 24 ||
    !report.checks.every((check) => check.passed === true) ||
    finite.schema_version !== "task08-finite-photon-reference-v1" ||
    finite.cryptographic_security !== false ||
    finite.configuration?.default_photon_pairs !== 1000 ||
    finite.configuration?.default_seed !== 2026 ||
    finite.configuration?.minimum_photon_pairs !== 10 ||
    finite.configuration?.maximum_photon_pairs !== 100000 ||
    !Array.isArray(finite.cases) ||
    finite.cases.length < 6
  ) {
    throw new Error("Task 8 statistical evidence is unsupported");
  }
  const official = finite.cases.find(
    (item) => item.identifier === "official_default",
  );
  if (
    !official ||
    official.classical.mismatches !== 363 ||
    official.quantum.mismatches !== 770 ||
    official.classical.matches !== 637 ||
    official.quantum.matches !== 230 ||
    !close(official.classical.observed_probability, 0.363) ||
    !close(official.quantum.observed_probability, 0.77)
  ) {
    throw new Error("Task 8 finite-photon anchor failed validation");
  }
}

export async function loadTask08Evidence() {
  const responses = await Promise.all(
    Object.values(URLS).map((url) => fetch(url, { cache: "no-store" })),
  );
  responses.forEach((response) => {
    if (!response.ok) {
      throw new Error(`Task 8 evidence request failed: ${response.status}`);
    }
  });
  const [
    sweepText,
    gridText,
    references,
    validation,
    manifest,
    finite,
    statisticalValidation,
    statisticalManifest,
  ] = await Promise.all([
    responses[0].text(),
    responses[1].text(),
    responses[2].json(),
    responses[3].json(),
    responses[4].json(),
    responses[5].json(),
    responses[6].json(),
    responses[7].json(),
  ]);

  validateManifest(manifest);
  validateReport(validation, manifest);
  const sweep = validateSweep(parseCsv(sweepText, "angle sweep"));
  const grid = validateGrid(parseCsv(gridText, "mismatch grid"));
  const referenceCases = validateReferences(references);
  validateStatistics(statisticalManifest, statisticalValidation, finite);

  return Object.freeze({
    manifest,
    validation,
    sweep,
    grid,
    references,
    referenceCases,
    finite,
    statisticalValidation,
    statisticalManifest,
  });
}
