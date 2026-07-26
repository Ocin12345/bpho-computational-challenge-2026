import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  clampDisplayAngle,
  detectorProbabilities,
  mismatchComparison,
  mismatchSweep,
  normalizePolarisationAngleDeg,
  relativeDetectorAngleDeg,
} from "../physics.js";

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

function close(actual, expected, tolerance = 5e-12) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `${actual} differs from ${expected}`,
  );
}

test("angle normalisation and relative-angle convention match Python", () => {
  assert.deepEqual(
    [-270, -180, -90, 0, 90, 180, 270].map(
      normalizePolarisationAngleDeg,
    ),
    [-90, 0, -90, 0, -90, 0, -90],
  );
  assert.equal(relativeDetectorAngleDeg(-30, 30), 60);
  assert.equal(relativeDetectorAngleDeg(80, -80), 20);
  assert.equal(clampDisplayAngle(-1000), -90);
  assert.equal(clampDisplayAngle(1000), 90);
});

test("all exact Python reference cases agree with JavaScript", async () => {
  const payload = JSON.parse(
    await readFile(new URL("data/task08/reference_cases.json", repositoryRoot), "utf8"),
  );
  assert.equal(payload.cases.length, 5);
  for (const reference of payload.cases) {
    const result = mismatchComparison(reference.theta_deg, reference.phi_deg);
    close(result.classicalMismatch, reference.classical_mismatch.decimal);
    close(result.quantumMismatch, reference.quantum_mismatch.decimal);
    close(result.signedDifference, reference.signed_difference.decimal);
  }
});

test("the complete 361-point Python sweep agrees with JavaScript", async () => {
  const rows = await readRows("data/task08/angle_sweep.csv");
  assert.equal(rows.length, 361);
  for (const row of rows) {
    const result = mismatchComparison(Number(row.theta_deg), Number(row.phi_deg));
    close(result.classicalMismatch, Number(row.classical_mismatch_probability));
    close(result.quantumMismatch, Number(row.quantum_mismatch_probability));
    close(result.signedDifference, Number(row.quantum_minus_classical));
  }
});

test("a deterministic sample of the Python grid agrees with JavaScript", async () => {
  const rows = await readRows("data/task08/mismatch_grid.csv");
  assert.equal(rows.length, 181 * 181);
  for (let index = 0; index < rows.length; index += 137) {
    const row = rows[index];
    const result = mismatchComparison(Number(row.theta_deg), Number(row.phi_deg));
    close(result.classicalMismatch, Number(row.classical_mismatch_probability));
    close(result.quantumMismatch, Number(row.quantum_mismatch_probability));
    close(result.signedDifference, Number(row.quantum_minus_classical));
  }
});

test("probability identities and invalid inputs are enforced", () => {
  for (let angle = -90; angle <= 90; angle += 1) {
    const detector = detectorProbabilities(angle);
    close(detector.x + detector.y, 1, 1e-15);
  }
  assert.throws(() => mismatchComparison(Number.NaN, 0), TypeError);
  assert.throws(() => mismatchComparison(true, 0), TypeError);
  assert.throws(() => detectorProbabilities("30"), TypeError);
});

test("the live chart sweep is complete, immutable and numerically exact", () => {
  const sweep = mismatchSweep(-30);
  assert.equal(sweep.length, 361);
  assert.equal(sweep[0].phiDeg, -90);
  assert.equal(sweep[180].phiDeg, 0);
  assert.equal(sweep.at(-1).phiDeg, 90);
  close(sweep[240].classicalMismatch, 3 / 8);
  close(sweep[240].quantumMismatch, 3 / 4);
  assert.ok(Object.isFrozen(sweep));
  assert.throws(() => mismatchSweep(0, -90, 90, 0.7), RangeError);
  assert.throws(() => mismatchSweep(0, 90, -90, 1), RangeError);
  assert.throws(() => mismatchSweep(0, -90, 90, 0), RangeError);
});
