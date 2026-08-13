#!/usr/bin/env node

import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:8081";

async function inspect(browser, viewport, mobile) {
  const context = await browser.newContext({ viewport, isMobile: mobile, hasTouch: mobile, reducedMotion: mobile ? "reduce" : "no-preference" });
  const page = await context.newPage();
  const errors = []; const external = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("request", (request) => { const url = request.url(); if (url.startsWith("http") && new URL(url).origin !== new URL(origin).origin) external.push(url); });
  await page.goto(`${origin}/site/advanced.html`, { waitUntil: "networkidle" });
  await page.locator("[data-task-tabs] .task-tab").nth(9).waitFor();
  assert.equal(await page.locator("[data-task-tabs] .task-tab").count(), 10);
  assert.equal(await page.locator("[data-check-total]").innerText(), "35/35 checks pass");
  assert.equal(errors.length, 0, `runtime errors: ${errors}`);
  assert.equal(external.length, 0, `external requests: ${external}`);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 1, `horizontal overflow: ${overflow}`);
  await page.getByRole("tab", { name: /Task 03/ }).click();
  assert.match(await page.locator("[data-task-title]").innerText(), /Copper calorimetry/);
  assert.ok((await page.locator("[data-advanced-chart]").getAttribute("aria-label"))?.includes("reference"));
  await page.getByRole("tab", { name: /Task 10/ }).click();
  await page.locator("[data-morph-slider]").fill("20");
  assert.equal(await page.locator("[data-morph-output]").textContent(), "50%");
  assert.match(await page.locator("[data-advanced-chart]").getAttribute("aria-label"), /50 percent morph/);
  await context.close();
}

async function inspectOfflineShell(browser, path, readySelector) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 820 }, reducedMotion: "reduce" });
  const page = await context.newPage(); const errors = []; const external = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("request", (request) => { const url = request.url(); if (url.startsWith("http") && new URL(url).origin !== new URL(origin).origin) external.push(url); });
  await page.goto(`${origin}${path}`, { waitUntil: "networkidle" });
  await page.locator(readySelector).first().waitFor();
  assert.equal(errors.length, 0, `${path} runtime errors: ${errors}`);
  assert.equal(external.length, 0, `${path} external requests: ${external}`);
  await context.close();
}

const browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined });
await inspect(browser, { width: 1440, height: 1000 }, false);
await inspect(browser, { width: 390, height: 844 }, true);
await inspectOfflineShell(browser, "/site/index.html", ".title");
await inspectOfflineShell(browser, "/site/tasks.html", "[data-task]");
await browser.close();
console.log("Advanced lab and public shell: desktop/mobile rendering, interaction and offline-request audit passed");
