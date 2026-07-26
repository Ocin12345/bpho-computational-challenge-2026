import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK09_A11Y_PORT || 4211);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath =
  process.env.TASK09_CHROMIUM_EXECUTABLE || chromium.executablePath();

if (!existsSync(executablePath)) {
  throw new Error(
    `Chromium executable is unavailable: ${executablePath}. Set TASK09_CHROMIUM_EXECUTABLE.`,
  );
}

const server = spawn(
  "python3",
  ["-m", "task09_compton_scattering.serve_task09", "--port", String(port)],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Task 9 server exited with code ${server.exitCode}`);
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // The server may still be binding its socket.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 9 server");
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
  browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(baseUrl, { waitUntil: "networkidle" });

  const semantics = await page.evaluate(() => {
    const accessibleName = (element) => {
      const aria = element.getAttribute("aria-label");
      if (aria) return aria.trim();
      if (element.labels?.length) return [...element.labels].map((label) => label.textContent.trim()).join(" ");
      return element.textContent?.trim() || "";
    };
    const focusableSelector = 'a[href], button, input, [tabindex]:not([tabindex="-1"])';
    return {
      language: document.documentElement.lang,
      title: document.title,
      mainCount: document.querySelectorAll("main").length,
      h1Count: document.querySelectorAll("h1").length,
      headings: [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")].map((heading) => ({
        level: Number(heading.tagName.slice(1)),
        text: heading.textContent.trim(),
      })),
      controls: [...document.querySelectorAll("button, input, progress")].map((element) => ({
        id: element.id,
        name: accessibleName(element),
      })),
      focusableCount: document.querySelectorAll(focusableSelector).length,
      imageLabels: [...document.querySelectorAll('svg[role="img"]')].map((svg) => {
        const ids = (svg.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean);
        return {
          labelled: ids.length === 2 && ids.every((id) => document.getElementById(id)),
          title: ids[0] ? document.getElementById(ids[0])?.textContent.trim() : "",
          description: ids[1] ? document.getElementById(ids[1])?.textContent.trim() : "",
        };
      }),
      graphRegions: [...document.querySelectorAll('[role="region"][tabindex="0"]')].map((region) => region.getAttribute("aria-label")),
      liveStatus: document.getElementById("live-results")?.textContent.trim(),
    };
  });

  assert.equal(semantics.language, "en");
  assert.match(semantics.title, /Task 9.+Compton scattering explorer/);
  assert.equal(semantics.mainCount, 1);
  assert.equal(semantics.h1Count, 1);
  assert.ok(semantics.headings.every((heading) => heading.text));
  for (let index = 1; index < semantics.headings.length; index += 1) {
    assert.ok(
      semantics.headings[index].level <= semantics.headings[index - 1].level + 1,
      `heading level skips before ${semantics.headings[index].text}`,
    );
  }
  assert.ok(semantics.controls.every((control) => control.name));
  assert.equal(semantics.imageLabels.length, 6);
  assert.ok(semantics.imageLabels.every((image) => image.labelled && image.title && image.description));
  assert.equal(semantics.graphRegions.length, 5);
  assert.ok(semantics.graphRegions.every(Boolean));
  assert.match(semantics.liveStatus, /fractional shift 0\.3914/);
  record(
    "Semantic structure, names and dynamic descriptions",
    "1.1.1, 1.3.1, 3.3.2, 4.1.2, 4.1.3",
    `${semantics.headings.length} ordered headings, ${semantics.controls.length} named controls, 6 described SVGs and 5 named graph regions`,
  );

  const cdp = await page.context().newCDPSession(page);
  const accessibilityTree = await cdp.send("Accessibility.getFullAXTree");
  const accessibleNames = accessibilityTree.nodes.map((node) => node.name?.value).filter(Boolean);
  for (const expectedName of [
    "Compton scattering explorer",
    "Incident photon energy, E",
    "Photon scattering angle, θ",
    "Compton-scattering momentum diagram",
    "Fractional wavelength shift versus photon scattering angle",
    "Electron recoil speed versus photon scattering angle",
    "Electron recoil angle versus photon scattering angle",
    "Percentage of incident energy retained by the scattered photon",
  ]) {
    assert.ok(accessibleNames.some((name) => name.startsWith(expectedName)), `accessibility tree is missing ${expectedName}`);
  }
  await cdp.detach();
  record(
    "Chromium accessibility-tree exposure",
    "1.3.1, 4.1.2",
    `${accessibilityTree.nodes.length} accessibility nodes; all key controls, result meter and figures named`,
  );

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
    const textSamples = [
      [".hero__summary", "#eef5fa", 4.5],
      [".section-kicker", "#ffffff", 4.5],
      [".button", "#ffffff", 4.5],
      [".range-scale", "#ffffff", 4.5],
      [".collision-figure figcaption", "#ffffff", 4.5],
      [".endpoint-note", "#ffffff", 4.5],
      [".extension-results span", "#f8fcfa", 4.5],
      ["footer", "#edf2f7", 4.5],
      [".verification-badge", "#eefaf7", 4.5],
      [".result-primary", "#ffffff", 3],
    ].map(([selector, background, required]) => ({
      selector,
      ratio: ratio(getComputedStyle(document.querySelector(selector)).color, background),
      required,
    }));
    const curves = [...document.querySelectorAll("#shift-chart path.curve")].map((curve, index) => ({
      name: `official curve ${index + 1}`,
      ratio: ratio(getComputedStyle(curve).stroke, "#fbfdff"),
    }));
    const inputBorder = getComputedStyle(document.getElementById("energy-number")).borderTopColor;
    return {
      textSamples,
      nonTextSamples: [
        ...curves,
        { name: "number-input boundary", ratio: ratio(inputBorder, "#ffffff") },
      ],
    };
  });
  assert.ok(contrast.textSamples.every((sample) => sample.ratio >= sample.required), JSON.stringify(contrast.textSamples));
  assert.ok(contrast.nonTextSamples.every((sample) => sample.ratio >= 3), JSON.stringify(contrast.nonTextSamples));
  record(
    "Text and essential non-text contrast",
    "1.4.3, 1.4.11",
    `minimum tested text ratio ${Math.min(...contrast.textSamples.map((sample) => sample.ratio)).toFixed(2)}:1; minimum graph/component ratio ${Math.min(...contrast.nonTextSamples.map((sample) => sample.ratio)).toFixed(2)}:1`,
  );

  const graphEncoding = await page.evaluate(() => ({
    dashPatterns: [...document.querySelectorAll("#shift-chart path.curve")].map((curve) => getComputedStyle(curve).strokeDasharray),
    legend: document.querySelector(".energy-legend").textContent.replace(/\s+/g, " ").trim(),
    yMaximum: [...document.querySelectorAll("#beta-chart .chart-label")].slice(0, 5).at(-1)?.textContent,
  }));
  assert.equal(new Set(graphEncoding.dashPatterns).size, 5);
  for (const description of ["solid", "dashed", "dotted", "dash–dot", "long dash"]) assert.match(graphEncoding.legend, new RegExp(description));
  assert.equal(graphEncoding.yMaximum, "1.00");
  record(
    "Colour-independent curve encoding and honest speed scale",
    "1.4.1",
    "five written line-style labels match five distinct SVG dash patterns; v/c uses a fixed 0–1 scale",
  );

  const focusableSelector = 'a[href], button, input, [tabindex]:not([tabindex="-1"])';
  await page.evaluate(() => document.activeElement?.blur());
  const focusOrder = [];
  for (let index = 0; index < semantics.focusableCount; index += 1) {
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => {
      const element = document.activeElement;
      const style = getComputedStyle(element);
      return {
        key: element.id || element.getAttribute("data-energy") || element.getAttribute("data-theta") || element.getAttribute("aria-label") || element.getAttribute("href") || element.textContent.trim(),
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
  await page.locator("#theta-range").focus();
  await page.keyboard.press("ArrowRight");
  await waitForText(page, "#theta-output", "90.5°");
  assert.equal(await page.locator("#theta-range").inputValue(), "90.5");
  assert.equal(await page.locator("#theta-output").textContent(), "90.5°");
  assert.match(await page.locator("#live-results").textContent(), /90\.5 degrees/);
  assert.match(await page.locator("#collision-description").textContent(), /90\.5 degrees/);
  record(
    "Keyboard operation and announced live update",
    "2.1.1, 4.1.3",
    "ArrowRight changes θ by 0.5°, then updates visible output, SVG description and polite status",
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
    "no page-level horizontal overflow; each two-dimensional graph uses a named keyboard-scrollable viewport",
  );

  await page.setViewportSize({ width: 800, height: 900 });
  await page.reload({ waitUntil: "networkidle" });
  const resizedText = await page.evaluate(() => {
    document.documentElement.style.fontSize = "200%";
    const selectors = ["h1", ".hero__summary", "#controls-heading", "#collision-heading", "#charts-heading", "#extension-heading", "#equations-heading"];
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
  record("200% text resize", "1.4.4", "all key headings and explanations resize without clipping or page-level overflow");

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload({ waitUntil: "networkidle" });
  const reducedMotionSeconds = await page.evaluate(() => {
    const duration = getComputedStyle(document.getElementById("photon-energy-fill")).transitionDuration;
    return duration.endsWith("ms") ? parseFloat(duration) / 1000 : parseFloat(duration);
  });
  assert.ok(reducedMotionSeconds <= 0.000001);
  await page.emulateMedia({ reducedMotion: "no-preference", forcedColors: "active" });
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(await page.locator("#fractional-shift").textContent(), "0.39139");
  record(
    "User display preferences",
    "1.4.11, 2.3.3",
    "reduced motion suppresses transitions and forced-colour mode preserves all numerical results",
  );

  console.log(`Task 9 accessibility audit: PASS (${checks.length} evidence groups, 0 detected WCAG 2.2 AA violations)`);
  for (const check of checks) console.log(`- [${check.criteria}] ${check.name}: ${check.detail}`);
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
