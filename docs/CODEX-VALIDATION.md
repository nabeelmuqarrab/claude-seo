# Codex compatibility validation — 21 October 2026

Candidate version: `2.4.2-codex.1`. Based on upstream/fork revision
`4b99de2f7de7e7d5247042e5fb5b4ea9368ef734`. Original Claude Code packaging remains
present. No nicknameff.id release, Hostinger configuration, MCQ project or
Unified Sites Manager repository was changed by this port.

## Coverage

All 57 source workflow definitions are mapped: 26 core skills, nine extension
skill definitions, 19 core specialist definitions and three extension specialist
definitions. Overlapping mirrors retain both bodies/resources. These become 53
unique Codex workflows plus four operations skills: setup, doctor, spend and
cockpit. `codex/coverage.json` records source hashes, adapted body hashes and every
generated file hash. All original 57 allowlisted executors and seven extension
script registrations remain available; maintenance/release source also remains.

Changes include a native Python runner, versioned environments/output folders,
Windows long-path support, optional provider setup templates, schema and paid-call
hooks, a local evidence dashboard with SVG charts, safe Unicode cleanup defaults,
escaped GSC query-table output, local cache selection, and visible-body word count.
Native browser sign-in uses a maintained OAuth library with PKCE/state, read-only
reporting scopes by default, permission checks before token writes, and atomic
token replacement. The original direct legacy auth paths remain available.

## Executed validation

| Check | Observed result |
|---|---|
| Broad Python regression run | 991 passed, 21 skipped, zero failures; 1,012 collected tests |
| Final focused Codex regression run | 33 passed, zero skips/failures, using the full dependency environment |
| Shipped skill validator | All 57 generated Codex skills passed |
| Offline executor registration smoke | All 64 core/extension `--help` invocations exited 0; network denied in these subprocesses |
| Native Codex CLI marketplace/install | Successful in an isolated CODEX_HOME using CLI 0.163.0-alpha.10.2 |
| Full Python + Chromium setup | Successful in a new versioned Windows runtime; doctor reported both ready |
| Browser execution | Native runner rendered a public example page with Playwright Chromium, HTTP 200 and no reported error |
| Native hook process smoke | Valid schema passed, malformed schema produced feedback, paid-provider dry event denied; UTF-8 filenames worked |
| Independent skill forward-test | Saved Indonesian HTML/sitemap reviewed using the native parser and metadata helper; no network or paid services |

The broad run excludes `test_extension_installer_injection.py`: it exercises
legacy shell installers which can clean up files in child processes. Those
installers are retained but not used by the Codex edition. The 21 skips are
recorded in JUnit, including host/platform conditions and explicitly disabled
live checks. This is not a claim that every test in every host/extension suite
has run, nor that every vendor's live functionality is verified.

Cross-platform CI configuration is included for Windows, Linux and macOS. Only
Windows was executed locally. CI results must be inspected separately; this
document does not claim that the added remote CI jobs already passed.

## Preserved attempts and evidence

Local development evidence is kept outside the checkout at `research/v033/` in
the owning workspace. Earlier artifacts were not deleted:

- `test-runs/v001`: fixture parent-directory setup failure; retained.
- `test-runs/v002`: 209 passed and three platform skips on the initial focused suite.
- `test-runs/v003`: 979 passed, 11 environment/isolation failures, 21 skips.
  These exposed denied home-cache writes, a temporary-file preservation issue,
  and public DNS checks blocked by the sandbox. Cache isolation/temp placement
  were corrected, and the network-dependent checks were rerun with permission.
- `test-runs/v004`: 991 passed, 21 skipped, zero failures.
- `test-runs/v005`: final focused native suite, 31 passed/one dependency skip.
- `test-runs/v006`: 33 native checks passed after canonical text hashing and the
  Windows/Linux line-ending regression test were added; no skips or failures.
- `runtime-tests/v001`: dependency installation hit Windows path-length limits.
  Native long-path handling fixed the subsequent setup.
- `runtime-tests/v002`: full Python dependency setup passed, browser deliberately skipped.
- `runtime-tests/v003`: dependency registry DNS failed; failed environment/log retained.
- `runtime-tests/v004`: full dependency and Chromium setup passed.
- `tool-smoke/v001`, `hook-smoke/v001`, `forward-test/v001`, CLI receipts, skill
  validation, browser result and dependency-resolution reports are retained.

No environment dumps or real token values were stored in command receipts.
The retained local test/config files contain synthetic fixtures, not connected
provider accounts. The private OAuth flow was mocked; no Google login occurred.

Git whitespace validation passed. Generated provenance uses UTF-8/LF canonical
text hashes, with binary payloads unchanged; `.gitattributes` keeps text checkout
line endings consistent. This prevents Windows `autocrlf` from invalidating the
coverage map when another host checks out the same commit.

## Remaining validation boundaries

Paid APIs, actual Google sign-in, account permissions, quotas, and vendor MCP
availability require the user's provider configuration and separate authorized
live checks. No paid account was connected or charged here. PDF export on Windows
may require native WeasyPrint libraries; Python installation alone does not prove
PDF readiness. Headless browser success does not prove every physical-device flow.

Codex hook trust remains a user/host decision. Hooks are workflow feedback, not
a complete authorization or network security boundary. Approval grants bind to
one exact tool input and expire, but do not constitute a provider-enforced hard
spend limit. Unknown actual charges remain unknown until checked in provider data.

The Claude cockpit's terminal mods and zero-token slash commands are host-specific.
Codex retains their operational purpose through native CLI diagnostics, ordinary
skills and the HTML evidence dashboard; it does not imitate unsupported terminal
UI APIs or claim pixel-identical behavior. No ranking or traffic guarantee is made.
