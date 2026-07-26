"use strict";

const fs = require("node:fs");
const path = require("node:path");
const JSZip = require("jszip");
const pptxgen = require("pptxgenjs");

const PRESENTATION_ROOT = __dirname;
const REPOSITORY_ROOT = path.resolve(PRESENTATION_ROOT, "..");
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const TASKS = [
  {
    number: 1,
    title: "Task 1 — Two-Dimensional Random Walk",
    subject: "Task 1 random-walk presentation slide",
    source: path.join(REPOSITORY_ROOT, "figures/task01/task01_summary.png"),
    image: "05_task01_summary.png",
    output: "Task01_Random_Walk.pptx",
    alt:
      "Task 1 summary. Fifty fixed-step random walks spread from a common " +
      "origin without preferred direction. A fifty-thousand-walk endpoint " +
      "cloud is circular and agrees with theoretical containment radii. " +
      "Result cards show uniform angular sampling, mean squared displacement " +
      "equal to N s squared, a fitted slope of 0.9992 plus or minus 0.0031, " +
      "and thirty-seven passing checks.",
  },
  {
    number: 2,
    title: "Task 2 — Collision-Driven Brownian Motion",
    subject: "Task 2 Brownian-motion presentation slide",
    source: path.join(
      REPOSITORY_ROOT,
      "task02_brownian_motion/figures/task02_summary.png",
    ),
    image: "06_task02_summary.png",
    output: "Task02_Brownian_Motion.pptx",
    alt:
      "Task 2 summary. A large tracer moves through one thousand small " +
      "particles. Sixty-four trajectories give a linear intermediate " +
      "mean-squared displacement with R squared 0.983 and diffusion " +
      "coefficient 2.25 times ten to the minus three square nanometres per " +
      "picosecond. The endpoint cloud and confidence intervals show no drift.",
  },
  {
    number: 3,
    title: "Task 3 — Planck Radiation and Einstein Heat Capacity",
    subject: "Task 3 Planck-radiation and Einstein-heat-capacity slide",
    source: path.join(REPOSITORY_ROOT, "figures/task03/task03_summary.png"),
    image: "05_task03_summary.png",
    output: "Task03_Planck_Einstein.pptx",
    alt:
      "Task 3 summary comparing three Planck black-body spectra, seven " +
      "Einstein heat-capacity curves, numerical errors against analytical " +
      "laws and the universal normalized Einstein curve. All twenty-seven " +
      "checks pass.",
  },
  {
    number: 4,
    title: "Task 4 — Photoelectric Effect",
    subject: "Task 4 photoelectric-effect presentation slide",
    source: path.join(REPOSITORY_ROOT, "figures/task04/task04_summary.png"),
    image: "06_task04_summary.png",
    output: "Task04_Photoelectric_Effect.pptx",
    alt:
      "Task 4 summary for nine metals. Stopping potential is plotted against " +
      "frequency and wavelength, the copper threshold separates a " +
      "mathematical extrapolation from the physical solution, and result text " +
      "states the common h over e gradient and forty-three passing checks.",
  },
  {
    number: 5,
    title: "Task 5 — Hydrogen Spectrum",
    subject: "Task 5 hydrogen-spectrum presentation slide",
    source: path.join(REPOSITORY_ROOT, "figures/task05/task05_summary.png"),
    image: "06_task05_summary.png",
    output: "Task05_Hydrogen_Spectrum.pptx",
    alt:
      "Task 5 summary. Forty-five discrete downward transitions among ten " +
      "Bohr levels are shown as photon energy versus wavelength, an energy " +
      "level diagram and visible Balmer line positions. The ideal H-alpha " +
      "line is 656.112 nanometres and all thirty checks pass.",
  },
  {
    number: 6,
    title: "Task 6 — Electron Diffraction",
    subject: "Task 6 electron-diffraction presentation slide",
    source: path.join(REPOSITORY_ROOT, "figures/task06/task06_summary.png"),
    image: "06_task06_summary.png",
    output: "Task06_Electron_Diffraction.pptx",
    alt:
      "Task 6 summary. A geometric graphite diffraction-ring rendering at " +
      "three kilovolts is paired with the required straight-line validation. " +
      "The fits recover both graphite spacings, 0.123 and 0.213 nanometres, " +
      "and all thirty-nine checks pass.",
  },
];

function finalScript(taskDirectory) {
  const markdown = fs.readFileSync(
    path.join(taskDirectory, "SPEAKER_SCRIPT.md"),
    "utf8",
  );
  const lines = markdown.split(/\r?\n/);
  const spoken = [];
  let collecting = false;
  for (const line of lines) {
    if (line.startsWith("> ")) {
      collecting = true;
      spoken.push(line.slice(2).trim());
    } else if (collecting) {
      break;
    }
  }
  if (spoken.length === 0) {
    throw new Error(`No final blockquote found in ${taskDirectory}`);
  }
  return spoken.join(" ");
}

async function writePresentationDeterministically(pptx, outputPath) {
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
    await pptx.writeFile({ fileName: outputPath, compression: true });
  } finally {
    global.Date = SystemDate;
  }
}

async function enforceTimesNewRomanTheme(outputPath) {
  const archive = await JSZip.loadAsync(fs.readFileSync(outputPath));
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
  fs.writeFileSync(outputPath, content);
}

async function buildTask(task) {
  if (!fs.existsSync(task.source)) {
    throw new Error(`Missing validated summary visual: ${task.source}`);
  }
  const taskDirectory = path.join(
    PRESENTATION_ROOT,
    `task${String(task.number).padStart(2, "0")}`,
  );
  const imageDirectory = path.join(taskDirectory, "images");
  fs.mkdirSync(imageDirectory, { recursive: true });
  const imagePath = path.join(imageDirectory, task.image);
  fs.copyFileSync(task.source, imagePath);

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Ocin12345";
  pptx.company = "BPhO Computational Challenge 2026";
  pptx.subject = task.subject;
  pptx.title = task.title;
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Times New Roman",
    bodyFontFace: "Times New Roman",
    lang: "en-GB",
  };

  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addImage({
    path: imagePath,
    x: 0.12,
    y: 0.08,
    w: 13.09,
    h: 7.36,
    altText: task.alt,
  });
  slide.addNotes(
    "FINAL SCRIPT\n\n" + finalScript(taskDirectory) +
      "\n\nMASTER-DECK CUE\nFollow model, validation evidence, then result.",
  );

  const outputPath = path.join(taskDirectory, task.output);
  await writePresentationDeterministically(pptx, outputPath);
  await enforceTimesNewRomanTheme(outputPath);
  console.log(`Created ${outputPath}`);
}

async function main() {
  const requestedNumbers = process.argv.slice(2).map((value) => Number(value));
  if (requestedNumbers.some((value) => !Number.isInteger(value))) {
    throw new Error("Task filters must be integer task numbers");
  }
  const selectedTasks = requestedNumbers.length
    ? TASKS.filter((task) => requestedNumbers.includes(task.number))
    : TASKS;
  if (selectedTasks.length === 0) {
    throw new Error(`No supported tasks selected: ${requestedNumbers.join(", ")}`);
  }
  for (const task of selectedTasks) {
    await buildTask(task);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
