import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  associatedFerrers,
  associatedLaguerre,
  densityAtScaledCoordinate,
  officialGalleryStates,
  realSphericalHarmonic,
  sampleOrthogonalSlices,
  sampleSliceStack,
  scaledRadialWavefunction,
  stateSummary,
  validateState,
} from "../physics.js";

const repositoryRoot = new URL("../../../", import.meta.url);

function close(actual, expected, absolute = 5e-12, relative = 3e-11) {
  const tolerance = Math.max(absolute, relative * Math.abs(expected));
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} differs from ${expected} by more than ${tolerance}`);
}

async function readRows(relativePath) {
  const text = await readFile(new URL(relativePath, repositoryRoot), "utf8");
  const [headerLine, ...lines] = text.trim().split("\n");
  const headers = headerLine.split(",");
  return lines.map((line) => Object.fromEntries(line.split(",").map((value, index) => [headers[index], value])));
}

test("frozen hydrogen and carbon anchors match Python", async () => {
  const anchors = JSON.parse(await readFile(new URL("data/task10/reference_anchors.json", repositoryRoot), "utf8"));
  const hydrogen = stateSummary({ n: 1, l: 0, m: 0, Z: 1, A: 1 });
  close(hydrogen.energyEv, anchors.hydrogen_1s.energy_ev, 2e-13);
  close(hydrogen.effectiveBohrRadiusAngstrom, anchors.hydrogen_1s.effective_bohr_radius_angstrom, 2e-13);
  close(hydrogen.reducedMassRatio, anchors.hydrogen_1s.reduced_mass_ratio, 2e-13);
  close(densityAtScaledCoordinate({ n: 1, l: 0, m: 0, Z: 1, A: 1 }, 0, 0, 0), anchors.hydrogen_1s.scaled_density_at_origin, 2e-13);
  const carbon = stateSummary({ n: 3, l: 2, m: 0, Z: 6, A: 12 });
  close(carbon.energyEv, anchors.carbon12_3d.energy_ev, 2e-12);
  close(carbon.effectiveBohrRadiusAngstrom, anchors.carbon12_3d.effective_bohr_radius_angstrom, 2e-13);
});

test("all 204 Python state summaries agree with JavaScript", async () => {
  const rows = await readRows("data/task10/orbital_state_catalog.csv");
  assert.equal(rows.length, 204);
  for (const row of rows) {
    const summary = stateSummary({
      n: Number(row.n), l: Number(row.l), m: Number(row.m),
      Z: Number(row.atomic_number), A: Number(row.mass_number),
    });
    close(summary.energyEv, Number(row.energy_ev), 5e-13);
    close(summary.effectiveBohrRadiusAngstrom, Number(row.effective_bohr_radius_angstrom), 5e-13);
    close(summary.reducedMassRatio, Number(row.reduced_mass_ratio), 5e-13);
    assert.equal(summary.radialNodes, Number(row.radial_nodes));
    assert.equal(summary.angularNodes, Number(row.angular_nodes));
    assert.equal(summary.degeneracy, Number(row.degeneracy));
    assert.equal(summary.parity, Number(row.parity));
  }
});

test("real P orientations and low-state analytic densities are exact", async () => {
  const anchors = JSON.parse(await readFile(new URL("data/task10/reference_anchors.json", repositoryRoot), "utf8"));
  close(realSphericalHarmonic(1, 1, Math.PI / 2, 0), anchors.real_harmonic_orientation.p_x_on_x_axis);
  close(realSphericalHarmonic(1, -1, Math.PI / 2, Math.PI / 2), anchors.real_harmonic_orientation.p_y_on_y_axis);
  close(realSphericalHarmonic(1, 0, 0, 0), anchors.real_harmonic_orientation.p_z_on_z_axis);
  close(densityAtScaledCoordinate({ n: 1, l: 0, m: 0 }, 2, 0, 0), anchors.analytic_densities.one_s_r_over_a_2);
  close(densityAtScaledCoordinate({ n: 2, l: 1, m: 0 }, 0, 0, 0.5), anchors.analytic_densities.two_pz_r_over_a_2_axis);
  close(densityAtScaledCoordinate({ n: 2, l: 1, m: 0 }, 0.5, 0, 0), anchors.analytic_densities.two_pz_r_over_a_2_equator, 1e-30);
});

test("every distinct radial function integrates to one", () => {
  for (let n = 1; n <= 8; n += 1) {
    for (let l = 0; l < n; l += 1) {
      const state = { n, l, m: 0 };
      const end = 16 * n * n;
      const steps = 40_000;
      const spacing = end / steps;
      let integral = 0;
      let previous = 0;
      for (let index = 1; index <= steps; index += 1) {
        const radius = spacing * index;
        const radial = scaledRadialWavefunction(state, radius);
        const current = radius ** 2 * radial ** 2;
        integral += 0.5 * spacing * (previous + current);
        previous = current;
      }
      close(integral, 1, 3e-7, 3e-7);
    }
  }
});

test("official gallery and sampled render grids are complete and finite", () => {
  const gallery = officialGalleryStates();
  assert.equal(gallery.length, 25);
  assert.equal(new Set(gallery.map((state) => `${state.n}/${state.l}/${state.m}`)).size, 25);
  const stack = sampleSliceStack({ n: 3, l: 2, m: 0 }, { extent: 3.2, resolution: 31, sliceCount: 7 });
  assert.equal(stack.slices.length, 7);
  assert.ok(stack.maximum > 0 && Number.isFinite(stack.maximum));
  assert.ok(stack.slices.every((slice) => slice.values.every((value) => value >= 0 && Number.isFinite(value))));
  const orthogonal = sampleOrthogonalSlices({ n: 5, l: 4, m: -4 }, { extent: 3.2, resolution: 31 });
  assert.equal(orthogonal.planes.length, 3);
  assert.ok(orthogonal.maximum > 0);
});

test("recurrences and invalid domains are explicit", () => {
  close(associatedLaguerre(2, 1, 0.3), 3 - 3 * 0.3 + 0.3 ** 2 / 2);
  close(associatedFerrers(2, 2, 0.4), 3 * (1 - 0.4 ** 2));
  assert.throws(() => validateState({ n: 2, l: 2, m: 0 }), RangeError);
  assert.throws(() => validateState({ n: 3, l: 2, m: 3 }), RangeError);
  assert.throws(() => validateState({ n: 1.5, l: 0, m: 0 }), TypeError);
  assert.throws(() => sampleSliceStack({ n: 1, l: 0, m: 0 }, { resolution: 30 }), RangeError);
});
