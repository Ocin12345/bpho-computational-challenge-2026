import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK10_MOTION_PORT || 4213);
const baseUrl = `http://127.0.0.1:${port}/figures/task10/orbital_view_rotation_viewer.html`;
const executablePath = process.env.TASK10_CHROMIUM_EXECUTABLE || chromium.executablePath();
const screenshotPath = process.env.TASK10_MOTION_SCREENSHOT_PATH;

if (!existsSync(executablePath)) throw new Error(`Chromium executable is unavailable: ${executablePath}`);

const server = spawn(
  "python3",
  ["-m", "http.server", String(port), "--bind", "127.0.0.1"],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`motion server exited with ${server.exitCode}`);
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // The local server may still be binding.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 10 motion viewer");
}

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
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
  await page.waitForFunction(() => {
    const image = document.getElementById("motion-artifact");
    return image?.complete && image.naturalWidth === 3840 && image.naturalHeight === 2160;
  });
  const defaultState = await page.locator("#motion-artifact").evaluate((image) => ({
    currentSrc: image.currentSrc,
    alt: image.alt,
    naturalWidth: image.naturalWidth,
    naturalHeight: image.naturalHeight,
  }));
  assert.match(defaultState.currentSrc, /orbital_view_rotation\.webp$/);
  assert.match(defaultState.alt, /stationary normalized hydrogen 3d/);
  assert.deepEqual([defaultState.naturalWidth, defaultState.naturalHeight], [3840, 2160]);
  await page.waitForFunction(() => {
    const image = document.getElementById("inspection-sheet");
    return image?.complete && image.naturalWidth === 2400 && image.naturalHeight === 2300;
  });
  assert.match(await page.locator("#inspection-sheet").getAttribute("alt"), /Five decoded frames/);

  if (screenshotPath) await page.screenshot({ path: screenshotPath, fullPage: true });

  await page.setViewportSize({ width: 320, height: 740 });
  await page.reload({ waitUntil: "networkidle" });
  const mobile = await page.evaluate(() => ({
    viewport: innerWidth,
    documentWidth: document.documentElement.scrollWidth,
  }));
  assert.ok(mobile.documentWidth <= mobile.viewport);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForFunction(() => document.getElementById("motion-artifact")?.complete);
  assert.match(await page.locator("#motion-artifact").evaluate((image) => image.currentSrc), /orbital_view_rotation_poster\.png$/);
  assert.match(await page.locator(".motion-note").evaluate((element) => getComputedStyle(element, "::after").content), /static 4K poster/);

  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(externalRequests, []);
  console.log("Task 10 motion browser: PASS (4K WebP and five decoded frames load; 320 px reflow; reduced-motion poster; 0 errors/remote requests)");
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
