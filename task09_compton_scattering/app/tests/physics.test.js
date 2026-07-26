import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  OFFICIAL_ENERGIES_KEV,
  angleSweep,
  clampIncidentEnergyKev,
  clampScatteringAngleDeg,
  comptonKinematics,
} from "../physics.js";
import {
  CLASSICAL_ELECTRON_RADIUS_M,
  THOMSON_CROSS_SECTION_M2,
  kleinNishinaState,
  kleinNishinaSweep,
  kleinNishinaTotalM2,
} from "../cross-section.js";

const repositoryRoot = new URL("../../../", import.meta.url);

async function readRows(relativePath) {
  const text = await readFile(new URL(relativePath, repositoryRoot), "utf8");
  const [headerLine, ...lines] = text.trim().split("\n");
  const headers = headerLine.split(",");
  return lines.map((line) =>
    Object.fromEntries(
      line.split(",").map((value, index) => [headers[index], value]),
    ),
  );
}

function close(actual, expected, absolute = 5e-12, relative = 2e-11) {
  const tolerance = Math.max(absolute, relative * Math.abs(expected));
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `${actual} differs from ${expected} by more than ${tolerance}`,
  );
}

test("controls clamp to the frozen interactive domain", () => {
  assert.equal(clampIncidentEnergyKev(-10), 1);
  assert.equal(clampIncidentEnergyKev(10_000), 5_000);
  assert.equal(clampScatteringAngleDeg(-10), 0);
  assert.equal(clampScatteringAngleDeg(200), 180);
  assert.throws(() => clampIncidentEnergyKev("100"), TypeError);
  assert.throws(() => clampScatteringAngleDeg(Number.NaN), TypeError);
});

test("all 3,605 Python kinematic states agree with JavaScript", async () => {
  const rows = await readRows("data/task09/compton_angle_study.csv");
  assert.equal(rows.length, 3_605);
  for (const row of rows) {
    const result = comptonKinematics(
      Number(row.incident_energy_kev),
      Number(row.theta_deg),
    );
    close(
      result.fractionalWavelengthShift,
      Number(row.fractional_wavelength_shift),
    );
    close(result.scatteredEnergyKev, Number(row.scattered_energy_kev));
    close(
      result.electronKineticEnergyKev,
      Number(row.electron_kinetic_energy_kev),
    );
    close(result.electronBeta, Number(row.electron_beta));
    close(result.electronPcKev, Number(row.electron_pc_kev));
    close(
      result.electronRecoilAngleDeg,
      Number(row.electron_recoil_angle_deg),
      2e-10,
    );
    assert.equal(
      result.electronRecoilDirectionDefined,
      row.electron_recoil_direction_defined === "true",
    );
  }
});

test("official endpoints and live angle sweeps are exact and immutable", () => {
  for (const energy of OFFICIAL_ENERGIES_KEV) {
    const forward = comptonKinematics(energy, 0);
    assert.equal(forward.fractionalWavelengthShift, 0);
    assert.equal(forward.electronBeta, 0);
    assert.equal(forward.electronRecoilAngleDeg, 90);
    assert.equal(forward.electronRecoilDirectionDefined, false);
    const sweep = angleSweep(energy);
    assert.equal(sweep.length, 361);
    assert.equal(sweep[180].thetaDeg, 90);
    assert.equal(sweep.at(-1).thetaDeg, 180);
    assert.ok(Object.isFrozen(sweep));
  }
  assert.throws(() => comptonKinematics(0, 90), RangeError);
  assert.throws(() => comptonKinematics(100, 181), RangeError);
  assert.throws(() => angleSweep(100, 0.7), RangeError);
});

test("all Klein–Nishina Python rows agree with JavaScript", async () => {
  const rows = await readRows("data/task09/klein_nishina_study.csv");
  assert.equal(rows.length, 3_605);
  for (const row of rows) {
    const result = kleinNishinaState(
      Number(row.incident_energy_kev),
      Number(row.theta_deg),
    );
    close(
      result.differentialM2Sr,
      Number(row.differential_cross_section_m2_sr),
      1e-45,
      3e-11,
    );
    close(
      result.relativeDifferential,
      Number(row.relative_differential_cross_section),
    );
    close(result.thetaPdfRadInv, Number(row.theta_pdf_rad_inv), 2e-12, 3e-11);
    close(result.totalBarn, Number(row.total_cross_section_barn), 2e-12, 3e-11);
  }
});

test("Klein–Nishina forward and total limits remain physical", () => {
  for (const energy of OFFICIAL_ENERGIES_KEV) {
    const state = kleinNishinaState(energy, 0);
    close(
      state.differentialM2Sr,
      CLASSICAL_ELECTRON_RADIUS_M ** 2,
      1e-45,
      2e-15,
    );
    assert.ok(state.totalM2 > 0 && state.totalM2 < THOMSON_CROSS_SECTION_M2);
    const sweep = kleinNishinaSweep(energy);
    assert.equal(sweep.length, 361);
    assert.ok(Object.isFrozen(sweep));
  }
  close(kleinNishinaTotalM2(1e-6), THOMSON_CROSS_SECTION_M2, 1e-36, 1e-8);
});
