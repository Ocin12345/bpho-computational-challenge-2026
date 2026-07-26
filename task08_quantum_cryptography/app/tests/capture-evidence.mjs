import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const outputDirectory = fileURLToPath(
  new URL("../../../figures/task08/screenshots/", import.meta.url),
);
const port = Number(process.env.TASK08_EVIDENCE_PORT || 4192);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath =
  process.env.TASK08_CHROMIUM_EXECUTABLE || chromium.executablePath();

if (!existsSync(executablePath)) {
  throw new Error(
    `Chromium executable is unavailable: ${executablePath}. Set TASK08_CHROMIUM_EXECUTABLE.`,
  );
}

mkdirSync(outputDirectory, { recursive: true });

const server = spawn(
  "python3",
  [
    "-m",
    "task08_quantum_cryptography.serve_task08",
    "--port",
    String(port),
  ],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) {
      throw new Error(`Task 8 server exited with code ${server.exitCode}`);
    }
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // The local server may still be binding its socket.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 8 evidence server");
}

function pngDimensions(path) {
  const bytes = readFileSync(path);
  assert.equal(bytes.subarray(1, 4).toString("ascii"), "PNG");
  return {
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
  };
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

async function preparePage(page, errorLog) {
  page.on("console", (message) => {
    if (message.type() === "error") errorLog.console.push(message.text());
  });
  page.on("pageerror", (error) => errorLog.page.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") errorLog.external.push(request.url());
  });
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  const rootFontFamily = await page.evaluate(
    () => getComputedStyle(document.documentElement).fontFamily,
  );
  assert.match(rootFontFamily, /Times New Roman/);
  assert.doesNotMatch(rootFontFamily, /Inter|Segoe UI|Cambria|DejaVu/);
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        caret-color: transparent !important;
      }
      .skip-link { display: none !important; }
    `,
  });
  await page.locator('[data-preset="official"]').click();
  await page.evaluate(() => document.activeElement?.blur());
  assert.equal(await page.locator("#classical-percent").textContent(), "37.5%");
  assert.equal(await page.locator("#quantum-percent").textContent(), "75.0%");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "363");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "770");
}

async function alignSection(page, selector, offset = 18) {
  await page.locator(selector).evaluate(
    (element, topOffset) => {
      const top = element.getBoundingClientRect().top + window.scrollY - topOffset;
      window.scrollTo({ top: Math.max(0, top), behavior: "instant" });
    },
    offset,
  );
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(resolve)));
}

const captures = [
  {
    name: "detector_workspace_4k.png",
    selector: ".workspace",
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2,
  },
  {
    name: "probability_chart_4k.png",
    selector: ".chart-panel",
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2,
  },
  {
    name: "finite_photon_extension_4k.png",
    selector: ".simulation-panel",
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2,
  },
  {
    name: "finite_photon_mobile_2x.png",
    selector: ".simulation-panel",
    viewport: { width: 430, height: 932 },
    deviceScaleFactor: 2,
  },
];

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({ headless: true, executablePath });
  const records = [];
  for (const capture of captures) {
    const context = await browser.newContext({
      viewport: capture.viewport,
      deviceScaleFactor: capture.deviceScaleFactor,
      colorScheme: "light",
      reducedMotion: "reduce",
      locale: "en-GB",
    });
    const page = await context.newPage();
    const errors = { console: [], page: [], external: [] };
    await preparePage(page, errors);
    await alignSection(page, capture.selector);
    const path = `${outputDirectory}${capture.name}`;
    await page.screenshot({ path, fullPage: false, animations: "disabled" });
    const dimensions = pngDimensions(path);
    assert.deepEqual(dimensions, {
      width: capture.viewport.width * capture.deviceScaleFactor,
      height: capture.viewport.height * capture.deviceScaleFactor,
    });
    assert.deepEqual(errors, { console: [], page: [], external: [] });
    const layout = await page.evaluate(() => ({
      viewportWidth: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
    }));
    assert.ok(
      layout.documentWidth <= layout.viewportWidth,
      `horizontal overflow in ${capture.name}`,
    );
    records.push({
      file: capture.name,
      css_viewport: capture.viewport,
      device_scale_factor: capture.deviceScaleFactor,
      pixel_dimensions: dimensions,
      sha256: sha256(path),
    });
    await context.close();
  }
  writeFileSync(
    `${outputDirectory}manifest.json`,
    `${JSON.stringify(
      {
        schema_version: "task08-browser-evidence-v1",
        source: "validated local Task 8 application",
        font_family: "Times New Roman",
        external_network_requests: 0,
        captures: records,
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
  console.log(
    "Task 8 browser evidence: PASS (three 3840x2160 captures, one 860x1864 mobile capture, no console/page/network errors)",
  );
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
