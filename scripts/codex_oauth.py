"""Maintained-library browser OAuth for the Codex runner; no raw code logging."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

SCOPES = {
    'gsc': 'https://www.googleapis.com/auth/webmasters.readonly',
    'ga4': 'https://www.googleapis.com/auth/analytics.readonly',
    'gsc-write': 'https://www.googleapis.com/auth/webmasters',
    'indexing': 'https://www.googleapis.com/auth/indexing',
}

def protect(path: Path):
    if os.name != 'nt':
        os.chmod(path, 0o600)
        return
    system32 = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32'
    identity = subprocess.run([str(system32 / 'whoami.exe'), '/user', '/fo', 'csv', '/nh'],
                              capture_output=True, text=True, check=True)
    sid = list(csv.reader(identity.stdout.splitlines()))[0][1]
    if not re.fullmatch(r'S-1-(?:\d+-)*\d+', sid):
        raise ValueError('Could not establish the current Windows security identity')
    subprocess.run([str(system32 / 'icacls.exe'), str(path), '/inheritance:r', '/grant:r', '*' + sid + ':F'],
                   capture_output=True, check=True)

def protected_write(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(path.name + '.next-' + uuid.uuid4().hex)
    fd = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    protect(stage)  # Establish ACLs before writing any secret bytes; fail closed.
    with stage.open('w', encoding='utf-8') as f:
        json.dump(value, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    if path.exists():
        backup = path.with_name(path.name + '.previous-' + uuid.uuid4().hex)
        old = json.loads(path.read_text(encoding='utf-8'))
        protected_write(backup, old)
    os.replace(stage, path)

def login(creds_path: Path, services: list[str], open_browser: bool = True) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow
    import google_auth
    config = json.loads(creds_path.read_text(encoding='utf-8'))
    client = config.get('installed') or config.get('web')
    if not isinstance(client, dict):
        raise ValueError('Provide a Google OAuth client JSON file')
    if client.get('auth_uri') not in {'https://accounts.google.com/o/oauth2/auth', 'https://accounts.google.com/o/oauth2/v2/auth'}:
        raise ValueError('Unexpected Google authorization endpoint')
    if client.get('token_uri') not in {'https://oauth2.googleapis.com/token', 'https://accounts.google.com/o/oauth2/token'}:
        raise ValueError('Unexpected Google token endpoint')
    flow = InstalledAppFlow.from_client_config(config, scopes=[SCOPES[s] for s in services],
                                               autogenerate_code_verifier=True)
    # The library binds a state value and performs S256 PKCE. No callback/code
    # parsing, logging, or token exchange is implemented by this wrapper.
    credentials = flow.run_local_server(host='localhost', port=0 if 'installed' in config else 8085,
        redirect_uri_trailing_slash='installed' in config, timeout_seconds=300,
        access_type='offline', prompt='consent',
        open_browser=open_browser, authorization_prompt_message='Open this Google authorization URL:\n{url}',
        success_message='Authentication complete. You may close this tab.')
    expiry = credentials.expiry
    if expiry is None:
        raise ValueError('Google returned credentials without an expiry')
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    token = {'access_token': credentials.token, 'refresh_token': credentials.refresh_token,
             'expires_at': expiry.timestamp(), 'client_id': client['client_id'],
             'scope': ' '.join(credentials.granted_scopes or [SCOPES[s] for s in services])}
    protected_write(Path(google_auth.TOKEN_PATH), token)
    google_auth._persist_oauth_client_path(str(creds_path.resolve()))
    print('Google credentials saved with restricted local permissions. No token values were logged.')

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--auth', action='store_true')
    parser.add_argument('--creds', type=Path, required=True)
    parser.add_argument('--service', choices=SCOPES, action='append', dest='services')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        login(args.creds, args.services or ['gsc', 'ga4'], not args.no_browser)
        return 0
    except Exception as exc:
        print('Google sign-in did not complete: ' + type(exc).__name__ + '. Existing credentials were retained.', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
