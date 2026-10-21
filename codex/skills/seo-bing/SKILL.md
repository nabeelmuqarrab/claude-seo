---
name: seo-bing
description: "Bing Webmaster Tools + IndexNow extension. Microsoft Copilot citations are fed by the Bing index; this skill makes Bing visibility, link data, and IndexNow URL submission first-class."
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


## Extension Bing Webmaster workflow


# seo-bing

The non-Google indexing surface. Google still rejects IndexNow (per
Gary Illyes, multiple SOTR episodes 2024-2025), so this skill is
specifically for **Amazon/Bing/Naver/Seznam.cz/Yandex/Yep indexing** and
**Microsoft Copilot AI citation** (which pulls from the Bing index).

## Prerequisites

- Run `python "<SEO_ROOT>/scripts/codex-seo.py" integration bing-webmaster` or `install.ps1`.
- A Bing Webmaster Tools API key.
- Optional: an IndexNow host key (32+ chars) published at the URL
  declared as `INDEXNOW_KEY_LOCATION`.

## Routing

| Command | Underlying script |
|---|---|
| `$seo bing links <url>` | `python "<SEO_ROOT>/scripts/codex-seo.py" run bing_webmaster.py links <url>` |
| `$seo bing compare <urlA> <urlB>` | `python "<SEO_ROOT>/scripts/codex-seo.py" run bing_webmaster.py compare <urlA> <urlB>`; both properties must be registered to the API account |
| `$seo bing submit <url>` (single URL) | `python "<SEO_ROOT>/scripts/codex-seo.py" run indexnow_submit.py --host ... --urls <url>` |
| `$seo bing submit-batch <file>` | `python "<SEO_ROOT>/scripts/codex-seo.py" run indexnow_submit.py --host ... --urls-file <file>` |
| `$seo bing verify-indexnow` | `python "<SEO_ROOT>/scripts/codex-seo.py" run indexnow_submit.py --host ... --verify-only` |

## When this skill applies

- The user is publishing new pages and wants Microsoft Copilot
  citation eligibility (Bing index ingestion).
- The user wants to nudge Amazon/Bing/Naver/Seznam.cz/Yandex/Yep indexing for fresh
  URLs.
- The user manages both properties and wants to compare their Bing link data.
  For an arbitrary competitor, route to DataForSEO, Moz, or Common Crawl.

## Cross-skill delegation

- For Google indexing (very different model, sitemap-driven, no
  IndexNow), use `seo-google indexing`.
- For multi-source backlink confidence weighting, fall back to
  `seo-backlinks` which already integrates Bing + Moz + CC.
