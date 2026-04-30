"""
White-Label SaaS Platform Router
==================================
Multi-tenant branding, feature flags, custom domains, and per-tenant settings.
Branding config is stored in company metadata (JSON column).

GET  /white-label/tenants                            — List tenants
POST /white-label/tenants                            — Provision new tenant
GET  /white-label/tenants/{company_id}/branding      — Get branding config
PUT  /white-label/tenants/{company_id}/branding      — Update branding
GET  /white-label/tenants/{company_id}/features      — Feature flags
PUT  /white-label/tenants/{company_id}/features      — Update feature flags
GET  /white-label/tenants/{company_id}/domain        — Custom domain config
PUT  /white-label/tenants/{company_id}/domain        — Set custom domain
GET  /white-label/tenants/{company_id}/usage         — Tenant usage metrics
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/white-label", tags=["white-label"])


# ---------------------------------------------------------------------------
# Default feature flags template
# ---------------------------------------------------------------------------

DEFAULT_FEATURES = {
    "ai_agent": True,
    "forecasting": True,
    "anomaly_detection": True,
    "blockchain_audit": True,
    "voice_commands": True,
    "ml_marketplace": True,
    "multi_currency": True,
    "erp_sync": True,
    "consolidation": False,
    "investor_portal": False,
    "white_label": False,
    "custom_domain": False,
    "advanced_tax": True,
    "payroll": True,
    "purchase_orders": True,
    "regulatory_compliance": True,
}

DEFAULT_BRANDING = {
    "app_name": "Vireon",
    "logo_url": None,
    "favicon_url": None,
    "primary_color": "#b3622d",
    "secondary_color": "#f6f3ee",
    "accent_color": "#ce6f35",
    "font_family": "Inter",
    "support_email": "support@vireon.ai",
    "terms_url": None,
    "privacy_url": None,
    "hide_powered_by": False,
    "custom_css": None,
}


def _get_company(company_id: uuid.UUID, db: Session) -> models.Company:
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company / tenant not found.")
    return company


def _get_branding(company: models.Company) -> dict:
    stored = {}
    if company.settings and isinstance(company.settings, dict):
        stored = company.settings.get("branding", {})
    return {**DEFAULT_BRANDING, **stored}


def _get_features(company: models.Company) -> dict:
    stored = {}
    if company.settings and isinstance(company.settings, dict):
        stored = company.settings.get("features", {})
    return {**DEFAULT_FEATURES, **stored}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class TenantProvision(BaseModel):
    name: str
    subdomain: Optional[str] = None
    owner_email: str
    plan: str = "starter"


class BrandingUpdate(BaseModel):
    app_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    support_email: Optional[str] = None
    terms_url: Optional[str] = None
    privacy_url: Optional[str] = None
    hide_powered_by: Optional[bool] = None
    custom_css: Optional[str] = None


class FeatureFlagsUpdate(BaseModel):
    flags: Dict[str, bool]


class DomainConfig(BaseModel):
    custom_domain: str
    ssl_enabled: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/tenants")
def list_tenants(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all tenant companies."""
    companies = db.query(models.Company).order_by(models.Company.created_at.desc()).all()
    return {
        "total": len(companies),
        "tenants": [
            {
                "id": str(c.id),
                "name": c.name,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "branding": _get_branding(c),
                "plan": (c.settings or {}).get("plan", "starter") if c.settings else "starter",
                "custom_domain": (c.settings or {}).get("custom_domain") if c.settings else None,
            }
            for c in companies
        ],
    }


@router.post("/tenants", status_code=201)
def provision_tenant(
    payload: TenantProvision,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Provision a new white-label tenant."""
    subdomain = payload.subdomain or payload.name.lower().replace(" ", "-")
    new_company = models.Company(
        name=payload.name,
        settings={
            "plan": payload.plan,
            "owner_email": payload.owner_email,
            "subdomain": subdomain,
            "provisioned_at": datetime.utcnow().isoformat(),
            "branding": {**DEFAULT_BRANDING, "app_name": payload.name},
            "features": {**DEFAULT_FEATURES},
        },
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return {
        "id": str(new_company.id),
        "name": new_company.name,
        "subdomain": subdomain,
        "app_url": f"https://{subdomain}.vireon.ai",
        "plan": payload.plan,
        "provisioned_at": datetime.utcnow().isoformat(),
        "status": "active",
        "message": f"Tenant '{payload.name}' provisioned at {subdomain}.vireon.ai",
    }


@router.get("/tenants/{company_id}/branding")
def get_branding(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the branding configuration for a tenant."""
    company = _get_company(company_id, db)
    return {
        "company_id": str(company_id),
        "company_name": company.name,
        "branding": _get_branding(company),
    }


@router.put("/tenants/{company_id}/branding")
def update_branding(
    company_id: uuid.UUID,
    payload: BrandingUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update branding config for a tenant."""
    company = _get_company(company_id, db)
    settings = dict(company.settings or {})
    existing_branding = settings.get("branding", {})

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    existing_branding.update(updates)
    settings["branding"] = existing_branding
    company.settings = settings
    db.commit()

    return {
        "company_id": str(company_id),
        "updated_at": datetime.utcnow().isoformat(),
        "branding": {**DEFAULT_BRANDING, **existing_branding},
        "message": "Branding updated successfully.",
    }


@router.get("/tenants/{company_id}/features")
def get_feature_flags(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return feature flags for a tenant."""
    company = _get_company(company_id, db)
    return {
        "company_id": str(company_id),
        "features": _get_features(company),
        "available_flags": list(DEFAULT_FEATURES.keys()),
    }


@router.put("/tenants/{company_id}/features")
def update_feature_flags(
    company_id: uuid.UUID,
    payload: FeatureFlagsUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update feature flags for a tenant."""
    company = _get_company(company_id, db)
    settings = dict(company.settings or {})
    existing_features = settings.get("features", {})

    invalid = [k for k in payload.flags if k not in DEFAULT_FEATURES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown feature flags: {invalid}")

    existing_features.update(payload.flags)
    settings["features"] = existing_features
    company.settings = settings
    db.commit()

    return {
        "company_id": str(company_id),
        "updated_at": datetime.utcnow().isoformat(),
        "features": {**DEFAULT_FEATURES, **existing_features},
        "message": "Feature flags updated.",
    }


@router.get("/tenants/{company_id}/domain")
def get_domain_config(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return custom domain configuration for a tenant."""
    company = _get_company(company_id, db)
    settings = company.settings or {}
    subdomain = settings.get("subdomain", company.name.lower().replace(" ", "-"))

    return {
        "company_id": str(company_id),
        "default_url": f"https://{subdomain}.vireon.ai",
        "custom_domain": settings.get("custom_domain"),
        "ssl_enabled": settings.get("ssl_enabled", False),
        "dns_verified": settings.get("dns_verified", False),
        "cname_target": "cname.vireon.ai",
        "instructions": [
            "Add a CNAME record pointing your domain to cname.vireon.ai",
            "Wait for DNS propagation (up to 48 hours)",
            "Call PUT /white-label/tenants/{id}/domain to register",
            "SSL certificate will be auto-provisioned via Let's Encrypt",
        ],
    }


@router.put("/tenants/{company_id}/domain")
def set_custom_domain(
    company_id: uuid.UUID,
    payload: DomainConfig,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Register a custom domain for a tenant."""
    company = _get_company(company_id, db)
    settings = dict(company.settings or {})
    settings["custom_domain"] = payload.custom_domain
    settings["ssl_enabled"] = payload.ssl_enabled
    settings["dns_verified"] = False
    company.settings = settings
    db.commit()

    return {
        "company_id": str(company_id),
        "custom_domain": payload.custom_domain,
        "ssl_enabled": payload.ssl_enabled,
        "dns_verified": False,
        "status": "pending_dns_verification",
        "message": f"Domain {payload.custom_domain} registered. Add a CNAME to cname.vireon.ai and DNS verification will complete automatically.",
    }


@router.get("/tenants/{company_id}/usage")
def get_tenant_usage(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return usage metrics for a tenant (users, invoices, API calls, storage)."""
    company = _get_company(company_id, db)

    user_count = db.query(models.Employee).filter(models.Employee.company_id == company_id).count()
    invoice_count = db.query(models.Invoice).filter(models.Invoice.company_id == company_id).count()
    audit_count = db.query(models.AuditEvent).filter(models.AuditEvent.company_id == company_id).count()
    ledger_count = db.query(models.FinancialLedgerEntry).filter(
        models.FinancialLedgerEntry.company_id == company_id
    ).count()

    plan = (company.settings or {}).get("plan", "starter")
    plan_limits = {
        "starter": {"users": 5, "invoices": 500, "api_calls_monthly": 10000},
        "growth": {"users": 25, "invoices": 5000, "api_calls_monthly": 100000},
        "enterprise": {"users": -1, "invoices": -1, "api_calls_monthly": -1},
    }
    limits = plan_limits.get(plan, plan_limits["starter"])

    return {
        "company_id": str(company_id),
        "plan": plan,
        "usage": {
            "users": user_count,
            "invoices": invoice_count,
            "ledger_entries": ledger_count,
            "audit_events": audit_count,
        },
        "limits": limits,
        "utilization": {
            "users_pct": round(user_count / limits["users"] * 100, 1) if limits["users"] > 0 else 0,
            "invoices_pct": round(invoice_count / limits["invoices"] * 100, 1) if limits["invoices"] > 0 else 0,
        },
    }
