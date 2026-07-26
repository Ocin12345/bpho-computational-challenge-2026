import { ELECTRON_REST_ENERGY_KEV } from "./physics.js";

export const CLASSICAL_ELECTRON_RADIUS_M = 2.817_940_3205e-15;
export const BARN_M2 = 1e-28;
export const THOMSON_CROSS_SECTION_M2 =
  (8 * Math.PI * CLASSICAL_ELECTRON_RADIUS_M ** 2) / 3;

function positiveEnergy(value) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    throw new TypeError("incidentEnergyKev must be a finite positive number");
  }
  return value;
}

function angle(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError("thetaDeg must be a finite number");
  }
  if (value < 0 || value > 180) {
    throw new RangeError("thetaDeg must lie within 0 to 180 degrees");
  }
  return value;
}

export function kleinNishinaDifferentialM2Sr(incidentEnergyKev, thetaDeg) {
  const energy = positiveEnergy(incidentEnergyKev);
  const theta = angle(thetaDeg);
  const thetaRad = (theta * Math.PI) / 180;
  const cosine = Math.cos(thetaRad);
  const sineSquared = Math.sin(thetaRad) ** 2;
  const alpha = energy / ELECTRON_REST_ENERGY_KEV;
  const ratio = 1 / (1 + alpha * (1 - cosine));
  return (
    0.5 *
    CLASSICAL_ELECTRON_RADIUS_M ** 2 *
    ratio ** 2 *
    (ratio + 1 / ratio - sineSquared)
  );
}

export function kleinNishinaTotalM2(incidentEnergyKev) {
  const energy = positiveEnergy(incidentEnergyKev);
  const alpha = energy / ELECTRON_REST_ENERGY_KEV;
  if (alpha < 1e-3) {
    const ratio =
      1 - 2 * alpha + (26 / 5) * alpha ** 2 - (133 / 10) * alpha ** 3;
    return THOMSON_CROSS_SECTION_M2 * ratio;
  }
  const logarithm = Math.log1p(2 * alpha);
  const bracket =
    ((1 + alpha) / alpha ** 2) *
      ((2 * (1 + alpha)) / (1 + 2 * alpha) - logarithm / alpha) +
    logarithm / (2 * alpha) -
    (1 + 3 * alpha) / (1 + 2 * alpha) ** 2;
  return 2 * Math.PI * CLASSICAL_ELECTRON_RADIUS_M ** 2 * bracket;
}

export function kleinNishinaState(incidentEnergyKev, thetaDeg) {
  const energy = positiveEnergy(incidentEnergyKev);
  const theta = angle(thetaDeg);
  const thetaRad = (theta * Math.PI) / 180;
  const differentialM2Sr = kleinNishinaDifferentialM2Sr(energy, theta);
  const totalM2 = kleinNishinaTotalM2(energy);
  const thetaDensityM2Rad =
    theta === 0 || theta === 180
      ? 0
      : 2 * Math.PI * Math.sin(thetaRad) * differentialM2Sr;
  return Object.freeze({
    differentialM2Sr,
    differentialBarnSr: differentialM2Sr / BARN_M2,
    relativeDifferential:
      differentialM2Sr / CLASSICAL_ELECTRON_RADIUS_M ** 2,
    thetaDensityM2Rad,
    thetaPdfRadInv: thetaDensityM2Rad / totalM2,
    totalM2,
    totalBarn: totalM2 / BARN_M2,
  });
}

export function kleinNishinaSweep(incidentEnergyKev, stepDeg = 0.5) {
  const step = Number(stepDeg);
  if (!Number.isFinite(step) || step <= 0 || !Number.isInteger(180 / step)) {
    throw new RangeError("stepDeg must divide 180 degrees exactly");
  }
  const values = [];
  for (let theta = 0; theta <= 180 + step / 2; theta += step) {
    values.push(
      Object.freeze({
        thetaDeg: Math.min(theta, 180),
        ...kleinNishinaState(incidentEnergyKev, Math.min(theta, 180)),
      }),
    );
  }
  return Object.freeze(values);
}
