"use strict";

const fs = require("node:fs");
const path = require("node:path");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(
  REPOSITORY_ROOT,
  "task02_brownian_motion",
  "figures",
);
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task02_Brownian_Motion.pptx",
);

const COLOURS = {
  background: "F7FAFC",
  white: "FFFFFF",
  text: "243447",
  muted: "6B7B8C",
  border: "DCE3E8",
  blue: "0072B2",
  orange: "D55E00",
  green: "009E73",
};

const ASSETS = [
  ["reference_animation.gif", "01_reference_animation.gif"],
  ["baseline_statistics.png", "02_baseline_statistics.png"],
  ["reference_particle_scene.png", "03_reference_particle_scene.png"],
  ["parameter_experiments.png", "04_parameter_experiments.png"],
  ["numerical_validation.png", "05_numerical_validation.png"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(FIGURE_DIRECTORY, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing Step 9 visual: ${sourcePath}`);
    }
    fs.copyFileSync(sourcePath, path.join(IMAGE_DIRECTORY, targetName));
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

function addResultRow(slide, pptx, y, colour, text) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 5.31,
    y: y + 0.08,
    w: 0.14,
    h: 0.14,
    fill: { color: colour },
    line: { color: colour, transparency: 100 },
  });
  slide.addText(text, {
    x: 5.58,
    y,
    w: 7.02,
    h: 0.34,
    margin: 0,
    fontFace: "Arial",
    fontSize: 17.5,
    color: COLOURS.text,
    breakLine: false,
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
  pptx.subject = "Task 2 Brownian motion presentation slide";
  pptx.title = "Task 2 — Collision-Driven Brownian Motion";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Arial",
    bodyFontFace: "Arial",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: COLOURS.background };

  slide.addText("Task 2 — Collision-Driven Brownian Motion", {
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
    "Random molecular impacts produce unbiased diffusive tracer motion.",
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

  addCard(slide, pptx, 0.46, 1.31, 4.38, 5.69);
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "01_reference_animation.gif"),
    x: 0.64,
    y: 1.49,
    w: 4.02,
    h: 4.02,
    altText:
      "One thousand blue small particles collide with a large translucent " +
      "yellow tracer while an orange irregular path accumulates.",
  });
  slide.addText("Reference simulation", {
    x: 0.7,
    y: 5.74,
    w: 3.9,
    h: 0.31,
    margin: 0,
    fontFace: "Arial",
    fontSize: 17,
    bold: true,
    align: "center",
    color: COLOURS.text,
  });
  slide.addText("N = 1,000  •  200 ps  •  3,721 collision impulses", {
    x: 0.64,
    y: 6.13,
    w: 4.02,
    h: 0.52,
    margin: 0,
    fontFace: "Arial",
    fontSize: 13.5,
    align: "center",
    color: COLOURS.muted,
    fit: "shrink",
    valign: "mid",
  });

  addCard(slide, pptx, 5.04, 1.31, 7.84, 3.58);
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "02_baseline_statistics.png"),
    x: 5.22,
    y: 1.51,
    w: 7.48,
    h: 3.23,
    altText:
      "A 64-run mean-squared-displacement curve with a linear fit and " +
      "confidence band, beside an approximately circular endpoint cloud.",
  });

  addCard(slide, pptx, 5.04, 5.08, 7.84, 1.92);
  addResultRow(
    slide,
    pptx,
    5.29,
    COLOURS.green,
    "64-run ensemble: ⟨Δx⟩ and ⟨Δy⟩ 95% CIs include 0",
  );
  addResultRow(
    slide,
    pptx,
    5.81,
    COLOURS.orange,
    "MSD ∝ t: R² = 0.983; D = 2.25 × 10⁻³ nm² ps⁻¹",
  );
  addResultRow(
    slide,
    pptx,
    6.33,
    COLOURS.blue,
    "Time-step halving: ΔD = 5.7%; all 224 runs numerically valid",
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
      "Task 2 models one thousand small particles colliding with a larger " +
      "particle initially at rest, producing an irregular path. Across " +
      "sixty-four runs, displacement was unbiased and mean-squared " +
      "displacement was linear: R squared 0.983, with a diffusion " +
      "coefficient of 2.25 times ten to the minus three.\n\n" +
      "CUES\n0–6 s: tracer animation and trail.\n" +
      "6–12 s: endpoint cloud and unbiased result.\n" +
      "12–18 s: linear fit and diffusion coefficient.",
  );

  await pptx.writeFile({ fileName: OUTPUT_PATH, compression: true });
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
