# Codex edition

The repository supports both agent hosts. Original Claude Code skills, agents,
installers, scripts, references and cockpit remain present. Codex uses a separate
compatibility manifest and generated skill surface. No Claude account is needed
to use the Codex surface; optional data providers retain their own account/API
requirements.

## Install from this repository

On a compatible Codex CLI, register the repository checkout and install:

```text
codex plugin marketplace add /absolute/path/to/claude-seo
codex plugin add claude-seo@nicknameff-seo-tools
```

After this branch is available remotely, a pinned installation can use:

```text
codex plugin marketplace add nabeelmuqarrab/claude-seo --ref codex/codex-compat-v001
codex plugin add claude-seo@nicknameff-seo-tools
```

Start a new chat to discover the installed skills. Hooks require the host's
review/trust step; never bypass hook trust. Installing does not authorize paid
research or deploy anything to a website. The user-level installation is distinct
from the isolated CODEX_HOME used by automated smoke tests.

Run `$seo-doctor` first. Run `$seo-setup` to create an isolated Python environment;
Python 3.11+ is required for new Codex environments. Node is needed for the trusted
hook launcher and optional Node-based integrations. Chromium setup supports the
rendering/screenshot tools; `setup --skip-browser` is appropriate for static-only
work. PDF export may require the platform's native WeasyPrint libraries.

## Use

| Request | Codex skill |
|---|---|
| Full site review | `$seo audit https://example.com` or `$seo-audit` |
| One page | `$seo-page` |
| Technical, sitemap, schema or images | `$seo-technical`, `$seo-sitemap`, `$seo-schema`, `$seo-images` |
| Content, briefs, clustering, programmatic plans | `$seo-content`, `$seo-content-brief`, `$seo-cluster`, `$seo-programmatic` |
| Search experience, performance and release changes | `$seo-sxo`, `$seo-google`, `$seo-drift` |
| Local/maps, ecommerce, hreflang, GEO, agent readiness, FLOW | Corresponding `$seo-*` skill |
| Google, backlinks and all optional providers | `$seo-google`, `$seo-backlinks` and provider `$seo-*` skills |
| Specialist pass | `$seo-specialist-*` skills (original procedures retained) |
| Readiness, spend, dashboard | `$seo-doctor`, `$seo-spend`, `$seo-cockpit` |

The Python runner works without Bash:

```text
python /absolute/path/to/claude-seo/scripts/codex-seo.py doctor --json
python /absolute/path/to/claude-seo/scripts/codex-seo.py setup --skip-browser
python /absolute/path/to/claude-seo/scripts/codex-seo.py run parse_html.py /absolute/path/to/page.html --url https://example.com --json
python /absolute/path/to/claude-seo/scripts/codex-seo.py run --extension banana generate.py --help
```

Use the actual available Python executable (`python3`, `py -3`, or a quoted
absolute executable with PowerShell `&`). The native runner preserves argument
boundaries with subprocess arrays. It never interpolates a tool's data into shell
code. `CODEX_SEO_PYTHON` may select an existing isolated interpreter;
`CODEX_SEO_DATA_DIR` selects a dedicated writable runtime/output directory.
Codex plugin data is used when supplied by the host.

## Function coverage and deliberate platform differences

`scripts/build_codex.py` derives all Codex workflows from all core skills, extension
skills, core specialist definitions, and extension specialist definitions. Duplicate
core/extension mirrors retain both workflow bodies and supporting resources.
`codex/coverage.json` maps every source and records canonical UTF-8/LF text hashes
for the generated surface; binary assets retain their exact byte hashes.
All existing runtime-allowlisted core scripts and extension scripts remain usable.
Rerunning the generator is deterministic; changed generated files are retained in
`output/codex-build-history/` before replacement. It never removes obsolete files
silently; review removed/renamed upstream capabilities when updating the source.

Codex does not use Claude's model names or Markdown agent-registration mechanism.
Specialist procedures are discoverable skills and can run inline, or be delegated
when the actual host supports and permits that. This retains audit coverage on
hosts without subagents. The original Claude cockpit's live terminal mods,
model-switching and token-free slash commands are host-specific. Codex provides
normal skill turns, readiness/spend commands and a portable HTML evidence dashboard
instead; it does not pretend to register Claude terminal UI in Codex.

The schema hook accepts Codex's native `apply_patch` JSON event and reads changed
files only within the event's working directory. It gives post-edit feedback and
cannot undo a write. JSON-LD lint is not a guarantee of Google rich-result display.

## Integrations and cost control

All nine providers are retained: Ahrefs, Banana/Gemini, Bing Webmaster, DataForSEO,
Firecrawl, Matomo, Profound, SE Ranking and Unlighthouse. Show the exact retained
configuration with:

```text
python /absolute/path/to/claude-seo/scripts/codex-seo.py integration ahrefs
```

For stdio MCP providers, the command returns a Codex TOML template with `env_vars`
names, not embedded secret values. Configure it through the Codex MCP settings or
an authorized configuration edit. API-only providers use the scripts/reference
procedures with environment-backed credentials. The Banana Python fallbacks remain
available; no image provider is connected automatically. Do not run extension
installers that modify `.claude.json` to configure Codex.

The trusted paid-call hook checks known billable provider MCP calls and API shell
commands. Free reference lookups and GSC reporting are not classified as paid.
Blocked calls create a local request ID containing hashes, not raw tool inputs.
After the user authorizes the exact action and estimated budget, record a one-use,
short-lived grant:

```text
python /absolute/path/to/claude-seo/scripts/codex-seo.py approve --request REQUEST_ID --max-usd 0.10 --expires-min 10
```

The grant binds to the exact pending tool input and is claimed atomically. It is
not an invoice or a provider-enforced spending cap. Recheck actual provider prices,
charge records and quotas. Do not grant approvals on the user's behalf without
their authorization. Local hooks are workflow guardrails, not security boundaries;
unsupported tool paths may bypass hook coverage. Legacy cost estimates and ledger
functions remain available through `dataforseo_costs.py`.

## Data and preservation

Every native runner command gets a new output folder. Relative input files are
resolved before changing directories; relative output files land in the new folder.
Existing explicitly named output files are refused. Runtime setup retains each
version and failed attempt; the previous active state is retained on replacement.
Drift fetch evidence is retained in preservation mode. Receipts store tool names
and exit codes but not arguments, stdout or credentials. Keep private local data
outside Git and out of hosted public directories.

The Codex prose cleanup preserves Unicode by default. Its original removal behavior
is still available through explicit `--strip-invisible`; never apply it blindly to
nickname values, copy data or code examples. GSC report query strings are escaped
in the detail and quick-win HTML tables.

Separate reporting credentials from write operations. The Codex runner routes
`google_auth.py --auth --creds ...` through a maintained library with state and
PKCE, restricted local token files and atomic writes. Default scopes are read-only
GSC and Analytics; add `--service gsc-write` or `--service indexing` only for an
explicitly authorized eligible write operation. `--no-browser` displays the URL
for manual browser opening. Existing read-only connections, ADC and service
accounts remain usable. Original direct legacy login/code-exchange commands are
retained for compatibility; use the native browser path for Codex. Live OAuth and
every provider account still require separate validation; no blanket security
certification is implied.

## Validate updates

```text
python scripts/build_codex.py
python -m pytest tests/test_codex_port.py
```

For preserved runs, set `SEO_TEST_RETAIN_DIR` to a new run's `retained` directory,
pass a new `--basetemp`, use a run-specific pytest cache path and JUnit output,
and load `-p tests.preserve_artifacts`. The opt-in fixture moves cleanup targets
into retained storage instead of deleting them; it refuses deletions outside the
test-owned directory. Keep failed runs and dependency-resolution reports.

Official packaging references: [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins),
[Claude plugin conversion](https://developers.openai.com/plugins/guides/submit-claude-plugin),
and [hook event contracts](https://learn.chatgpt.com/docs/hooks).
