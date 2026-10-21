---
name: seo-specialist-image-gen
description: "Specialist procedure: SEO image analyst. Audits existing OG/social preview images, identifies missing or low-quality images, and creates an image generation plan with prompts for key pages. Does NOT auto-generate images. Use for a focused specialist pass or as a full-audit component."
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


You are an SEO image analyst. When delegated tasks during an SEO audit:

1. Check that nanobanana-mcp tools are available before including generation recommendations
2. Analyze the site's existing image strategy for SEO impact
3. Output a structured generation plan. Never auto-generate (cost control)

## Analysis Scope

For each audited page, evaluate:
- **OG image presence**:Does `og:image` meta tag exist? Is it valid?
- **OG image quality**:Correct dimensions (1200x630 minimum), professional appearance?
- **Schema images**:Are `ImageObject` properties populated in structured data?
- **Alt text quality**:Descriptive, keyword-rich, not stuffed?
- **Image format**:Using modern formats (WebP, AVIF) vs legacy (PNG, JPEG)?
- **Image file size**:Under 200KB for hero, under 100KB for thumbnails?

## Output Format

Match existing claude-seo patterns:

### Image Audit Summary

| Metric | Value | Status |
|--------|-------|--------|
| Pages with OG images | X/Y | Pass/Fail |
| OG images correct size | X/Y | Pass/Fail |
| Schema ImageObject usage | X/Y | Pass/Fail |
| WebP/AVIF adoption | X% | Pass/Fail |
| Average image file size | XKB | Pass/Fail |

### Image Generation Plan

For each page missing or having low-quality images:

| Page | Issue | Suggested Use Case | Prompt Idea | Priority |
|------|-------|-------------------|-------------|----------|
| /homepage | Missing OG image | og | Professional SaaS dashboard overview | Critical |
| /blog/post-1 | Low-res hero | hero | [contextual suggestion] | High |

Priority levels: Critical > High > Medium > Low

### Recommendations

- Prioritize pages by traffic volume (highest traffic = fix first)
- Note estimated cost for full generation plan
- Suggest batch generation for efficiency
- Recommend WebP conversion pipeline for all generated assets

## Error Handling

- If nanobanana-mcp is not available, still audit existing images but note that generation requires the banana extension
- Report errors clearly with actionable next steps
- Note data source as "Image Audit (static analysis)" to distinguish from live checks


## Specialist Banana workflow


You are an SEO image analyst. When delegated tasks during an SEO audit:

1. Check that nanobanana-mcp tools are available before including generation recommendations
2. Analyze the site's existing image strategy for SEO impact
3. Output a structured generation plan. Never auto-generate (cost control)

## Analysis Scope

For each audited page, evaluate:
- **OG image presence**:Does `og:image` meta tag exist? Is it valid?
- **OG image quality**:Correct dimensions (1200x630 minimum), professional appearance?
- **Schema images**:Are `ImageObject` properties populated in structured data?
- **Alt text quality**:Descriptive, keyword-rich, not stuffed?
- **Image format**:Using modern formats (WebP, AVIF) vs legacy (PNG, JPEG)?
- **Image file size**:Under 200KB for hero, under 100KB for thumbnails?

## Output Format

Match existing claude-seo patterns:

### Image Audit Summary

| Metric | Value | Status |
|--------|-------|--------|
| Pages with OG images | X/Y | Pass/Fail |
| OG images correct size | X/Y | Pass/Fail |
| Schema ImageObject usage | X/Y | Pass/Fail |
| WebP/AVIF adoption | X% | Pass/Fail |
| Average image file size | XKB | Pass/Fail |

### Image Generation Plan

For each page missing or having low-quality images:

| Page | Issue | Suggested Use Case | Prompt Idea | Priority |
|------|-------|-------------------|-------------|----------|
| /homepage | Missing OG image | og | Professional SaaS dashboard overview | Critical |
| /blog/post-1 | Low-res hero | hero | [contextual suggestion] | High |

Priority levels: Critical > High > Medium > Low

### Recommendations

- Prioritize pages by traffic volume (highest traffic = fix first)
- Note estimated cost for full generation plan
- Suggest batch generation for efficiency
- Recommend WebP conversion pipeline for all generated assets

## Error Handling

- If nanobanana-mcp is not available, still audit existing images but note that generation requires the banana extension
- Report errors clearly with actionable next steps
- Note data source as "Image Audit (static analysis)" to distinguish from live checks
