import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK10_TEST_PORT || 4211);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath = process.env.TASK10_CHROMIUM_EXECUTABLE || chromium.executablePath();
const screenshotPath = process.env.TASK10_SCREENSHOT_PATH;
const mobileScreenshotPath = process.env.TASK10_MOBILE_SCREENSHOT_PATH;

if (!existsSync(executablePath)) throw new Error(`Chromium executable is unavailable: ${executablePath}`);

const server = spawn(
  "python3",
  ["-m", "task10_hydrogenic_orbitals.serve_task10", "--port", String(port)],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Task 10 server exited with ${server.exitCode}`);
    try {
      const response = await fetch(baseUrl);
      if (response.ok) {
        assert.match(response.headers.get("content-security-policy") || "", /default-src 'self'/);
        return;
      }
    } catch {
      // Local server may still be binding.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for Task 10 server");
}

async function waitForText(page, selector, expected) {
  await page.waitForFunction(
    ({ target, text }) => document.querySelector(target)?.textContent === text,
    { target: selector, text: expected },
  );
}

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  const pageErrors = [];
  const externalRequests = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") externalRequests.push(request.url());
  });

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  assert.match(await page.title(), /Task 10.+Hydrogenic orbital explorer/);
  const rootFont = await page.evaluate(() =>
    getComputedStyle(document.documentElement).fontFamily,
  );
  assert.match(rootFont, /^"?Times New Roman"?/);
  await waitForText(page, "#state-label", "3d (m=+0)");
  assert.equal(await page.locator("#energy-value").textContent(), "−1.510915 eV");
  assert.equal(await page.locator("#bohr-value").textContent(), "0.529468 Å");
  assert.equal(await page.locator("#node-value").textContent(), "0 radial · 2 angular");
  assert.equal(await page.locator("#l-select option").count(), 3);
  assert.equal(await page.locator("#m-select option").count(), 5);
  assert.equal(await page.locator("#gallery-preset option").count(), 26);
  const initialCanvas = await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL());
  assert.ok(initialCanvas.length > 20_000, `canvas payload too small: ${initialCanvas.length}`);

  await page.locator("#gallery-preset").selectOption("5,4,4");
  await waitForText(page, "#state-label", "5g (m=+4)");
  assert.equal(await page.locator("#n-select").inputValue(), "5");
  assert.equal(await page.locator("#l-select").inputValue(), "4");
  assert.equal(await page.locator("#m-select").inputValue(), "4");
  assert.equal(await page.locator("#node-value").textContent(), "0 radial · 4 angular");

  await page.locator("#n-select").selectOption("2");
  await waitForText(page, "#state-label", "2p (m=+1)");
  assert.equal(await page.locator("#l-select option").count(), 2);
  assert.equal(await page.locator("#m-select option").count(), 3);
  assert.equal(await page.locator('#l-select option[value="2"]').count(), 0);
  assert.equal(await page.locator('#m-select option[value="2"]').count(), 0);

  await page.locator("#n-select").selectOption("3");
  await page.locator("#l-select").selectOption("2");
  await page.locator("#m-select").selectOption("0");
  await page.locator("#z-select").selectOption("6");
  await waitForText(page, "#state-label", "3d (m=+0)");
  assert.equal(await page.locator("#isotope-label").textContent(), "C-12 · Z=6 · A=12");
  assert.equal(await page.locator("#energy-value").textContent(), "−54.420285 eV");
  assert.equal(await page.locator("#bohr-value").textContent(), "0.088200 Å");

  await page.locator("#slice-range").fill("25");
  await waitForText(page, "#slice-output", "25");
  await page.locator("#threshold-range").fill("0.25");
  await waitForText(page, "#threshold-output", "0.25");
  await page.locator("#opacity-range").fill("0.9");
  await waitForText(page, "#opacity-output", "90%");
  assert.match(await page.locator("#glass-canvas-description").textContent(), /25 x-y planes.+0.25 display cutoff/);

  const beforeOrbit = await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL());
  await page.locator("#orbit-right").click();
  const afterOrbit = await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL());
  assert.notEqual(afterOrbit, beforeOrbit);
  await page.locator("#glass-canvas").focus();
  await page.keyboard.press("ArrowLeft");
  const afterKeyboard = await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL());
  assert.notEqual(afterKeyboard, afterOrbit);

  await page.locator("#reset-all").click();
  await waitForText(page, "#threshold-output", "0.15");
  assert.equal(await page.locator("#state-label").textContent(), "3d (m=+0)");
  assert.equal(await page.locator("#z-select").inputValue(), "1");
  assert.equal(await page.locator("#threshold-output").textContent(), "0.15");

  const galleryTimings = await page.evaluate(async () => {
    const preset = document.getElementById("gallery-preset");
    const values = [...preset.options].map((option) => option.value).filter(Boolean);
    const timings = [];
    for (const value of values) {
      const expected = value.split(",");
      const started = performance.now();
      preset.value = value;
      preset.dispatchEvent(new Event("change", { bubbles: true }));
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      if (document.getElementById("n-select").value !== expected[0]) throw new Error(`preset ${value} failed`);
      timings.push(performance.now() - started);
    }
    return timings;
  });
  const maximumGalleryUpdateMs = Math.max(...galleryTimings);
  assert.ok(maximumGalleryUpdateMs < 450, `gallery update ${maximumGalleryUpdateMs} ms`);

  if (screenshotPath) {
    await page.locator("#reset-all").click();
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }

  for (const width of [320, 390, 740, 1050, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.reload({ waitUntil: "networkidle" });
    const layout = await page.evaluate(() => {
      const chart = document.querySelector(".chart-scroll");
      return {
        viewport: innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        chartClient: chart.clientWidth,
        chartScroll: chart.scrollWidth,
      };
    });
    assert.ok(layout.documentWidth <= layout.viewport, `${width}px overflows to ${layout.documentWidth}px`);
    if (width <= 740) assert.ok(layout.chartScroll > layout.chartClient);
  }

  if (mobileScreenshotPath) {
    await page.setViewportSize({ width: 320, height: 740 });
    await page.reload({ waitUntil: "networkidle" });
    await page.screenshot({ path: mobileScreenshotPath, fullPage: true });
  }

  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(externalRequests, []);
  console.log(`Task 10 UI smoke: PASS (25 presets; 5 breakpoints; 0 external requests; max gallery update ${maximumGalleryUpdateMs.toFixed(2)} ms)`);
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
