# Vireon Project Status

Last updated: 2026-03-24

## Current State
- Frontend and backend are running via Docker Compose.
- Core UI branding is updated with the Vireon wing-arrow logo and larger tagline styling.
- Landing page copy no longer includes the "Inspired by vireo" line.
- Frontend API calls are now normalized to versioned endpoints only (`/api/v1/...`).
- Backend unversioned route mounts were removed; legacy root endpoints intentionally return 404.
- Deterministic startup bootstrap is enabled on backend startup (schema compatibility + baseline company/metrics/rates/transactions seed).
- Startup health checks are exposed at `/api/v1/system/startup-health` and shown in dashboard UI if setup is incomplete.
- FX module now supports default rate sync and conversion (`/api/v1/fx/sync-default`, `/api/v1/fx/convert`).
- FX revaluation workflow is available (`/api/v1/fx/revalue/{company_id}` and `/api/v1/fx/snapshots/{company_id}`) with monthly Celery schedule.
- Document upload now performs basic local extraction for text/json/pdf and stores OCR text when available.
- OCR async worker path is implemented via Celery task (`OCR_ASYNC=true`) for queued extraction.
- CTO and Finance dashboards now call real backend endpoints for burn/expenses/reconciliation/pending-review flows.
- Startup-health now includes per-table readiness and actionable setup hints.
- CI workflow added for bootstrap/FX startup checks (`.github/workflows/backend-ci.yml`).
- Recommendations engine now has deterministic fallback logic and product-margin signal handling (even without LLM).
- Banking sync now performs local enrichment (category + SaaS flagging + duplicate candidate detection) instead of a no-op stub.
- Cloud cost recommendations now return data-driven optimization suggestions from observed 30-day usage patterns.
- CTO and Finance dashboards now include CSV export actions for operational drill-down workflows.
- CTO and Finance dashboards now include PDF export actions and 6-month trend visualizations.
- Startup-health banner now supports one-click remediation actions (`bootstrap_seed`, `sync_default_fx_rates`, `run_monthly_fx_revaluation`).
- FX accounting close workflow is implemented with preview/post/approve endpoints (`/api/v1/fx/close/*`) and persistent close batches.
- Reports module now supports group consolidated P&L (`/api/v1/reports/pl/consolidated-group`) as a baseline for multi-company reporting.
- Group consolidated P&L now supports optional intercompany elimination controls (`apply_eliminations`, `elimination_mode`) with elimination telemetry.
- OCR pipeline supports configurable storage backend (`STORAGE_BACKEND=local|s3`) and optional provider route (`OCR_PROVIDER=local|textract`) with retryable async task behavior.
- Startup-health now reports credential readiness for OCR/storage/connectors and exposes connector conflict policy state.
- Connector conflict-resolution policy controls are available at `/api/v1/system/connectors/conflict-policy`.
- Backend CI now runs startup/bootstrap plus dashboard API integration tests.
- Backend CI now also executes the full backend test suite (`pytest tests -q`).
- Notifications are email-only by design; Slack/WhatsApp delivery is not active.
- Backend runtime compatibility fixed for Python 3.9 by converting new-style union annotations in route-facing code paths to `typing.Optional`/`typing.List` where required.
- Margin service outputs and alert API now include backward-compatible keys/signature (`total_revenue`, `total_cogs`, `gross_margin_pct`, `threshold_pct`) to keep tests and legacy callers stable.
- Local backend verification passed: `38 passed` via `cd backend && ../.venv/bin/python -m pytest -q`.
- Verified versioned dashboard endpoints return 200:
  - `/api/v1/revenue`
  - `/api/v1/scorecard`
  - `/api/v1/runway`
  - `/api/v1/expenses`
  - `/api/v1/cash-balance`
  - `/api/v1/benchmarks/sass-health`
- Benchmark endpoint now returns a safe fallback payload when monthly metrics are missing (instead of 500).

## What Is Working
- Financial ledger ingestion and analytics services.
- Forecasting service with SARIMA/Prophet/fallback logic.
- Documents upload/status API with baseline local extraction.
- Role-aware authentication with demo user fallback when no token is provided.

## Known Gaps
- OCR production path requires real cloud credentials/configuration for S3 and managed OCR provider in deployment.
- Multi-company consolidation has elimination controls, but robust legal-entity-level matching/reconciliation rules still need expansion.
- External connectors still need production credentials and live ingest job rollout (Plaid/cloud provider APIs, Merge production sync cadence).
- Advanced ML layer (XGBoost/Monte Carlo/peer live-market benchmarking) is still pending.
- Frontend lint/build validation could not be executed in this runtime because `npm` is unavailable in PATH; run `npm run lint && npm run build` in `frontend/` on a Node-enabled machine.

## Immediate TODO (Priority)
1. Configure production secrets for OCR/storage and verify S3/Textract in deployed environment.
2. Expand intercompany elimination from tag/keyword heuristics to strict counterparty matching + reconciliation controls.
3. Add Plaid/cloud provider live ingest jobs with production-grade scheduling and retry policies.
4. Add connector policy governance (audit trail + per-company overrides in DB instead of file-backed defaults).
5. Add advanced ML layer (XGBoost/Monte Carlo/peer live-market benchmarking) with model validation gates.

## Runbook
1. Start stack: ./start.sh
2. Backend docs: `http://localhost:8000/api/v1/docs`
3. Frontend: `http://localhost:3000`

## Notes for Next Contributor
- Keep this file as the single project-state tracker.
- If major architecture or roadmap changes happen, update this file in the same PR.