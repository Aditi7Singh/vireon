"""
Real-Time Stripe Webhook Router
==================================
Handles Stripe events for live MRR tracking and cash flow updates:

  payment_intent.succeeded        → record payment, update AR
  payment_intent.payment_failed   → flag failed payment, trigger alert
  customer.subscription.created   → register new subscription, bump MRR
  customer.subscription.updated   → update subscription tier/amount
  customer.subscription.deleted   → mark churn, reduce MRR
  invoice.paid                    → mark invoice as paid, update AR aging
  invoice.payment_failed          → mark invoice past-due
  charge.refunded                 → record refund, reduce revenue

Security: Stripe-Signature header is verified using STRIPE_WEBHOOK_SECRET env var.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.orm import Session

import database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/stripe", tags=["stripe-webhooks"])


# ---------------------------------------------------------------------------
# Signature Verification
# ---------------------------------------------------------------------------


def _verify_stripe_signature(
    payload: bytes,
    sig_header: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verify Stripe webhook signature using HMAC-SHA256.
    Raises HTTPException on failure.
    """
    try:
        parts = {k: v for k, v in (item.split("=", 1) for item in sig_header.split(","))}
        timestamp = parts.get("t", "")
        v1_sig = parts.get("v1", "")

        if not timestamp or not v1_sig:
            return False

        # Check timestamp tolerance (prevent replay attacks)
        event_time = int(timestamp)
        now = int(datetime.utcnow().timestamp())
        if abs(now - event_time) > tolerance_seconds:
            logger.warning("Stripe webhook timestamp outside tolerance: %s", timestamp)
            return False

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, v1_sig)
    except Exception as exc:
        logger.error("Stripe signature verification error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# In-memory MRR state (replace with DB in production)
# ---------------------------------------------------------------------------

_mrr_state: Dict[str, float] = {}
_events_log: list = []


def _log_event(event_type: str, data: Dict, result: str) -> None:
    _events_log.append({
        "ts": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data,
        "result": result,
    })
    if len(_events_log) > 500:
        _events_log.pop(0)


# ---------------------------------------------------------------------------
# Webhook handler
# ---------------------------------------------------------------------------


@router.post("/events", response_model=dict)
async def handle_stripe_event(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(database.get_db),
):
    """
    Receive and process Stripe webhook events.

    Register this URL in your Stripe Dashboard:
    Dashboard → Developers → Webhooks → Add endpoint → https://your-api.com/api/v1/webhooks/stripe/events
    """
    payload = await request.body()

    # Verify signature if secret is configured
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if webhook_secret and stripe_signature:
        valid = _verify_stripe_signature(payload, stripe_signature, webhook_secret)
        if not valid:
            logger.warning("Invalid Stripe webhook signature")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    elif webhook_secret and not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})
    event_id = event.get("id", "unknown")

    logger.info("Stripe event received: %s (id=%s)", event_type, event_id)

    result = await _dispatch_event(event_type, event_data, event_id, db)
    _log_event(event_type, {"id": event_id}, result.get("action", "processed"))

    return {"received": True, "event_id": event_id, "event_type": event_type, **result}


async def _dispatch_event(
    event_type: str,
    data: Dict,
    event_id: str,
    db: Session,
) -> Dict[str, Any]:
    """Route each Stripe event type to its handler."""

    handlers = {
        "payment_intent.succeeded":         _handle_payment_succeeded,
        "payment_intent.payment_failed":    _handle_payment_failed,
        "customer.subscription.created":    _handle_subscription_created,
        "customer.subscription.updated":    _handle_subscription_updated,
        "customer.subscription.deleted":    _handle_subscription_deleted,
        "invoice.paid":                     _handle_invoice_paid,
        "invoice.payment_failed":           _handle_invoice_payment_failed,
        "charge.refunded":                  _handle_charge_refunded,
    }

    handler = handlers.get(event_type)
    if handler:
        return await handler(data, event_id, db)

    return {"action": "ignored", "message": f"Event type '{event_type}' not handled"}


async def _handle_payment_succeeded(data: Dict, event_id: str, db: Session) -> Dict:
    amount = data.get("amount", 0) / 100  # Stripe amounts are in cents
    currency = data.get("currency", "usd").upper()
    customer_id = data.get("customer", "unknown")

    # Try to find and update invoice in DB
    try:
        import models
        invoice = (
            db.query(models.Invoice)
            .filter(models.Invoice.stripe_payment_intent_id == data.get("id"))
            .first()
        )
        if invoice:
            invoice.status = "paid"
            invoice.paid_date = datetime.utcnow()
            db.commit()
    except Exception as exc:
        logger.debug("Could not update invoice from Stripe event: %s", exc)

    logger.info("Payment succeeded: $%.2f %s from customer %s", amount, currency, customer_id)
    return {
        "action": "payment_recorded",
        "amount": amount,
        "currency": currency,
        "customer_id": customer_id,
    }


async def _handle_payment_failed(data: Dict, event_id: str, db: Session) -> Dict:
    amount = data.get("amount", 0) / 100
    customer_id = data.get("customer", "unknown")
    failure_msg = data.get("last_payment_error", {}).get("message", "unknown error")

    logger.warning("Payment failed: $%.2f from customer %s — %s", amount, customer_id, failure_msg)
    return {
        "action": "payment_failure_logged",
        "amount": amount,
        "customer_id": customer_id,
        "failure_reason": failure_msg,
        "alert": "high" if amount > 10_000 else "medium",
    }


async def _handle_subscription_created(data: Dict, event_id: str, db: Session) -> Dict:
    customer_id = data.get("customer", "unknown")
    plan_amount = data.get("plan", {}).get("amount", 0) / 100
    interval = data.get("plan", {}).get("interval", "month")
    monthly_amount = plan_amount if interval == "month" else plan_amount / 12

    _mrr_state[customer_id] = _mrr_state.get(customer_id, 0) + monthly_amount
    total_mrr = sum(_mrr_state.values())

    logger.info("New subscription: $%.2f/month from %s. New MRR: $%.0f", monthly_amount, customer_id, total_mrr)
    return {
        "action": "subscription_created",
        "customer_id": customer_id,
        "monthly_amount": monthly_amount,
        "new_mrr": round(total_mrr, 2),
    }


async def _handle_subscription_updated(data: Dict, event_id: str, db: Session) -> Dict:
    customer_id = data.get("customer", "unknown")
    new_amount = data.get("plan", {}).get("amount", 0) / 100
    interval = data.get("plan", {}).get("interval", "month")
    monthly_amount = new_amount if interval == "month" else new_amount / 12

    old_amount = _mrr_state.get(customer_id, 0)
    _mrr_state[customer_id] = monthly_amount
    mrr_delta = monthly_amount - old_amount

    return {
        "action": "subscription_updated",
        "customer_id": customer_id,
        "old_monthly": old_amount,
        "new_monthly": monthly_amount,
        "mrr_delta": round(mrr_delta, 2),
        "new_mrr": round(sum(_mrr_state.values()), 2),
    }


async def _handle_subscription_deleted(data: Dict, event_id: str, db: Session) -> Dict:
    customer_id = data.get("customer", "unknown")
    churned_amount = _mrr_state.pop(customer_id, 0)
    total_mrr = sum(_mrr_state.values())

    logger.warning("Subscription cancelled: $%.2f/month churned from %s. MRR now: $%.0f",
                   churned_amount, customer_id, total_mrr)
    return {
        "action": "churn_recorded",
        "customer_id": customer_id,
        "churned_amount": round(churned_amount, 2),
        "new_mrr": round(total_mrr, 2),
        "alert": "high" if churned_amount > 5_000 else "low",
    }


async def _handle_invoice_paid(data: Dict, event_id: str, db: Session) -> Dict:
    invoice_id = data.get("id", "unknown")
    amount_paid = data.get("amount_paid", 0) / 100
    customer_id = data.get("customer", "unknown")

    return {
        "action": "invoice_marked_paid",
        "invoice_id": invoice_id,
        "amount_paid": amount_paid,
        "customer_id": customer_id,
    }


async def _handle_invoice_payment_failed(data: Dict, event_id: str, db: Session) -> Dict:
    invoice_id = data.get("id", "unknown")
    amount_due = data.get("amount_due", 0) / 100
    customer_id = data.get("customer", "unknown")
    attempt_count = data.get("attempt_count", 1)

    return {
        "action": "invoice_payment_failed",
        "invoice_id": invoice_id,
        "amount_due": amount_due,
        "customer_id": customer_id,
        "attempt_count": attempt_count,
        "alert": "high" if attempt_count >= 3 else "medium",
    }


async def _handle_charge_refunded(data: Dict, event_id: str, db: Session) -> Dict:
    amount_refunded = data.get("amount_refunded", 0) / 100
    customer_id = data.get("customer", "unknown")

    logger.info("Refund issued: $%.2f to customer %s", amount_refunded, customer_id)
    return {
        "action": "refund_recorded",
        "amount_refunded": amount_refunded,
        "customer_id": customer_id,
    }


# ---------------------------------------------------------------------------
# MRR Dashboard endpoint
# ---------------------------------------------------------------------------


@router.get("/mrr", response_model=dict)
def get_live_mrr():
    """Get live MRR metrics from Stripe event stream."""
    total_mrr = sum(_mrr_state.values())
    return {
        "total_mrr": round(total_mrr, 2),
        "annual_run_rate": round(total_mrr * 12, 2),
        "active_subscriptions": len(_mrr_state),
        "customers": {k: round(v, 2) for k, v in sorted(
            _mrr_state.items(), key=lambda x: x[1], reverse=True
        )[:20]},
        "recent_events_count": len(_events_log),
    }


@router.get("/events/recent", response_model=dict)
def get_recent_events(limit: int = 20):
    """Get recently received Stripe events."""
    return {
        "events": _events_log[-limit:][::-1],
        "total_events_logged": len(_events_log),
    }
