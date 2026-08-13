#!/usr/bin/env node

import assert from "node:assert/strict";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "../../task08_quantum_cryptography/app/node_modules/playwright",
);

const repositoryRoot = resolve(import.meta.dirname, "../..");
const outputDirectory = resolve(repositoryRoot, "audit/task07-gold/screenshots");
const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:4174";
const pageUrl = `${origin}/site/tasks/task-07.html`;
const executablePath =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
mkdirSync(outputDirectory, { recursive: true });

const screenshotPath = (name) => resolve(outputDirectory, name);
const errors = [];
const failedResponses = [];
const externalRequests = [];

function monitor(page) {
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${response.url()}`);
    }
  });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.protocol.startsWith("http") && url.origin !== origin) {
      externalRequests.push(url.href);
    }
  });
}

async function waitForReady(page) {
  await page.goto(pageUrl, { waitUntil: "networkidle" });
  await page.locator("#quantum-number:not([disabled])").waitFor();
  await page.locator("body[data-task07-status='verified']").waitFor();
  await page.waitForTimeout(250);
}

async function verifyScientificEvidence(page) {
  const evidence = await page.evaluate(async () => {
    const text = await fetch("../../data/task07/numerical_moments.csv").then(
      (response) => response.text(),
    );
    const [headerLine, ...lines] = text.trim().split(/\r?\n/);
    const headers = headerLine.split(",");
    const rows = lines.map((line) =>
      Object.fromEntries(
        line.split(",").map((value, index) => [headers[index], Number(value)]),
      ),
    );
    return {
      rowCount: rows.length,
      finest: rows.filter((row) => row.interior_point_count === 1600),
      n5: rows.find(
        (row) =>
          row.interior_point_count === 1600 && row.quantum_number_n === 5,
      ),
    };
  });
  assert.equal(evidence.rowCount, 50);
  assert.equal(evidence.finest.length, 10);
  assert.ok(evidence.finest.every((row) => row.heisenberg_ratio_numeric >= 1));
  assert.ok(Math.abs(evidence.n5.expected_x_m_numeric / 1e-9 - 0.5) < 1e-12);
  assert.ok(
    Math.abs(evidence.n5.expected_x_squared_m2_numeric / 1e-18 - 0.331306909659) <
      5e-13,
  );
  assert.ok(
    Math.abs(evidence.n5.p_squared_kg2_m2_s2_numeric - 2.744028339689e-48) <
      5e-60,
  );
}

async function verifySemanticsAndAccessibility(page) {
  const semantics = await page.evaluate(() => {
    const focusable = [
      ...document.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), canvas[tabindex="0"], [tabindex="0"]',
      ),
    ];
    const headings = [...document.querySelectorAll("h1, h2, h3")].map(
      (heading) => ({
        level: Number(heading.tagName.slice(1)),
        text: heading.textContent.trim(),
      }),
    );
    const label = (element) =>
      element.getAttribute("aria-label") ||
      [...(element.labels || [])].map((item) => item.textContent.trim()).join(" ") ||
      element.textContent.trim();
    return {
      language: document.documentElement.lang,
      mains: document.querySelectorAll("main").length,
      h1s: document.querySelectorAll("h1").length,
      headings,
      unnamedControls: [...document.querySelectorAll("button, input")].filter(
        (element) => !label(element),
      ).length,
      unnamedCanvases: [...document.querySelectorAll("canvas")].filter(
        (canvas) => !canvas.getAttribute("aria-label"),
      ).length,
      tableCaption: document.querySelector("#numerical-moments-table caption")
        ?.textContent,
      headerScopes: [...document.querySelectorAll("#numerical-moments-table th")].every(
        (header) => header.scope === "col",
      ),
      focusableCount: focusable.length,
      horizontalOverflow: document.documentElement.scrollWidth - window.innerWidth,
      mathFocusTargets: document.querySelectorAll(".math-scroll[tabindex='0']").length,
      tableRows: document.querySelectorAll("#numerical-moments-table tbody tr").length,
    };
  });
  assert.equal(semantics.language, "en");
  assert.equal(semantics.mains, 1);
  assert.equal(semantics.h1s, 1);
  assert.ok(semantics.headings.every((heading) => heading.text));
  for (let index = 1; index < semantics.headings.length; index += 1) {
    assert.ok(
      semantics.headings[index].level <= semantics.headings[index - 1].level + 1,
      `heading skip before ${semantics.headings[index].text}`,
    );
  }
  assert.equal(semantics.unnamedControls, 0);
  assert.equal(semantics.unnamedCanvases, 0);
  assert.match(semantics.tableCaption, /Numerical versus analytical/);
  assert.equal(semantics.headerScopes, true);
  assert.ok(semantics.focusableCount > 20);
  assert.ok(semantics.horizontalOverflow <= 1);
  assert.ok(semantics.mathFocusTargets >= 4);
  assert.equal(semantics.tableRows, 5);

  const cdp = await page.context().newCDPSession(page);
  const tree = await cdp.send("Accessibility.getFullAXTree");
  const names = tree.nodes.map((node) => node.name?.value).filter(Boolean);
  for (const expected of [
    "Particle in a box",
    "Quantum number",
    "Reset experiment",
    "Finite-difference Hamiltonian equation",
    "Numerical versus analytical uncertainty, N = 1600",
    "Five-grid convergence of numerical momentum uncertainty",
  ]) {
    assert.ok(
      names.some((name) => name.startsWith(expected)),
      `accessibility tree is missing ${expected}`,
    );
  }
  await cdp.detach();

  const contrast = await page.evaluate(() => {
    const rgb = (colour) => colour.match(/[\d.]+/g).slice(0, 3).map(Number);
    const luminance = (colour) => {
      const values = rgb(colour).map((value) => {
        const channel = value / 255;
        return channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2];
    };
    const ratio = (foreground, background) => {
      const first = luminance(foreground);
      const second = luminance(background);
      return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
    };
    const samples = [
      [".moment-ledger__result strong", ".moment-ledger__result"],
      [".section-introduction > span", ".uncertainty-section"],
      [".validation-ledger small", ".validation-ledger article"],
      [".reset-state", ".reset-state"],
      [".state-presets button.is-current", ".state-presets button.is-current"],
    ];
    return samples.map(([textSelector, backgroundSelector]) => {
      const text = document.querySelector(textSelector);
      const background = document.querySelector(backgroundSelector);
      const textStyle = getComputedStyle(text);
      const backgroundStyle = getComputedStyle(background);
      return {
        selector: textSelector,
        ratio: ratio(textStyle.color, backgroundStyle.backgroundColor),
      };
    });
  });
  assert.ok(contrast.every((sample) => sample.ratio >= 4.5), JSON.stringify(contrast));

  await page.locator(".math-scroll").first().focus();
  const focusStyle = await page.locator(".math-scroll").first().evaluate((element) => {
    const style = getComputedStyle(element);
    return { outline: style.outlineStyle, width: parseFloat(style.outlineWidth) };
  });
  assert.notEqual(focusStyle.outline, "none");
  assert.ok(focusStyle.width >= 2);

  const selected = page.locator("[data-state-preset='1']");
  const hover = page.locator("[data-state-preset='2']");
  await hover.hover();
  const presetColours = await Promise.all([
    selected.evaluate((element) => getComputedStyle(element).backgroundColor),
    hover.evaluate((element) => getComputedStyle(element).backgroundColor),
  ]);
  assert.notEqual(presetColours[0], presetColours[1]);
}

async function verifyInteractions(page) {
  const stateTitle = page.locator("[data-state-title]");
  await page.locator("[data-state-preset='2']").click();
  await assert.match(await stateTitle.textContent(), /n = 2/);
  await page.locator("#box-state-canvas").press("End");
  await assert.match(await stateTitle.textContent(), /n = 10/);
  await page.locator("#box-state-canvas").press("Home");
  await assert.match(await stateTitle.textContent(), /n = 1/);
  await page.locator('input[name="state-view"][value="wavefunction"]').check();
  assert.equal(
    await page.locator('input[name="state-view"][value="wavefunction"]').isChecked(),
    true,
  );
  await page.locator("[data-density-state='4']").uncheck();
  assert.equal(await page.locator("[data-density-state='4']").isChecked(), false);
  await page.locator("[data-reset-state]").click();
  await assert.match(await stateTitle.textContent(), /n = 1/);
  assert.equal(
    await page.locator('input[name="state-view"][value="both"]').isChecked(),
    true,
  );
  assert.ok(
    await page.locator("[data-density-state]").evaluateAll((items) =>
      items.every((item) => item.checked),
    ),
  );

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Numerical moments CSV" }).click();
  const download = await downloadPromise;
  assert.equal(download.suggestedFilename(), "numerical_moments.csv");
}

const browser = await chromium.launch({ headless: true, executablePath });
try {
  const desktop = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
  });
  const page = await desktop.newPage();
  monitor(page);
  await waitForReady(page);
  await verifyScientificEvidence(page);
  await verifySemanticsAndAccessibility(page);
  await page.evaluate(() => document.activeElement?.blur());

  await page.screenshot({ path: screenshotPath("01-task07-full-desktop.png"), fullPage: true });
  await page.locator("[data-state-laboratory]").screenshot({ path: screenshotPath("02-n1-state.png") });
  await page.locator("[data-state-preset='5'], #quantum-number").first().evaluate((element) => {
    if (element instanceof HTMLInputElement) {
      element.value = "5";
      element.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
  await page.locator("[data-state-laboratory]").screenshot({ path: screenshotPath("03-n5-state.png") });
  await page.locator("[data-reset-state]").click();
  await page.locator("[data-spectrum-laboratory]").screenshot({ path: screenshotPath("04-energy-graph.png") });
  await page.locator(".uncertainty-grid").screenshot({ path: screenshotPath("05-uncertainty-plot.png") });
  await page.locator(".numerical-evidence").screenshot({ path: screenshotPath("06-numerical-uncertainty-evidence.png") });
  await page.locator(".numerical-table-wrap").screenshot({ path: screenshotPath("07-numerical-delta-p-comparison.png") });
  await page.locator(".convergence-figure").screenshot({ path: screenshotPath("08-convergence-view.png") });
  const sectionCaptureStyle = await page.addStyleTag({
    content: ".task-header, .skip-link { visibility: hidden !important; }",
  });
  await page.locator("#method").screenshot({ path: screenshotPath("09-method.png") });
  await page.locator("#validation").screenshot({ path: screenshotPath("10-validation.png") });
  await sectionCaptureStyle.evaluate((element) => element.remove());
  await verifyInteractions(page);
  await desktop.close();

  const mobile = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    isMobile: true,
    hasTouch: true,
    reducedMotion: "reduce",
  });
  const mobilePage = await mobile.newPage();
  monitor(mobilePage);
  await waitForReady(mobilePage);
  const mobileOverflow = await mobilePage.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  assert.ok(mobileOverflow <= 1, `mobile overflow is ${mobileOverflow}px`);
  await mobilePage.screenshot({ path: screenshotPath("11-mobile.png"), fullPage: true });
  await mobile.close();
} finally {
  await browser.close();
}

assert.deepEqual(errors, [], `runtime errors: ${errors.join("; ")}`);
assert.deepEqual(failedResponses, [], `failed responses: ${failedResponses.join("; ")}`);
assert.deepEqual(externalRequests, [], `external requests: ${externalRequests.join("; ")}`);

console.log("Task 7 Gold browser, interaction and accessibility audit: PASS");
for (const name of [
  "01-task07-full-desktop.png",
  "02-n1-state.png",
  "03-n5-state.png",
  "04-energy-graph.png",
  "05-uncertainty-plot.png",
  "06-numerical-uncertainty-evidence.png",
  "07-numerical-delta-p-comparison.png",
  "08-convergence-view.png",
  "09-method.png",
  "10-validation.png",
  "11-mobile.png",
]) {
  console.log(screenshotPath(name));
}
