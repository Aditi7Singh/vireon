from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

import models
import database
import bootstrap
from api.routers import auth, analytics, agent, ingest, erpnext, alerts, benchmarks, planning, loans, payroll, depreciation, documents, reports, banking, cloud_costs, ledger, inputs, forecasting, burn, recommendations, notifications, system, fx

# Basic generic logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

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

# Configure CORS (allow local frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)
bootstrap.run_bootstrap()

@app.get("/")
def read_root():
    return {"message": "Welcome to SeedlingLabs CFO AI API. Visit /api/v1/docs for documentation."}

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

# API routes are intentionally versioned under /api/v1

