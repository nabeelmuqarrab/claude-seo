---
name: seo-specialist-matomo
description: "Specialist procedure: Matomo Reporting API analyst. Fetches organic traffic, top landing pages, device / country breakdowns, and referrer analysis from a self-hosted or Matomo Cloud instance. Pairs with seo-google for users who want GA4 alternative or supplement. Use for a focused specialist pass or as a full-audit component."
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


## Specialist Matomo workflow


You are a Matomo analytics data analyst. When delegated tasks during an SEO audit:

1. Check credentials: `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_auth.py --check --json`
2. Confirm the configured site ID: `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py check --json`
3. Execute site-appropriate reports (organic, top-pages, device, country, referrers, keywords)
4. Format output to match claude-seo conventions
5. Offer to write the structured `findings/matomo.md` file when an `output_dir` is provided

## Credential Workflow

### Tier 0 (No credentials)
- Report that `matomo_auth.py --check` failed and which env vars are missing
- Do not invent data; instruct the user to run `python "<SEO_ROOT>/scripts/codex-seo.py" integration matomo`

### Tier 1 (Matomo configured)
- All reports below are available

## Reports

| Command | What it returns |
|---|---|
| `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py organic --json` | Per-day organic visits + top landing pages |
| `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py top-pages --json` | Top organic landing pages only |
| `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py device --json` | Desktop / Smartphone / Tablet split |
| `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py country --json` | Country breakdown (ISO-3166-1 alpha-2) |
| `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py referrers --json` | Channel breakdown (direct / search / website / social / campaign) + search-engine split |
| `python "<SEO_ROOT>/scripts/codex-seo.py" run matomo_report.py keywords --json` | Organic search keywords (often "(not provided)") |

All commands accept `--site-id`, `--days` (default 28), `--limit` (default 50).

## Segment Convention

Matomo does not have GA4's `sessionDefaultChannelGroup == "Organic Search"`.
The scripts approximate "organic search" via the standard Matomo segment
`referrerType==search`. This includes all search-engine referrals but
excludes direct, social, website, and campaign traffic. Document this
when comparing against GA4 numbers: counts will not match exactly
because of segmentation differences, attribution windows, and bot
filtering rules.

## Output Format

Match existing claude-seo patterns:
- Tables for metrics with traffic-light ratings where applicable
- Scores as XX/100
- Priority: Critical > High > Medium > Low
- Note data source as "Matomo Reporting API (live)" to distinguish from
  GA4, CrUX, or static crawl analysis
- Include data freshness notes (Matomo archives data; the
  `VisitsSummary.get` per-day numbers may lag by 30-60 minutes; archived
  reports can take longer)

## Audit Persistence

If `output_dir` is provided by the audit orchestrator, write a partial findings
file after the first analysis pass and overwrite it with the complete findings
before finishing, so a turn-budget stop never loses completed work:
- `output_dir/findings/matomo.md`: organic trend, top landing pages,
  device / country split, referrer split, search-engine split, organic
  keywords with anonymized share noted
- Structured JSON-compatible findings for `audit-data.json` under the
  Matomo Analytics category; label as "Matomo Reporting API (live)"

## Error Handling

- If credentials are missing, report which env vars / config keys are
  unset and remind the user to run `python "<SEO_ROOT>/scripts/codex-seo.py" integration matomo`
- If HTTP 401/403, the token lacks view access for the site; verify the
  token scope in Matomo Administration -> Personal -> Security -> API
  Tokens. Never log the token
- If `result=error` from Matomo (e.g. invalid `idSite`), surface the
  message verbatim; do not guess
- If `anonymized_share_pct > 80%` for keywords, flag that organic keyword
  visibility is privacy-limited (normal on modern browsers) and
  recommend topical landing-page analysis as the substitute signal
- Never fail silently: always report what succeeded and what failed
