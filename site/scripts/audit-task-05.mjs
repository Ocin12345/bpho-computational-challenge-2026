#!/usr/bin/env node

import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const target = process.env.TASK05_URL || "http://127.0.0.1:4174/site/tasks/task-05.html";

const browser = await chromium.launch({ headless: true });
const findings = [];

async function auditViewport(label, viewport) {
  const page = await browser.newPage({ viewportSize: viewport });
  const consoleErrors = [];
  const networkErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));
  page.on("requestfailed", (request) =>
    networkErrors.push(`${request.method()} ${request.url()} ${request.failure()?.errorText}`),
  );
  page.on("response", (response) => {
    if (response.status() >= 400) {
      networkErrors.push(`${response.status()} ${response.url()}`);
    }
  });

  await page.goto(target, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () =>
      document.documentElement.dataset.task05Status === "ready" &&
      document.body.dataset.task05ExtensionStatus === "ready",
  );

  const snapshot = await page.evaluate(() => {
    const visible = (selector) => {
      const element = document.querySelector(selector);
      if (!element) return false;
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && box.height > 0;
    };
    return {
      navLabels: [...document.querySelectorAll(".section-nav a")].map((link) =>
        link.textContent.trim(),
      ),
      sections: ["#spectrum", "#atlas", "#balmer", "#model", "#validation", "#convergence", "#extension"].map(visible),
      validationRows: document.querySelectorAll("[data-validation-transitions] tr").length,
      validationSummary: document.querySelector("[data-validation-summary]")?.textContent.trim(),
      energyScale: document.querySelector("[data-energy-scale]")?.textContent.trim(),
      rydbergResidual: document.querySelector("[data-rydberg-residual]")?.textContent.trim(),
      extensionStatus: document.querySelector("[data-mass-status]")?.textContent.trim(),
      bodyClass: document.body.className,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });

  assert.deepEqual(snapshot.navLabels, [
    "Transition",
    "Energy graph",
    "Spectrum",
    "Method",
    "Validation",
  ]);
  assert(snapshot.sections.every(Boolean), `${label}: a judge-facing section is hidden`);
  assert(snapshot.validationRows >= 6, `${label}: representative validation rows are missing`);
  assert.match(snapshot.validationSummary, /30\/30/);
  assert.match(snapshot.energyScale, /13\.605693/);
  assert.match(snapshot.rydbergResidual, /10/);
  assert.notEqual(snapshot.extensionStatus, "Loading reduced-mass model");
  assert(!snapshot.bodyClass.includes("video-cut"), `${label}: filming cut still active`);
  assert(snapshot.overflow <= 2, `${label}: ${snapshot.overflow}px horizontal overflow`);
  assert.deepEqual(consoleErrors, [], `${label}: console errors: ${consoleErrors.join(" | ")}`);
  assert.deepEqual(networkErrors, [], `${label}: network errors: ${networkErrors.join(" | ")}`);

  const downloadPromise = page.waitForEvent("download");
  await page.locator("[data-download-transition-csv]").click();
  const download = await downloadPromise;
  assert.equal(download.suggestedFilename(), "emission_transitions.csv");

  const hBetaValue = await page.locator("#transition-selector option").evaluateAll((options) =>
    options.find((option) => option.textContent.includes("4→2"))?.value,
  );
  assert.notEqual(hBetaValue, undefined);
  await page.selectOption("#transition-selector", hBetaValue);
  await page.waitForFunction(
    () => document.querySelectorAll(".balmer-line.is-selected").length === 1,
  );
  assert.match((await page.locator("[data-transition-title]").textContent()).trim(), /H-β.*4 → 2/);
  assert.match((await page.locator("[data-photon-energy]").textContent()).trim(), /2\.551067 eV/);
  assert.match((await page.locator("[data-photon-wavelength-readout]").textContent()).trim(), /486\.009 nm/);
  assert.equal((await page.locator("[data-atlas-transition]").textContent()).trim(), "4→2");
  assert.match((await page.locator("[data-atlas-wavelength]").textContent()).trim(), /486\.009 nm/);
  assert.match((await page.locator("#energy-level-stage").getAttribute("aria-label")), /4.*descends to level 2/);
  assert.match((await page.locator("[data-spectrum-selection]").textContent()).trim(), /H-β.*4→2.*486\.009 nm/);

  const selectedBeforeKeyboard = await page.locator("#transition-selector").inputValue();
  await page.locator("#energy-level-stage").focus();
  await page.keyboard.press("ArrowRight");
  assert.notEqual(await page.locator("#transition-selector").inputValue(), selectedBeforeKeyboard);
  await page.selectOption("#transition-selector", hBetaValue);

  await page.getByRole("button", { name: "Balmer", exact: true }).click();
  assert.match((await page.locator("[data-atlas-status]").textContent()).trim(), /8 emissions shown/);
  await page.locator("[data-visible-only]").check();
  assert.match((await page.locator("[data-atlas-status]").textContent()).trim(), /7 emissions shown.*visible window/);
  await page.locator("[data-visible-only]").uncheck();
  await page.getByRole("button", { name: "All", exact: true }).click();
  assert.match((await page.locator("[data-atlas-status]").textContent()).trim(), /45 emissions shown/);

  const lymanAlphaValue = await page.locator("#transition-selector option").evaluateAll((options) =>
    options.find((option) => option.textContent.includes("2→1"))?.value,
  );
  await page.selectOption("#transition-selector", lymanAlphaValue);
  assert.equal((await page.locator("[data-region-badge]").textContent()).trim(), "UV");
  assert.equal(await page.locator(".balmer-line.is-selected").count(), 0);
  assert.match((await page.locator("[data-spectrum-selection]").textContent()).trim(), /outside 380–750 nm/);

  for (const href of ["#spectrum", "#atlas", "#balmer", "#model", "#validation"]) {
    assert.equal(await page.locator(`.section-nav a[href="${href}"]`).count(), 1);
    assert.equal(await page.locator(href).count(), 1);
  }

  findings.push(`${label}: navigation, visibility, synchronization, extension, and overflow checks passed`);
  await page.close();
}

try {
  await auditViewport("desktop 1440×1000", { width: 1440, height: 1000 });
  await auditViewport("mobile 390×844", { width: 390, height: 844 });
  findings.forEach((finding) => console.log(`PASS ${finding}`));
  console.log("Task 5 judge-facing browser audit passed.");
} finally {
  await browser.close();
}
