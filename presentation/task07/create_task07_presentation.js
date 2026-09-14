"use strict";

const fs = require("node:fs");
const path = require("node:path");
const JSZip = require("jszip");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(REPOSITORY_ROOT, "figures", "task07");
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task07_Particle_In_A_Box.pptx",
);
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const ASSETS = [
  ["energy_spectrum.png", "01_energy_spectrum.png"],
  ["probability_densities.png", "02_probability_densities.png"],
  ["wavefunctions_and_density.png", "03_wavefunctions_and_density.png"],
  ["energy_level_wavefunctions.png", "04_energy_level_wavefunctions.png"],
  ["uncertainty_principle.png", "05_uncertainty_principle.png"],
  ["task07_summary.png", "06_task07_summary.png"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(FIGURE_DIRECTORY, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing validated Task 7 visual: ${sourcePath}`);
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
  pptx.subject = "Task 7 particle-in-a-box presentation slide";
  pptx.title = "Task 7 — Particle in a One-Dimensional Box";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Times New Roman",
    bodyFontFace: "Times New Roman",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "06_task07_summary.png"),
    x: 0.12,
    y: 0.08,
    w: 13.09,
    h: 7.36,
    altText:
      "Task 7 summary for an electron in a one-nanometre infinite well. " +
      "The left panel shows four normalized stationary probability densities " +
      "with increasing node count. The upper middle panel shows ten discrete " +
      "energies growing as quantum number squared. The lower middle panel " +
      "shows the uncertainty product above the one-half-h-bar bound. Result " +
      "cards give the ground energy, ground uncertainty, finite-difference " +
      "error and fifty passing checks.",
  });

  slide.addNotes(
    "FINAL SCRIPT (approximately 18 seconds)\n\n" +
      "Task 7 solves an electron in a one-nanometre infinite box. Boundary " +
      "conditions create standing waves and discrete energies growing as n " +
      "squared. The probability densities remain normalised, while the " +
      "uncertainty calculation gives 0.568 h-bar in the ground state, above " +
      "Heisenberg's half-h-bar limit. Fifty independent checks pass.\n\n" +
      "CUES\n0–6 s: probability densities.\n" +
      "6–11 s: discrete energy spectrum.\n" +
      "11–16 s: uncertainty product and lower bound.\n" +
      "16–18 s: validation badge.",
  );

  await writePresentationDeterministically(pptx);
  await enforceTimesNewRomanTheme();
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
