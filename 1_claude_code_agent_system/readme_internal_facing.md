# Claude Agent Workflow 

Concise, repeatable flow for planning, implementing, validating, documenting, and safely shipping changes across the Bellaventure monorepo (Python 3.11, GCP).

## Agents
- [PLANNER](1_planner.md) (strategy) — define root cause, phases, and parallelizable steps.
- [EXECUTER](2_executer.md) (build) — implement per Phase 1 using established patterns.
- [VERIFIER](3_verifier.md) (quality) — run static checks and repo rules.
- [TESTER](4_tester.md) (validation) — run targeted/unit/integration tests as applicable.
- [DOCUMENTER](5_documenter.md) (history) — update docs and patterns.
- UPDATER (vc) — commit, push, and open PR safely.

## Flow
1) Plan
 - Review `docs/`, service `/services/../src/`, relevant SQL transformations in services/ab-terraform/src/queries organized by BigQuery dataset, recent changes.
  - Produce phases with clear acceptance criteria; mark any parallel phases.
  - Output: `dev_artifacts/agents/YYYY.MM.DD_[service_name_or_component_name]/WORK.md` created from `docs/ai_agents/templates/WORK_TEMPLATE.md`.
2) Execute
   - Implement only what PLANNER scoped. Prefer shared utilities in `shared_helpers`.
3) Verify & Test
   - VERIFIER: ruff, mypy, import/order/style rules; dry-run checks for SQL.
   - TESTER: pytest or service-level checks; add/adjust tests if needed.
4) Document & Update
   - Update `PROJECT_DOCUMENTATION.md` and `agent_rules.md` if patterns change.
   - UPDATER: Conventional commits; push branch and open PR (no direct push to `main`).

## Quality Gates (must pass)
- ruff and mypy clean; no ad-hoc `print` logging.
- Use `shared_helpers.logging_utils` and emit `service_start/service_completed/service_failed`.
- BigQuery SQL: `--dry_run` passes; Terraform plans clean if touched.
- No secrets in code; use Secret Manager; see `README.md: Security & Secrets`.
- Branch policy: feature branches → PR → `main` via review; no direct to `main`.

## Quick Start
1) Open repo in Claude/Cursor and run `/planner "problem or feature"`.
2) Follow phases with: `/executer`, `/verifier`, `/tester`, `/documenter`, `/updater`.

## Notes
- Keep scope narrow; fix root cause, not symptoms.
- Prefer existing conventions in `README.md` (service skeleton, endpoints) and `shared_helpers` over new patterns.
- Keep this doc concise; add new patterns to `agent_rules.md`.
