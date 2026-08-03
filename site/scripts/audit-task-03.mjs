#!/usr/bin/env node

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = dirname(here);
const baseUrl =
  process.env.TASK03_URL ||
  "http://127.0.0.1:8080/site/tasks/task-03.html";

const browser = await chromium.launch({ headless: true });
const errors = [];
const externalRequests = [];

async function preparePage(page) {
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(`console: ${message.text()}`);
    }
  });
  page.on("request", (request) => {
    const requestUrl = request.url();
    if (!requestUrl.startsWith("http")) return;
    if (new URL(requestUrl).origin !== new URL(baseUrl).origin) {
      externalRequests.push(requestUrl);
    }
  });
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator("[data-evidence-content]").first().waitFor({
    state: "visible",
  });
  await page.evaluate(() => document.fonts.ready);
  await page.locator("html.is-page-ready").waitFor({ state: "attached" });
}

const desktopContext = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
});
const desktop = await desktopContext.newPage();
await preparePage(desktop);

assert.equal(
  await desktop.locator("html").getAttribute("data-gsap-status"),
  "active",
);
assert.ok(
  await desktop.evaluate(
    () => window.ScrollTrigger?.getAll?.().length >= 3,
  ),
  "GSAP ScrollTrigger scenes were not registered",
);

assert.equal(
  await desktop.locator("[data-check-count]").textContent(),
  "27 / 27",
);
assert.match(
  await desktop.locator("[data-evidence-provenance]").textContent(),
  /27\/27 checks pass/,
);

for (const selector of [
  "#planck-live-chart",
  "#einstein-chart",
  "#planck-evidence-chart",
  "#einstein-collapse-chart",
]) {
  const size = await desktop.locator(selector).evaluate((canvas) => ({
    clientWidth: canvas.clientWidth,
    clientHeight: canvas.clientHeight,
    width: canvas.width,
    height: canvas.height,
  }));
  assert.ok(size.clientWidth > 250, `${selector} is too narrow`);
  assert.ok(size.clientHeight > 240, `${selector} is too short`);
  assert.ok(size.width >= size.clientWidth, `${selector} lacks DPR width`);
  assert.ok(size.height >= size.clientHeight, `${selector} lacks DPR height`);
}

await desktop.locator("#surface-temperature").evaluate((input) => {
  input.value = "6000";
  input.dispatchEvent(new Event("input", { bubbles: true }));
});
assert.equal(
  await desktop.locator("[data-peak-readout]").textContent(),
  "483.0 nm",
);
assert.match(
  await desktop.locator("[data-integral-readout]").textContent(),
  /23\.39 MW m⁻² sr⁻¹/,
);
assert.match(
  await desktop.locator("[data-live-quantity-title]").textContent(),
  /Bλ\(λ,T\)/,
);

await desktop.locator('[data-planck-quantity="exitance"]').click();
assert.match(
  await desktop.locator("[data-integral-readout]").textContent(),
  /73\.49 MW m⁻²/,
);
assert.match(
  await desktop.locator("[data-live-quantity-title]").textContent(),
  /Mλ\(λ,T\)/,
);
await desktop.locator('[data-planck-quantity="radiance"]').click();

await desktop.locator('[data-temperature-preset="4000"]').click();
await desktop.waitForTimeout(180);
const transitionalTemperature = Number(
  await desktop.locator("#surface-temperature").inputValue(),
);
assert.ok(
  transitionalTemperature > 4000 && transitionalTemperature < 6000,
  `preset transition did not pass through intermediate values: ${transitionalTemperature}`,
);
await desktop.waitForTimeout(650);
assert.equal(
  await desktop.locator("[data-temperature-output]").textContent(),
  "4,000 K",
);

const sweepStart = Number(
  await desktop.locator("#surface-temperature").inputValue(),
);
await desktop.locator("[data-sweep]").click();
await desktop.waitForTimeout(320);
const sweepEnd = Number(
  await desktop.locator("#surface-temperature").inputValue(),
);
assert.ok(
  Math.abs(sweepEnd - sweepStart) > 10,
  "automatic temperature sweep did not animate",
);
await desktop.locator("[data-sweep]").click();

await desktop.locator('[data-evidence-quantity="exitance"]').click();
assert.match(
  await desktop.locator("#planck-evidence-chart").getAttribute("aria-label"),
  /spectral exitance/,
);
await desktop.locator('[data-evidence-quantity="radiance"]').click();
assert.match(
  await desktop.locator("#planck-evidence-chart").getAttribute("aria-label"),
  /spectral radiance/,
);
assert.match(
  await desktop.locator(".brief-coverage").textContent(),
  /Planck B\(λ,T\)[\s\S]*4,000 K[\s\S]*gold, copper and iron/,
);

await desktop.locator('[data-material="C"]').click();
await desktop.locator("#solid-temperature").evaluate((input) => {
  input.value = "800";
  input.dispatchEvent(new Event("input", { bubbles: true }));
});
await desktop.waitForTimeout(650);
assert.equal(
  await desktop.locator("[data-selected-material]").textContent(),
  "Carbon · C",
);
assert.match(
  await desktop.locator("[data-einstein-temperature]").textContent(),
  /1,?797\.4 K|1797\.4 K/,
);
const activeMaterialWidth = await desktop
  .locator('[data-material="C"]')
  .evaluate((button) => button.getBoundingClientRect().width);
const inactiveMaterialWidth = await desktop
  .locator('[data-material="Si"]')
  .evaluate((button) => button.getBoundingClientRect().width);
assert.ok(
  activeMaterialWidth > inactiveMaterialWidth * 1.4,
  "active material accordion panel did not expand",
);

const verdictStatusBefore = await desktop
  .locator("[data-verdict-status]")
  .textContent();
const verdictNumberBefore = Number(verdictStatusBefore.split("/")[0].trim());
await desktop.locator("[data-verdict-next]").click();
await desktop.waitForTimeout(800);
assert.equal(
  await desktop.locator("[data-verdict-status]").textContent(),
  `${(verdictNumberBefore % 3) + 1} / 3`,
);
assert.equal(
  await desktop.locator(".validation-verdict.is-active").count(),
  1,
);
assert.equal(
  await desktop.locator(".action-link").count(),
  2,
);
assert.ok(
  await desktop.locator(".action-link--primary").getAttribute("href"),
  "primary action link is missing",
);

const desktopOverflow = await desktop.evaluate(
  () => document.documentElement.scrollWidth - window.innerWidth,
);
assert.ok(desktopOverflow <= 1, `desktop horizontal overflow: ${desktopOverflow}`);

const desktopA11y = await new AxeBuilder({ page: desktop })
  .withTags(["wcag2a", "wcag2aa"])
  .analyze();
const seriousDesktop = desktopA11y.violations.filter((violation) =>
  ["serious", "critical"].includes(violation.impact),
);

await desktop.locator('[data-material="Au"]').click();
await desktop.locator("#surface-temperature").evaluate((input) => {
  input.value = "5000";
  input.dispatchEvent(new Event("input", { bubbles: true }));
});
await desktop.locator("#solid-temperature").evaluate((input) => {
  input.value = "300";
  input.dispatchEvent(new Event("input", { bubbles: true }));
});
await desktop.evaluate(() => {
  document.documentElement.style.scrollBehavior = "auto";
  document.body.style.scrollBehavior = "auto";
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
  window.scrollTo(0, 0);
});
await desktop.waitForTimeout(100);

await desktop.screenshot({
  path: join(siteRoot, "task-03-hero-preview.png"),
  animations: "disabled",
});
await desktop.locator(".einstein-section").scrollIntoViewIfNeeded();
await desktop.waitForTimeout(700);
await desktop.screenshot({
  path: join(siteRoot, "task-03-einstein-preview.png"),
  animations: "disabled",
});
await desktop.locator(".evidence-section").evaluate((section) => {
  window.scrollTo(0, section.offsetTop);
});
await desktop.waitForTimeout(1350);
await desktop.screenshot({
  path: join(siteRoot, "task-03-evidence-preview.png"),
  animations: "disabled",
});
await desktop.locator(".action-chapter").scrollIntoViewIfNeeded();
await desktop.waitForTimeout(700);
await desktop.screenshot({
  path: join(siteRoot, "task-03-action-preview.png"),
  animations: "disabled",
});
await desktop.evaluate(() => window.scrollTo(0, 0));
await desktop.waitForTimeout(100);
await desktop.screenshot({
  path: join(siteRoot, "task-03-preview.png"),
  fullPage: true,
  animations: "disabled",
});

const mobileContext = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 1,
  isMobile: true,
  hasTouch: true,
  reducedMotion: "reduce",
});
const mobile = await mobileContext.newPage();
await preparePage(mobile);
const mobileOverflow = await mobile.evaluate(
  () => document.documentElement.scrollWidth - window.innerWidth,
);
assert.ok(mobileOverflow <= 1, `mobile horizontal overflow: ${mobileOverflow}`);

const mobileA11y = await new AxeBuilder({ page: mobile })
  .withTags(["wcag2a", "wcag2aa"])
  .analyze();
const seriousMobile = mobileA11y.violations.filter((violation) =>
  ["serious", "critical"].includes(violation.impact),
);
await mobile.locator('[data-temperature-preset="4000"]').click();
assert.equal(
  await mobile.locator("[data-temperature-output]").textContent(),
  "4,000 K",
);
await mobile.locator("#surface-temperature").evaluate((input) => {
  input.value = "5000";
  input.dispatchEvent(new Event("input", { bubbles: true }));
});
await mobile.evaluate(() => {
  document.documentElement.style.scrollBehavior = "auto";
  document.body.style.scrollBehavior = "auto";
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
  window.scrollTo(0, 0);
});
await mobile.waitForTimeout(100);
await mobile.screenshot({
  path: join(siteRoot, "task-03-mobile-preview.png"),
  animations: "disabled",
});

await browser.close();

if (errors.length) {
  throw new Error(`Browser errors:\n${errors.join("\n")}`);
}
if (externalRequests.length) {
  throw new Error(
    `Unexpected external browser requests:\n${externalRequests.join("\n")}`,
  );
}
if (seriousDesktop.length || seriousMobile.length) {
  const violations = [...seriousDesktop, ...seriousMobile]
    .map(
      (violation) =>
        `${violation.id} (${violation.impact}): ${violation.help}`,
    )
    .join("\n");
  throw new Error(`Serious accessibility violations:\n${violations}`);
}

console.log("Task 03 browser audit passed.");
console.log("  desktop: 1440 × 1000, no horizontal overflow");
console.log("  mobile: 390 × 844, no horizontal overflow");
console.log("  live Planck and Einstein interactions: passed");
console.log("  console and page errors: none");
console.log("  external runtime requests: none");
console.log("  serious WCAG 2 A/AA violations: none");
