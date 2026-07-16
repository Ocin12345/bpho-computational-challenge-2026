"use strict";

const fs = require("node:fs");
const path = require("node:path");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(REPOSITORY_ROOT, "figures", "task04");
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task04_Photoelectric_Effect.pptx",
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
  orangePale: "FCEDE6",
  green: "009E73",
  greenPale: "E7F5ED",
  greenBorder: "8ED1AC",
};

const ASSETS = [
  ["stopping_voltage_frequency.png", "01_stopping_voltage_frequency.png"],
  ["photoelectric_demo.gif", "02_photoelectric_demo.gif"],
  ["stopping_voltage_wavelength.png", "03_stopping_voltage_wavelength.png"],
  ["copper_threshold_explanation.png", "04_copper_threshold_explanation.png"],
  ["photoelectric_validation.png", "05_photoelectric_validation.png"],
  ["task04_summary.png", "06_task04_summary.png"],
  ["photoelectric_demo_storyboard.png", "07_photoelectric_demo_storyboard.png"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(FIGURE_DIRECTORY, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing validated Task 4 visual: ${sourcePath}`);
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

async function buildPresentation() {
  prepareAssets();

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Ocin12345";
  pptx.company = "BPhO Computational Challenge 2026";
  pptx.subject = "Task 4 photoelectric-effect presentation slide";
  pptx.title = "Task 4 — Photoelectric Effect";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Arial",
    bodyFontFace: "Arial",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: COLOURS.background };

  slide.addText("Task 4 — Photoelectric Effect", {
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
    "Work function sets the emission threshold; photon energy above it sets the stopping potential.",
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

  addCard(slide, pptx, 0.46, 1.29, 8.02, 5.63);
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "01_stopping_voltage_frequency.png"),
    x: 0.61,
    y: 1.43,
    w: 7.72,
    h: 4.31,
    altText:
      "Stopping-potential magnitude against photon frequency for all nine " +
      "official metals. Seven physical curves are visible because silver, " +
      "aluminium, and lead coincide. Threshold markers show where each " +
      "curve begins, and the absent region is no photoemission.",
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.86,
    y: 5.93,
    w: 7.22,
    h: 0.64,
    rectRadius: 0.04,
    fill: { color: COLOURS.orangePale },
    line: { color: "F0B397", width: 1 },
  });
  slide.addText("All physical curves share gradient h/e; W shifts the threshold", {
    x: 1.01,
    y: 6.10,
    w: 6.92,
    h: 0.25,
    margin: 0,
    fontFace: "Arial",
    fontSize: 15,
    bold: true,
    align: "center",
    color: COLOURS.orange,
    fit: "shrink",
  });

  addCard(slide, pptx, 8.68, 1.29, 4.19, 2.94);
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "02_photoelectric_demo.gif"),
    x: 8.84,
    y: 1.43,
    w: 3.87,
    h: 2.18,
    altText:
      "Four-scene schematic sodium photoelectric demonstration. At 550 " +
      "nanometres there is no emission; at 450 nanometres electrons reach " +
      "the collector; higher intensity adds illustrative electrons without " +
      "changing maximum energy; and reverse stopping potential gives zero " +
      "photocurrent.",
  });
  slide.addText("Intensity changes count, not maximum energy", {
    x: 8.94,
    y: 3.77,
    w: 3.67,
    h: 0.23,
    margin: 0,
    fontFace: "Arial",
    fontSize: 12.5,
    bold: true,
    align: "center",
    color: COLOURS.blue,
    fit: "shrink",
  });

  addCard(slide, pptx, 8.68, 4.42, 4.19, 2.50);
  slide.addText("eVₛ = hf − W", {
    x: 8.98,
    y: 4.66,
    w: 3.59,
    h: 0.38,
    margin: 0,
    fontFace: "Arial",
    fontSize: 23,
    bold: true,
    align: "center",
    color: COLOURS.text,
    fit: "shrink",
  });
  slide.addText("Vₛ = (h/e)f − W/e", {
    x: 8.98,
    y: 5.08,
    w: 3.59,
    h: 0.28,
    margin: 0,
    fontFace: "Arial",
    fontSize: 16.5,
    align: "center",
    color: COLOURS.muted,
    fit: "shrink",
  });
  slide.addText("Na visible cut-off: 516.6 nm", {
    x: 9.02,
    y: 5.50,
    w: 3.51,
    h: 0.27,
    margin: 0,
    fontFace: "Arial",
    fontSize: 15.5,
    bold: true,
    align: "center",
    color: COLOURS.orange,
    fit: "shrink",
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 9.25,
    y: 6.03,
    w: 3.05,
    h: 0.56,
    rectRadius: 0.04,
    fill: { color: COLOURS.greenPale },
    line: { color: COLOURS.greenBorder, width: 1 },
  });
  slide.addText("43/43 CHECKS PASS", {
    x: 9.42,
    y: 6.17,
    w: 2.71,
    h: 0.24,
    margin: 0,
    fontFace: "Arial",
    fontSize: 15.5,
    bold: true,
    align: "center",
    color: COLOURS.green,
    fit: "shrink",
  });

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
      "Task 4 models Einstein's photoelectric equation for nine metals. " +
      "Every stopping-potential curve has gradient h over e; the work " +
      "function sets the threshold. Sodium reaches visible light up to " +
      "517 nanometres. Below threshold, no photoelectrons exist, so " +
      "stopping potential is undefined. All forty-three independent checks " +
      "passed.\n\n" +
      "CUES\n0–7 s: curves and threshold markers.\n" +
      "7–12 s: sodium cut-off.\n" +
      "12–18 s: animation status and validation badge.",
  );

  await writePresentationDeterministically(pptx);
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
