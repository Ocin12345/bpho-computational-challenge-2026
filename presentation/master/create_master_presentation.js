"use strict";

const fs = require("node:fs");
const path = require("node:path");
const JSZip = require("jszip");
const pptxgen = require("pptxgenjs");

const MASTER_DIRECTORY = __dirname;
const PRESENTATION_ROOT = path.resolve(MASTER_DIRECTORY, "..");
const REPOSITORY_ROOT = path.resolve(PRESENTATION_ROOT, "..");
const IMAGE_DIRECTORY = path.join(MASTER_DIRECTORY, "images");
const OUTPUT_PATH = path.join(
  MASTER_DIRECTORY,
  "BPhO_Computational_Challenge_Tasks_1_to_10.pptx",
);
const NARRATION_PATH = path.join(MASTER_DIRECTORY, "MASTER_NARRATION.md");
const REPRODUCIBLE_TIMESTAMP = "2026-01-01T00:00:00.000Z";

const TASKS = [
  {
    number: 1,
    source: path.join(REPOSITORY_ROOT, "figures/task01/task01_summary.png"),
    alt:
      "Task 1 summary: fixed-step random-walk paths, a circular endpoint " +
      "distribution, agreement with mean squared displacement N s squared, " +
      "and thirty-seven passing checks.",
  },
  {
    number: 2,
    source: path.join(
      REPOSITORY_ROOT,
      "task02_brownian_motion/figures/task02_summary.png",
    ),
    alt:
      "Task 2 summary: a collision-driven Brownian tracer, linear ensemble " +
      "mean-squared displacement, an unbiased endpoint cloud and sixty-four " +
      "trajectories.",
  },
  {
    number: 3,
    source: path.join(REPOSITORY_ROOT, "figures/task03/task03_summary.png"),
    alt:
      "Task 3 summary: Planck spectra, Einstein heat capacities, analytical " +
      "error checks, normalized curve collapse and twenty-seven passing checks.",
  },
  {
    number: 4,
    source: path.join(REPOSITORY_ROOT, "figures/task04/task04_summary.png"),
    alt:
      "Task 4 summary: photoelectric stopping potential versus frequency and " +
      "wavelength, the copper threshold and forty-three passing checks.",
  },
  {
    number: 5,
    source: path.join(REPOSITORY_ROOT, "figures/task05/task05_summary.png"),
    alt:
      "Task 5 summary: Bohr photon energy versus wavelength, bound-state " +
      "levels, visible Balmer lines and thirty passing checks.",
  },
  {
    number: 6,
    source: path.join(REPOSITORY_ROOT, "figures/task06/task06_summary.png"),
    alt:
      "Task 6 summary: graphite electron-diffraction rings, the required " +
      "straight-line graph, recovered spacings and thirty-nine passing checks.",
  },
  {
    number: 7,
    source: path.join(REPOSITORY_ROOT, "figures/task07/task07_summary.png"),
    alt:
      "Task 7 summary: stationary probability densities, quantized energies, " +
      "Heisenberg uncertainty and thirty-seven passing checks.",
  },
  {
    number: 8,
    source: path.join(REPOSITORY_ROOT, "figures/task08/task08_summary.png"),
    alt:
      "Task 8 summary: classical and entangled detector probabilities, an " +
      "angle sweep, finite sampling and sixty-six validation checks.",
  },
  {
    number: 9,
    source: path.join(REPOSITORY_ROOT, "figures/task09/task09_summary.png"),
    alt:
      "Task 9 summary: exact Compton-scattering geometry, angle-dependent " +
      "fractional shift, electron speed, recoil angle and conservation checks.",
  },
  {
    number: 10,
    source: path.join(REPOSITORY_ROOT, "figures/task10/task10_summary.png"),
    alt:
      "Task 10 summary: normalized hydrogenic orbitals, colored-glass density, " +
      "S-through-G states, radial structure and twenty-two passing checks.",
  },
];

function parseNarration() {
  const lines = fs.readFileSync(NARRATION_PATH, "utf8").split(/\r?\n/);
  const sections = new Map();
  let current = null;
  for (let index = 0; index < lines.length; index += 1) {
    const heading = lines[index].match(/^## Task (\d+)\s+—\s+(.+)$/);
    if (heading) {
      current = {
        number: Number(heading[1]),
        title: heading[2],
        spoken: [],
        cue: [],
      };
      sections.set(current.number, current);
      continue;
    }
    if (!current) {
      continue;
    }
    if (lines[index].startsWith("> ")) {
      current.spoken.push(lines[index].slice(2).trim());
      continue;
    }
    if (lines[index].startsWith("Cue: ")) {
      current.cue.push(lines[index].slice(5).trim());
      let next = index + 1;
      while (next < lines.length && lines[next].trim() !== "") {
        if (lines[next].startsWith("## ")) {
          break;
        }
        current.cue.push(lines[next].trim());
        next += 1;
      }
    }
  }
  for (const task of TASKS) {
    const section = sections.get(task.number);
    if (!section || section.spoken.length === 0 || section.cue.length === 0) {
      throw new Error(`Narration is incomplete for Task ${task.number}`);
    }
    section.spoken = section.spoken.join(" ");
    section.cue = section.cue.join(" ");
  }
  return sections;
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

async function buildMasterPresentation() {
  const narration = parseNarration();
  fs.mkdirSync(IMAGE_DIRECTORY, { recursive: true });

  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Ocin12345";
  pptx.company = "BPhO Computational Challenge 2026";
  pptx.subject = "Validated computational physics Tasks 1 to 10";
  pptx.title = "BPhO Computational Challenge — Tasks 1 to 10";
  pptx.lang = "en-GB";
  pptx.theme = {
    headFontFace: "Times New Roman",
    bodyFontFace: "Times New Roman",
    lang: "en-GB",
  };

  for (const task of TASKS) {
    if (!fs.existsSync(task.source)) {
      throw new Error(`Missing validated Task ${task.number} summary: ${task.source}`);
    }
    const imageName = `${String(task.number).padStart(2, "0")}_task${String(task.number).padStart(2, "0")}_summary.png`;
    const imagePath = path.join(IMAGE_DIRECTORY, imageName);
    fs.copyFileSync(task.source, imagePath);

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
    const section = narration.get(task.number);
    slide.addNotes(
      `TASK ${task.number} FINAL MASTER SCRIPT\n\n${section.spoken}` +
        `\n\nVISUAL CUE\n${section.cue}`,
    );
  }

  await writePresentationDeterministically(pptx);
  await enforceTimesNewRomanTheme();
  console.log(`Created ${OUTPUT_PATH}`);
}

buildMasterPresentation().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
