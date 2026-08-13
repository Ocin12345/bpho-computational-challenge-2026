#!/usr/bin/env node

import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:4174";
const pageUrl = `${origin}/site/tasks/task-03.html`;

async function canvasPixels(page, selector) {
  return page.locator(selector).evaluate((canvas) => {
    const data = canvas
      .getContext("2d")
      .getImageData(0, 0, canvas.width, canvas.height).data;
    let nonZero = 0;
    for (let index = 0; index < data.length; index += 4) {
      if (data[index] || data[index + 1] || data[index + 2] || data[index + 3]) {
        nonZero += 1;
      }
    }
    return nonZero;
  });
}

async function inspect(browser, viewport, mobile) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    isMobile: mobile,
    hasTouch: mobile,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const runtimeErrors = [];
  const failedRequests = [];

  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") runtimeErrors.push(message.text());
  });
  page.on("requestfailed", (request) => {
    failedRequests.push(
      `${request.url()} ${request.failure()?.errorText || ""}`,
    );
  });

  await page.goto(pageUrl, { waitUntil: "networkidle" });
  await page.locator("[data-evidence-content]:not([hidden])").waitFor({
    timeout: 15_000,
  });

  const state = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    navigation: [...document.querySelectorAll(".section-nav a")].map((link) =>
      link.textContent.trim(),
    ),
    sections: ["spectrum", "einstein", "method", "validation"].map((id) => ({
      id,
      visible: getComputedStyle(document.getElementById(id)).display !== "none",
    })),
    evidenceChecks: document.querySelector("[data-check-count]")?.textContent.trim(),
    benchmarkRows: document.querySelectorAll("[data-benchmark-body] tr").length,
  }));

  assert.deepEqual(state.navigation, [
    "Spectrum",
    "Heat capacity",
    "Method",
    "Validation",
  ]);
  assert.ok(state.sections.every((section) => section.visible));
  assert.equal(state.evidenceChecks, "27 / 27");
  assert.equal(state.benchmarkRows, 3);
  assert.ok(state.overflow <= 1, `Horizontal overflow: ${state.overflow}px`);

  assert.ok((await canvasPixels(page, "#einstein-chart")) > 1000);
  assert.ok((await canvasPixels(page, "#planck-evidence-chart")) > 1000);
  assert.ok((await canvasPixels(page, "#einstein-collapse-chart")) > 1000);

  await page.locator('[data-material="Cu"]').click();
  await page.waitForTimeout(120);
  assert.equal(
    (await page.locator("[data-selected-material]").textContent()).trim(),
    "Copper · Cu",
  );
  assert.equal(
    (await page.locator("[data-heat-capacity]").textContent()).trim(),
    "23.25 J mol⁻¹ K⁻¹",
  );
  assert.equal(
    (await page.locator("[data-einstein-frequency]").textContent()).trim(),
    "0.5769 × 10¹³ Hz",
  );

  await page.locator('[data-material="Fe"]').click();
  await page.locator("#solid-temperature").fill("50");
  await page.locator("#solid-temperature").dispatchEvent("input");
  await page.waitForTimeout(120);
  assert.equal(
    (await page.locator("[data-selected-material]").textContent()).trim(),
    "Iron · Fe",
  );
  assert.equal(
    (await page.locator("[data-heat-capacity]").textContent()).trim(),
    "0.73 J mol⁻¹ K⁻¹",
  );

  await page.locator('[data-planck-mode="compare"]').click();
  assert.equal(
    await page.locator('[data-planck-mode="compare"]').getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(await page.locator("[data-planck-legend]").getAttribute("hidden"), null);
  assert.match(
    (await page.locator("[data-live-quantity-title]").textContent()).trim(),
    /Planck comparison/,
  );
  assert.ok((await canvasPixels(page, "#planck-live-chart")) > 1000);

  const chart = page.locator("#einstein-chart");
  await chart.scrollIntoViewIfNeeded();
  const chartBox = await chart.boundingBox();
  assert.ok(chartBox);
  await page.mouse.move(chartBox.x + chartBox.width * 0.55, chartBox.y + chartBox.height * 0.45);
  await page.waitForTimeout(50);
  assert.equal(await page.locator("[data-einstein-tooltip]").isVisible(), true);

  assert.deepEqual(runtimeErrors, []);
  assert.deepEqual(failedRequests, []);
  await context.close();
}

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
});
try {
  await inspect(browser, { width: 1440, height: 1000 }, false);
  await inspect(browser, { width: 390, height: 844 }, true);
} finally {
  await browser.close();
}

console.log("Task 03 Gold browser audit passed on desktop and mobile.");
