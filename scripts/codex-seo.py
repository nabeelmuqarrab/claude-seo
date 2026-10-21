#!/usr/bin/env python3
"""Native cross-platform Codex entry point; no Bash or global installation."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import runtime as legacy

INTEGRATIONS = {
 'ahrefs': {'type': 'stdio', 'command': 'npx', 'args': ['--yes', '--package=@ahrefs/mcp@0.0.11', 'mcp'], 'env_vars': ['AHREFS_API_TOKEN']},
 'dataforseo': {'type': 'stdio', 'command': 'npx', 'args': ['-y', 'dataforseo-mcp-server@2.8.10'], 'env_vars': ['DATAFORSEO_USERNAME', 'DATAFORSEO_PASSWORD', 'ENABLED_MODULES']},
 'firecrawl': {'type': 'stdio', 'command': 'npx', 'args': ['-y', 'firecrawl-mcp@3.11.0'], 'env_vars': ['FIRECRAWL_API_KEY']},
 'banana': {'type': 'environment', 'env_vars': ['GOOGLE_AI_API_KEY', 'NANOBANANA_MODEL'], 'note': 'Use the retained generate.py/edit.py Python fallbacks via run --extension banana; connect an image MCP separately if desired.'},
 'bing-webmaster': {'type': 'environment', 'env_vars': ['BING_WEBMASTER_API_KEY', 'INDEXNOW_KEY', 'INDEXNOW_KEY_LOCATION']},
 'matomo': {'type': 'environment', 'env_vars': ['MATOMO_URL', 'MATOMO_API_TOKEN', 'MATOMO_SITE_ID']},
 'profound': {'type': 'environment', 'env_vars': ['PROFOUND_API_KEY']},
 'seranking': {'type': 'environment', 'env_vars': ['SERANKING_API_KEY']},
 'unlighthouse': {'type': 'local-node', 'note': 'Use run unlighthouse_run.py with Node/npm available; the pinned Node tool is downloaded only on explicit invocation.'},
}

def data_dir() -> Path:
    raw = os.environ.get('CODEX_SEO_DATA_DIR') or os.environ.get('PLUGIN_DATA') or os.environ.get('CLAUDE_PLUGIN_DATA')
    path = Path(raw).expanduser().resolve() if raw else Path.home() / '.local/share/codex-seo'
    if path == Path(path.anchor) or path == Path.home():
        raise ValueError('Use a dedicated runtime data directory')
    return path

def new_dir(parent: Path, label: str) -> Path:
    path = parent / (label + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    path.mkdir(parents=True, exist_ok=False)
    return path

def write_json(path: Path, data: object):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + '.previous-' + uuid.uuid4().hex))
    staged = path.with_name(path.name + '.next-' + uuid.uuid4().hex)
    with staged.open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    os.replace(staged, path)

def long_path(path: Path) -> str:
    value = str(path.resolve())
    if os.name == 'nt' and not value.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value
    return value

def ordinary_path(path: Path) -> Path:
    value = str(path)
    if value.startswith('\\\\?\\UNC\\'):
        value = '\\\\' + value[8:]
    elif value.startswith('\\\\?\\'):
        value = value[4:]
    return Path(value).resolve()

def load_state() -> dict:
    try:
        state = json.loads((data_dir() / 'codex-runtime.json').read_text(encoding='utf-8'))
        if not isinstance(state, dict):
            return {}
        python = ordinary_path(Path(state['python']))
        if not python.is_relative_to((data_dir() / 'runtimes').resolve()):
            return {}
        return state
    except (OSError, ValueError, KeyError, TypeError):
        return {}

def req_hash() -> str:
    return hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest()

def executable() -> str | None:
    # Explicit venv selection enables isolated tests and existing managed installs.
    override = os.environ.get('CODEX_SEO_PYTHON')
    if override and Path(override).is_file():
        return str(Path(override).resolve())
    state = load_state()
    if state.get('requirements_sha256') == req_hash() and Path(state.get('python', '')).is_file():
        return state['python']
    status = legacy._status(ROOT)
    if status['ready']:
        return str(status['python_path'])
    return None

def setup(skip_browser: bool) -> int:
    if sys.version_info < (3, 11):
        raise ValueError('Codex setup requires Python 3.11 or newer')
    version = new_dir(data_dir() / 'runtimes', 'v')
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(version / 'browsers')
    log = version / 'setup.log'
    python = Path(long_path(legacy._venv_python(version / '.venv')))
    commands = [[sys.executable, '-m', 'venv', long_path(version / '.venv')],
                [str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                 '--report', str(version / 'resolved-dependencies.json'), '-r', str(ROOT / 'requirements.txt')]]
    if not skip_browser:
        commands.append([str(python), '-m', 'playwright', 'install', 'chromium'])
    with log.open('x', encoding='utf-8') as output:
        for command in commands:
            process = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            output.write(legacy._redact(process.stdout or ''))
            output.flush()
            if process.returncode:
                print(json.dumps({'ready': False, 'stage': command[2:4], 'evidence': str(version)}))
                return process.returncode
    state = {'schema': 1, 'python': str(python), 'requirements_sha256': req_hash(),
             'browser_ready': not skip_browser, 'browser_path': env['PLAYWRIGHT_BROWSERS_PATH']}
    write_json(data_dir() / 'codex-runtime.json', state)
    print(json.dumps({'ready': True, 'browser_ready': not skip_browser, 'evidence': str(version)}))
    return 0

def doctor() -> dict:
    state = load_state()
    return {'ready': bool(executable()), 'browser_ready': bool(state.get('browser_ready')),
            'harness': 'codex', 'core_scripts': len(list((ROOT / 'scripts').glob('*.py'))),
            'legacy_scripts_preserved': len(legacy.ALLOWED_CORE_SCRIPTS), 'extensions': sorted(INTEGRATIONS),
            'setup_required': not bool(executable()), 'hook_trust': 'Managed by Codex; never bypass trust',
            'note': 'No credential checks, dependency installation, or API calls were performed.'}

def integration(name: str) -> dict:
    if name not in INTEGRATIONS:
        raise ValueError('Unknown integration: ' + name)
    result = dict(INTEGRATIONS[name])
    result.update({'provider': name, 'configured_automatically': False,
                   'setup': 'Connect this provider in Codex MCP settings using the command and arguments below. Keep secrets in environment variables, never in source or command arguments. Do not run the Claude installers.',
                   'scripts': [p.name for p in sorted((ROOT / 'extensions' / name / 'scripts').glob('*.py'))],
                   'live_tested': False, 'cost': 'Check current provider terms; connecting does not authorize paid calls.'})
    if result['type'] == 'stdio':
        result['codex_toml_template'] = ('[mcp_servers.' + name.replace('-', '_') + ']\ncommand = ' + json.dumps(result['command']) + '\nargs = ' + json.dumps(result['args']) + '\nenv_vars = ' + json.dumps(result['env_vars']) + '\n')
    return result

def run(script: str, args: list[str], extension: str | None) -> int:
    if extension and script == 'setup_mcp.py':
        print(json.dumps(integration(extension), indent=2))
        return 0
    path = legacy._resolve_script(ROOT, script, extension)
    if script == 'google_auth.py' and '--auth' in args and extension is None:
        path = ROOT / 'scripts/codex_oauth.py'
    python = executable()
    if not python:
        print('Runtime not ready. Run the explicitly requested $seo-setup first.', file=sys.stderr)
        return 3
    source_cwd = Path.cwd()
    # Input files remain resolvable after reports move to a unique working folder.
    resolved_args = []
    for arg in args:
        try:
            is_file = not arg.startswith('-') and Path(arg).is_file()
        except (OSError, ValueError):
            is_file = False
        resolved_args.append(str(Path(arg).resolve()) if is_file else arg)
    outputs = []
    output_flags = {'--output', '-o', '--output-dir'}
    for at, arg in enumerate(args):
        if arg in output_flags and at + 1 < len(args):
            outputs.append(args[at + 1])
        elif any(arg.startswith(flag + '=') for flag in output_flags):
            outputs.append(arg.split('=', 1)[1])
    if any((source_cwd / value).exists() for value in outputs):
        raise ValueError('Output already exists; choose a new versioned output path')
    if script == 'content_humanize.py' and '--strip-invisible' not in args:
        resolved_args.append('--preserve-unicode')
    folder = new_dir(data_dir() / 'runs', script.removesuffix('.py'))
    for value in outputs:
        target = Path(value)
        (target if target.is_absolute() else folder / target).parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1',
                'CLAUDE_SEO_PRESERVE_ARTIFACTS': '1', 'CLAUDE_SEO_RUN_DIR': str(folder),
                'CODEX_SEO_CACHE_DIR': str(data_dir() / 'cache')})
    state = load_state()
    if state.get('browser_path'):
        env['PLAYWRIGHT_BROWSERS_PATH'] = state['browser_path']
    process = subprocess.run([python, str(path), *resolved_args], cwd=folder, env=env)
    write_json(folder / 'run-receipt.json', {'script': script, 'extension': extension,
               'returncode': process.returncode, 'finished_at': datetime.now(timezone.utc).isoformat(),
               'arguments_recorded': False, 'stdout_logged': False, 'reason': 'Avoid logging credentials and private query/input content'})
    return process.returncode

def cockpit(input_file: Path) -> Path:
    data = json.loads(input_file.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Cockpit input must be a JSON object')
    folder = new_dir(data_dir() / 'runs', 'cockpit')
    panels = []
    for title, values in data.items():
        # All JSON evidence is retained as visible text, never executable markup.
        text = html.escape(json.dumps(values, indent=2, ensure_ascii=False))
        chart = evidence_chart(values, str(title))
        panels.append('<section><h2>' + html.escape(str(title)) + '</h2>' + chart + '<details><summary>All source data</summary><pre>' + text + '</pre></details></section>')
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:"><title>SEO evidence cockpit</title><style>body{max-width:75rem;margin:2rem auto;padding:1rem;font:1rem/1.6 system-ui;color:#162e49;background:#f5f7fa}section{background:white;border:1px solid #ccd6df;border-radius:.7rem;padding:1rem;margin:1rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}svg{width:100%;max-width:44rem;height:auto}h1{line-height:1.2}summary{cursor:pointer}svg text{font:12px system-ui;fill:#162e49}</style><h1>SEO evidence cockpit</h1><p>Saved evidence only. No background API calls. Charts use supplied numeric observations; expand each panel for complete source data and dates.</p>' + ''.join(panels) + '</html>'
    target = folder / 'cockpit.html'
    target.write_text(page, encoding='utf-8')
    write_json(folder / 'evidence.json', data)
    return target

def evidence_chart(values: object, title: str) -> str:
    """Render comparable observed values only; never invent a trend or score."""
    rows = values.get('rows') if isinstance(values, dict) else values
    if isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows):
        metric = next((key for key in ('impressions', 'clicks', 'sessions', 'cost', 'score')
                       if all(isinstance(r.get(key), (int, float)) for r in rows)), None)
        points = [(str(r.get('date') or r.get('query') or r.get('page') or i + 1), r[metric])
                  for i, r in enumerate(rows[:12])] if metric else []
    elif isinstance(values, dict):
        # Scalar metrics have different units; use labelled values without bars.
        metrics = [(str(k), v) for k, v in values.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if metrics:
            return '<dl>' + ''.join('<dt>' + html.escape(k) + '</dt><dd>' + html.escape(str(v)) + '</dd>' for k, v in metrics) + '</dl>'
        return '<p>No comparable numeric series supplied.</p>'
    else:
        points, metric = [], None
    import math
    points = [(label, value) for label, value in points if math.isfinite(value) and value >= 0]
    if not points:
        return '<p>No comparable numeric series supplied.</p>'
    largest = max(v for _, v in points) or 1
    height = 36 * len(points) + 40
    bars = []
    for i, (label, value) in enumerate(points):
        y = 35 + i * 36
        bars.append('<text x="0" y="' + str(y + 14) + '">' + html.escape(label[:24]) + '</text><rect x="180" y="' + str(y) + '" width="' + str(round(value / largest * 350, 2)) + '" height="22" fill="#287b9e"/><text x="540" y="' + str(y + 14) + '">' + html.escape(str(value)) + '</text>')
    return '<svg viewBox="0 0 650 ' + str(height) + '" role="img" aria-label="' + html.escape(title + ': ' + str(metric), quote=True) + '"><title>' + html.escape(str(metric) + ' (first 12 supplied rows)') + '</title>' + ''.join(bars) + '</svg>'

def main(argv=None) -> int:
    legacy._configure_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='cmd', required=True)
    setup_parser = sub.add_parser('setup')
    setup_parser.add_argument('--skip-browser', action='store_true')
    sub.add_parser('doctor').add_argument('--json', action='store_true')
    sub.add_parser('catalog')
    sub.add_parser('integration').add_argument('provider', choices=sorted(INTEGRATIONS))
    approval = sub.add_parser('approve', help='Record a one-use grant only after explicit user authorization')
    approval.add_argument('--request', required=True)
    approval.add_argument('--max-usd', required=True, type=float)
    approval.add_argument('--expires-min', type=int, default=10)
    run_parser = sub.add_parser('run')
    run_parser.add_argument('--extension')
    run_parser.add_argument('script')
    run_parser.add_argument('args', nargs=argparse.REMAINDER)
    sub.add_parser('cockpit').add_argument('--input', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.cmd == 'setup':
            return setup(args.skip_browser)
        if args.cmd == 'doctor':
            result = doctor()
        elif args.cmd == 'catalog':
            result = json.loads((ROOT / 'codex/coverage.json').read_text(encoding='utf-8'))
        elif args.cmd == 'integration':
            result = integration(args.provider)
        elif args.cmd == 'approve':
            sys.path.insert(0, str(ROOT / 'codex/hooks'))
            import paid_guard
            result = paid_guard.approve(args.request, args.max_usd, args.expires_min)
        elif args.cmd == 'cockpit':
            result = {'output': str(cockpit(args.input.resolve()))}
        else:
            return run(args.script, args.args, args.extension)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(legacy._redact(str(exc)), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
