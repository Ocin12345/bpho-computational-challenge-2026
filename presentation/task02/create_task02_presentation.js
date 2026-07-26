"use strict";

const path = require("node:path");
const { spawnSync } = require("node:child_process");

const builder = path.resolve(__dirname, "../build_task_presentations.js");
const result = spawnSync(process.execPath, [builder, "2"], { stdio: "inherit" });
process.exitCode = result.status ?? 1;
