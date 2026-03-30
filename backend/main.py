from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
import logging
import os
import time
import socket
from typing import Optional
from urllib.parse import urlparse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

import models
import database
import bootstrap
from api.routers import auth, analytics, agent, ingest, erpnext, alerts, benchmarks, planning, loans, payroll, depreciation, documents, reports, banking, cloud_costs, ledger, inputs, forecasting, burn, recommendations, notifications, system, fx, tax, merge, financial_alerts, invoice_lifecycle

# Basic generic logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _check_database() -> dict:
    start = time.time()
    try:
        with database.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "ok": True,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "error": str(exc),
        }


def _check_redis() -> dict:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    start = time.time()
    try:
        parsed = urlparse(redis_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        timeout = float(os.getenv("REDIS_HEALTHCHECK_TIMEOUT", "1.5"))
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return {
            "ok": True,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "error": str(exc),
        }


def run_dependency_checks(require_redis: Optional[bool] = None) -> dict:
    if require_redis is None:
        require_redis = _bool_env("REQUIRE_REDIS_FOR_READINESS", False)

    db_check = _check_database()
    redis_check = _check_redis()
    ready = db_check["ok"] and ((not require_redis) or redis_check["ok"])

    return {
        "ready": ready,
        "require_redis": require_redis,
        "checks": {
            "database": db_check,
            "redis": redis_check,
        },
        "environment": os.getenv("ENV", "development"),
    }


def wait_for_dependencies() -> dict:
    max_retries = int(os.getenv("STARTUP_MAX_RETRIES", "15"))
    retry_delay = float(os.getenv("STARTUP_RETRY_DELAY_SECONDS", "2"))
    strict = _bool_env("STRICT_STARTUP_CHECKS", False)

    report = {}
    for attempt in range(1, max_retries + 1):
        report = run_dependency_checks()
        report["attempt"] = attempt
        report["max_retries"] = max_retries
        if report["ready"]:
            logger.info("Startup dependency checks passed on attempt %s/%s", attempt, max_retries)
            return report

        logger.warning(
            "Startup dependency checks failed on attempt %s/%s: %s",
            attempt,
            max_retries,
            report,
        )
        time.sleep(retry_delay)

    if strict:
        raise RuntimeError(f"Startup dependency checks failed after {max_retries} attempts: {report}")

    logger.warning("Continuing startup without strict dependency checks")
    return report

# Core Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="SeedlingLabs CFO AI API", 
    docs_url="/api/v1/docs", 
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)
bootstrap.run_bootstrap()


@app.on_event("startup")
def on_startup() -> None:
    app.state.startup_check_report = wait_for_dependencies()

@app.get("/")
def read_root():
    return {"message": "Welcome to SeedlingLabs CFO AI API. Visit /api/v1/docs for documentation."}


@app.get("/health/live")
def health_live():
    return {
        "status": "alive",
        "service": "vireon-backend",
        "environment": os.getenv("ENV", "development"),
        "timestamp": time.time(),
    }


@app.get("/health/ready")
def health_ready():
    report = run_dependency_checks()
    status_code = 200 if report["ready"] else 503
    return JSONResponse(status_code=status_code, content=report)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "detail": str(exc)},
    )

# Include Routers with API Versioning
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(erpnext.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(benchmarks.router, prefix="/api/v1")
app.include_router(planning.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(payroll.router, prefix="/api/v1")
app.include_router(depreciation.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(banking.router, prefix="/api/v1")
app.include_router(cloud_costs.router, prefix="/api/v1")
app.include_router(ledger.router, prefix="/api/v1")
app.include_router(inputs.router, prefix="/api/v1")
app.include_router(forecasting.router, prefix="/api/v1")
app.include_router(burn.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(fx.router, prefix="/api/v1")
app.include_router(tax.router, prefix="/api/v1")
app.include_router(financial_alerts.router, prefix="/api/v1")
app.include_router(merge.router, prefix="/api/v1")
app.include_router(invoice_lifecycle.router, prefix="/api/v1")

# API routes are intentionally versioned under /api/v1

