const URLS = {
  cutoffs: new URL("../../data/task04/material_cutoffs.csv", import.meta.url),
  validation: new URL(
    "../../data/task04/validation_report.json",
    import.meta.url,
  ),
  manifest: new URL(
    "../../data/task04/reproducibility_manifest.json",
    import.meta.url,
  ),
};

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) throw new Error("Material cut-off CSV is empty");
  const headers = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const fields = line.split(",");
    return Object.fromEntries(
      headers.map((header, index) => [header, fields[index] ?? ""]),
    );
  });
}

function finiteNumber(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new Error(`${label} is not finite`);
  }
  return number;
}

function validateMaterials(rows, manifest) {
  if (rows.length !== 9 || manifest.official_materials?.length !== 9) {
    throw new Error("Task 4 must contain exactly nine official metals");
  }

  const officialBySymbol = new Map(
    manifest.official_materials.map((material) => [
      material.symbol,
      material,
    ]),
  );

  const materials = rows.map((row) => {
    const official = officialBySymbol.get(row.symbol);
    if (!official || official.name !== row.material) {
      throw new Error(`Official material mismatch for ${row.symbol}`);
    }

    const material = {
      name: row.material,
      symbol: row.symbol,
      workFunctionEv: finiteNumber(
        row.work_function_ev,
        `${row.symbol} work function`,
      ),
      workFunctionJ: finiteNumber(
        row.work_function_j,
        `${row.symbol} work function in joules`,
      ),
      cutoffFrequencyHz: finiteNumber(
        row.cutoff_frequency_hz,
        `${row.symbol} threshold frequency`,
      ),
      cutoffWavelengthNm: finiteNumber(
        row.cutoff_wavelength_nm,
        `${row.symbol} threshold wavelength`,
      ),
    };

    if (material.workFunctionEv !== official.work_function_ev) {
      throw new Error(`Official work function mismatch for ${row.symbol}`);
    }

    return material;
  });

  const overlap = materials.filter((material) =>
    ["Ag", "Al", "Pb"].includes(material.symbol),
  );
  if (
    overlap.length !== 3 ||
    !overlap.every(
      (material) =>
        material.workFunctionEv === overlap[0].workFunctionEv &&
        material.cutoffFrequencyHz === overlap[0].cutoffFrequencyHz &&
        material.cutoffWavelengthNm === overlap[0].cutoffWavelengthNm,
    )
  ) {
    throw new Error("Ag, Al and Pb must overlap exactly");
  }

  return materials;
}

function validateReport(report) {
  if (
    report.schema_version !== "task04-v1" ||
    report.passed !== true ||
    !Array.isArray(report.checks) ||
    report.checks.length !== 43 ||
    !report.checks.every((check) => check.passed === true)
  ) {
    throw new Error("The committed Task 4 validation report is not locked");
  }
}

function validateManifest(manifest) {
  const constants = manifest.constants;
  if (
    manifest.schema_version !== "task04-v1" ||
    manifest.output_schema_version !== "task04-data-v1" ||
    !constants ||
    constants.planck_constant_j_s !== 6.62607015e-34 ||
    constants.elementary_charge_c !== 1.602176634e-19 ||
    constants.speed_of_light_m_s !== 299792458 ||
    constants.planck_over_charge_v_s !== 4.135667696923859e-15
  ) {
    throw new Error("Task 4 manifest constants are unsupported");
  }
}

async function fetchChecked(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url.pathname} returned HTTP ${response.status}`);
  }
  return response;
}

export async function loadTask04Evidence() {
  const [cutoffResponse, validationResponse, manifestResponse] =
    await Promise.all([
      fetchChecked(URLS.cutoffs),
      fetchChecked(URLS.validation),
      fetchChecked(URLS.manifest),
    ]);

  const [cutoffText, validation, manifest] = await Promise.all([
    cutoffResponse.text(),
    validationResponse.json(),
    manifestResponse.json(),
  ]);

  validateManifest(manifest);
  validateReport(validation);
  const materials = validateMaterials(parseCsv(cutoffText), manifest);

  return Object.freeze({
    materials: Object.freeze(materials.map(Object.freeze)),
    validation: Object.freeze(validation),
    manifest: Object.freeze(manifest),
  });
}
