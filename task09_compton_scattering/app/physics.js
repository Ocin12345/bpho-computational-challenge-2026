export const SPEED_OF_LIGHT_M_S = 299_792_458;
export const PLANCK_CONSTANT_J_S = 6.626_070_15e-34;
export const ELEMENTARY_CHARGE_C = 1.602_176_634e-19;
export const ELECTRON_MASS_KG = 9.109_383_7139e-31;
export const JOULES_PER_KEV = 1_000 * ELEMENTARY_CHARGE_C;
export const ELECTRON_REST_ENERGY_KEV =
  (ELECTRON_MASS_KG * SPEED_OF_LIGHT_M_S ** 2) / JOULES_PER_KEV;
export const ELECTRON_COMPTON_WAVELENGTH_M =
  PLANCK_CONSTANT_J_S / (ELECTRON_MASS_KG * SPEED_OF_LIGHT_M_S);
export const OFFICIAL_ENERGIES_KEV = Object.freeze([50, 100, 200, 500, 1_000]);

const MINIMUM_ENERGY_KEV = 1;
const MAXIMUM_ENERGY_KEV = 5_000;

function finiteNumber(value, name) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
  return value;
}

export function clampIncidentEnergyKev(value) {
  const energy = finiteNumber(value, "incidentEnergyKev");
  return Math.min(MAXIMUM_ENERGY_KEV, Math.max(MINIMUM_ENERGY_KEV, energy));
}

export function clampScatteringAngleDeg(value) {
  const theta = finiteNumber(value, "thetaDeg");
  return Math.min(180, Math.max(0, theta));
}

export function comptonKinematics(incidentEnergyKev, thetaDeg) {
  const energy = finiteNumber(incidentEnergyKev, "incidentEnergyKev");
  const theta = finiteNumber(thetaDeg, "thetaDeg");
  if (energy < MINIMUM_ENERGY_KEV || energy > MAXIMUM_ENERGY_KEV) {
    throw new RangeError("incidentEnergyKev must lie within 1 to 5000 keV");
  }
  if (theta < 0 || theta > 180) {
    throw new RangeError("thetaDeg must lie within 0 to 180 degrees");
  }

  const thetaRad = (theta * Math.PI) / 180;
  const cosine = Math.cos(thetaRad);
  const sine = theta === 0 || theta === 180 ? 0 : Math.sin(thetaRad);
  const angularFactor = 1 - cosine;
  const alpha = energy / ELECTRON_REST_ENERGY_KEV;
  const incidentWavelengthM =
    (PLANCK_CONSTANT_J_S * SPEED_OF_LIGHT_M_S) / (energy * JOULES_PER_KEV);
  const wavelengthShiftM = ELECTRON_COMPTON_WAVELENGTH_M * angularFactor;
  const scatteredWavelengthM = incidentWavelengthM + wavelengthShiftM;
  const fractionalWavelengthShift = wavelengthShiftM / incidentWavelengthM;
  const electronKineticEnergyKev =
    (energy * wavelengthShiftM) / scatteredWavelengthM;
  const scatteredEnergyKev = energy - electronKineticEnergyKev;
  const kineticOverRest = electronKineticEnergyKev / ELECTRON_REST_ENERGY_KEV;
  const electronGamma = 1 + kineticOverRest;
  const electronBeta = Math.sqrt(
    (kineticOverRest * (kineticOverRest + 2)) / (kineticOverRest + 1) ** 2,
  );
  const photonXDifferenceKev = energy - scatteredEnergyKev * cosine;
  const scatteredPhotonYKev = scatteredEnergyKev * sine;
  const electronPcKev = Math.hypot(photonXDifferenceKev, scatteredPhotonYKev);
  const electronRecoilDirectionDefined = theta !== 0;
  const electronRecoilAngleDeg = electronRecoilDirectionDefined
    ? theta === 180
      ? 0
      : (Math.atan2(scatteredPhotonYKev, photonXDifferenceKev) * 180) / Math.PI
    : 90;

  return Object.freeze({
    incidentEnergyKev: energy,
    thetaDeg: theta,
    alpha,
    incidentWavelengthM,
    wavelengthShiftM,
    fractionalWavelengthShift,
    scatteredWavelengthM,
    scatteredEnergyKev,
    electronKineticEnergyKev,
    electronGamma,
    electronBeta,
    electronSpeedMS: electronBeta * SPEED_OF_LIGHT_M_S,
    electronPcKev,
    electronRecoilAngleDeg,
    electronRecoilDirectionDefined,
  });
}

export function angleSweep(incidentEnergyKev, stepDeg = 0.5) {
  const energy = finiteNumber(incidentEnergyKev, "incidentEnergyKev");
  const step = finiteNumber(stepDeg, "stepDeg");
  if (step <= 0 || !Number.isInteger(180 / step)) {
    throw new RangeError("stepDeg must divide 180 degrees exactly");
  }
  const values = [];
  for (let theta = 0; theta <= 180 + step / 2; theta += step) {
    values.push(comptonKinematics(energy, Math.min(theta, 180)));
  }
  return Object.freeze(values);
}
