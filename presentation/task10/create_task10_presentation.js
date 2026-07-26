"use strict";

const fs = require("node:fs");
const path = require("node:path");
const JSZip = require("jszip");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(REPOSITORY_ROOT, "figures", "task10");
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task10_Hydrogenic_Orbitals.pptx",
);
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const ASSETS = [
  ["required_orbital_gallery.png", "01_required_orbital_gallery.png"],
  ["radial_and_nodal_structure.png", "02_radial_and_nodal_structure.png"],
  ["coloured_glass_density.png", "03_coloured_glass_density.png"],
  ["rendering_comparison.png", "04_rendering_comparison.png"],
  ["task10_summary.png", "05_task10_summary.png"],
  ["orbital_view_rotation_poster.png", "06_orbital_view_rotation_poster.png"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(FIGURE_DIRECTORY, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing validated Task 10 visual: ${sourcePath}`);
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
  pptx.subject = "Task 10 normalized hydrogenic-orbital presentation slide";
  pptx.title = "Task 10 — Hydrogenic Orbitals";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Times New Roman",
    bodyFontFace: "Times New Roman",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "05_task10_summary.png"),
    x: 0.12,
    y: 0.08,
    w: 13.09,
    h: 7.36,
    altText:
      "Task 10 normalized hydrogenic-orbital summary. Panel A shows a " +
      "17-plane semi-transparent coloured-glass rendering of hydrogen 3d, " +
      "m equals zero, with nodal surfaces visible. Result cards report " +
      "energy minus 1.51091 electron volts, a 99.95-percent radius of " +
      "15.13 angstroms, zero radial nodes and two angular nodes. Panel B " +
      "shows the S-through-G family progression 1s, 2p, 3d, 4f and 5g for " +
      "m equals zero. Panel C plots scaled radial probability. Validation totals show " +
      "22 of 22 scientific checks passing across 204 validated states. A " +
      "footer states that the threshold changes opacity only and view " +
      "rotation is camera motion, not electron motion.",
  });

  slide.addNotes(
    "FINAL SCRIPT (approximately 18 seconds)\n\n" +
      "Task 10 constructs normalized hydrogenic orbitals from S through G. " +
      "The gallery contains twenty-five real states, while coloured-glass " +
      "slices reveal three-dimensional density and nodes. Energy scales as Z " +
      "squared over n squared, and size as one over Z. View rotation is camera " +
      "motion, not electron motion; all twenty-two checks pass.\n\n" +
      "CUES\n0–5 s: coloured-glass density and node result cards.\n" +
      "5–10 s: S-through-G family progression and 25-state gallery.\n" +
      "10–15 s: radial structure and Z-scaling relationships.\n" +
      "15–18 s: validation totals and camera-motion caveat.",
  );

  await writePresentationDeterministically(pptx);
  await enforceTimesNewRomanTheme();
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
