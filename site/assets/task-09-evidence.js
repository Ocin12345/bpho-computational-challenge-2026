const URLS = {
  kinematics: new URL(
    "../../data/task09/compton_angle_study.csv",
    import.meta.url,
  ),
  summary: new URL("../../data/task09/energy_summary.csv", import.meta.url),
  references: new URL(
    "../../data/task09/reference_anchors.json",
    import.meta.url,
  ),
  validation: new URL(
    "../../data/task09/validation_report.json",
    import.meta.url,
  ),
  manifest: new URL("../../data/task09/manifest.json", import.meta.url),
  crossSection: new URL(
    "../../data/task09/klein_nishina_study.csv",
    import.meta.url,
  ),
  crossSummary: new URL(
    "../../data/task09/klein_nishina_summary.csv",
    import.meta.url,
  ),
  crossValidation: new URL(
    "../../data/task09/cross_section_validation_report.json",
    import.meta.url,
  ),
  crossManifest: new URL(
    "../../data/task09/cross_section_manifest.json",
    import.meta.url,
  ),
  mediaManifest: new URL("../../figures/task09/manifest.json", import.meta.url),
};

const REST_ENERGY_KEV = 510.9989506917531;
const CLASSICAL_ELECTRON_RADIUS_M = 2.8179403205e-15;
const OFFICIAL_ENERGIES = Object.freeze([50, 100, 200, 500, 1000]);

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

function close(observed, expected, tolerance = 5e-11) {
  return Math.abs(observed - expected) <=
    tolerance * Math.max(1, Math.abs(expected));
}

function kinematicReference(energyKev, thetaDeg) {
  const theta = (thetaDeg * Math.PI) / 180;
  const cosine = Math.cos(theta);
  const sine = thetaDeg === 0 || thetaDeg === 180 ? 0 : Math.sin(theta);
  const alpha = energyKev / REST_ENERGY_KEV;
  const fractionalShift = alpha * (1 - cosine);
  const scatteredEnergy = energyKev / (1 + fractionalShift);
  const kineticEnergy = energyKev - scatteredEnergy;
  const gamma = 1 + kineticEnergy / REST_ENERGY_KEV;
  const beta = Math.sqrt(Math.max(0, 1 - gamma ** -2));
  const px = energyKev - scatteredEnergy * cosine;
  const py = scatteredEnergy * sine;
  const recoilAngle =
    thetaDeg === 0
      ? 90
      : thetaDeg === 180
        ? 0
        : (Math.atan2(py, px) * 180) / Math.PI;
  return {
    fractionalShift,
    scatteredEnergy,
    kineticEnergy,
    gamma,
    beta,
    recoilAngle,
    directionDefined: thetaDeg !== 0,
  };
}

function kleinNishinaReference(energyKev, thetaDeg) {
  const theta = (thetaDeg * Math.PI) / 180;
  const alpha = energyKev / REST_ENERGY_KEV;
  const ratio = 1 / (1 + alpha * (1 - Math.cos(theta)));
  const differential =
    0.5 *
    CLASSICAL_ELECTRON_RADIUS_M ** 2 *
    ratio ** 2 *
    (ratio + 1 / ratio - Math.sin(theta) ** 2);
  return {
    ratio,
    differential,
    relative:
      differential / CLASSICAL_ELECTRON_RADIUS_M ** 2,
  };
}

function validateManifest(manifest) {
  const config = manifest.configuration;
  if (
    manifest.schema_version !== "task09-manifest-v1" ||
    manifest.output_schema_version !== "task09-output-v1" ||
    manifest.validation_passed !== true ||
    manifest.validation_check_count !== 44 ||
    manifest.model !==
      "relativistic free-electron Compton-scattering kinematics" ||
    config?.angle_minimum_deg !== 0 ||
    config?.angle_maximum_deg !== 180 ||
    config?.angle_point_count !== 721 ||
    config?.angle_spacing_deg !== 0.25 ||
    JSON.stringify(config?.incident_energies_kev) !==
      JSON.stringify(OFFICIAL_ENERGIES) ||
    !String(manifest.equations?.fractional_wavelength_shift).includes(
      "1 - cos theta",
    ) ||
    !String(manifest.equations?.electron_recoil_angle).includes("atan2")
  ) {
    throw new Error("Task 9 kinematic manifest is unsupported");
  }
}

function validateReport(report, manifest, expectedCount, schema) {
  if (
    report.schema_version !== schema ||
    report.passed !== true ||
    report.study_digest !== manifest.study_digest ||
    !Array.isArray(report.checks) ||
    report.checks.length !== expectedCount ||
    !report.checks.every((check) => check.passed === true)
  ) {
    throw new Error(`Task 9 ${schema} is not locked`);
  }
}

function validateKinematics(rows) {
  if (rows.length !== 5 * 721) {
    throw new Error("Task 9 kinematic study must contain 3,605 points");
  }
  return rows.map((row, rowIndex) => {
    const energyIndex = Math.floor(rowIndex / 721);
    const angleIndex = rowIndex % 721;
    const energyKev = finiteNumber(row.incident_energy_kev, "incident energy");
    const thetaDeg = finiteNumber(row.theta_deg, "photon angle");
    const expected = kinematicReference(energyKev, thetaDeg);
    if (
      Number(row.energy_index) !== energyIndex ||
      Number(row.angle_index) !== angleIndex ||
      energyKev !== OFFICIAL_ENERGIES[energyIndex] ||
      thetaDeg !== angleIndex * 0.25 ||
      !close(
        Number(row.fractional_wavelength_shift),
        expected.fractionalShift,
      ) ||
      !close(Number(row.scattered_energy_kev), expected.scatteredEnergy) ||
      !close(
        Number(row.electron_kinetic_energy_kev),
        expected.kineticEnergy,
      ) ||
      !close(Number(row.electron_gamma), expected.gamma) ||
      !close(Number(row.electron_beta), expected.beta) ||
      !close(
        Number(row.electron_recoil_angle_deg),
        expected.recoilAngle,
      ) ||
      (row.electron_recoil_direction_defined === "true") !==
        expected.directionDefined
    ) {
      throw new Error(`Task 9 kinematic row ${rowIndex} failed validation`);
    }
    return Object.freeze({
      energyKev,
      thetaDeg,
      fractionalShift: Number(row.fractional_wavelength_shift),
      beta: Number(row.electron_beta),
      recoilAngleDeg: Number(row.electron_recoil_angle_deg),
      directionDefined: row.electron_recoil_direction_defined === "true",
    });
  });
}

function validateCrossSection(rows, summaries) {
  if (rows.length !== 5 * 721 || summaries.length !== 5) {
    throw new Error("Task 9 cross-section tables are incomplete");
  }
  const summaryByEnergy = new Map(
    summaries.map((row) => [
      finiteNumber(row.incident_energy_kev, "summary energy"),
      Object.freeze({
        totalBarn: finiteNumber(
          row.analytical_total_cross_section_barn,
          "total cross-section",
        ),
        forwardProbability: finiteNumber(
          row.forward_hemisphere_probability,
          "forward probability",
        ),
        modalAngleDeg: finiteNumber(
          row.modal_polar_angle_deg,
          "modal angle",
        ),
      }),
    ]),
  );
  const values = rows.map((row, rowIndex) => {
    const energyIndex = Math.floor(rowIndex / 721);
    const angleIndex = rowIndex % 721;
    const energyKev = finiteNumber(row.incident_energy_kev, "cross energy");
    const thetaDeg = finiteNumber(row.theta_deg, "cross angle");
    const expected = kleinNishinaReference(energyKev, thetaDeg);
    const differential = finiteNumber(
      row.differential_cross_section_m2_sr,
      "differential cross-section",
    );
    const relative = finiteNumber(
      row.relative_differential_cross_section,
      "relative cross-section",
    );
    const thetaPdf = finiteNumber(row.theta_pdf_rad_inv, "theta density");
    if (
      Number(row.energy_index) !== energyIndex ||
      Number(row.angle_index) !== angleIndex ||
      energyKev !== OFFICIAL_ENERGIES[energyIndex] ||
      thetaDeg !== angleIndex * 0.25 ||
      !close(
        Number(row.scattered_to_incident_energy_ratio),
        expected.ratio,
      ) ||
      !close(differential, expected.differential, 2e-11) ||
      !close(relative, expected.relative) ||
      differential < 0 ||
      thetaPdf < 0
    ) {
      throw new Error(`Task 9 cross-section row ${rowIndex} failed validation`);
    }
    return Object.freeze({
      energyKev,
      thetaDeg,
      relative,
      thetaPdf,
      totalBarn: Number(row.total_cross_section_barn),
      differentialBarnSr: Number(row.differential_cross_section_barn_sr),
    });
  });
  return { values, summaryByEnergy };
}

function validateReferences(references) {
  if (
    references.schema_version !== "task09-reference-v1" ||
    !Array.isArray(references.anchors) ||
    references.anchors.length !== 15
  ) {
    throw new Error("Task 9 reference anchors are unsupported");
  }
  for (const item of references.anchors) {
    const expected = kinematicReference(
      item.incident_energy_kev,
      item.theta_deg,
    );
    if (
      !close(
        item.fractional_wavelength_shift,
        expected.fractionalShift,
      ) ||
      !close(item.scattered_energy_kev, expected.scatteredEnergy) ||
      !close(item.electron_beta, expected.beta) ||
      !close(item.electron_recoil_angle_deg, expected.recoilAngle) ||
      item.electron_recoil_direction_defined !== expected.directionDefined
    ) {
      throw new Error("Task 9 reference anchor failed validation");
    }
  }
}

function validateMedia(manifest) {
  const files = new Map(
    (manifest.files || []).map((entry) => [entry.filename, entry]),
  );
  const staticFigures = [
    "required_kinematics.png",
    "energy_transfer_geometry.png",
    "klein_nishina_extension.png",
  ];
  if (
    manifest.schema_version !== "task09-media-manifest-v2" ||
    manifest.rendering_contract?.font_family !== "Times New Roman" ||
    !staticFigures.every(
      (name) =>
        files.get(name)?.width_px === 2400 &&
        files.get(name)?.height_px === 1500,
    ) ||
    files.get("task09_summary.png")?.width_px !== 3840 ||
    files.get("task09_summary.png")?.height_px !== 2160 ||
    files.get("compton_angle_sweep.gif")?.frame_count !== 73
  ) {
    throw new Error("Task 9 media manifest failed validation");
  }
}

export async function loadTask09Evidence() {
  const responses = await Promise.all(
    Object.values(URLS).map((url) => fetch(url, { cache: "no-store" })),
  );
  responses.forEach((response) => {
    if (!response.ok) {
      throw new Error(`Task 9 evidence request failed: ${response.status}`);
    }
  });
  const [
    kinematicsText,
    summaryText,
    references,
    validation,
    manifest,
    crossText,
    crossSummaryText,
    crossValidation,
    crossManifest,
    mediaManifest,
  ] = await Promise.all([
    responses[0].text(),
    responses[1].text(),
    responses[2].json(),
    responses[3].json(),
    responses[4].json(),
    responses[5].text(),
    responses[6].text(),
    responses[7].json(),
    responses[8].json(),
    responses[9].json(),
  ]);

  validateManifest(manifest);
  validateReport(validation, manifest, 44, "task09-validation-v1");
  if (
    crossManifest.schema_version !== "task09-cross-section-manifest-v1" ||
    crossManifest.validation_passed !== true ||
    crossManifest.validation_check_count !== 30 ||
    crossManifest.scope !==
      "optional extension; separate from the three official kinematic curves"
  ) {
    throw new Error("Task 9 cross-section manifest is unsupported");
  }
  validateReport(
    crossValidation,
    crossManifest,
    30,
    "task09-cross-section-validation-v1",
  );

  const kinematics = validateKinematics(
    parseCsv(kinematicsText, "kinematics"),
  );
  const summaries = parseCsv(summaryText, "energy summary");
  const cross = validateCrossSection(
    parseCsv(crossText, "cross section"),
    parseCsv(crossSummaryText, "cross-section summary"),
  );
  validateReferences(references);
  validateMedia(mediaManifest);

  return Object.freeze({
    manifest,
    validation,
    references,
    summaries,
    kinematics,
    crossSection: cross.values,
    crossSummaryByEnergy: cross.summaryByEnergy,
    crossManifest,
    crossValidation,
    mediaManifest,
  });
}
