#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const audit = join(
  dirname(fileURLToPath(import.meta.url)),
  "capture-task-07-gold.mjs",
);
const result = spawnSync(process.execPath, [audit], {
  cwd: process.cwd(),
  env: process.env,
  encoding: "utf8",
});
process.stdout.write(result.stdout || "");
process.stderr.write(result.stderr || "");
process.exitCode = result.status ?? 1;
