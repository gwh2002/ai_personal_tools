## 2025-10-20
- Updated BigQuery chunk loading to truncate only on the first chunk and append subsequent chunks so intermediate loads persist. (Codex GPT-5)

## 2025-10-22
- **Extended test suite to catch deployment issues before Cloud Run**: Created comprehensive `test_deployment_readiness.py` (45 tests) to validate all imports, module exports, Flask initialization, and configuration loading. This suite catches issues like import errors that previously only surfaced in production.
- **Fixed critical import error in run_report.py**: Updated imports from deleted `read_and_clean` module to `ifms_ab_processing.models`, preventing Cloud Run startup failures.
- **Rewrote test_main_endpoints.py**: Completely refactored endpoint tests to work with current codebase, using proper mocking for all external dependencies (12 tests covering `/health`, `/run`, error handling, and config overrides).
- Fixed Cloud Run startup failure: updated `src/main.py` to stop importing non-existent config symbols at module import time, added safe config fallbacks, and mapped to existing `config.py` values. Container now binds to `PORT=8080` reliably. (Codex CLI)
- Implemented feedback from issues.md:
  - Drive API pagination in `drive_utils.list_sheets_in_folder` to avoid missing files.
  - Increased Gunicorn timeout to 3600s to match Cloud Run.
  - `/run` now parses JSON payload (`sources`, `dry_run`); added `/healthz` endpoint.
  - Use `PROJECT_ID` for Secret Manager lookups; disable Google API discovery cache.
  - BigQuery helper logs and skips when there are no rows to load.
  - Fixed Ruff errors: forward-ref typing for `DiscoveredSheet`; test import order E402.