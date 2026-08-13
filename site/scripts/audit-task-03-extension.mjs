#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const html = readFileSync(join(siteRoot, "tasks", "task-03.html"), "utf8");
const script = readFileSync(join(siteRoot, "assets", "task-03-extension.js"), "utf8");

assert.match(
  html,
  /<section class="debye-section" id="extension" aria-labelledby="debye-title" hidden>/,
  "The Debye extension must stay outside the three-minute filming path",
);
assert.ok(
  !html.includes("../assets/task-03-extension.js"),
  "The hidden extension must not load an unnecessary runtime",
);
assert.ok(
  script.includes("task-03-debye-validation.json") &&
    script.includes("interpolateCurve"),
  "The validated Debye implementation must remain available in source",
);

console.log("Task 3 Debye extension boundary audit passed: validated implementation retained in source and hidden from the filming path.");
