"""Codex paid-call guard. Local one-use approvals bind to exact tool inputs.

This is a trusted-hook workflow guard, not a security sandbox. Approval must
follow the user's authorization; callers with local write access can edit policy.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

MAX_INPUT = 2 * 1024 * 1024
PAID_SERVERS = re.compile(r'ahrefs|se-?ranking|firecrawl|profound|banana|dataforseo', re.I)
FREE_DATAFORSEO = re.compile(r'(?:_locations|_languages|_filters|_loc_and_lang|_categories|llm_models)$')
PAID_SCRIPTS = re.compile(r'\b(?:moz_api|keywordseverywhere_api|nlp_analyze|indexing_notify|dataforseo_merchant)\.py\b|--extension\s+banana\s+(?:generate|batch|edit)\.py\b|\bbanana[\\/]scripts[\\/](?:generate|batch|edit)\.py\b')
PAID_HOSTS = re.compile(r'\bapi\d?\.seranking\.com\b|\bapi\.tryprofound\.com\b|\bapi\.dataforseo\.com\b', re.I)

def storage() -> Path:
    raw = os.environ.get('CODEX_SEO_DATA_DIR') or os.environ.get('PLUGIN_DATA') or os.environ.get('CLAUDE_PLUGIN_DATA')
    path = Path(raw).expanduser().resolve() if raw else Path.home() / '.local/share/codex-seo'
    if path == Path(path.anchor) or path == Path.home():
        raise ValueError('Use a dedicated policy directory')
    return path / 'paid-policy'

def classify(event: dict) -> str | None:
    name = event.get('tool_name', '')
    match = re.match(r'^mcp__(.+?)__(.+)$', name)
    if match and PAID_SERVERS.search(match[1]):
        if 'dataforseo' in match[1].lower() and FREE_DATAFORSEO.search(match[2]):
            return None
        return name
    tool = event.get('tool_input') or {}
    if not isinstance(tool, dict):
        tool = {'command': tool} if isinstance(tool, str) else {}
    command = tool.get('command') or tool.get('cmd') or ''
    if name in {'Bash', 'PowerShell', 'exec_command'} and isinstance(command, str):
        match = PAID_SCRIPTS.search(command) or PAID_HOSTS.search(command)
        if match:
            # --help and non-network inspection remain usable.
            if re.search(r'\s--help(?:\s|$)', command) and not re.search(r'&&|\|\||[;|\n]', command):
                return None
            return 'shell:' + match[0]
    return None

def identity(event: dict) -> str:
    payload = {'tool_name': event.get('tool_name'), 'tool_input': event.get('tool_input')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def approve(request_id: str, max_usd: float, minutes: int = 10) -> dict:
    if not re.fullmatch(r'[a-f0-9]{64}', request_id) or not (0 < max_usd < 100000) or not 0 < minutes <= 60:
        raise ValueError('Specify a valid request ID, positive budget and expiry of 1–60 minutes')
    request = json.loads((storage() / 'requests' / (request_id + '.json')).read_text(encoding='utf-8'))
    grant = {'request_id': request_id, 'tool': request['tool'], 'budget_ceiling_usd': max_usd,
             'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(),
             'actual_charge': None, 'authorization': 'Requires explicit user approval for this exact action'}
    parent = storage() / 'grants'
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / (request_id + '-' + uuid.uuid4().hex + '.json')
    with path.open('x', encoding='utf-8') as f:
        json.dump(grant, f, indent=2)
    return {'approved_request': request_id, 'uses': 1, 'max_usd': max_usd, 'expires_at': grant['expires_at'],
            'limitation': 'Unknown provider charges must still be checked; a grant is not an invoice or hard provider spend limit.'}

def evaluate(event: dict) -> dict:
    paid = classify(event)
    if not paid:
        return {}
    key = identity(event)
    now = datetime.now(timezone.utc)
    for path in sorted((storage() / 'grants').glob(key + '-*.json')):
        try:
            grant = json.loads(path.read_text(encoding='utf-8'))
            if grant.get('request_id') != key or datetime.fromisoformat(grant['expires_at']) <= now:
                continue
            claim = path.with_suffix('.claimed')
            # Atomic single-use reservation; parallel calls cannot share a grant.
            with claim.open('x', encoding='utf-8') as f:
                json.dump({'claimed_at': now.isoformat(), 'actual_charge': None}, f)
            return {}
        except (OSError, ValueError, KeyError, TypeError):
            continue
    parent = storage() / 'requests'
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / (key + '.json')
    if not path.exists():
        try:
            with path.open('x', encoding='utf-8') as f:
                json.dump({'request_id': key, 'tool': paid, 'created_at': now.isoformat(),
                           'arguments_stored': False, 'actual_charge': None}, f, indent=2)
        except FileExistsError:
            pass
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
            'permissionDecisionReason': 'Paid/quota-consuming SEO action requires user authorization. Tool: ' + paid +
            '. Review its exact inputs and estimated provider cost. After approval, use the native runner approve command with request ' + key + '. No call has been made.'}}

def main() -> int:
    raw = sys.stdin.read(MAX_INPUT + 1)
    try:
        if len(raw.encode('utf-8')) > MAX_INPUT:
            raise ValueError('oversized event')
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError('event must be an object')
        print(json.dumps(evaluate(event)))
        return 0
    except Exception as exc:
        print('SEO paid guard could not inspect the event: ' + type(exc).__name__, file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
