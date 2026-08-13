#!/usr/bin/env node

import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:8081";
const routes = [
  { task: 1, path: "/site/tasks/task-01.html#method", selector: ".proof-math .katex", count: 5 },
  { task: 2, path: "/site/tasks/task-02.html#method", selector: ".math-display .katex", count: 10 },
  { task: 3, path: "/site/tasks/task-03.html#model", selector: ".proof-math .katex", count: 8 },
  { task: 4, path: "/site/apps/task-04/index.html?lab=method", selector: ".task4-method-equations .proof-math .katex", count: 3 },
  { task: 5, path: "/site/tasks/task-05.html#model", selector: ".proof-math .katex", count: 10 },
  { task: 6, path: "/site/tasks/task-06.html#model", selector: ".proof-math .katex", count: 8 },
  { task: 7, path: "/site/tasks/task-07.html#uncertainty", selector: ".proof-math .katex", count: 11 },
  { task: 8, path: "/site/tasks/task-08.html#model", selector: ".proof-math .katex", count: 5 },
  { task: 9, path: "/site/tasks/task-09.html#model", selector: ".proof-math .katex", count: 4 },
  { task: 10, path: "/site/tasks/task-10.html#model", selector: ".proof-math .katex", count: 4 },
];

async function inspect(browser, route, viewport, mobile) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    isMobile: mobile,
    hasTouch: mobile,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors = [];

  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });

  await page.goto(`${origin}${route.path}`, { waitUntil: "networkidle" });
  await page.locator(route.selector).first().waitFor({
    state: "attached",
    timeout: 15_000,
  });

  const state = await page.evaluate((selector) => ({
    equations: document.querySelectorAll(selector).length,
    mathml: document.querySelectorAll(`${selector} .katex-mathml`).length,
    failures: document.querySelectorAll(".proof-math-fallback").length,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  }), route.selector);

  assert.equal(errors.length, 0, `Task ${route.task} runtime errors: ${errors.join(" | ")}`);
  assert.ok(state.equations >= route.count, `Task ${route.task} rendered ${state.equations}/${route.count} equations`);
  assert.ok(state.mathml >= route.count, `Task ${route.task} exposed ${state.mathml}/${route.count} MathML equations`);
  assert.equal(state.failures, 0, `Task ${route.task} has equation fallbacks`);
  assert.ok(state.overflow <= 1, `Task ${route.task} horizontal overflow: ${state.overflow}px`);

  await context.close();
}

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
});

try {
  for (const route of routes) {
    await inspect(browser, route, { width: 1440, height: 1000 }, false);
    await inspect(browser, route, { width: 390, height: 844 }, true);
    console.log(`Task ${String(route.task).padStart(2, "0")}: proof mathematics passed`);
  }
  console.log("All ten task proof systems passed desktop and mobile rendering checks.");
} finally {
  await browser.close();
}
