"use strict";

const fs = require("node:fs");
const path = require("node:path");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(REPOSITORY_ROOT, "figures", "task03");
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task03_Planck_Einstein.pptx",
);
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const COLOURS = {
  background: "F7FAFC",
  white: "FFFFFF",
  text: "243447",
  muted: "6B7B8C",
  border: "DCE3E8",
  blue: "0072B2",
  orange: "D55E00",
  green: "009E73",
  greenPale: "E7F5ED",
  greenBorder: "8ED1AC",
};

const ASSETS = [
  ["planck_spectra.png", "01_planck_spectra.png"],
  ["einstein_heat_capacity.png", "02_einstein_heat_capacity.png"],
  ["planck_validation.png", "03_planck_validation.png"],
  ["einstein_normalized.png", "04_einstein_normalized.png"],
  ["task03_summary.png", "05_task03_summary.png"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(FIGURE_DIRECTORY, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing Stage 9 visual: ${sourcePath}`);
    }
    fs.copyFileSync(sourcePath, path.join(IMAGE_DIRECTORY, targetName));
  }
}

async function writePresentationDeterministically(pptx) {
  // PptxGenJS otherwise writes the current time into core.xml and ZIP entries.
  // Freezing the clock only during export makes clean builds byte-identical.
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

function addCard(slide, pptx, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.05,
    fill: { color: COLOURS.white },
    line: { color: COLOURS.border, width: 1 },
  });
}

function addEvidenceBlock(slide, x, title, body, colour) {
  slide.addShape("line", {
    x,
    y: 5.96,
    w: 0.05,
    h: 0.69,
    line: { color: colour, width: 3.2 },
  });
  slide.addText(title, {
    x: x + 0.19,
    y: 5.93,
    w: 3.82,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12.5,
    bold: true,
    color: COLOURS.muted,
    fit: "shrink",
  });
  slide.addText(body, {
    x: x + 0.19,
    y: 6.24,
    w: 3.82,
    h: 0.32,
    margin: 0,
    fontFace: "Arial",
    fontSize: 17.5,
    bold: true,
    color: COLOURS.text,
    fit: "shrink",
    valign: "mid",
  });
}

async function buildPresentation() {
  prepareAssets();

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Ocin12345";
  pptx.company = "BPhO Computational Challenge 2026";
  pptx.subject = "Task 3 Planck radiation and Einstein heat capacity slide";
  pptx.title = "Task 3 — Thermal Radiation and Heat Capacity";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Arial",
    bodyFontFace: "Arial",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: COLOURS.background };

  slide.addText("Task 3 — Thermal Radiation and Heat Capacity", {
    x: 0.52,
    y: 0.22,
    w: 12.3,
    h: 0.48,
    margin: 0,
    fontFace: "Arial",
    fontSize: 28,
    bold: true,
    color: COLOURS.text,
    fit: "shrink",
  });
  slide.addText(
    "Hotter black bodies peak at shorter wavelengths; higher Tₑ delays the rise to 3R.",
    {
      x: 0.54,
      y: 0.76,
      w: 12.1,
      h: 0.28,
      margin: 0,
      fontFace: "Arial",
      fontSize: 16.5,
      color: COLOURS.blue,
      bold: true,
      fit: "shrink",
    },
  );
  slide.addShape(pptx.ShapeType.line, {
    x: 0.52,
    y: 1.12,
    w: 12.3,
    h: 0,
    line: { color: COLOURS.blue, width: 2.25 },
  });

  addCard(slide, pptx, 0.46, 1.29, 6.12, 4.28);
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "01_planck_spectra.png"),
    x: 0.59,
    y: 1.40,
    w: 5.86,
    h: 3.63,
    altText:
      "Planck spectral exitance from 100 to 3000 nanometres for 4000, " +
      "5000, and 6000 kelvin. The hotter curves are taller and peak at " +
      "shorter wavelengths; the visible band and numerical peaks are marked.",
  });
  slide.addText("Peak shifts 724 → 483 nm from 4000 → 6000 K", {
    x: 0.70,
    y: 5.15,
    w: 5.64,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 13.5,
    bold: true,
    align: "center",
    color: COLOURS.blue,
    fit: "shrink",
  });

  addCard(slide, pptx, 6.75, 1.29, 6.12, 4.28);
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "02_einstein_heat_capacity.png"),
    x: 6.88,
    y: 1.40,
    w: 5.86,
    h: 3.63,
    altText:
      "Einstein molar heat capacity from zero to 800 kelvin for seven " +
      "official solids. Every curve rises from zero towards the dashed " +
      "three-R Dulong–Petit limit, with carbon rising most slowly.",
  });
  slide.addText("At 800 K: Au ≈ 3R; carbon remains below the limit", {
    x: 6.99,
    y: 5.15,
    w: 5.64,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 13.5,
    bold: true,
    align: "center",
    color: COLOURS.orange,
    fit: "shrink",
  });

  addCard(slide, pptx, 0.46, 5.75, 12.41, 1.17);
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.72,
    y: 5.95,
    w: 2.52,
    h: 0.64,
    rectRadius: 0.04,
    fill: { color: COLOURS.greenPale },
    line: { color: COLOURS.greenBorder, width: 1 },
  });
  slide.addText("27/27 CHECKS PASS", {
    x: 0.84,
    y: 6.09,
    w: 2.28,
    h: 0.27,
    margin: 0,
    fontFace: "Arial",
    fontSize: 15.5,
    bold: true,
    align: "center",
    color: COLOURS.green,
    fit: "shrink",
  });
  addEvidenceBlock(
    slide,
    3.57,
    "PLANCK VALIDATION",
    "λₘₐₓT = b   •   M = σT⁴",
    COLOURS.blue,
  );
  addEvidenceBlock(
    slide,
    8.02,
    "EINSTEIN VALIDATION",
    "0 ≤ Cᵥ ≤ 3R   •   universal vs T/Tₑ",
    COLOURS.orange,
  );

  slide.addText("BPhO Computational Challenge 2026", {
    x: 9.6,
    y: 7.15,
    w: 3.2,
    h: 0.16,
    margin: 0,
    fontFace: "Arial",
    fontSize: 8.5,
    align: "right",
    color: COLOURS.muted,
  });

  slide.addNotes(
    "FINAL SCRIPT (approximately 17–18 seconds)\n\n" +
      "Task 3 models Planck radiation and Einstein heat capacity. Increasing " +
      "temperature moves the black-body peak to shorter wavelengths, while " +
      "total emission follows T to the fourth. For solids, the Einstein " +
      "temperature sets how quickly heat capacity rises towards three R. " +
      "All twenty-seven analytical and numerical checks passed.\n\n" +
      "CUES\n0–7 s: Planck spectrum and peak shift.\n" +
      "7–14 s: Einstein curves and three-R limit.\n" +
      "14–18 s: validation band.",
  );

  await writePresentationDeterministically(pptx);
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
