#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const audit = join(dirname(fileURLToPath(import.meta.url)), "audit-all-tasks.mjs");
const result = spawnSync(process.execPath, [audit], {
  cwd: process.cwd(),
  env: { ...process.env, TASK_NUMBER: "8" },
  encoding: "utf8",
});
process.stdout.write(result.stdout || "");
process.stderr.write(result.stderr || "");
assert.equal(result.status, 0, "Task 8 official filming-page audit failed");
console.log("Task 8 official classical-versus-quantum calculator filming page audit passed; finite-sample statistics remain covered by the data validator.");
