#!/usr/bin/env python3
"""Generate the Codex skill surface from every upstream skill and specialist.

No network, shell, credential access, or deletion. Changed generated files are
retained under output/codex-build-history before replacement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if b'\0' in data:
        return data
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return data
    return data.replace(b'\r\n', b'\n')

def split_skill(text: str) -> tuple[str, str, str]:
    match = re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z', text, re.S)
    if not match:
        raise ValueError('Missing frontmatter')
    meta, body = match.groups()
    name = re.search(r'^name:\s*[\"\']?([a-z0-9-]+)', meta, re.M).group(1)
    desc = re.search(r'^description:\s*(.*?)(?=\n[^ \t\n]|\Z)', meta, re.M | re.S).group(1)
    raw_description = desc.lstrip('>|- ').strip()
    if raw_description.startswith('"') and raw_description.endswith('"'):
        try:
            raw_description = json.loads(raw_description)
        except ValueError:
            raw_description = raw_description.strip('"')
    elif raw_description.startswith("'") and raw_description.endswith("'"):
        raw_description = raw_description[1:-1].replace("''", "'")
    desc = ' '.join(raw_description.split())
    return name, desc, body

def adapt(body: str, prefix: str = '') -> str:
    for token in ('"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo"', '${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo', './scripts/claude-seo'):
        body = body.replace(token, 'python "<SEO_ROOT>/scripts/codex-seo.py"')
    body = body.replace('${CLAUDE_PLUGIN_ROOT}', '<SEO_ROOT>')
    body = body.replace('${CLAUDE_SKILL_DIR}', '<SKILL_ROOT>' + ('/' + prefix.rstrip('/') if prefix else ''))
    body = re.sub(r'(?<![\w-])/seo\b', '$seo', body)
    body = body.replace('Claude Code', 'the agent host').replace('Claude reads', 'the model reads')
    body = re.sub(r'(?:\./)?extensions/([a-z-]+)/install\.(?:sh|ps1)',
                  lambda m: 'python "<SEO_ROOT>/scripts/codex-seo.py" integration ' + m[1], body)
    if prefix:
        body = re.sub(r'(?<![\w/-])(references|templates|assets|scripts)/', prefix + r'\1/', body)
    return body.rstrip() + '\n'

BOUNDARY = '''## Codex execution

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

'''

EXTRAS = {
 'seo-setup': ('Set up the isolated Codex SEO Python runtime or inspect its readiness when setup or dependency repair is requested.',
    'Run `python "<SEO_ROOT>/scripts/codex-seo.py" doctor --json` first. For explicitly requested setup, run `python "<SEO_ROOT>/scripts/codex-seo.py" setup`. Use `--skip-browser` only when the requested work does not need screenshots or rendered pages. Setup retains every environment version; it never edits the global Python or Claude configuration. Report core/browser readiness separately.'),
 'seo-doctor': ('Diagnose Codex SEO runtime, module coverage, hooks and optional integrations without spending API credits.',
    'Run `python "<SEO_ROOT>/scripts/codex-seo.py" doctor --json` and `python "<SEO_ROOT>/scripts/codex-seo.py" catalog`. Explain missing dependencies without installing anything unless setup is requested. For provider details use the integration command. Hook trust is owned by Codex; never bypass it.'),
 'seo-spend': ('Review the existing SEO API spend ledger and budget settings without starting paid research.',
    'Run `python "<SEO_ROOT>/scripts/codex-seo.py" run dataforseo_costs.py summary`. Label missing or incomplete ledger data; no spending is implied by viewing the ledger. Estimates are not invoices or permission for paid calls.'),
 'seo-cockpit': ('Create a portable local SEO dashboard with SVG charts from saved audit, GSC, performance, maps and budget JSON evidence.',
    'Run `python "<SEO_ROOT>/scripts/codex-seo.py" cockpit --input ABSOLUTE_JSON_PATH`. Supply an audit/report JSON object or an object of named panels. Each panel retains its source/date and renders its data; missing values stay missing. The dashboard is a local HTML artifact, not a hosted admin panel. Fetch fresh data through the relevant skills only when requested, then supply it as input. Use $seo-spend and $seo-doctor for native diagnostics. Claude terminal mods and token-free slash commands remain available in the original Claude companion; Codex uses regular skill turns and the exported dashboard.'),
}

def source_entries(root: Path):
    entries = []
    for path in sorted((root / 'skills').glob('*/SKILL.md')):
        entries.append((path, 'core', False))
    for path in sorted((root / 'extensions').glob('*/skills/*/SKILL.md')):
        entries.append((path, 'extension-' + path.relative_to(root).parts[1], False))
    for path in sorted((root / 'agents').glob('*.md')):
        entries.append((path, 'specialist-core', True))
    for path in sorted((root / 'extensions').glob('*/agents/*.md')):
        entries.append((path, 'specialist-' + path.relative_to(root).parts[1], True))
    return entries

def generate(root: Path = ROOT, destination: Path | None = None) -> dict:
    destination = destination or root / 'codex' / 'skills'
    entries = source_entries(root)
    grouped = {}
    for path, origin, specialist in entries:
        name, desc, body = split_skill(path.read_text(encoding='utf-8'))
        target = 'seo-specialist-' + name.removeprefix('seo-') if specialist else name
        grouped.setdefault(target, []).append((path, origin, desc, body))
    planned = {}
    coverage = []
    for name, variants in sorted(grouped.items()):
        # Core stays primary; extension-only resources live beside their variant.
        body = BOUNDARY
        if name == 'seo-page':
            body += '''## Saved HTML and offline review

For supplied HTML, run `python "<SEO_ROOT>/scripts/codex-seo.py" run parse_html.py ABSOLUTE_HTML_PATH --url PAGE_URL --json`. A file argument uses
local input; do not fetch the page or discover its sitemap unless network review
is requested. Read a supplied sitemap locally with a safe XML parser. Compare
its listed URLs with the canonical/robots evidence, without claiming live status,
indexing or link availability from saved files. Read the shared
[quality reference](../seo/references/quality-gates.md) as context rather than
word-count quotas. Inspect viewport, layout hints and whether the primary task
(generate/copy/etc.) has an implementation; source inspection cannot prove it
works on a real phone. A one-page metadata result does not establish site-wide
quality. Use the evidence/status output when no validated scoring rubric exists.

'''
        for i, (path, origin, desc, original) in enumerate(variants):
            prefix = '' if i == 0 else '_variants/' + origin + '/'
            body += '\n## ' + origin.replace('-', ' ').title() + ' workflow\n\n' + adapt(original, prefix) + '\n'
            if path.name == 'SKILL.md':
                for asset in sorted(path.parent.rglob('*')):
                    if asset.is_file() and asset.name != 'SKILL.md':
                        planned[Path(name) / prefix / asset.relative_to(path.parent)] = canonical_bytes(asset)
            coverage.append({'source': path.relative_to(root).as_posix(), 'skill': name,
                             'source_sha256': hashlib.sha256(canonical_bytes(path)).hexdigest(),
                             'adapted_body_sha256': hashlib.sha256(adapt(original, prefix).encode()).hexdigest()})
        desc = variants[0][2]
        if name.startswith('seo-specialist-'):
            desc = 'Specialist procedure: ' + desc + ' Use for a focused specialist pass or as a full-audit component.'
        planned[Path(name) / 'SKILL.md'] = ('---\nname: ' + name + '\ndescription: ' + json.dumps(desc[:1024]) + '\n---\n\n' + body.rstrip() + '\n').encode()
    for name, (desc, body) in EXTRAS.items():
        planned[Path(name) / 'SKILL.md'] = ('---\nname: ' + name + '\ndescription: ' + json.dumps(desc) + '\n---\n\n' + BOUNDARY + body + '\n').encode()
    changed = []
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for rel, data in planned.items():
        path = destination / rel
        if path.is_file() and path.read_bytes() == data:
            continue
        if path.exists():
            history = root / 'output/codex-build-history' / stamp / rel
            history.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, history)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        changed.append(rel.as_posix())
    manifest = {'schema': 1, 'source_workflows': len(entries), 'generated_skills': len(grouped) + len(EXTRAS),
                'coverage': coverage, 'files': {p.as_posix(): hashlib.sha256(b).hexdigest() for p, b in sorted(planned.items())}}
    out = destination.parent / 'coverage.json'
    encoded = (json.dumps(manifest, indent=2) + '\n').encode()
    if not out.exists() or out.read_bytes() != encoded:
        if out.exists():
            old = root / 'output/codex-build-history' / stamp / 'coverage.json'
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, old)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(encoded)
    return {'source_workflows': len(entries), 'generated_skills': manifest['generated_skills'], 'changed_files': len(changed)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(destination=args.output)))
