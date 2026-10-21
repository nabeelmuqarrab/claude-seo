---
name: seo-cockpit
description: "Create a portable local SEO dashboard with SVG charts from saved audit, GSC, performance, maps and budget JSON evidence."
---

## Codex execution

Resolve `SEO_ROOT` from this skill's installed path (three directories above its
folder); `SKILL_ROOT` is this folder. Replace angle-bracket path placeholders
with those absolute paths. They are documentation placeholders, not shell variables.
Use the available Python 3.11+ executable (`python3` on POSIX, `py -3` or
`python` on Windows; use PowerShell's `&` for a quoted executable path).
Run bundled tools with [the native runner](../../../scripts/codex-seo.py).
Use actual host tools for file reads, edits, web access and optional delegation;
Claude tool/model names in reference material are not executable tool IDs.
Keep the user's selected Codex model; Claude model allocations are historical.
Use numeric scores only with a disclosed rubric and evidence coverage; otherwise
give an evidence/status card. Reference word floors, keyword density and English
readability targets are heuristics, not requirements for every language or tool.
Run specialist procedures inline when delegation is unavailable or not authorized.
Follow [the Codex operating rules](../../OPERATING-RULES.md) and keep each project's
scope, market, evidence, private credentials and output directory separate.
Provider setup: `python "<SEO_ROOT>/scripts/codex-seo.py" integration PROVIDER`
shows Codex instructions; it never runs the legacy Claude installers.

Run `python "<SEO_ROOT>/scripts/codex-seo.py" cockpit --input ABSOLUTE_JSON_PATH`. Supply an audit/report JSON object or an object of named panels. Each panel retains its source/date and renders its data; missing values stay missing. The dashboard is a local HTML artifact, not a hosted admin panel. Fetch fresh data through the relevant skills only when requested, then supply it as input. Use $seo-spend and $seo-doctor for native diagnostics. Claude terminal mods and token-free slash commands remain available in the original Claude companion; Codex uses regular skill turns and the exported dashboard.
