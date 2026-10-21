"use strict";
// Native executable selection; no shell interpolation of tool arguments.
const {spawnSync} = require("child_process");
const path = require("path");
const fs = require("fs");
const chunks = [];
let size = 0;
for (;;) {
  const buffer = Buffer.alloc(8192);
  const count = fs.readSync(0, buffer, 0, buffer.length, null);
  if (!count) break;
  size += count;
  if (size > 2 * 1024 * 1024) {
    console.error("SEO hook event exceeded the 2 MiB limit"); process.exit(2);
  }
  chunks.push(buffer.subarray(0, count));
}
const payload = Buffer.concat(chunks).toString("utf8");
const script = process.argv[2] === "paid" ? "paid_guard.py" : "schema_hook.py";
const candidates = process.env.CLAUDE_SEO_PYTHON
  ? [[process.env.CLAUDE_SEO_PYTHON, []]]
  : [["py", ["-3"]], ["python3", []], ["python", []]];
for (const [exe, prefix] of candidates) {
  const probe = spawnSync(exe, [...prefix, "-c", "import sys; raise SystemExit(sys.version_info < (3, 10))"], {encoding: "utf8"});
  if (probe.status !== 0) continue;
  const run = spawnSync(exe, [...prefix, path.join(__dirname, script)], {input: payload, encoding: "utf8",
    env: {...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8", PYTHONDONTWRITEBYTECODE: "1"}});
  if (run.error) { console.error("SEO schema hook could not start Python"); process.exit(2); }
  process.stdout.write(run.stdout || "");
  process.stderr.write(run.stderr || "");
  process.exit(run.status === null ? 2 : run.status);
}
console.error("SEO schema hook needs Python 3.10+ (CLAUDE_SEO_PYTHON, py -3, python3 or python)");
process.exit(2);
