# Vireon Project Status

Last updated: 2026-03-21

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
- OCR worker is local queue-based today; cloud object storage + managed OCR + structured receipt field mapping are still pending.
- FX revaluation snapshots exist; full accounting close automation (journal posting + approval workflow) is still pending.
- CTO/Finance advanced widgets still need trend history and drill-down exports.

## Immediate TODO (Priority)
1. Add production OCR storage + OCR provider integration (S3 + worker retries + field mapping).
2. Add accounting close workflow on top of FX snapshots (GL posting + approvals).
3. Expand CTO/Finance dashboards with historical trend series and CSV/PDF exports.
4. Extend CI coverage to run dashboard API integration tests (beyond startup/bootstrap smoke tests).
5. Add startup-health remediation links in UI (one-click actions where safe).

## Runbook
1. Start stack: ./start.sh
2. Backend docs: `http://localhost:8000/api/v1/docs`
3. Frontend: `http://localhost:3000`

## Notes for Next Contributor
- Keep this file as the single project-state tracker.
- If major architecture or roadmap changes happen, update this file in the same PR.