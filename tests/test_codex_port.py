"""Functional compatibility checks: all capabilities stay mapped, no live APIs."""
from __future__ import annotations
import hashlib
from html import escape
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_codex
import content_humanize
import google_report
import parse_html

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

runner = load_module('codex_runner', ROOT / 'scripts/codex-seo.py')
schema = load_module('codex_schema', ROOT / 'codex/hooks/schema_hook.py')
paid = load_module('codex_paid', ROOT / 'codex/hooks/paid_guard.py')

def test_every_upstream_workflow_retains_full_adapted_body_and_assets():
    coverage = json.loads((ROOT / 'codex/coverage.json').read_text(encoding='utf-8'))
    sources = {p.relative_to(ROOT).as_posix() for p, _, _ in build_codex.source_entries(ROOT)}
    assert {item['source'] for item in coverage['coverage']} == sources
    grouped = {}
    for item in coverage['coverage']:
        grouped.setdefault(item['skill'], []).append(item)
    for name, variants in grouped.items():
        generated = (ROOT / 'codex/skills' / name / 'SKILL.md').read_text(encoding='utf-8')
        for i, item in enumerate(variants):
            path = ROOT / item['source']
            _, _, body = build_codex.split_skill(path.read_text(encoding='utf-8'))
            # Find the same variant origin as the generator, rather than dropping mirrors.
            origin = next(origin for p, origin, _ in build_codex.source_entries(ROOT) if p == path)
            prefix = '' if i == 0 else '_variants/' + origin + '/'
            assert build_codex.adapt(body, prefix) in generated
            assert hashlib.sha256(build_codex.canonical_bytes(path)).hexdigest() == item['source_sha256']
    for rel, digest in coverage['files'].items():
        assert hashlib.sha256((ROOT / 'codex/skills' / rel).read_bytes()).hexdigest() == digest

def test_generator_is_deterministic_and_keeps_prior_changed_files(tmp_path):
    destination = tmp_path / 'generated/skills'
    first = build_codex.generate(destination=destination)
    before = (destination.parent / 'coverage.json').read_bytes()
    second = build_codex.generate(destination=destination)
    assert first['source_workflows'] == len(build_codex.source_entries(ROOT))
    assert second['changed_files'] == 0
    assert (destination.parent / 'coverage.json').read_bytes() == before

def test_canonical_hashes_survive_windows_line_endings_without_changing_unicode(tmp_path):
    lf, crlf = tmp_path / 'lf.md', tmp_path / 'crlf.md'
    text = 'Nama A\u3164B\nCopy A\u00a0B\n'
    lf.write_bytes(text.encode())
    crlf.write_bytes(text.replace('\n', '\r\n').encode())
    assert build_codex.canonical_bytes(lf) == build_codex.canonical_bytes(crlf) == text.encode()
    binary = tmp_path / 'image.bin'
    binary.write_bytes(b'\0\r\n\xff')
    assert build_codex.canonical_bytes(binary) == b'\0\r\n\xff'

def test_generated_skill_metadata_is_valid_codex_yaml():
    for path in (ROOT / 'codex/skills').glob('*/SKILL.md'):
        text = path.read_text(encoding='utf-8')
        front = yaml.safe_load(text.split('---', 2)[1])
        assert front['name'] == path.parent.name
        assert isinstance(front['description'], str) and 0 < len(front['description']) <= 1024
        assert not {'model', 'tools', 'maxTurns', 'user-invocable', 'argument-hint'} & front.keys()
        assert 'python "<SEO_ROOT>/scripts/codex-seo.py"' in text

def test_all_core_executors_and_extension_scripts_remain_dispatchable():
    for script in runner.legacy.ALLOWED_CORE_SCRIPTS:
        assert runner.legacy._resolve_script(ROOT, script, None).is_file()
    for folder in (ROOT / 'extensions').iterdir():
        for path in (folder / 'scripts').glob('*.py'):
            assert runner.legacy._resolve_script(ROOT, path.name, folder.name) == path.resolve()

@pytest.mark.parametrize('name', list(runner.INTEGRATIONS))
def test_provider_setup_does_not_write_legacy_config(name, tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    result = runner.integration(name)
    assert result['provider'] == name and result['configured_automatically'] is False
    assert not (tmp_path / 'data').exists()

def test_runner_rejects_traversal_before_starting_child(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    with pytest.raises(ValueError):
        runner.run('../google_auth.py', [], None)
    assert not (tmp_path / 'data').exists()

def test_runner_keeps_relative_input_and_preserves_unicode(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_PYTHON', sys.executable)
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.chdir(tmp_path)
    text = 'A\u3164B A\u00a0B A\u200bB'
    (tmp_path / 'draft.txt').write_text(text, encoding='utf-8')
    rc = runner.run('content_humanize.py', ['draft.txt', '-o', 'cleaned.txt'], None)
    assert rc == 0
    outputs = list((tmp_path / 'data/runs').glob('*/cleaned.txt'))
    assert len(outputs) == 1 and outputs[0].read_text(encoding='utf-8') == text
    assert runner.run('content_humanize.py', ['draft.txt', '-o', 'cleaned.txt'], None) == 0
    assert len(list((tmp_path / 'data/runs').glob('*/cleaned.txt'))) == 2
    receipts = list((tmp_path / 'data/runs').glob('*/run-receipt.json'))
    assert len(receipts) == 2 and all(json.loads(p.read_text())['arguments_recorded'] is False for p in receipts)

def test_runner_refuses_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('CODEX_SEO_PYTHON', sys.executable)
    (tmp_path / 'saved.txt').write_text('keep')
    with pytest.raises(ValueError, match='already exists'):
        runner.run('content_humanize.py', ['-', '-o', 'saved.txt'], None)
    assert (tmp_path / 'saved.txt').read_text() == 'keep'
    with pytest.raises(ValueError, match='already exists'):
        runner.run('content_humanize.py', ['-', '--output=saved.txt'], None)

def test_legacy_cleanup_behavior_is_retained_as_explicit_option():
    value = 'A\u3164B A\u00a0B'
    assert content_humanize.humanize(value)['cleaned'] == 'AB A B'
    assert content_humanize.humanize(value, preserve_unicode=True)['cleaned'] == value

def test_report_queries_are_escaped_in_detail_and_quick_win_tables():
    query = '<img src=x onerror="window.review=1">'
    data = {'rows': [{'query': query, 'clicks': 0, 'impressions': 1, 'ctr': 0, 'position': 8}],
            'quick_wins': [{'keys': [query], 'position': 8, 'impressions': 60, 'clicks': 0}]}
    output, _ = google_report._build_gsc_section(data, {})
    assert query not in output and escape(query) in output

def test_schema_hook_consumes_native_patch_and_rejects_external_paths(tmp_path):
    page = tmp_path / 'page.html'
    page.write_text('<script type="application/ld+json">{bad}</script>')
    event = {'cwd': str(tmp_path), 'tool_name': 'apply_patch',
             'tool_input': {'command': '*** Begin Patch\n*** Update File: page.html\n*** End Patch'}}
    assert schema.inspect_event(event)['findings']
    external = tmp_path.parent / 'external.html'
    event['tool_input']['command'] = '*** Update File: ' + str(external)
    assert schema.changed_paths(event) == []

def test_valid_schema_passes_and_general_json_is_not_a_schema(tmp_path):
    page = tmp_path / 'page.html'
    page.write_text('<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Test","url":"https://example.com"}</script>')
    event = {'cwd': str(tmp_path), 'tool_input': {'file_path': str(page)}}
    assert schema.inspect_event(event)['findings'] == []

def test_invalid_jsonld_file_and_array_schema_are_inspected(tmp_path):
    path = tmp_path / 'schema.jsonld'
    path.write_text('{bad}')
    event = {'cwd': str(tmp_path), 'tool_input': {'file_path': str(path)}}
    assert schema.inspect_event(event)['findings']
    path.write_text('[{"@context":"https://schema.org","@type":"WebSite"}]')
    assert schema.inspect_event(event)['findings'] == []
    config = tmp_path / 'config.json'
    config.write_text('{"items": [1,2]}')
    event['tool_input']['file_path'] = str(config)
    assert schema.inspect_event(event)['findings'] == []

def test_paid_guard_is_fail_closed_and_exact_input_grant_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    event = {'tool_name': 'mcp__dataforseo__serp_organic_live_advanced', 'tool_input': {'keyword': 'nama ff'}}
    result = paid.evaluate(event)
    assert result['hookSpecificOutput']['permissionDecision'] == 'deny'
    key = paid.identity(event)
    paid.approve(key, 0.1)
    changed = {**event, 'tool_input': {'keyword': 'other'}}
    assert paid.evaluate(changed)['hookSpecificOutput']['permissionDecision'] == 'deny'
    assert paid.evaluate(event) == {}
    assert paid.evaluate(event)['hookSpecificOutput']['permissionDecision'] == 'deny'
    assert 'nama ff' not in (paid.storage() / 'requests' / (key + '.json')).read_text()

def test_paid_guard_does_not_block_free_reference_or_gsc_calls(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    assert paid.evaluate({'tool_name': 'mcp__dataforseo__serp_locations', 'tool_input': {}}) == {}
    assert paid.evaluate({'tool_name': 'mcp__gsc__query', 'tool_input': {}}) == {}
    assert not (tmp_path / 'data').exists()

def test_paid_shell_chaining_does_not_hide_a_billable_call(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    event = {'tool_name': 'Bash', 'tool_input': {'command': 'python dataforseo_costs.py check x && python dataforseo_merchant.py search x'}}
    assert paid.evaluate(event)['hookSpecificOutput']['permissionDecision'] == 'deny'

def test_expired_paid_grant_is_not_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    event = {'tool_name': 'mcp__ahrefs__backlinks', 'tool_input': {}}
    paid.evaluate(event)
    key = paid.identity(event)
    paid.approve(key, 1)
    grant = next((paid.storage() / 'grants').glob('*.json'))
    data = json.loads(grant.read_text())
    data['expires_at'] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    grant.write_text(json.dumps(data))
    assert paid.evaluate(event)['hookSpecificOutput']['permissionDecision'] == 'deny'

def test_cockpit_is_local_escaped_and_preserves_all_panels(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    input_file = tmp_path / 'evidence.json'
    data = {'GSC': {'query': '<script>bad()</script>', 'impressions': 10}, 'maps': {'status': 'not measured'}}
    input_file.write_text(json.dumps(data))
    target = runner.cockpit(input_file)
    page = target.read_text(encoding='utf-8')
    assert '<script>bad()' not in page and '&lt;script&gt;' in page
    assert json.loads((target.parent / 'evidence.json').read_text()) == data
    assert 'default-src' in page and 'No background API calls' in page

def test_cockpit_svg_charts_use_observed_series_and_escape_labels():
    result = runner.evidence_chart({'rows': [{'query': '<unsafe>', 'impressions': 4}, {'query': 'safe', 'impressions': 8}]}, 'Search')
    assert '<svg' in result and '&lt;unsafe&gt;' in result and '<unsafe>' not in result
    assert 'width="175.0"' in result and 'width="350.0"' in result
    assert '<svg' not in runner.evidence_chart({'status': 'not measured'}, 'Search')

def test_visible_word_count_excludes_the_head_title():
    parsed = parse_html.parse_html('<html><head><title>Head only words</title></head><body><p>Visible body</p></body></html>', 'https://example.com/')
    assert parsed['title'] == 'Head only words'
    assert parsed['word_count'] == 2

def test_native_oauth_uses_library_pkce_and_minimum_scopes(tmp_path, monkeypatch):
    library = pytest.importorskip('google_auth_oauthlib.flow')
    import google_auth
    native = load_module('native_oauth', ROOT / 'scripts/codex_oauth.py')
    client = {'client_id': 'test-client', 'client_secret': 'not-a-real-secret',
              'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token'}
    path = tmp_path / 'client.json'
    path.write_text(json.dumps({'installed': client}))
    captured = {}
    class Flow:
        def run_local_server(self, **kwargs):
            captured['local_server'] = kwargs
            from types import SimpleNamespace
            return SimpleNamespace(token='test-token', refresh_token='test-refresh', granted_scopes=None,
                                   expiry=datetime.now(timezone.utc) + timedelta(hours=1))
    def factory(config, **kwargs):
        captured['flow'] = kwargs
        return Flow()
    monkeypatch.setattr(library.InstalledAppFlow, 'from_client_config', factory)
    monkeypatch.setattr(native, 'protected_write', lambda path, token: captured.update({'token': token}))
    monkeypatch.setattr(google_auth, '_persist_oauth_client_path', lambda path: None)
    native.login(path, ['gsc', 'ga4'], False)
    assert captured['flow']['autogenerate_code_verifier'] is True
    assert all(scope.endswith('readonly') for scope in captured['flow']['scopes'])
    assert captured['local_server']['timeout_seconds'] == 300
    assert captured['local_server']['open_browser'] is False
    assert 'client_secret' not in captured['token']

def test_native_oauth_never_writes_secrets_when_permission_setup_fails(tmp_path, monkeypatch):
    native = load_module('native_oauth_permission', ROOT / 'scripts/codex_oauth.py')
    def denied(path):
        raise PermissionError('test')
    monkeypatch.setattr(native, 'protect', denied)
    target = tmp_path / 'token.json'
    with pytest.raises(PermissionError):
        native.protected_write(target, {'access_token': 'must-not-be-written'})
    assert not target.exists()
    assert all(p.stat().st_size == 0 for p in tmp_path.iterdir())

def test_setup_retains_failed_attempt_and_previous_active_state(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_SEO_DATA_DIR', str(tmp_path / 'data'))
    runner.write_json(tmp_path / 'data/codex-runtime.json', {'sentinel': 'old'})
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a[0], 1, 'failure'))
    assert runner.setup(True) == 1
    assert json.loads((tmp_path / 'data/codex-runtime.json').read_text()) == {'sentinel': 'old'}
    assert len(list((tmp_path / 'data/runtimes').glob('*/setup.log'))) == 1

def test_state_replacement_keeps_previous_versions(tmp_path):
    path = tmp_path / 'state.json'
    runner.write_json(path, {'version': 1})
    runner.write_json(path, {'version': 2})
    assert json.loads(path.read_text())['version'] == 2
    previous = list(tmp_path.glob('state.json.previous-*'))
    assert len(previous) == 1 and json.loads(previous[0].read_text())['version'] == 1
