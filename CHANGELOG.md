# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.0] - 2026-05-27

### Added

- `health_check` MCP tool — verifies authentication status and Google connectivity
- `usage_stats` MCP tool — local usage statistics (privacy-friendly, nothing sent externally)
- `src/exceptions.py` — 5 typed exception classes (AuthExpiredError, CaptchaRequiredError, RpcStructureError, NotebookNotFoundError, RateLimitError)
- `src/rpc_ids.py` — all 9 RPC IDs as named constants (no more magic strings)
- `src/status_codes.py` — ResearchStatus, ArtifactStatus enums + parse functions
- `src/config.py` — centralized Settings dataclass (http_timeout, csrf_ttl, ports)
- `src/validators.py` — input validation for notebook_id, url, question, mode, artifact_type
- `src/retry.py` — exponential backoff retry for transient errors (timeout, 5xx, 429)
- `src/telemetry.py` — local usage tracking in ~/.notebooklmcp/telemetry.json
- `safe_get()` helper — defensive array access replacing 12+ unprotected magic indexes
- CAPTCHA detection in `_parse_batch_response` and `refresh_at_and_bl`
- Auth expiry detection (HTTP 401/403, redirect to accounts.google.com)
- Fixture capture instrumentation (`RTK_CAPTURE_FIXTURES=1` env var)
- `tests/scripts/anonymize_fixtures.py` — anonymizes captured response fixtures
- `scripts/import_cookies_from_node.py` — imports cookies from Node.js auth.json
- `COORDINATION.md` — coexistence rules for Claude Code + Antigravity IDE
- `SACRED.md` — anti-bot fingerprint items that must never be changed without A/B test
- `.handoff.md` — session state handoff between AI agents
- `requirements-dev.txt` — pytest + pytest-asyncio
- 38 unit tests covering: auth parsing, status codes, exceptions, RPC IDs, safe_get, _parse_batch_response

### Changed

- `req_id_counter` → UUID (eliminates race condition in concurrent use)
- `print(..., file=sys.stderr)` in browser_auth.py → `logger.info()` (prevents stdio protocol corruption)
- Magic status code numbers (1, 2, 3, 6) replaced by `ResearchStatus`/`ArtifactStatus` enums
- Magic RPC ID strings replaced by `RpcId.*` constants
- `CLAUDE.md` rewritten — was incorrectly describing a Node.js project
- `AGENTS.md` updated — added coordination section for Claude/Antigravity

### Fixed

- Race condition in `req_id_counter` when used concurrently
- Silent failures on Google API structure changes (now logs warnings via safe_get)
- CAPTCHA scenarios that previously produced cryptic errors
- `print()` calls in browser_auth.py that could corrupt MCP stdio transport

### Security

- **README corrected**: cookies are stored as plaintext in `.env` file, protected only by filesystem
  permissions. Previous README falsely claimed they were "encrypted".

## [2.1.0] - 2026-05-23

- Initial public version with Deep Research, Studio artifacts, Chrome CDP auth
- 9 MCP tools via FastMCP
- Support for Claude Code and Antigravity IDE
