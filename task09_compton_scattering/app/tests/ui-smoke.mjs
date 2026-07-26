import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK09_TEST_PORT || 4210);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath =
  process.env.TASK09_CHROMIUM_EXECUTABLE || chromium.executablePath();
const screenshotPath = process.env.TASK09_SCREENSHOT_PATH;
const mobileScreenshotPath = process.env.TASK09_MOBILE_SCREENSHOT_PATH;

if (!existsSync(executablePath)) {
  throw new Error(
    `Chromium executable is unavailable: ${executablePath}. Set TASK09_CHROMIUM_EXECUTABLE.`,
  );
}

const server = spawn(
  "python3",
  ["-m", "task09_compton_scattering.serve_task09", "--port", String(port)],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) {
      throw new Error(`Task 9 server exited with code ${server.exitCode}`);
    }
    try {
      const response = await fetch(baseUrl);
      if (response.ok) {
        assert.match(response.headers.get("content-security-policy") || "", /default-src 'self'/);
        return;
      }
    } catch {
      // The local server may still be binding its socket.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 9 server");
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
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  const pageErrors = [];
  const externalRequests = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") externalRequests.push(request.url());
  });

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  assert.match(await page.title(), /Task 9.+Compton scattering explorer/);
  const rootFont = await page.evaluate(() =>
    getComputedStyle(document.documentElement).fontFamily,
  );
  assert.match(rootFont, /^"?Times New Roman"?/);
  assert.equal(await page.locator("#energy-number").inputValue(), "200");
  assert.equal(await page.locator("#theta-number").inputValue(), "90");
  assert.equal(await page.locator("#fractional-shift").textContent(), "0.39139");
  assert.equal(await page.locator("#electron-beta").textContent(), "0.43419 c");
  assert.equal(await page.locator("#recoil-angle").textContent(), "35.71°");
  assert.equal(await page.locator("#scattered-energy").textContent(), "143.741 keV");
  assert.equal(await page.locator("#kinetic-energy").textContent(), "56.259 keV");
  assert.equal(await page.locator("#total-cross-section").textContent(), "0.4065 barn");
  assert.equal(await page.locator("path.curve").count(), 17);
  for (const path of await page.locator("path.curve").evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("d")),
  )) {
    assert.ok(path?.startsWith("M "));
    assert.ok(!path.includes("NaN"));
  }

  await page.locator('[data-theta="0"]').click();
  await waitForText(page, "#recoil-angle", "undefined");
  assert.equal(await page.locator("#fractional-shift").textContent(), "0");
  assert.equal(await page.locator("#electron-beta").textContent(), "0 c");
  assert.equal(await page.locator("#recoil-angle").textContent(), "undefined");
  assert.match(await page.locator("#recoil-direction-note").textContent(), /pₑ = 0/);
  assert.match(await page.locator("#phi-chart-description").textContent(), /continuous limit/);

  await page.locator('[data-energy="1000"]').click();
  await page.locator('[data-theta="180"]').click();
  await waitForText(page, "#fractional-shift", "3.9139");
  assert.equal(await page.locator("#fractional-shift").textContent(), "3.9139");
  assert.equal(await page.locator("#electron-beta").textContent(), "0.92047 c");
  assert.equal(await page.locator("#recoil-angle").textContent(), "0.00°");
  assert.equal(await page.locator("#total-cross-section").textContent(), "0.2112 barn");
  assert.equal(await page.locator("#energy-number").inputValue(), "1000");
  assert.equal(await page.locator("#theta-number").inputValue(), "180");

  await page.locator("#energy-number").fill("5000");
  await page.locator("#energy-number").press("Enter");
  await waitForText(page, "#energy-output", "5,000 keV");
  assert.equal(await page.locator("#energy-output").textContent(), "5,000 keV");
  assert.equal(await page.locator("#selected-energy-label").textContent(), "selected: 5,000 keV");
  assert.equal(await page.locator("path.curve").count(), 20);
  assert.equal(await page.locator('[data-energy][aria-pressed="true"]').count(), 0);

  await page.locator("#reset-button").click();
  await waitForText(page, "#theta-output", "90°");
  assert.equal(await page.locator("#energy-number").inputValue(), "200");
  assert.equal(await page.locator("#theta-number").inputValue(), "90");

  const updateTimings = await page.evaluate(async () => {
    const slider = document.getElementById("theta-range");
    const samples = [];
    for (let value = 0; value <= 180; value += 9) {
      const started = performance.now();
      slider.value = String(value);
      slider.dispatchEvent(new Event("input", { bubbles: true }));
      await new Promise((resolve) => requestAnimationFrame(resolve));
      samples.push(performance.now() - started);
    }
    return samples;
  });
  const maximumUpdateMs = Math.max(...updateTimings);
  assert.ok(maximumUpdateMs < 100, `interaction latency ${maximumUpdateMs} ms`);
  assert.equal(await page.locator("#theta-output").textContent(), "180°");

  if (screenshotPath) {
    await page.locator("#reset-button").click();
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }

  for (const width of [320, 390, 740, 1050, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.reload({ waitUntil: "networkidle" });
    const layout = await page.evaluate(() => {
      const graph = document.querySelector(".chart-scroll");
      return {
        viewportWidth: innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        graphClientWidth: graph.clientWidth,
        graphScrollWidth: graph.scrollWidth,
      };
    });
    assert.ok(
      layout.documentWidth <= layout.viewportWidth,
      `${width}px layout overflows to ${layout.documentWidth}px`,
    );
    if (width <= 740) assert.ok(layout.graphScrollWidth > layout.graphClientWidth);
  }

  if (mobileScreenshotPath) {
    await page.setViewportSize({ width: 320, height: 740 });
    await page.reload({ waitUntil: "networkidle" });
    await page.screenshot({ path: mobileScreenshotPath, fullPage: true });
  }

  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(externalRequests, []);
  console.log(
    `Task 9 UI smoke: PASS (exact default/forward/backscatter/custom states; 5 breakpoints; 0 external requests; maximum measured update ${maximumUpdateMs.toFixed(2)} ms)`,
  );
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
