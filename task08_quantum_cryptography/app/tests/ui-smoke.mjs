import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK08_TEST_PORT || 4188);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath =
  process.env.TASK08_CHROMIUM_EXECUTABLE || chromium.executablePath();
const screenshotPath = process.env.TASK08_SCREENSHOT_PATH;
const mobileScreenshotPath = process.env.TASK08_MOBILE_SCREENSHOT_PATH;

if (!existsSync(executablePath)) {
  throw new Error(
    `Chromium executable is unavailable: ${executablePath}. Set TASK08_CHROMIUM_EXECUTABLE.`,
  );
}

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
      // The server may still be binding its socket.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 8 server");
}

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
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
  const rootFontFamily = await page.evaluate(
    () => getComputedStyle(document.documentElement).fontFamily,
  );
  assert.match(rootFontFamily, /Times New Roman/);
  assert.doesNotMatch(rootFontFamily, /Inter|Segoe UI|Cambria|DejaVu/);
  assert.match(await page.title(), /Quantum mismatch calculator/);
  assert.equal(await page.locator("#theta-number").inputValue(), "-30");
  assert.equal(await page.locator("#phi-number").inputValue(), "30");
  assert.equal(await page.locator("#classical-percent").textContent(), "37.5%");
  assert.equal(await page.locator("#quantum-percent").textContent(), "75.0%");
  assert.equal(await page.locator("#difference-value").textContent(), "+37.5 pp");
  const officialClassicalCurve = await page.locator("#classical-curve").getAttribute("d");
  const officialQuantumCurve = await page.locator("#quantum-curve").getAttribute("d");
  assert.ok(officialClassicalCurve.startsWith("M88.00,"));
  assert.ok(officialQuantumCurve.startsWith("M88.00,"));
  assert.ok(!officialClassicalCurve.includes("NaN"));
  assert.ok(!officialQuantumCurve.includes("NaN"));
  assert.equal(await page.locator("#chart-current-line").getAttribute("x1"), "728.00");
  assert.equal(await page.locator("#classical-marker").getAttribute("cy"), "240.00");
  assert.equal(await page.locator("#quantum-marker").getAttribute("cy"), "114.00");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "363");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "770");
  assert.equal(await page.locator("#classical-sample-percent").textContent(), "36.3%");
  assert.equal(await page.locator("#quantum-sample-percent").textContent(), "77.0%");
  assert.equal(await page.locator("#observed-sample-difference").textContent(), "+40.7 pp");

  await page.locator("#next-sample-button").click();
  assert.equal(await page.locator("#simulation-seed").inputValue(), "2027");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "387");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "764");
  assert.match(await page.locator("#simulation-live").textContent(), /seed 2,027/);
  await page.locator("#reset-simulation-button").click();
  assert.equal(await page.locator("#simulation-seed").inputValue(), "2026");

  const maximumSimulationMs = await page.evaluate(() => {
    const button = document.querySelector('[data-photon-pairs="100000"]');
    const started = performance.now();
    button.click();
    return performance.now() - started;
  });
  assert.ok(
    maximumSimulationMs < 100,
    `maximum finite-photon simulation took ${maximumSimulationMs} ms`,
  );
  assert.equal(await page.locator("#photon-count").inputValue(), "100000");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "37,454");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "75,102");
  await page.locator("#reset-simulation-button").click();

  await page.locator('[data-preset="aligned"]').click();
  assert.equal(await page.locator("#theta-number").inputValue(), "45");
  assert.equal(await page.locator("#phi-number").inputValue(), "45");
  assert.equal(await page.locator("#classical-percent").textContent(), "50.0%");
  assert.equal(await page.locator("#quantum-percent").textContent(), "0.0%");
  assert.equal(await page.locator("#difference-value").textContent(), "−50.0 pp");
  assert.notEqual(
    await page.locator("#classical-curve").getAttribute("d"),
    officialClassicalCurve,
  );
  assert.equal(await page.locator("#chart-current-line").getAttribute("x1"), "808.00");
  assert.equal(await page.locator("#classical-marker").getAttribute("cy"), "198.00");
  assert.equal(await page.locator("#quantum-marker").getAttribute("cy"), "366.00");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "0");
  assert.equal(await page.locator("#quantum-sample-residual").textContent(), "deterministic");

  await page.locator("#theta-number").fill("0");
  await page.locator("#phi-number").fill("90");
  assert.equal(await page.locator("#classical-percent").textContent(), "100.0%");
  assert.equal(await page.locator("#quantum-percent").textContent(), "100.0%");
  assert.equal(await page.locator("#difference-value").textContent(), "0.0 pp");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "1,000");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "1,000");

  const timings = await page.evaluate(() => {
    const slider = document.getElementById("theta-range");
    const samples = [];
    for (let value = -90; value <= 90; value += 3) {
      const started = performance.now();
      slider.value = String(value);
      slider.dispatchEvent(new Event("input", { bubbles: true }));
      samples.push(performance.now() - started);
    }
    return samples;
  });
  const maximumLatencyMs = Math.max(...timings);
  assert.ok(maximumLatencyMs < 100, `interaction latency ${maximumLatencyMs} ms`);

  await page.locator('[data-preset="official"]').click();
  if (screenshotPath) {
    await page.evaluate(() => document.activeElement?.blur());
    await page.locator(".skip-link").evaluate((element) => {
      element.style.display = "none";
    });
    await page.screenshot({ path: screenshotPath, fullPage: true });
    await page.locator(".skip-link").evaluate((element) => {
      element.style.display = "";
    });
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload({ waitUntil: "networkidle" });
  const mobileLayout = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    graphClientWidth: document.querySelector(".chart-frame").clientWidth,
    graphScrollWidth: document.querySelector(".chart-frame").scrollWidth,
    graphScrollLeft: document.querySelector(".chart-frame").scrollLeft,
  }));
  assert.ok(
    mobileLayout.documentWidth <= mobileLayout.viewportWidth,
    `mobile overflow: ${mobileLayout.documentWidth}px > ${mobileLayout.viewportWidth}px`,
  );
  assert.equal(await page.locator("#classical-percent").textContent(), "37.5%");
  assert.equal(await page.locator("#quantum-percent").textContent(), "75.0%");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "363");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "770");
  assert.ok(mobileLayout.graphScrollWidth > mobileLayout.graphClientWidth);
  assert.ok(mobileLayout.graphScrollLeft > 0);
  if (mobileScreenshotPath) {
    await page.evaluate(() => document.activeElement?.blur());
    await page.locator(".skip-link").evaluate((element) => {
      element.style.display = "none";
    });
    await page.screenshot({ path: mobileScreenshotPath, fullPage: true });
    await page.locator(".skip-link").evaluate((element) => {
      element.style.display = "";
    });
  }
  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(externalRequests, []);
  console.log(
    `Task 8 UI smoke: PASS (live 361-point chart; reproducible finite-photon samples; official, aligned and perpendicular cases; desktop/mobile; max angle update ${maximumLatencyMs.toFixed(2)} ms; 100,000-pair sample ${maximumSimulationMs.toFixed(2)} ms)`,
  );
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
