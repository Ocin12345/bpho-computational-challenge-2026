"use strict";

const fs = require("node:fs");
const path = require("node:path");
const JSZip = require("jszip");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(REPOSITORY_ROOT, "figures", "task09");
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task09_Compton_Scattering.pptx",
);
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const ASSETS = [
  ["required_kinematics.png", "01_required_kinematics.png"],
  ["energy_transfer_geometry.png", "02_energy_transfer_geometry.png"],
  ["klein_nishina_extension.png", "03_klein_nishina_extension.png"],
  ["task09_summary.png", "04_task09_summary.png"],
  ["compton_angle_sweep.gif", "05_compton_angle_sweep.gif"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(FIGURE_DIRECTORY, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing validated Task 9 visual: ${sourcePath}`);
    }
    fs.copyFileSync(sourcePath, path.join(IMAGE_DIRECTORY, targetName));
  }
}

async function writePresentationDeterministically(pptx) {
  const SystemDate = global.Date;
  const fixedTime = SystemDate.parse(REPRODUCIBLE_TIMESTAMP);
  global.Date = class ReproducibleDate extends SystemDate {
    constructor(...args) {
      super(...(args.length === 0 ? [fixedTime] : args));
    }

    static now() {
      return fixedTime;
    }
  };
  try {
    await pptx.writeFile({ fileName: OUTPUT_PATH, compression: true });
  } finally {
    global.Date = SystemDate;
  }
}

async function enforceTimesNewRomanTheme() {
  const archive = await JSZip.loadAsync(fs.readFileSync(OUTPUT_PATH));
  const themePath = "ppt/theme/theme1.xml";
  const themeFile = archive.file(themePath);
  if (!themeFile) {
    throw new Error(`Missing PowerPoint theme: ${themePath}`);
  }
  const themeXml = (await themeFile.async("string")).replaceAll(
    'typeface="Arial"',
    'typeface="Times New Roman"',
  );
  const fixedDate = new Date(REPRODUCIBLE_TIMESTAMP);
  archive.file(themePath, themeXml, { date: fixedDate });
  archive.forEach((_relativePath, entry) => {
    entry.date = fixedDate;
  });
  const content = await archive.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  });
  fs.writeFileSync(OUTPUT_PATH, content);
}

async function buildPresentation() {
  prepareAssets();

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Ocin12345";
  pptx.company = "BPhO Computational Challenge 2026";
  pptx.subject = "Task 9 exact relativistic Compton-scattering presentation slide";
  pptx.title = "Task 9 — Compton Scattering";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Times New Roman",
    bodyFontFace: "Times New Roman",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "04_task09_summary.png"),
    x: 0.12,
    y: 0.08,
    w: 13.09,
    h: 7.36,
    altText:
      "Task 9 Compton-scattering summary. Panel A shows the exact 200 keV " +
      "momentum triangle at a 90-degree photon-scattering angle, with the " +
      "scattered photon at 143.741 keV and the electron recoiling at 35.705 " +
      "degrees. Panels B, C and D plot fractional wavelength shift, " +
      "relativistic electron speed as a fraction of c, and electron recoil " +
      "angle against photon angle for 50, 100, 200, 500 and 1000 keV. The " +
      "200 keV reference values are 0.391390, 0.434186 c and 35.705 degrees. " +
      "Validation totals show 44 of 44 core and 30 of 30 extension checks passing.",
  });

  slide.addNotes(
    "FINAL SCRIPT (approximately 18 seconds)\n\n" +
      "Task 9 models exact Compton scattering at five energies. Fractional " +
      "shift and electron speed rise with angle, while recoil angle falls to " +
      "zero at backscatter. At 200 keV and 90 degrees we obtain 0.391, " +
      "0.434 c and 35.7 degrees. Energy-momentum conservation passed all 44 " +
      "checks.\n\n" +
      "CUES\n0–4 s: exact 200 keV momentum triangle.\n" +
      "4–10 s: wavelength-shift and relativistic-speed curves.\n" +
      "10–15 s: recoil-angle curves and 200 keV reference markers.\n" +
      "15–18 s: core and extension validation totals.",
  );

  await writePresentationDeterministically(pptx);
  await enforceTimesNewRomanTheme();
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
