import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  SIMULATION_MAXIMUM_PHOTON_PAIRS,
  UINT32_MAXIMUM,
  advanceSeed,
  binomialMismatchCount,
  derivedStreamSeed,
  mulberry32Uint32Sequence,
  mulberry32UniformSequence,
  simulateFinitePhotonExperiment,
  wilsonInterval,
} from "../statistics.js";

const repositoryRoot = new URL("../../../", import.meta.url);

function close(actual, expected, tolerance = 5e-12) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `${actual} differs from ${expected}`,
  );
}

test("Mulberry32 outputs and stream derivation match frozen vectors", () => {
  assert.deepEqual(mulberry32Uint32Sequence(0, 5), [
    1144304738, 1416247, 958946056, 627933444, 2007157716,
  ]);
  assert.ok(mulberry32UniformSequence(0, 100).every((value) => value >= 0 && value < 1));
  assert.equal(derivedStreamSeed(2026, "classical"), 608136546);
  assert.equal(derivedStreamSeed(2026, "quantum"), 3084998280);
  assert.equal(advanceSeed(UINT32_MAXIMUM), 0);
});

test("binomial edge cases and Wilson intervals are robust", () => {
  assert.equal(binomialMismatchCount(100, 0, 5), 0);
  assert.equal(binomialMismatchCount(100, 1, 5), 100);
  close(wilsonInterval(0, 10).upper, 0.2775327998628892);
  close(wilsonInterval(10, 10).lower, 0.7224672001371107);
  assert.equal(wilsonInterval(0, 10).lower, 0);
  assert.equal(wilsonInterval(10, 10).upper, 1);
  assert.throws(() => wilsonInterval(11, 10), RangeError);
  assert.throws(() => binomialMismatchCount(10, -0.1, 1), RangeError);
});

test("every Python finite-photon fixture agrees with JavaScript", async () => {
  const fixture = JSON.parse(
    await readFile(
      new URL("data/task08/finite_photon_reference.json", repositoryRoot),
      "utf8",
    ),
  );
  assert.equal(fixture.cases.length, 6);
  assert.deepEqual(
    mulberry32Uint32Sequence(0, 10),
    fixture.prng_reference.uint32,
  );
  for (const reference of fixture.cases) {
    const result = simulateFinitePhotonExperiment(
      reference.theta_deg,
      reference.phi_deg,
      reference.photon_pairs,
      reference.seed,
    );
    for (const model of ["classical", "quantum"]) {
      const actual = result[model];
      const expected = reference[model];
      assert.equal(actual.streamSeed, expected.stream_seed);
      assert.equal(actual.mismatches, expected.mismatches);
      assert.equal(actual.matches, expected.matches);
      close(actual.theoreticalProbability, expected.theoretical_probability);
      close(actual.observedProbability, expected.observed_probability);
      close(actual.expectedMismatches, expected.expected_mismatches);
      close(actual.standardDeviationCount, expected.standard_deviation_count);
      if (expected.standardized_residual === null) {
        assert.equal(actual.standardizedResidual, null);
      } else {
        close(actual.standardizedResidual, expected.standardized_residual);
      }
      close(actual.wilsonInterval.lower, expected.wilson_interval.lower);
      close(actual.wilsonInterval.upper, expected.wilson_interval.upper);
    }
  }
});

test("simulation is immutable, reproducible and validates its domain", () => {
  const first = simulateFinitePhotonExperiment(-30, 30, 1000, 2026);
  const repeated = simulateFinitePhotonExperiment(-30, 30, 1000, 2026);
  assert.deepEqual(first, repeated);
  assert.equal(first.classical.mismatches, 363);
  assert.equal(first.quantum.mismatches, 770);
  assert.ok(Object.isFrozen(first));
  assert.ok(Object.isFrozen(first.classical));
  assert.throws(
    () => simulateFinitePhotonExperiment(-30, 30, 9, 2026),
    RangeError,
  );
  assert.throws(
    () =>
      simulateFinitePhotonExperiment(
        -30,
        30,
        SIMULATION_MAXIMUM_PHOTON_PAIRS + 1,
        2026,
      ),
    RangeError,
  );
  assert.throws(
    () => simulateFinitePhotonExperiment(-30, 30, 1000, 2 ** 32),
    RangeError,
  );
});
