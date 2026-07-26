import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const port = Number(process.env.TASK08_A11Y_PORT || 4205);
const baseUrl = `http://127.0.0.1:${port}/`;
const executablePath =
  process.env.TASK08_CHROMIUM_EXECUTABLE || chromium.executablePath();

if (!existsSync(executablePath)) {
  throw new Error(
    `Chromium executable is unavailable: ${executablePath}. Set TASK08_CHROMIUM_EXECUTABLE.`,
  );
}

const server = spawn(
  "python3",
  ["-m", "task08_quantum_cryptography.serve_task08", "--port", String(port)],
  { cwd: repositoryRoot, stdio: ["ignore", "pipe", "pipe"] },
);

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (server.exitCode !== null) {
      throw new Error(`Task 8 server exited with code ${server.exitCode}`);
    }
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // The local server may still be binding its socket.
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for the Task 8 server");
}

const checks = [];
function record(name, criteria, detail) {
  checks.push({ name, criteria, detail });
}

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  await page.goto(baseUrl, { waitUntil: "networkidle" });

  const semantics = await page.evaluate(() => {
    const labelFor = (element) => {
      const aria = element.getAttribute("aria-label");
      if (aria) return aria.trim();
      if (element.labels?.length) {
        return [...element.labels]
          .map((label) => label.textContent.trim())
          .join(" ");
      }
      return element.textContent?.trim() || "";
    };
    const focusableSelector =
      'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
    return {
      language: document.documentElement.lang,
      title: document.title,
      mainCount: document.querySelectorAll("main").length,
      h1Count: document.querySelectorAll("h1").length,
      headings: [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")].map(
        (heading) => ({
          level: Number(heading.tagName.slice(1)),
          text: heading.textContent.trim(),
        }),
      ),
      controls: [...document.querySelectorAll("button, input")].map((element) => ({
        id: element.id,
        name: labelFor(element),
      })),
      focusableCount: document.querySelectorAll(focusableSelector).length,
      imageLabels: [...document.querySelectorAll('svg[role="img"]')].map((svg) => {
        const ids = (svg.getAttribute("aria-labelledby") || "").split(/\s+/).filter(Boolean);
        return {
          labelled: ids.length >= 2 && ids.every((id) => document.getElementById(id)),
          title: ids[0] ? document.getElementById(ids[0])?.textContent.trim() : "",
          description: ids[1]
            ? document.getElementById(ids[1])?.textContent.trim()
            : "",
        };
      }),
      meters: [...document.querySelectorAll('[role="meter"]')].map((meter) => ({
        label: meter.getAttribute("aria-label"),
        now: meter.getAttribute("aria-valuenow"),
        text: meter.getAttribute("aria-valuetext"),
      })),
      liveStatus: document.getElementById("live-results")?.textContent.trim(),
    };
  });

  assert.equal(semantics.language, "en");
  assert.match(semantics.title, /Task 8.+Quantum mismatch calculator/);
  assert.equal(semantics.mainCount, 1);
  assert.equal(semantics.h1Count, 1);
  assert.ok(semantics.headings.every((heading) => heading.text.length > 0));
  for (let index = 1; index < semantics.headings.length; index += 1) {
    assert.ok(
      semantics.headings[index].level <= semantics.headings[index - 1].level + 1,
      `heading level skips before ${semantics.headings[index].text}`,
    );
  }
  assert.ok(semantics.controls.every((control) => control.name.length > 0));
  assert.equal(semantics.imageLabels.length, 3);
  assert.ok(
    semantics.imageLabels.every(
      (image) => image.labelled && image.title && image.description,
    ),
  );
  assert.equal(semantics.meters.length, 2);
  assert.ok(
    semantics.meters.every((meter) => meter.label && meter.now && meter.text),
  );
  assert.match(semantics.liveStatus, /Classical mismatch 37\.5%/);
  record(
    "Semantic structure, labels and dynamic values",
    "1.1.1, 1.3.1, 3.3.2, 4.1.2, 4.1.3",
    `${semantics.headings.length} ordered headings, ${semantics.controls.length} named controls, 3 described SVG figures and 2 named meters`,
  );

  const cdp = await page.context().newCDPSession(page);
  const accessibilityTree = await cdp.send("Accessibility.getFullAXTree");
  const accessibleNames = accessibilityTree.nodes
    .map((node) => node.name?.value)
    .filter(Boolean);
  for (const expectedName of [
    "Quantum mismatch calculator",
    "Detector A angle, θ",
    "Detector B angle, φ",
    "Classical mismatch probability",
    "Quantum mismatch probability",
    "Classical and quantum mismatch probability curves",
    "Detected photon pairs, N",
    "Reproducible sample seed",
    "Draw next sample",
  ]) {
    assert.ok(
      accessibleNames.some((name) => name.startsWith(expectedName)),
      `accessibility tree is missing ${expectedName}`,
    );
  }
  await cdp.detach();
  record(
    "Chromium accessibility-tree exposure",
    "1.3.1, 4.1.2",
    `${accessibilityTree.nodes.length} accessibility nodes; all key controls, meters and figures named`,
  );

  const contrast = await page.evaluate(() => {
    const samples = [
      [".hero__summary", "#f4f7fb", 4.5],
      [".button--quiet", "#ffffff", 4.5],
      [".preset", "#ffffff", 4.5],
      [".range-scale", "#ffffff", 4.5],
      [".result-card__descriptor", "#ffffff", 4.5],
      [".comparison-figure figcaption", "#ffffff", 4.5],
      ["footer", "#f4f7fb", 4.5],
      [".result-card--classical .model-pill", "#fff0e7", 4.5],
      [".result-card--quantum .model-pill", "#e7f7f2", 4.5],
      [".detector-card--a .detector-tag", "#e8f5fb", 4.5],
      [".detector-card--b .detector-tag", "#f5ecf8", 4.5],
      [".verification-badge", "#ebf9f5", 4.5],
      [".result-card--classical .result-card__percent", "#ffffff", 3],
      [".result-card--quantum .result-card__percent", "#ffffff", 3],
      [".extension-label", "#fff5cf", 4.5],
      [".simulation-panel__summary", "#ffffff", 4.5],
      [".control-help", "#f7faff", 4.5],
      [".sample-statistics dt", "#f5f8fb", 4.5],
      [".simulation-warning", "#ffffff", 4.5],
      [".button--primary", "#006f64", 4.5],
      [".sample-card--classical .theory-chip output", "#fff0e7", 4.5],
      [".sample-card--quantum .theory-chip output", "#e7f7f2", 4.5],
    ];
    const parse = (colour) => {
      if (colour.startsWith("#")) {
        return [1, 3, 5].map((index) => parseInt(colour.slice(index, index + 2), 16));
      }
      const values = colour.match(/[\d.]+/g)?.map(Number);
      if (!values || values.length < 3) throw new Error(`Cannot parse ${colour}`);
      return values.slice(0, 3);
    };
    const luminance = (colour) => {
      const channels = parse(colour).map((value) => {
        const normalized = value / 255;
        return normalized <= 0.04045
          ? normalized / 12.92
          : ((normalized + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    };
    const ratio = (foreground, background) => {
      const first = luminance(foreground);
      const second = luminance(background);
      return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
    };
    const text = samples.map(([selector, background, required]) => {
      const foreground = getComputedStyle(document.querySelector(selector)).color;
      return { selector, ratio: ratio(foreground, background), required };
    });
    const buttonBorder = getComputedStyle(document.querySelector(".button--quiet"))
      .borderTopColor;
    const classicalStroke = getComputedStyle(
      document.getElementById("classical-curve"),
    ).stroke;
    const quantumStroke = getComputedStyle(
      document.getElementById("quantum-curve"),
    ).stroke;
    return {
      text,
      nonText: [
        { name: "button boundary", ratio: ratio(buttonBorder, "#ffffff") },
        { name: "classical curve", ratio: ratio(classicalStroke, "#ffffff") },
        { name: "quantum curve", ratio: ratio(quantumStroke, "#ffffff") },
      ],
    };
  });
  assert.ok(
    contrast.text.every((sample) => sample.ratio >= sample.required),
    JSON.stringify(contrast.text),
  );
  assert.ok(
    contrast.nonText.every((sample) => sample.ratio >= 3),
    JSON.stringify(contrast.nonText),
  );
  const minimumTextContrast = Math.min(...contrast.text.map((sample) => sample.ratio));
  const minimumNonTextContrast = Math.min(
    ...contrast.nonText.map((sample) => sample.ratio),
  );
  record(
    "Text and essential non-text contrast",
    "1.4.3, 1.4.11",
    `minimum tested text ratio ${minimumTextContrast.toFixed(2)}:1; minimum tested component/graph ratio ${minimumNonTextContrast.toFixed(2)}:1`,
  );

  const graphEncoding = await page.evaluate(() => ({
    classicalDash: getComputedStyle(document.getElementById("classical-curve"))
      .strokeDasharray,
    quantumDash: getComputedStyle(document.getElementById("quantum-curve"))
      .strokeDasharray,
    legend: document.querySelector(".chart-legend").textContent,
    yLabels: [...document.querySelectorAll(".chart-axes text")]
      .slice(0, 5)
      .map((label) => label.textContent),
  }));
  assert.ok(["none", "0px"].includes(graphEncoding.classicalDash));
  assert.notEqual(graphEncoding.quantumDash, "none");
  assert.match(graphEncoding.legend, /solid/);
  assert.match(graphEncoding.legend, /dashed/);
  assert.deepEqual(graphEncoding.yLabels, ["100", "75", "50", "25", "0"]);
  record(
    "Colour-independent graph encoding and honest scale",
    "1.4.1",
    "solid/dashed line styles, written legend labels and a fixed labelled 0–100% axis",
  );

  const focusableSelector =
    'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
  await page.evaluate(() => {
    document.activeElement?.blur();
    window.scrollTo(0, 0);
  });
  const focusOrder = [];
  for (let index = 0; index < semantics.focusableCount; index += 1) {
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => {
      const element = document.activeElement;
      const style = getComputedStyle(element);
      return {
        key:
          element.id ||
          element.getAttribute("data-preset") ||
          element.getAttribute("data-photon-pairs") ||
          element.getAttribute("href") ||
          element.className,
        outlineStyle: style.outlineStyle,
        outlineWidth: parseFloat(style.outlineWidth),
      };
    });
    assert.notEqual(focused.outlineStyle, "none", `${focused.key} lacks a focus outline`);
    assert.ok(focused.outlineWidth >= 3, `${focused.key} focus outline is too thin`);
    focusOrder.push(focused.key);
  }
  assert.equal(new Set(focusOrder).size, semantics.focusableCount);
  assert.deepEqual(
    focusOrder,
    await page.evaluate((selector) =>
      [...document.querySelectorAll(selector)].map(
        (element) =>
          element.id ||
          element.getAttribute("data-preset") ||
          element.getAttribute("data-photon-pairs") ||
          element.getAttribute("href") ||
          element.className,
      ),
    focusableSelector),
  );
  record(
    "Complete keyboard route and visible focus",
    "2.1.1, 2.4.3, 2.4.7",
    `${focusOrder.length} focusable elements reached once in DOM order with 3px focus indicators`,
  );

  await page.reload({ waitUntil: "networkidle" });
  await page.keyboard.press("Tab");
  assert.equal(await page.evaluate(() => document.activeElement?.className), "skip-link");
  await page.keyboard.press("Enter");
  assert.equal(await page.evaluate(() => window.location.hash), "#calculator-main");
  assert.equal(await page.evaluate(() => document.activeElement?.id), "calculator-main");
  record("Working skip link", "2.4.1", "first tab stop moves focus directly to main content");

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  const curveBefore = await page.locator("#classical-curve").getAttribute("d");
  await page.locator("#theta-range").focus();
  await page.keyboard.press("ArrowRight");
  assert.equal(await page.locator("#theta-range").inputValue(), "-29");
  assert.notEqual(await page.locator("#classical-curve").getAttribute("d"), curveBefore);
  assert.match(
    await page.locator("#comparison-chart-description").textContent(),
    /minus 29 degrees/,
  );
  assert.match(await page.locator("#live-results").textContent(), /Detector A minus 29/);
  record(
    "Keyboard operation and announced live update",
    "2.1.1, 4.1.3",
    "ArrowRight changes θ by one degree and updates the SVG curve, description and polite status",
  );

  await page.locator('[data-preset="official"]').click();
  await page.locator("#photon-count").focus();
  await page.keyboard.press(process.platform === "darwin" ? "Meta+A" : "Control+A");
  await page.keyboard.type("100");
  assert.equal(await page.locator("#classical-sample-count").textContent(), "42");
  assert.equal(await page.locator("#quantum-sample-count").textContent(), "80");
  assert.match(await page.locator("#simulation-live").textContent(), /100 photon pairs/);
  await page.locator("#next-sample-button").focus();
  await page.keyboard.press("Enter");
  assert.equal(await page.locator("#simulation-seed").inputValue(), "2027");
  assert.match(await page.locator("#simulation-live").textContent(), /seed 2,027/);
  record(
    "Keyboard-controlled finite-photon experiment",
    "2.1.1, 3.3.2, 4.1.3",
    "photon count and next-sample seed update the two counts and the dedicated polite status without pointer input",
  );

  await page.setViewportSize({ width: 320, height: 800 });
  await page.reload({ waitUntil: "networkidle" });
  const reflow = await page.evaluate(() => {
    const frame = document.querySelector(".chart-frame");
    return {
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      graphClientWidth: frame.clientWidth,
      graphScrollWidth: frame.scrollWidth,
      hintVisible: getComputedStyle(document.querySelector(".chart-scroll-hint")).display,
    };
  });
  assert.ok(reflow.documentWidth <= reflow.viewport);
  assert.ok(reflow.graphScrollWidth > reflow.graphClientWidth);
  assert.notEqual(reflow.hintVisible, "none");
  record(
    "320px reflow",
    "1.4.10",
    "no page-level horizontal overflow; the two-dimensional graph alone has a labelled keyboard-scrollable viewport",
  );

  await page.setViewportSize({ width: 800, height: 900 });
  await page.reload({ waitUntil: "networkidle" });
  const resizedText = await page.evaluate(() => {
    document.documentElement.style.fontSize = "200%";
    const selectors = [
      "h1",
      ".hero__summary",
      "#detector-heading",
      "#results-heading",
      "#comparison-chart-heading",
      "#simulation-heading",
      ".simulation-panel",
      ".formula-panel",
    ];
    return {
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      overflows: selectors.filter((selector) => {
        const element = document.querySelector(selector);
        return element.scrollWidth > element.clientWidth + 1;
      }),
    };
  });
  assert.ok(resizedText.documentWidth <= resizedText.viewport);
  assert.deepEqual(resizedText.overflows, []);
  record(
    "200% text resize",
    "1.4.4",
    "key headings, explanations and formulas resize without clipping or page-level horizontal overflow",
  );

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload({ waitUntil: "networkidle" });
  const reducedMotionDuration = await page.evaluate(() =>
    getComputedStyle(document.getElementById("classical-fill")).transitionDuration,
  );
  const reducedMotionSeconds = reducedMotionDuration.endsWith("ms")
    ? parseFloat(reducedMotionDuration) / 1000
    : parseFloat(reducedMotionDuration);
  assert.ok(reducedMotionSeconds <= 0.000001);
  await page.emulateMedia({ reducedMotion: "no-preference", forcedColors: "active" });
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(await page.locator("#classical-percent").textContent(), "37.5%");
  assert.equal(await page.locator("#quantum-percent").textContent(), "75.0%");
  record(
    "User display preferences",
    "1.4.11, 2.3.3",
    "reduced motion suppresses transitions and forced-colour mode preserves the calculation",
  );

  console.log(
    `Task 8 accessibility audit: PASS (${checks.length} evidence groups, 0 detected WCAG 2.2 AA violations)`,
  );
  for (const check of checks) {
    console.log(`- [${check.criteria}] ${check.name}: ${check.detail}`);
  }
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}
