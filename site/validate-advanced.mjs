#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const site = dirname(fileURLToPath(import.meta.url));
const project = resolve(site, "..");
const read = (path) => readFile(resolve(project, path), "utf8");

const [html, css, javascript, evidence, reports] = await Promise.all([
  read("site/advanced.html"),
  read("site/assets/advanced.css"),
  read("site/assets/advanced.js"),
  read("site/data/advanced-extensions.json").then(JSON.parse),
  read("reports/advanced_extensions/README.md"),
]);

assert.equal(evidence.schema_version, "bpho-advanced-extensions-v1");
assert.equal(evidence.accepted, true);
assert.equal(evidence.task_count, 10);
assert.equal(evidence.passed_check_count, evidence.check_count);
assert.deepEqual(Object.keys(evidence.tasks).sort((a, b) => Number(a) - Number(b)), ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]);
for (const [number, task] of Object.entries(evidence.tasks)) {
  assert.equal(task.status, "complete", `Task ${number} status`);
  assert.ok(Object.keys(task.checks).length >= 2, `Task ${number} checks`);
  assert.ok(Object.values(task.checks).every(Boolean), `Task ${number} failed check`);
  assert.match(reports, new RegExp(`task${number}\\.md`));
}

assert.match(html, /<h1[^>]*id="advanced-title"/);
assert.match(html, /data-task-tabs/);
assert.match(html, /data-advanced-chart/);
assert.match(html, /data-morph-slider/);
assert.match(html, /\.\/assets\/advanced\.js/);
assert.match(html, /\.\/assets\/advanced\.css/);
assert.match(javascript, /m_morph/);
assert.match(javascript, /createImageData/);
assert.match(javascript, /privacy amplification/i);
assert.match(css, /@media \(max-width: 620px\)/);
assert.match(css, /prefers-reduced-motion/);

const runtimeText = `${html}\n${javascript}`;
assert.doesNotMatch(runtimeText, /(?:src|href|import\s*\()[^\n]*(?:cdn\.jsdelivr|esm\.sh|fonts\.googleapis|fonts\.gstatic)/i);

console.log(`Advanced lab validation: PASS (${evidence.passed_check_count}/${evidence.check_count} science checks, 10 reports)`);
