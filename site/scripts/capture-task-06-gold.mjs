#!/usr/bin/env node

import { mkdir, readdir, rename } from "node:fs/promises";
import { createRequire } from "node:module";
import { join } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "../../task08_quantum_cryptography/app/node_modules/playwright",
);

const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:4174";
const outputDirectory =
  process.env.TASK06_CAPTURE_DIRECTORY ||
  "/Users/nicoliao/.codex/visualizations/2026/08/13/019ff974-7ca1-7c92-8d4e-3e4637431384/task06-gold-upgrade";

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });

async function waitForTask(page) {
  await page.goto(`${origin}/site/tasks/task-06.html`, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () =>
      document.documentElement.dataset.task06Status === "ready" &&
      document.documentElement.dataset.task06Relativity === "ready",
  );
  await page.evaluate(() => document.fonts.ready);
}

const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await waitForTask(desktop);
await desktop.screenshot({
  path: join(outputDirectory, "task06-desktop-full.png"),
  fullPage: true,
});
async function captureDesktopSection(sectionId, filename) {
  await desktop.evaluate((id) => {
    document.documentElement.style.scrollBehavior = "auto";
    const section = document.querySelector(`#${id}`);
    window.scrollTo(0, section.offsetTop - 48);
  }, sectionId);
  await desktop.waitForTimeout(250);
  await desktop.screenshot({ path: join(outputDirectory, filename) });
}

async function captureDesktopElement(selector, filename) {
  await desktop.evaluate((target) => {
    document.documentElement.style.scrollBehavior = "auto";
    const element = document.querySelector(target);
    window.scrollTo(0, element.getBoundingClientRect().top + window.scrollY - 48);
  }, selector);
  await desktop.waitForTimeout(250);
  await desktop.screenshot({ path: join(outputDirectory, filename) });
}

await captureDesktopSection("experiment", "task06-desktop-experiment.png");
await captureDesktopSection("plot", "task06-desktop-plot.png");
await captureDesktopSection("method", "task06-desktop-method.png");
await captureDesktopSection("validation", "task06-desktop-validation.png");
await captureDesktopSection("extension", "task06-desktop-extension.png");
await captureDesktopElement("[data-live-diagnostics]", "task06-live-diagnostics.png");

await desktop.locator("[data-reset-model]").click();
await captureDesktopSection("experiment", "task06-both-families.png");

await desktop.locator('[data-voltage-preset="1000"]').click();
await captureDesktopSection("experiment", "task06-rings-1kv.png");
await desktop.locator('[data-voltage-preset="5000"]').click();
await captureDesktopSection("experiment", "task06-rings-5kv.png");
await desktop.locator("[data-reset-model]").click();

const mobile = await browser.newPage({
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
  reducedMotion: "reduce",
});
await waitForTask(mobile);
await mobile.screenshot({
  path: join(outputDirectory, "task06-mobile-full.png"),
  fullPage: true,
});
await mobile.locator("#experiment").scrollIntoViewIfNeeded();
await mobile.waitForTimeout(250);
await mobile.screenshot({ path: join(outputDirectory, "task06-mobile-experiment.png") });
await mobile.locator("#validation").scrollIntoViewIfNeeded();
await mobile.waitForTimeout(250);
await mobile.screenshot({ path: join(outputDirectory, "task06-mobile-validation.png") });

const videoDirectory = join(outputDirectory, "video-temporary");
await mkdir(videoDirectory, { recursive: true });
const videoContext = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  recordVideo: { dir: videoDirectory, size: { width: 1440, height: 1000 } },
});
const videoPage = await videoContext.newPage();
await waitForTask(videoPage);
await videoPage.locator("#experiment").scrollIntoViewIfNeeded();
await videoPage.waitForTimeout(700);
await videoPage.locator('[data-voltage-preset="1000"]').click();
await videoPage.waitForTimeout(650);
await videoPage.locator("[data-sweep-toggle]").click();
await videoPage.waitForTimeout(3400);
await videoPage.locator("[data-sweep-toggle]").click();
await videoPage.waitForTimeout(700);
await videoPage.locator("[data-reset-model]").click();
await videoPage.waitForTimeout(650);
await videoPage.locator('a[href="#plot"]').click();
await videoPage.waitForTimeout(900);
await videoPage.locator('a[href="#method"]').click();
await videoPage.waitForTimeout(900);
await videoPage.locator('a[href="#validation"]').click();
await videoPage.waitForTimeout(1200);
const recordedVideo = await videoPage.video().path();
await videoContext.close();
await rename(recordedVideo, join(outputDirectory, "task06-interaction-demo.webm"));

await browser.close();

const files = (await readdir(outputDirectory))
  .filter((file) => !file.startsWith("video-temporary"))
  .sort();
console.log(files.map((file) => join(outputDirectory, file)).join("\n"));
