"use strict";

const fs = require("node:fs");
const path = require("node:path");
const JSZip = require("jszip");
const pptxgen = require("pptxgenjs");

const PRESENTATION_DIRECTORY = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_DIRECTORY, "../..");
const FIGURE_DIRECTORY = path.join(REPOSITORY_ROOT, "figures", "task08");
const SCREENSHOT_DIRECTORY = path.join(FIGURE_DIRECTORY, "screenshots");
const IMAGE_DIRECTORY = path.join(PRESENTATION_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  PRESENTATION_DIRECTORY,
  "Task08_Quantum_Mismatch_Calculator.pptx",
);
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const ASSETS = [
  [FIGURE_DIRECTORY, "probability_sweep.png", "01_probability_sweep.png"],
  [FIGURE_DIRECTORY, "mismatch_landscape.png", "02_mismatch_landscape.png"],
  [FIGURE_DIRECTORY, "finite_photon_sampling.png", "03_finite_photon_sampling.png"],
  [FIGURE_DIRECTORY, "task08_summary.png", "04_task08_summary.png"],
  [SCREENSHOT_DIRECTORY, "detector_workspace_4k.png", "05_detector_workspace_4k.png"],
  [SCREENSHOT_DIRECTORY, "probability_chart_4k.png", "06_probability_chart_4k.png"],
  [SCREENSHOT_DIRECTORY, "finite_photon_extension_4k.png", "07_finite_photon_extension_4k.png"],
  [SCREENSHOT_DIRECTORY, "finite_photon_mobile_2x.png", "08_finite_photon_mobile_2x.png"],
];

function prepareAssets() {
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });
  for (const [sourceDirectory, sourceName, targetName] of ASSETS) {
    const sourcePath = path.join(sourceDirectory, sourceName);
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Missing validated Task 8 visual: ${sourcePath}`);
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
  pptx.subject = "Task 8 quantum mismatch calculator presentation slide";
  pptx.title = "Task 8 — Quantum Mismatch Calculator";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Times New Roman",
    bodyFontFace: "Times New Roman",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addImage({
    path: path.join(IMAGE_DIRECTORY, "04_task08_summary.png"),
    x: 0.12,
    y: 0.08,
    w: 13.09,
    h: 7.36,
    altText:
      "Task 8 quantum mismatch summary. Panel A shows detector axes at minus " +
      "thirty and plus thirty degrees, separated by sixty degrees. Panel B " +
      "plots classical solid orange and quantum dashed teal mismatch over the " +
      "full detector-B angle range, with the official values at thirty-seven " +
      "point five and seventy-five percent. Panel C maps quantum minus " +
      "classical contrast across both detector angles. Panel D shows a " +
      "reproducible one-thousand-pair sample with 363 classical and 770 quantum " +
      "mismatches. Badges show forty-two scientific and twenty-four statistical " +
      "checks passing.",
  });

  slide.addNotes(
    "FINAL SCRIPT (approximately 18 seconds)\n\n" +
      "Task 8 compares classical Malus probabilities with the entangled " +
      "quantum prediction. At minus thirty and plus thirty degrees, classical " +
      "mismatch is thirty-seven point five percent, while quantum mismatch is " +
      "seventy-five percent. The sweep exposes their different angle " +
      "dependence; a finite sample shows counting fluctuations. All sixty-six " +
      "validation checks pass.\n\n" +
      "CUES\n0–5 s: detector geometry and sixty-degree separation.\n" +
      "5–11 s: exact sweep and official probability markers.\n" +
      "11–15 s: contrast heatmap and finite sample.\n" +
      "15–18 s: scientific and statistical validation statement.",
  );

  await writePresentationDeterministically(pptx);
  await enforceTimesNewRomanTheme();
  console.log(`Created ${OUTPUT_PATH}`);
}

buildPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
