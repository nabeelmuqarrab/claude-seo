"""Read Codex stdin events; validate changed files without executing tool input."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 2 * 1024 * 1024
SUFFIXES = {'.html', '.htm', '.php', '.jsx', '.tsx', '.vue', '.svelte', '.ejs', '.json', '.jsonld'}

def changed_paths(event: dict) -> list[Path]:
    cwd = Path(event.get('cwd') or '.').resolve()
    tool = event.get('tool_input') or {}
    if not isinstance(tool, dict):
        tool = {'command': tool} if isinstance(tool, str) else {}
    raw = []
    if isinstance(tool.get('file_path'), str):
        raw.append(tool['file_path'])
    command = tool.get('command') or tool.get('patch') or ''
    if isinstance(command, str):
        raw.extend(re.findall(r'^\*\*\* (?:Add File|Update File|Move to): (.+)$', command, re.M))
    paths = []
    for value in raw:
        try:
            path = (cwd / value).resolve()
            if path.is_relative_to(cwd) and path.is_file() and path.suffix.lower() in SUFFIXES:
                if path not in paths:
                    paths.append(path)
        except (OSError, ValueError):
            pass
    return paths

def inspect_event(event: dict) -> dict:
    spec = importlib.util.spec_from_file_location('seo_schema_lint', ROOT / 'hooks/validate-schema.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    findings, skipped = [], []
    for path in changed_paths(event):
        if path.stat().st_size > MAX_BYTES:
            skipped.append(path.name)
            continue
        content = path.read_text(encoding='utf-8', errors='replace')
        if path.suffix.lower() in {'.json', '.jsonld'}:
            try:
                obj = json.loads(content)
            except ValueError:
                obj = None
            # General JSON data/config is not necessarily structured data.
            is_schema = path.suffix.lower() == '.jsonld' or (isinstance(obj, dict) and '@context' in obj)
            is_schema = is_schema or (isinstance(obj, list) and any(isinstance(v, dict) and '@context' in v for v in obj))
            if not is_schema:
                continue
            content = '<script type="application/ld+json">' + content + '</script>'
        findings.extend(path.name + ': ' + f for f in validator.validate_jsonld(content, str(path)))
    return {'findings': findings, 'oversized_files_skipped': skipped}

def main() -> int:
    raw = sys.stdin.read(MAX_BYTES + 1)
    if len(raw.encode('utf-8')) > MAX_BYTES:
        print('SEO hook event exceeded the size limit; run the standalone schema check.', file=sys.stderr)
        return 2
    try:
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError('event must be an object')
        result = inspect_event(event)
    except (ValueError, OSError) as exc:
        print('SEO schema hook could not inspect the event: ' + type(exc).__name__, file=sys.stderr)
        return 2
    if result['findings'] or result['oversized_files_skipped']:
        reason = '\n'.join(result['findings'])
        if result['oversized_files_skipped']:
            reason += '\nLarge files skipped: ' + ', '.join(result['oversized_files_skipped'])
        print(json.dumps({'decision': 'block', 'reason': reason + '\nPost-edit feedback only; the file edit has already happened.'}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
