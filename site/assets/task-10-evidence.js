const URLS = {
  catalog: new URL(
    "../../data/task10/orbital_state_catalog.csv",
    import.meta.url,
  ),
  gallery: new URL(
    "../../data/task10/official_gallery.csv",
    import.meta.url,
  ),
  radialProfiles: new URL(
    "../../data/task10/radial_profiles.csv",
    import.meta.url,
  ),
  radialNodes: new URL(
    "../../data/task10/radial_nodes.csv",
    import.meta.url,
  ),
  references: new URL(
    "../../data/task10/reference_anchors.json",
    import.meta.url,
  ),
  validation: new URL(
    "../../data/task10/validation_report.json",
    import.meta.url,
  ),
  manifest: new URL("../../data/task10/manifest.json", import.meta.url),
  figureManifest: new URL(
    "../../figures/task10/manifest.json",
    import.meta.url,
  ),
  motionManifest: new URL(
    "../../figures/task10/motion_manifest.json",
    import.meta.url,
  ),
};

const FAMILY_LABELS = Object.freeze(["S", "P", "D", "F", "G", "H", "I", "K"]);

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

function expectedStateRows() {
  const rows = [];
  for (let n = 1; n <= 8; n += 1) {
    for (let l = 0; l < n; l += 1) {
      for (let m = -l; m <= l; m += 1) rows.push({ n, l, m });
    }
  }
  return rows;
}

function validateManifest(manifest) {
  if (
    manifest.schema_version !== "task10-manifest-v1" ||
    manifest.output_schema_version !== "task10-output-v1" ||
    manifest.model !== "normalized real hydrogenic Coulomb eigenstates" ||
    manifest.domain?.n?.[0] !== 1 ||
    manifest.domain?.n?.[1] !== 8 ||
    manifest.domain?.official_gallery !== "1s, 2p, 3d, 4f, 5g; every m" ||
    manifest.validation?.passed !== true ||
    manifest.validation?.check_count !== 22 ||
    manifest.visualization_contract?.default_display_threshold !== 0.15 ||
    manifest.visualization_contract?.threshold_affects_normalization !== false ||
    manifest.visualization_contract?.radial_profile_points !== 1201
  ) {
    throw new Error("Task 10 scientific manifest is unsupported");
  }
}

function validateReport(report, manifest) {
  if (
    report.schema_version !== "task10-validation-v1" ||
    report.passed !== true ||
    report.state_digest !== manifest.validation.state_digest ||
    !Array.isArray(report.checks) ||
    report.checks.length !== 22 ||
    !report.checks.every(
      (check) =>
        check.passed === true &&
        Number.isFinite(check.maximum_error) &&
        Number.isFinite(check.tolerance),
    )
  ) {
    throw new Error("Task 10 validation report is not locked");
  }
}

function validateCatalog(rows, manifest) {
  const expected = expectedStateRows();
  const hartree = manifest.constants.hartree_energy_ev;
  const electronMass = manifest.constants.electron_mass_kg;
  const atomicMass = manifest.constants.atomic_mass_constant_kg;
  const muRatio = atomicMass / (electronMass + atomicMass);
  if (rows.length !== expected.length || rows.length !== 204) {
    throw new Error("Task 10 catalog must contain 204 states");
  }
  return rows.map((row, index) => {
    const state = expected[index];
    const n = finiteNumber(row.n, "catalog n");
    const l = finiteNumber(row.l, "catalog l");
    const m = finiteNumber(row.m, "catalog m");
    const expectedEnergy = -0.5 * hartree * muRatio / n ** 2;
    if (
      n !== state.n ||
      l !== state.l ||
      m !== state.m ||
      row.family !== FAMILY_LABELS[l] ||
      Number(row.atomic_number) !== 1 ||
      Number(row.mass_number) !== 1 ||
      !close(Number(row.energy_ev), expectedEnergy) ||
      Number(row.radial_nodes) !== n - l - 1 ||
      Number(row.angular_nodes) !== l ||
      Number(row.degeneracy) !== 2 * l + 1 ||
      Number(row.parity) !== (l % 2 === 0 ? 1 : -1)
    ) {
      throw new Error(`Task 10 catalog row ${index} failed validation`);
    }
    return Object.freeze({
      n,
      l,
      m,
      family: row.family,
      label: row.label,
      energyEv: Number(row.energy_ev),
      bohrAngstrom: Number(row.effective_bohr_radius_angstrom),
      radialNodes: Number(row.radial_nodes),
      angularNodes: Number(row.angular_nodes),
      degeneracy: Number(row.degeneracy),
      parity: Number(row.parity),
      orientation: row.orientation,
    });
  });
}

function validateGallery(rows) {
  if (rows.length !== 25) {
    throw new Error("Task 10 official gallery must contain 25 states");
  }
  let index = 0;
  for (let l = 0; l <= 4; l += 1) {
    for (let m = -l; m <= l; m += 1) {
      const row = rows[index];
      if (
        Number(row.n) !== l + 1 ||
        Number(row.l) !== l ||
        Number(row.m) !== m ||
        row.family !== FAMILY_LABELS[l] ||
        Number(row.radial_nodes) !== 0 ||
        Number(row.angular_nodes) !== l
      ) {
        throw new Error(`Task 10 gallery row ${index} failed validation`);
      }
      index += 1;
    }
  }
}

function validateRadialProfiles(rows) {
  if (rows.length !== 5 * 1201) {
    throw new Error("Task 10 radial profiles must contain 6,005 points");
  }
  const profiles = new Map();
  rows.forEach((row, rowIndex) => {
    const profileIndex = Math.floor(rowIndex / 1201);
    const sampleIndex = rowIndex % 1201;
    const n = profileIndex + 1;
    const l = profileIndex;
    const radius = finiteNumber(row.radius_over_n_squared_a, "profile radius");
    const probability = finiteNumber(
      row.scaled_radial_probability,
      "radial probability",
    );
    const cumulative = finiteNumber(
      row.cumulative_probability,
      "cumulative probability",
    );
    if (
      Number(row.n) !== n ||
      Number(row.l) !== l ||
      Number(row.m) !== 0 ||
      Number(row.sample_index) !== sampleIndex ||
      probability < 0 ||
      cumulative < -1e-14 ||
      cumulative > 1.00001
    ) {
      throw new Error(`Task 10 radial-profile row ${rowIndex} failed validation`);
    }
    const key = `${n}/${l}`;
    if (!profiles.has(key)) profiles.set(key, []);
    profiles.get(key).push(
      Object.freeze({
        radius,
        probability,
        cumulative,
      }),
    );
  });
  for (const profile of profiles.values()) {
    for (let index = 1; index < profile.length; index += 1) {
      if (
        profile[index].radius <= profile[index - 1].radius ||
        profile[index].cumulative + 1e-12 <
          profile[index - 1].cumulative
      ) {
        throw new Error("Task 10 radial profile is not ordered");
      }
    }
  }
  return profiles;
}

function validateRadialNodes(rows) {
  if (rows.length !== 84) {
    throw new Error("Task 10 radial-node table must contain 84 roots");
  }
  const counts = new Map();
  for (const row of rows) {
    const n = finiteNumber(row.n, "node n");
    const l = finiteNumber(row.l, "node l");
    const radius = finiteNumber(row.radius_over_a, "node radius");
    const key = `${n}/${l}`;
    counts.set(key, (counts.get(key) || 0) + 1);
    if (
      n < 2 ||
      l < 0 ||
      l >= n - 1 ||
      Number(row.node_index) !== counts.get(key) ||
      radius <= 0 ||
      !close(
        Number(row.radius_over_n_squared_a),
        radius / n ** 2,
      )
    ) {
      throw new Error("Task 10 radial-node row failed validation");
    }
  }
  for (let n = 1; n <= 8; n += 1) {
    for (let l = 0; l < n; l += 1) {
      if ((counts.get(`${n}/${l}`) || 0) !== n - l - 1) {
        throw new Error("Task 10 radial-node count failed validation");
      }
    }
  }
}

function validateReferences(references) {
  if (
    references.schema_version !== "task10-reference-anchors-v1" ||
    !close(
      references.hydrogen_1s?.analytic_scaled_density_at_origin,
      1 / Math.PI,
    ) ||
    !close(
      references.hydrogen_1s?.scaled_density_at_origin,
      1 / Math.PI,
    ) ||
    !close(
      references.analytic_densities?.two_s_r_over_a_2_node,
      0,
      1e-14,
    ) ||
    references.hydrogen_3d?.radial_nodes !== 0 ||
    references.hydrogen_3d?.angular_nodes !== 2 ||
    !close(
      references.real_harmonic_orientation?.p_x_on_x_axis,
      references.real_harmonic_orientation?.p_y_on_y_axis,
    ) ||
    !close(
      references.real_harmonic_orientation?.p_x_on_x_axis,
      references.real_harmonic_orientation?.p_z_on_z_axis,
    )
  ) {
    throw new Error("Task 10 analytic reference anchors failed validation");
  }
}

function validateMedia(figures, motion, manifest) {
  const fileMap = new Map(
    (figures.figures || []).map((entry) => [entry.path, entry]),
  );
  if (
    figures.schema_version !== "task10-figure-manifest-v2" ||
    figures.renderer?.font_family !== "Times New Roman" ||
    figures.science_gate?.state_digest !== manifest.validation.state_digest ||
    fileMap.get("figures/task10/required_orbital_gallery.png")?.width_px !==
      3840 ||
    fileMap.get("figures/task10/required_orbital_gallery.png")?.height_px !==
      2400 ||
    fileMap.get("figures/task10/coloured_glass_density.png")?.width_px !==
      3000 ||
    fileMap.get("figures/task10/coloured_glass_density.png")?.height_px !==
      1875 ||
    fileMap.get("figures/task10/task10_summary.png")?.width_px !== 3840 ||
    fileMap.get("figures/task10/task10_summary.png")?.height_px !== 2160 ||
    motion.schema_version !== "task10-motion-v2" ||
    motion.science_gate?.state_digest !== manifest.validation.state_digest ||
    motion.animation?.width_px !== 3840 ||
    motion.animation?.height_px !== 2160 ||
    motion.animation?.frame_count !== 80 ||
    motion.animation?.duration_ms !== 4000 ||
    motion.rendering_contract?.motion_interpretation !==
      "view rotation only; normalized state is stationary" ||
    motion.poster?.width_px !== 3840 ||
    motion.poster?.height_px !== 2160
  ) {
    throw new Error("Task 10 media manifests failed validation");
  }
}

export async function loadTask10Evidence() {
  const responses = await Promise.all(
    Object.values(URLS).map((url) => fetch(url, { cache: "no-store" })),
  );
  responses.forEach((response) => {
    if (!response.ok) {
      throw new Error(`Task 10 evidence request failed: ${response.status}`);
    }
  });
  const [
    catalogText,
    galleryText,
    profilesText,
    nodesText,
    references,
    validation,
    manifest,
    figureManifest,
    motionManifest,
  ] = await Promise.all([
    responses[0].text(),
    responses[1].text(),
    responses[2].text(),
    responses[3].text(),
    responses[4].json(),
    responses[5].json(),
    responses[6].json(),
    responses[7].json(),
    responses[8].json(),
  ]);

  validateManifest(manifest);
  validateReport(validation, manifest);
  const catalog = validateCatalog(parseCsv(catalogText, "catalog"), manifest);
  const gallery = parseCsv(galleryText, "gallery");
  validateGallery(gallery);
  const radialProfiles = validateRadialProfiles(
    parseCsv(profilesText, "radial profile"),
  );
  const radialNodes = parseCsv(nodesText, "radial nodes");
  validateRadialNodes(radialNodes);
  validateReferences(references);
  validateMedia(figureManifest, motionManifest, manifest);

  return Object.freeze({
    manifest,
    validation,
    references,
    catalog,
    gallery,
    radialProfiles,
    radialNodes,
    figureManifest,
    motionManifest,
  });
}
