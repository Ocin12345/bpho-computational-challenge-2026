#!/usr/bin/env node

import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:4174";
const pageUrl = `${origin}/site/tasks/task-02.html`;

async function inspect(browser, viewport, mobile) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    isMobile: mobile,
    hasTouch: mobile,
    reducedMotion: mobile ? "reduce" : "no-preference",
  });
  const page = await context.newPage();
  const runtimeErrors = [];
  const failedRequests = [];

  page.on("pageerror", (error) => runtimeErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") runtimeErrors.push(message.text());
  });
  page.on("requestfailed", (request) => {
    failedRequests.push(`${request.url()} ${request.failure()?.errorText || ""}`);
  });

  await page.goto(pageUrl, { waitUntil: "networkidle" });
  await page.locator("[data-evidence-content]:not([hidden])").waitFor({
    timeout: 15_000,
  });

  const state = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    heading: document.querySelector("h1")?.textContent.trim(),
    navigation: [...document.querySelectorAll(".section-nav a")].map(
      (link) => link.textContent.trim(),
    ),
    extensionVisible: Boolean(document.querySelector("#extension")?.getClientRects().length),
    plotWidths: ["msd-chart", "endpoint-chart", "convergence-chart"].map(
      (id) => document.getElementById(id)?.getBoundingClientRect().width || 0,
    ),
  }));

  assert.equal(state.heading, "Brownian motion");
  assert.deepEqual(state.navigation, [
    "Simulation",
    "Plot",
    "Method",
    "Validation",
  ]);
  assert.ok(state.overflow <= 1, `Horizontal overflow: ${state.overflow}px`);
  assert.equal(state.extensionVisible, false, "Advanced extension is visible");
  assert.ok(state.plotWidths.every((width) => width >= 250));
  assert.deepEqual(runtimeErrors, []);
  assert.deepEqual(failedRequests, []);

  assert.equal(
    (await page.locator("[data-diffusion]").textContent()).trim(),
    "2.25e-3 nm² ps⁻¹",
  );
  assert.equal(
    (await page.locator("[data-r-squared]").textContent()).trim(),
    "R² = 0.983",
  );
  assert.equal(
    (await page.locator("[data-collision-error]").textContent()).trim(),
    "2.17e-15",
  );
  assert.equal(
    (await page.locator("[data-convergence-order]").textContent()).trim(),
    "1.003",
  );
  assert.equal(
    (await page.locator("[data-residual-penetration]").textContent()).trim(),
    "0.0 nm",
  );

  if (!mobile) {
    await page.locator("[data-step]").click();
    await page.waitForFunction(
      () => document.querySelector("[data-time]")?.textContent === "1.00 ps",
    );
    const firstStep = {
      displacement: (await page.locator("[data-displacement]").textContent()).trim(),
      collisions: (await page.locator("[data-collisions]").textContent()).trim(),
    };
    await page.locator("[data-reset]").click();
    assert.equal((await page.locator("[data-time]").textContent()).trim(), "0.00 ps");
    await page.locator("[data-step]").click();
    await page.waitForFunction(
      () => document.querySelector("[data-time]")?.textContent === "1.00 ps",
    );
    const repeatedStep = {
      displacement: (await page.locator("[data-displacement]").textContent()).trim(),
      collisions: (await page.locator("[data-collisions]").textContent()).trim(),
    };
    assert.deepEqual(repeatedStep, firstStep, "Seeded Step is not reproducible");

    await page.locator('[data-preset="heavy"]').click();
    assert.equal(await page.locator("#mass-ratio").inputValue(), "50");
    assert.equal(
      (await page.locator("[data-model-mass-ratio]").textContent()).trim(),
      "50",
    );
    assert.equal(
      (await page.locator("[data-diffusion]").textContent()).trim(),
      "2.25e-3 nm² ps⁻¹",
      "Locked reference evidence changed with live controls",
    );
  }

  await context.close();
}

const browser = await chromium.launch({ headless: true });
try {
  await inspect(browser, { width: 1440, height: 1000 }, false);
  await inspect(browser, { width: 390, height: 844 }, true);
} finally {
  await browser.close();
}

console.log("Task 02 Gold browser audit passed on desktop and mobile.");
