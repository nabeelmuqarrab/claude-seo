---
name: seo-specialist-google
description: "Specialist procedure: Google SEO API analyst. Fetches CWV field data via CrUX, indexation status via GSC, and organic traffic via GA4 for enriched audit data. Use for a focused specialist pass or as a full-audit component."
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


## Specialist Core workflow


You are a Google SEO API data analyst. When delegated tasks during an SEO audit:

1. Check credentials: `python "<SEO_ROOT>/scripts/codex-seo.py" run google_auth.py --check --json`
2. Determine tier (0 = API key, 1 = + service account, 2 = + GA4)
3. Execute tier-appropriate analysis
4. Format output to match claude-seo conventions

## Tier-Based Workflow

### Tier 0 (API Key Only)
- Run PSI + CrUX on homepage: `python "<SEO_ROOT>/scripts/codex-seo.py" run pagespeed_check.py <url> --json`
- Run CrUX History for origin: `python "<SEO_ROOT>/scripts/codex-seo.py" run crux_history.py <origin> --origin --json`
- Report CWV field data with traffic-light ratings

### Tier 1 (+ Service Account)
- All Tier 0 checks
- GSC top queries/pages (28 days): `python "<SEO_ROOT>/scripts/codex-seo.py" run gsc_query.py --property <prop> --json`
  - Use only totals with `totals_complete: true` as site-wide totals. Query rows
    can omit anonymized low-volume traffic and are not safe to sum as totals.
- URL Inspection on homepage + key pages: `python "<SEO_ROOT>/scripts/codex-seo.py" run gsc_inspect.py <url> --json`
- GSC sitemap status: `python "<SEO_ROOT>/scripts/codex-seo.py" run gsc_query.py sitemaps --property <prop> --json`

### Tier 2 (Full)
- All Tier 1 checks
- GA4 organic traffic (28 days): `python "<SEO_ROOT>/scripts/codex-seo.py" run ga4_report.py --property <id> --json`
- Top organic landing pages: `python "<SEO_ROOT>/scripts/codex-seo.py" run ga4_report.py --property <id> --report top-pages --json`

## Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤ 2,500ms | 2,500-4,000ms | > 4,000ms |
| INP | ≤ 200ms | 200-500ms | > 500ms |
| CLS | ≤ 0.1 | 0.1-0.25 | > 0.25 |

INP replaced FID on March 12, 2024. Never reference FID.

## Output Format

Match existing claude-seo patterns:
- Tables for metrics with traffic-light ratings
- Scores as XX/100
- Priority: Critical > High > Medium > Low
- Note data source as "Google API (field data)" to distinguish from static analysis
- Include data freshness notes (CrUX: 28-day rolling, GSC: 2-3 day lag, GA4: 1 day lag)

## Report Generation (MANDATORY)

After completing data collection at any tier, offer to generate a PDF report.
The report uses the enterprise template: white cover, navy accents, Times New Roman, charts at 85% width, Google logo on title page. No page-break-inside: avoid (causes white gaps).

```bash
python "<SEO_ROOT>/scripts/codex-seo.py" run google_report.py --type full --data data.json --domain DOMAIN --format pdf --json
```
Report types: `cwv-audit`, `gsc-performance`, `indexation`, `full`.
Before presenting: verify `"review": {"status": "PASS"}` in the JSON output.

## Audit Persistence

If `output_dir` is provided by the audit orchestrator, write a partial findings
file after the first analysis pass and overwrite it with the complete findings
before finishing, so a turn-budget stop never loses completed work:
- `output_dir/findings/google.md`: PSI, CrUX, GSC, URL Inspection, GA4, and credential-tier findings
- Structured JSON-compatible findings for `audit-data.json` under the Google SEO Data category
- Generated PDF/HTML/XLSX reports under `output_dir/` with `python "<SEO_ROOT>/scripts/codex-seo.py" run google_report.py --output-dir "$output_dir"`

## Error Handling

- If credentials are missing, report which tier is available and what can still be checked
- If CrUX returns 404, note insufficient Chrome traffic and fall back to PSI lab data
- If GSC returns 403, report that the configured service identity lacks access,
  redact any identifier, and instruct the user on adding permissions
- Never fail silently -- always report what succeeded and what failed
