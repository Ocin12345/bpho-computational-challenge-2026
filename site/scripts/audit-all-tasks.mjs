#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:8081";
const tasks = [
  { number: 1, path: "/site/tasks/task-01.html", ready: "#step-count" },
  { number: 2, path: "/site/tasks/task-02.html", ready: "#particle-count" },
  { number: 3, path: "/site/tasks/task-03.html", ready: "#surface-temperature" },
  {
    number: 4,
    path: "/site/apps/task-04/index.html?lab=experiment",
    ready: "canvas",
  },
  {
    number: 5,
    path: "/site/tasks/task-05.html",
    ready: "#transition-selector:not([disabled])",
  },
  {
    number: 6,
    path: "/site/tasks/task-06.html",
    ready: "#accelerating-voltage:not([disabled])",
  },
  {
    number: 7,
    path: "/site/tasks/task-07.html",
    ready: "#quantum-number:not([disabled])",
  },
  {
    number: 8,
    path: "/site/tasks/task-08.html",
    ready: "#theta-angle:not([disabled])",
  },
  {
    number: 9,
    path: "/site/tasks/task-09.html",
    ready: "#incident-energy:not([disabled])",
  },
  {
    number: 10,
    path: "/site/tasks/task-10.html",
    ready: "#gallery-preset:not([disabled])",
  },
];

const requestedTask = Number(process.env.TASK_NUMBER || 0);

if (!requestedTask) {
  for (const task of tasks) {
    const result = spawnSync(process.execPath, [fileURLToPath(import.meta.url)], {
      cwd: process.cwd(),
      env: { ...process.env, TASK_NUMBER: String(task.number) },
      encoding: "utf8",
    });
    process.stdout.write(result.stdout || "");
    process.stderr.write(result.stderr || "");
    assert.equal(result.status, 0, `Task ${task.number} audit process failed`);
  }
  console.log("All 10 task pages passed the cross-task rendered UI audit.");
  process.exit(0);
}

const selectedTasks = tasks.filter((task) => task.number === requestedTask);
assert.equal(selectedTasks.length, 1, `Unknown TASK_NUMBER=${requestedTask}`);

async function inspect(browser, task, viewport, mobile) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    isMobile: mobile,
    hasTouch: mobile,
    reducedMotion: mobile ? "reduce" : "no-preference",
  });
  const page = await context.newPage();
  const errors = [];
  const external = [];

  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("request", (request) => {
    const url = request.url();
    if (url.startsWith("http") && new URL(url).origin !== new URL(origin).origin) {
      external.push(url);
    }
  });

  await page.goto(`${origin}${task.path}`, { waitUntil: "networkidle" });
  await page.locator(task.ready).first().waitFor({ timeout: 15_000 });
  await page.waitForTimeout(150);

  assert.equal(errors.length, 0, `Task ${task.number} runtime errors: ${errors}`);
  assert.equal(external.length, 0, `Task ${task.number} external requests: ${external}`);

  const pageState = await page.evaluate(() => {
    const heading = document.querySelector("h1");
    const background = getComputedStyle(document.body).backgroundColor;
    const fontFamily = heading ? getComputedStyle(heading).fontFamily : "";
    return {
      overflow: document.documentElement.scrollWidth - window.innerWidth,
      headingVisible: Boolean(
        heading &&
          heading.getBoundingClientRect().width > 0 &&
          heading.getBoundingClientRect().height > 0,
      ),
      background,
      fontFamily,
      evidenceWalls: document.querySelectorAll(
        '.evidence-section, .validation-ledger, [data-evidence-lock], [data-validation-count], [data-core-checks]',
      ).length,
      unnamedButtons: [...document.querySelectorAll("button")].filter(
        (button) =>
          !button.textContent.trim() &&
          !button.getAttribute("aria-label") &&
          !button.getAttribute("title"),
      ).length,
      proofLanguage:
        document.body.innerText.match(
          /\b(?:validation|validated|evidence|checks? pass)\b/gi,
        ) || [],
    };
  });

  assert.ok(pageState.overflow <= 1, `Task ${task.number} overflow: ${pageState.overflow}`);
  assert.equal(pageState.headingVisible, true, `Task ${task.number} has no visible h1`);
  const backgroundChannels = pageState.background
    .match(/\d+(?:\.\d+)?/g)
    ?.slice(0, 3)
    .map(Number);
  assert.ok(
    backgroundChannels?.every((channel) => channel >= 230),
    `Task ${task.number} body is not white/cream: ${pageState.background}`,
  );
  assert.match(
    pageState.fontFamily,
    /Times New Roman|Times/i,
    `Task ${task.number} title is not Times-led: ${pageState.fontFamily}`,
  );
  assert.equal(
    pageState.evidenceWalls,
    0,
    `Task ${task.number} still contains visible validation/evidence wall markup`,
  );
  assert.equal(
    pageState.unnamedButtons,
    0,
    `Task ${task.number} contains unnamed buttons`,
  );
  assert.deepEqual(
    pageState.proofLanguage,
    [],
    `Task ${task.number} still exposes validation language: ${pageState.proofLanguage.join(", ")}`,
  );

  await context.close();
}

for (const task of selectedTasks) {
  const browser = await chromium.launch({
    headless: true,
    executablePath:
      process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
  });
  await inspect(browser, task, { width: 1440, height: 1000 }, false);
  await inspect(browser, task, { width: 390, height: 844 }, true);
  await browser.close();
  console.log(`Task ${String(task.number).padStart(2, "0")}: desktop and mobile passed`);
}
