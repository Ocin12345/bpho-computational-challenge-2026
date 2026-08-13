#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "../../task08_quantum_cryptography/app/node_modules/playwright",
);
const origin = process.env.BPHO_SITE_ORIGIN || "http://127.0.0.1:8081";

async function inspect(viewport, mobile) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    isMobile: mobile,
    hasTouch: mobile,
    reducedMotion: mobile ? "reduce" : "no-preference",
  });
  const page = await context.newPage();
  const errors = [];
  const failedResources = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("requestfailed", (request) =>
    failedResources.push(`${request.url()}: ${request.failure()?.errorText}`),
  );

  await page.goto(`${origin}/site/tasks/task-06.html`, { waitUntil: "networkidle" });
  await page.waitForFunction(
    () =>
      document.documentElement.dataset.task06Status === "ready" &&
      document.documentElement.dataset.task06Relativity === "ready",
  );

  assert.deepEqual(errors, [], `Task 6 runtime errors: ${errors.join(" | ")}`);
  assert.deepEqual(
    failedResources,
    [],
    `Task 6 failed resources: ${failedResources.join(" | ")}`,
  );

  for (const id of ["experiment", "plot", "method", "validation", "extension"]) {
    const section = page.locator(`#${id}`);
    await section.scrollIntoViewIfNeeded();
    assert.equal(await section.isVisible(), true, `#${id} must be judge-visible`);
  }

  assert.equal(
    await page.getByText("Loading relativistic model", { exact: true }).isVisible(),
    false,
    "No dormant relativistic loading state may remain visible",
  );

  await page.locator('[data-voltage-preset="1000"]').click();
  const radiusAt1Kv = Number(
    (await page.locator("[data-d1-live-radius]").innerText()).replace(/[^0-9.]/g, ""),
  );
  const thetaAt1Kv = Number(
    (await page.locator("[data-d1-theta]").innerText()).replace(/[^0-9.]/g, ""),
  );
  const phiAt1Kv = Number(
    (await page.locator("[data-d1-phi]").innerText()).replace(/[^0-9.]/g, ""),
  );
  assert.ok(Math.abs(radiusAt1Kv - 38.465) < 0.001);
  assert.ok(Math.abs(thetaAt1Kv - 9.070778) < 1e-6);
  assert.ok(Math.abs(phiAt1Kv - 18.141556) < 1e-6);
  assert.ok(Math.abs(phiAt1Kv - 2 * thetaAt1Kv) < 2e-6);
  const d2RadiusAt1Kv = Number(
    (await page.locator("[data-d2-live-radius]").innerText()).replace(/[^0-9.]/g, ""),
  );
  assert.ok(Math.abs(d2RadiusAt1Kv - 23.181332) < 1e-6);

  await page.locator("[data-sweep-toggle]").click();
  await page.waitForFunction(
    () => Number(document.querySelector("#accelerating-voltage").value) >= 1100,
  );
  const radiusDuringSweep = Number(
    (await page.locator("[data-d1-live-radius]").innerText()).replace(/[^0-9.]/g, ""),
  );
  assert.ok(radiusDuringSweep < radiusAt1Kv, "Sweep must contract the first-order ring");
  await page.locator("[data-sweep-toggle]").click();

  await page.locator("[data-reset-model]").click();
  assert.equal(await page.locator("#accelerating-voltage").inputValue(), "3000");
  assert.equal(await page.locator('[data-family="d1"]').isChecked(), true);
  assert.equal(await page.locator('[data-family="d2"]').isChecked(), true);

  await page.locator('[data-voltage-preset="5000"]').click();
  const radiiAt5Kv = await Promise.all(
    ["d1", "d2"].map(async (family) =>
      Number(
        (await page.locator(`[data-${family}-live-radius]`).innerText()).replace(
          /[^0-9.]/g,
          "",
        ),
      ),
    ),
  );
  assert.ok(Math.abs(radiiAt5Kv[0] - 18.10394) < 1e-6);
  assert.ok(Math.abs(radiiAt5Kv[1] - 10.541869) < 1e-6);

  await page.locator('[data-family="d2"]').uncheck();
  assert.equal(
    await page.locator('[data-diagnostic-family="d2"]').evaluate((row) =>
      row.classList.contains("is-disabled"),
    ),
    true,
  );
  await page.locator("[data-reset-model]").click();

  await page.locator("#accelerating-voltage").focus();
  await page.keyboard.press("Home");
  assert.equal(await page.locator("#accelerating-voltage").inputValue(), "1000");
  await page.keyboard.press("End");
  assert.equal(await page.locator("#accelerating-voltage").inputValue(), "5000");
  await page.locator("[data-reset-model]").click();

  for (const target of ["experiment", "plot", "method", "validation"]) {
    await page.locator(`.section-nav a[href="#${target}"]`).click();
    assert.equal(new URL(page.url()).hash, `#${target}`);
    assert.equal(
      await page.locator(`.section-nav a[href="#${target}"]`).getAttribute("aria-current"),
      "page",
    );
  }

  await page.locator('.section-nav a[href="#plot"]').click();
  const chartClick = await page.locator("#spacing-recovery-chart").evaluate((canvas) => {
    const compact = canvas.clientWidth < 620;
    const left = compact ? 65 : 92;
    const right = compact ? 20 : 44;
    const top = compact ? 54 : 66;
    const bottom = compact ? 72 : 84;
    const plotWidth = canvas.clientWidth - left - right;
    const plotHeight = canvas.clientHeight - top - bottom;
    const qAt1KvD1 = 0.15765444845498783;
    const yAt1Kv = 1 / Math.sqrt(1000);
    return {
      x: left + (qAt1KvD1 / 0.17) * plotWidth,
      y: top + plotHeight - (yAt1Kv / 0.033) * plotHeight,
    };
  });
  await page.locator("#spacing-recovery-chart").click({ position: chartClick });
  assert.equal(await page.locator("#accelerating-voltage").inputValue(), "1000");

  const downloadPromise = page.waitForEvent("download");
  await page.locator("[data-export-csv]").click();
  const download = await downloadPromise;
  const csv = await readFile(await download.path(), "utf8");
  assert.ok(csv.includes("# tube_radius_mm,65"));
  assert.ok(csv.includes("theta_deg,phi_deg,photographic_radius_x_mm"));
  assert.ok(csv.includes("inverse_sqrt_voltage_V_neg_half"));
  assert.equal(csv.trim().split(/\r?\n/).length, 810);

  const layout = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    loading: [...document.querySelectorAll("body *")]
      .filter((element) => {
        const bounds = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return bounds.width > 0 && bounds.height > 0 && style.visibility !== "hidden";
      })
      .map((element) => element.textContent?.trim())
      .filter((text) => text === "Loading relativistic model" || text === "Loading relativistic correction"),
  }));
  assert.ok(layout.overflow <= 1, `Task 6 overflow: ${layout.overflow}px`);
  assert.deepEqual(layout.loading, [], "Visible loading copy must clear");

  await context.close();
  await browser.close();
}

await inspect({ width: 1440, height: 1000 }, false);
await inspect({ width: 390, height: 844 }, true);
console.log("Task 6 Gold upgrade audit passed on desktop and mobile.");
