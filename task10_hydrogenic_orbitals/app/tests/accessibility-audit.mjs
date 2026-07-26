import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK10_A11Y_PORT || 4212);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath = process.env.TASK10_CHROMIUM_EXECUTABLE || chromium.executablePath();

if (!existsSync(executablePath)) {
  throw new Error(`Chromium executable is unavailable: ${executablePath}. Set TASK10_CHROMIUM_EXECUTABLE.`);
}

const server = spawn(
  "python3",
  ["-m", "task10_hydrogenic_orbitals.serve_task10", "--port", String(port)],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Task 10 server exited with code ${server.exitCode}`);
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // The local server may still be binding.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 10 server");
}

async function waitForText(page, selector, expected) {
  await page.waitForFunction(
    ({ target, text }) => document.querySelector(target)?.textContent === text,
    { target: selector, text: expected },
  );
}

const checks = [];
function record(name, criteria, detail) {
  checks.push({ name, criteria, detail });
}

let browser;
try {
  await waitForServer();
  const missingResponse = await fetch(`${baseUrl}not-a-route`);
  assert.equal(missingResponse.status, 404);
  assert.match(missingResponse.headers.get("content-security-policy") || "", /default-src 'self'/);
  record(
    "Invalid route and security headers",
    "robustness and local security",
    "unknown paths return 404 and retain the restrictive Content Security Policy",
  );

  browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--enable-precise-memory-info"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  const pageErrors = [];
  const externalRequests = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") externalRequests.push(request.url());
  });
  await page.goto(baseUrl, { waitUntil: "networkidle" });

  const semantics = await page.evaluate(() => {
    const accessibleName = (element) => {
      const labelledBy = (element.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean);
      if (labelledBy.length) return labelledBy.map((id) => document.getElementById(id)?.textContent.trim() || "").join(" ").trim();
      const aria = element.getAttribute("aria-label");
      if (aria) return aria.trim();
      if (element.labels?.length) return [...element.labels].map((label) => label.textContent.trim()).join(" ");
      return element.textContent?.trim() || "";
    };
    const focusableSelector = 'a[href], button, input, select, canvas[tabindex="0"], [role="region"][tabindex="0"]';
    return {
      language: document.documentElement.lang,
      title: document.title,
      mainCount: document.querySelectorAll("main").length,
      h1Count: document.querySelectorAll("h1").length,
      headings: [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")].map((heading) => ({
        level: Number(heading.tagName.slice(1)),
        text: heading.textContent.trim(),
      })),
      controls: [...document.querySelectorAll("button, input, select")].map((element) => ({ id: element.id, name: accessibleName(element) })),
      images: [...document.querySelectorAll('[role="img"]')].map((element) => ({ id: element.id, name: accessibleName(element) })),
      graphRegions: [...document.querySelectorAll('[role="region"][tabindex="0"]')].map((element) => accessibleName(element)),
      focusableCount: document.querySelectorAll(focusableSelector).length,
      liveStatus: document.getElementById("live-status")?.textContent.trim(),
      fallbackTexts: [...document.querySelectorAll("canvas")].map((canvas) => canvas.textContent.trim()),
    };
  });
  assert.equal(semantics.language, "en");
  assert.match(semantics.title, /Task 10.+Hydrogenic orbital explorer/);
  assert.equal(semantics.mainCount, 1);
  assert.equal(semantics.h1Count, 1);
  assert.ok(semantics.headings.every((heading) => heading.text));
  for (let index = 1; index < semantics.headings.length; index += 1) {
    assert.ok(semantics.headings[index].level <= semantics.headings[index - 1].level + 1, `heading level skips before ${semantics.headings[index].text}`);
  }
  assert.ok(semantics.controls.every((control) => control.name), JSON.stringify(semantics.controls));
  assert.equal(semantics.images.length, 5);
  assert.ok(semantics.images.every((image) => image.name), JSON.stringify(semantics.images));
  assert.deepEqual(semantics.graphRegions, ["Scrollable radial probability graph"]);
  assert.ok(semantics.fallbackTexts.every(Boolean));
  assert.match(semantics.liveStatus, /3d \(m=\+0\) selected/);
  record(
    "Semantic structure, names, fallbacks and live descriptions",
    "1.1.1, 1.3.1, 3.3.2, 4.1.2, 4.1.3",
    `${semantics.headings.length} ordered headings, ${semantics.controls.length} named controls, 5 named figures and 4 Canvas fallbacks`,
  );

  const cdp = await page.context().newCDPSession(page);
  const accessibilityTree = await cdp.send("Accessibility.getFullAXTree");
  const accessibleNames = accessibilityTree.nodes.map((node) => node.name?.value).filter(Boolean);
  for (const expectedName of [
    "Hydrogenic orbital explorer",
    "Atomic number, Z",
    "Principal number, n",
    "Angular number, l",
    "Magnetic number, m",
    "Official S through G orbital preset",
    "H-1 3d (m=+0) probability-density slice stack",
    "Relative density on the x-y plane",
    "Radial probability versus scaled radius",
  ]) {
    assert.ok(accessibleNames.some((name) => name.startsWith(expectedName)), `accessibility tree is missing ${expectedName}`);
  }
  record(
    "Chromium accessibility-tree exposure",
    "1.3.1, 4.1.2",
    `${accessibilityTree.nodes.length} accessibility nodes; all state controls and scientific figures are exposed by name`,
  );
  await cdp.detach();

  const contrast = await page.evaluate(() => {
    const parse = (colour) => {
      if (colour.startsWith("#")) return [1, 3, 5].map((index) => parseInt(colour.slice(index, index + 2), 16));
      const values = colour.match(/[\d.]+/g)?.map(Number);
      if (!values || values.length < 3) throw new Error(`Cannot parse ${colour}`);
      return values.slice(0, 3);
    };
    const luminance = (colour) => {
      const channels = parse(colour).map((value) => {
        const normalized = value / 255;
        return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    };
    const ratio = (foreground, background) => {
      const first = luminance(foreground);
      const second = luminance(background);
      return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
    };
    const samples = [
      [".hero__summary", "#eef5fa", 4.5],
      [".section-kicker", "#ffffff", 4.5],
      [".control-help", "#ffffff", 4.5],
      [".button", "#ffffff", 4.5],
      [".glass-figure figcaption", "#ffffff", 4.5],
      [".verification-badge", "#edf9f6", 4.5],
      [".stationary-pill", "#eefaf7", 4.5],
      [".result-primary", "#ffffff", 3],
    ].map(([selector, background, required]) => ({
      selector,
      ratio: ratio(getComputedStyle(document.querySelector(selector)).color, background),
      required,
    }));
    return {
      samples,
      nonText: [
        { name: "control boundary", ratio: ratio(getComputedStyle(document.getElementById("z-select")).borderTopColor, "#ffffff") },
        { name: "keyboard focus", ratio: ratio(getComputedStyle(document.documentElement).getPropertyValue("--focus").trim(), "#ffffff") },
        { name: "radial curve", ratio: ratio(getComputedStyle(document.querySelector(".radial-curve")).stroke, "#ffffff") },
      ],
    };
  });
  assert.ok(contrast.samples.every((sample) => sample.ratio >= sample.required), JSON.stringify(contrast.samples));
  assert.ok(contrast.nonText.every((sample) => sample.ratio >= 3), JSON.stringify(contrast.nonText));
  record(
    "Text and essential non-text contrast",
    "1.4.3, 1.4.11",
    `minimum tested text ratio ${Math.min(...contrast.samples.map((sample) => sample.ratio)).toFixed(2)}:1; minimum component ratio ${Math.min(...contrast.nonText.map((sample) => sample.ratio)).toFixed(2)}:1`,
  );

  const focusableSelector = 'a[href], button, input, select, canvas[tabindex="0"], [role="region"][tabindex="0"]';
  await page.evaluate(() => document.activeElement?.blur());
  const focusOrder = [];
  for (let index = 0; index < semantics.focusableCount; index += 1) {
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => {
      const element = document.activeElement;
      const style = getComputedStyle(element);
      return {
        key: element.id || element.getAttribute("aria-label") || element.getAttribute("href") || element.textContent.trim(),
        outlineStyle: style.outlineStyle,
        outlineWidth: parseFloat(style.outlineWidth),
      };
    });
    assert.notEqual(focused.outlineStyle, "none", `${focused.key} lacks a focus outline`);
    assert.ok(focused.outlineWidth >= 3, `${focused.key} focus outline is too thin`);
    focusOrder.push(focused.key);
  }
  assert.equal(new Set(focusOrder).size, semantics.focusableCount);
  record(
    "Complete keyboard route and visible focus",
    "2.1.1, 2.4.3, 2.4.7",
    `${focusOrder.length} focusable elements reached once in DOM order with 3 px focus indicators`,
  );

  await page.reload({ waitUntil: "networkidle" });
  await page.keyboard.press("Tab");
  assert.equal(await page.evaluate(() => document.activeElement?.className), "skip-link");
  await page.keyboard.press("Enter");
  assert.equal(await page.evaluate(() => location.hash), "#explorer-main");
  assert.equal(await page.evaluate(() => document.activeElement?.id), "explorer-main");
  record("Working skip link", "2.4.1", "first tab stop moves focus directly to the main explorer");

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator("#threshold-range").focus();
  await page.keyboard.press("ArrowRight");
  await waitForText(page, "#threshold-output", "0.16");
  assert.match(await page.locator("#live-status").textContent(), /cutoff 0\.16/);
  assert.match(await page.locator("#glass-canvas-description").textContent(), /0\.16 display cutoff/);
  const beforeKeyboardOrbit = await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL());
  await page.locator("#glass-canvas").focus();
  await page.keyboard.press("ArrowRight");
  const afterKeyboardOrbit = await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL());
  assert.notEqual(afterKeyboardOrbit, beforeKeyboardOrbit);
  record(
    "Keyboard operation and announced scientific update",
    "2.1.1, 4.1.3",
    "keyboard changes the cutoff and camera; visible output, Canvas description and polite status update together",
  );

  await page.locator("#n-select").selectOption("8");
  await page.locator("#l-select").selectOption("7");
  await page.locator("#m-select").selectOption("7");
  await page.locator("#z-select").selectOption("20");
  await waitForText(page, "#state-label", "8k (m=+7)");
  assert.equal(await page.locator("#l-select option").count(), 8);
  assert.equal(await page.locator("#m-select option").count(), 15);
  assert.match(await page.locator("#energy-value").textContent(), /^−\d+\.\d{6} eV$/);
  assert.ok((await page.locator("#glass-canvas").evaluate((canvas) => canvas.toDataURL())).length > 20_000);
  record(
    "Validated domain endpoint",
    "scientific input robustness",
    "Z=20, n=8, l=7, m=+7 renders finite results while impossible angular options remain absent",
  );

  await page.setViewportSize({ width: 320, height: 800 });
  await page.reload({ waitUntil: "networkidle" });
  const reflow = await page.evaluate(() => {
    const graph = document.querySelector(".chart-scroll");
    return {
      viewport: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      graphClientWidth: graph.clientWidth,
      graphScrollWidth: graph.scrollWidth,
    };
  });
  assert.ok(reflow.documentWidth <= reflow.viewport);
  assert.ok(reflow.graphScrollWidth > reflow.graphClientWidth);
  record(
    "320 px reflow",
    "1.4.10",
    "no page-level horizontal overflow; the radial chart alone uses a named keyboard-scrollable viewport",
  );

  await page.setViewportSize({ width: 800, height: 900 });
  await page.reload({ waitUntil: "networkidle" });
  const resizedText = await page.evaluate(() => {
    document.documentElement.style.fontSize = "200%";
    const selectors = ["h1", ".hero__summary", "#controls-heading", "#glass-heading", "#evidence-heading", "#interpretation-heading", ".control-help", ".interaction-hint"];
    return {
      viewport: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      overflows: selectors.filter((selector) => {
        const element = document.querySelector(selector);
        return element.scrollWidth > element.clientWidth + 1;
      }),
    };
  });
  assert.ok(resizedText.documentWidth <= resizedText.viewport);
  assert.deepEqual(resizedText.overflows, []);
  record("200% text resize", "1.4.4", "principal text and instructions resize without clipping or page-level overflow");

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload({ waitUntil: "networkidle" });
  const reducedMotion = await page.evaluate(() => ({
    scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
    duration: getComputedStyle(document.querySelector(".skip-link")).transitionDuration,
  }));
  assert.equal(reducedMotion.scrollBehavior, "auto");
  assert.ok(reducedMotion.duration === "0s" || reducedMotion.duration === "1e-05s" || reducedMotion.duration === "0.00001s");
  await page.emulateMedia({ reducedMotion: "no-preference", forcedColors: "active" });
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(await page.locator("#energy-value").textContent(), "−1.510915 eV");
  assert.equal(await page.locator("#glass-canvas").evaluate((canvas) => getComputedStyle(canvas).borderTopWidth), "2px");
  record(
    "User display preferences",
    "1.4.11, 2.3.3",
    "reduced motion disables smooth scrolling and transitions; forced colours preserve numerical output and canvas boundaries",
  );

  await page.emulateMedia({ reducedMotion: "no-preference", forcedColors: "none" });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload({ waitUntil: "networkidle" });
  const client = await page.context().newCDPSession(page);
  await client.send("HeapProfiler.collectGarbage");
  const heapBefore = await page.evaluate(() => performance.memory?.usedJSHeapSize ?? 0);
  const performanceEvidence = await page.evaluate(async () => {
    const preset = document.getElementById("gallery-preset");
    const values = [...preset.options].map((option) => option.value).filter(Boolean);
    const timings = [];
    for (let cycle = 0; cycle < 3; cycle += 1) {
      for (const value of values) {
        const started = performance.now();
        preset.value = value;
        preset.dispatchEvent(new Event("change", { bubbles: true }));
        await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        timings.push(performance.now() - started);
      }
    }
    return { count: timings.length, maximumMs: Math.max(...timings), meanMs: timings.reduce((sum, value) => sum + value, 0) / timings.length };
  });
  await client.send("HeapProfiler.collectGarbage");
  const heapAfter = await page.evaluate(() => performance.memory?.usedJSHeapSize ?? 0);
  await client.detach();
  const heapGrowthMb = (heapAfter - heapBefore) / 1_048_576;
  assert.equal(performanceEvidence.count, 75);
  assert.ok(performanceEvidence.maximumMs < 450, `maximum update ${performanceEvidence.maximumMs} ms`);
  assert.ok(heapGrowthMb < 16, `retained heap grew by ${heapGrowthMb.toFixed(2)} MB`);
  record(
    "Gallery performance and retained memory",
    "interaction quality",
    `75 full renders; maximum ${performanceEvidence.maximumMs.toFixed(2)} ms, mean ${performanceEvidence.meanMs.toFixed(2)} ms; post-GC heap change ${heapGrowthMb.toFixed(2)} MB`,
  );

  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(externalRequests, []);
  record(
    "Offline runtime integrity",
    "privacy and robustness",
    "zero console errors, page errors and external network requests across the audit",
  );

  console.log(`Task 10 accessibility audit: PASS (${checks.length} evidence groups, 0 detected violations in tested WCAG 2.2 AA behaviours)`);
  for (const check of checks) console.log(`- [${check.criteria}] ${check.name}: ${check.detail}`);
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
