"""
Financial alert system for detecting and notifying on anomalies and risks.
Sends email alerts to CEO, Finance team for critical financial events.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import math
import os
import re
import models
import database
import auth
from services import burn_service
from tasks import alert_tasks

router = APIRouter(prefix="/financial-alerts", tags=["alerts"])

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _safe_number(value: Any, default: float = 0.0) -> float:
    try:
        num = float(value)
        return num if math.isfinite(num) else default
    except Exception:
        return default


def _extract_valid_emails(value: Any) -> List[str]:
    """Extract valid email addresses from strings/lists and deduplicate while preserving order."""
    candidates: List[str] = []
    if isinstance(value, str):
        candidates.extend(EMAIL_REGEX.findall(value))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, str):
                candidates.extend(EMAIL_REGEX.findall(item))

    deduped: List[str] = []
    seen = set()
    for email in candidates:
        normalized = email.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _calculate_financial_risk_score(company_id: UUID, db: Session) -> Dict[str, Any]:
    """Calculate comprehensive financial risk score (0-100, higher=riskier)."""
    try:
        month = date.today().strftime("%Y-%m")
        
        # Get burn metrics
        burn_data = burn_service.get_net_burn(company_id, db, month)
        burn_multiple = burn_service.get_burn_multiple(company_id, db, month)
        expense_breakdown = burn_service.get_expense_breakdown(company_id, db, month)
        
        risk_factors = {
            "high_burn_multiple": 0,  # 0-25 points
            "runway_critical": 0,      # 0-35 points
            "expense_spike": 0,         # 0-15 points
            "low_margin": 0,            # 0-15 points
            "concentration_risk": 0,    # 0-10 points
        }
        
        # Factor 1: Burn Multiple (0-25)
        bm = _safe_number(burn_multiple.get("burn_multiple", 0), 0.0)
        if bm > 3:
            risk_factors["high_burn_multiple"] = 25
        elif bm > 2:
            risk_factors["high_burn_multiple"] = 18
        elif bm > 1.5:
            risk_factors["high_burn_multiple"] = 10
        elif bm > 1:
            risk_factors["high_burn_multiple"] = 5
        
        # Factor 2: Runway Critical (0-35)
        cash = _safe_number(burn_data.get("total_credits", 0), 0.0)
        net_burn = _safe_number(burn_data.get("net_burn", 0), 0.0)
        runway_months = (cash / net_burn * 30) if net_burn > 0 else float('inf')
        safe_runway = _safe_number(runway_months, 9999.0)
        
        if runway_months < 3:
            risk_factors["runway_critical"] = 35
        elif runway_months < 6:
            risk_factors["runway_critical"] = 25
        elif runway_months < 12:
            risk_factors["runway_critical"] = 15
        elif runway_months < 18:
            risk_factors["runway_critical"] = 5
        
        # Factor 3: Expense Spike (0-15)
        # Compare current month to last 3 months average
        curr_burn = burn_data.get("net_burn", 0)
        prev_month = (datetime.strptime(month, "%Y-%m") - timedelta(days=1)).strftime("%Y-%m")
        prev_data = burn_service.get_net_burn(company_id, db, prev_month)
        prev_burn = prev_data.get("net_burn", 0)
        
        if curr_burn > 0 and prev_burn > 0:
            burn_increase = ((curr_burn - prev_burn) / prev_burn) * 100
            if burn_increase > 30:
                risk_factors["expense_spike"] = 15
            elif burn_increase > 15:
                risk_factors["expense_spike"] = 10
            elif burn_increase > 5:
                risk_factors["expense_spike"] = 5
        
        # Factor 4: Low Margin (0-15)
        products = burn_service.get_product_pl(company_id, db, month)
        avg_margin = sum(p.get("gross_margin_pct", 0) for p in products.values()) / len(products) if products else 0
        
        if avg_margin < 10:
            risk_factors["low_margin"] = 15
        elif avg_margin < 20:
            risk_factors["low_margin"] = 10
        elif avg_margin < 30:
            risk_factors["low_margin"] = 5
        
        # Factor 5: Concentration Risk (0-10) - any expense > 40% of burn
        breakdown = burn_data.get("breakdown_by_category", {})
        max_category_pct = max((v / net_burn * 100) if net_burn > 0 else 0 for v in breakdown.values())
        
        if max_category_pct > 50:
            risk_factors["concentration_risk"] = 10
        elif max_category_pct > 40:
            risk_factors["concentration_risk"] = 7
        elif max_category_pct > 35:
            risk_factors["concentration_risk"] = 4
        
        total_risk_score = sum(risk_factors.values())
        
        return {
            "total_score": min(100, total_risk_score),
            "factors": risk_factors,
            "runway_months": safe_runway,
            "burn_multiple": bm,
            "breakdown": burn_data.get("breakdown_by_category", {}),
        }
    
    except Exception as e:
        print(f"Error calculating risk score: {e}")
        return {
            "total_score": 0,
            "factors": {},
            "error": str(e),
        }


def _detect_anomalies(company_id: UUID, db: Session) -> List[Dict[str, Any]]:
    """Detect financial anomalies that should trigger alerts."""
    anomalies = []
    month = date.today().strftime("%Y-%m")
    
    try:
        burn_data = burn_service.get_net_burn(company_id, db, month)
        breakdown = burn_data.get("breakdown_by_category", {})
        net_burn = burn_data.get("net_burn", 0)
        
        # Anomaly 1: Expense category spike > 50% MoM
        prev_month = (datetime.strptime(month, "%Y-%m") - timedelta(days=1)).strftime("%Y-%m")
        prev_breakdown = burn_service.get_net_burn(company_id, db, prev_month).get("breakdown_by_category", {})
        
        for category, amount in breakdown.items():
            prev_amount = prev_breakdown.get(category, 0)
            if prev_amount > 0:
                pct_change = ((amount - prev_amount) / prev_amount) * 100
                if pct_change > 50:
                    anomalies.append({
                        "type": "expense_spike",
                        "severity": "warning" if pct_change < 75 else "critical",
                        "category": category,
                        "message": f"{category} expense increased {pct_change:.1f}% month-over-month",
                        "current_value": float(amount),
                        "previous_value": float(prev_amount),
                        "pct_change": pct_change,
                    })
        
        # Anomaly 2: Zero revenue month
        revenue_entries = db.query(models.FinancialLedgerEntry).filter(
            models.FinancialLedgerEntry.company_id == company_id,
            models.FinancialLedgerEntry.transaction_date >= datetime.strptime(month + "-01", "%Y-%m-%d").date(),
            models.FinancialLedgerEntry.entry_type == models.LedgerEntryType.CREDIT,
        ).all()
        
        total_revenue = sum(float(e.amount_inr) for e in revenue_entries)
        if total_revenue == 0:
            anomalies.append({
                "type": "zero_revenue",
                "severity": "critical",
                "message": "No revenue recorded this month - investigate billing/invoicing",
                "impact": "Runway impact: Critical",
            })
        
        # Anomaly 3: Runway crossing critical threshold
        cash = burn_data.get("total_credits", 0)
        runway_months = (cash / net_burn * 30) if net_burn > 0 else float('inf')
        
        if 0 < runway_months < 3:
            anomalies.append({
                "type": "critical_runway",
                "severity": "critical",
                "message": f"Only {runway_months:.1f} months of runway remaining",
                "runway_months": runway_months,
                "action": "Immediate action required - fundraise or cut costs",
            })
        elif 3 <= runway_months < 6:
            anomalies.append({
                "type": "low_runway",
                "severity": "warning",
                "message": f"Runway dropped below 6 months: {runway_months:.1f} months",
                "runway_months": runway_months,
                "action": "Begin contingency planning",
            })
        
        # Anomaly 4: Headcount increase without revenue increase
        employees = db.query(models.Employee).filter(
            models.Employee.company_id == company_id,
            models.Employee.status == "active"
        ).all()
        
        payroll_total = burn_data.get("breakdown_by_category", {}).get("payroll", 0) + \
                        burn_data.get("breakdown_by_category", {}).get("hiring", 0)
        
        if len(employees) > 5 and total_revenue < payroll_total:
            anomalies.append({
                "type": "negative_unit_economics",
                "severity": "warning",
                "message": f"Payroll (₹{payroll_total:,.0f}) exceeds revenue (₹{total_revenue:,.0f})",
                "payroll_total": float(payroll_total),
                "revenue_total": float(total_revenue),
                "implication": "Unsustainable cost structure",
            })
        
    except Exception as e:
        print(f"Error detecting anomalies: {e}")
    
    return anomalies


@router.get("/financial-health/{company_id}")
def get_financial_health(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Get comprehensive financial health assessment with risk score and anomalies."""
    try:
        risk_assessment = _calculate_financial_risk_score(company_id, db)
        anomalies = _detect_anomalies(company_id, db)
        
        # Determine overall health status
        score = risk_assessment.get("total_score", 0)
        if score >= 70:
            health_status = "critical"
        elif score >= 50:
            health_status = "warning"
        elif score >= 30:
            health_status = "caution"
        else:
            health_status = "healthy"
        
        return {
            "company_id": str(company_id),
            "health_status": health_status,
            "risk_score": score,
            "risk_factors": risk_assessment.get("factors", {}),
            "runway_months": risk_assessment.get("runway_months", 0),
            "burn_multiple": risk_assessment.get("burn_multiple", 0),
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "critical_anomalies": len([a for a in anomalies if a.get("severity") == "critical"]),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-alerts/{company_id}")
def send_financial_alerts(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_user_role: Optional[str] = Header(None),
):
    """
    Scan for financial anomalies and send alerts to CEO and Finance team.
    """
    try:
        resolved_role = (str(current_user.role) if current_user and getattr(current_user, "role", None) else (x_user_role or "")).lower()
        if resolved_role not in ["ceo", "finance", "system"]:
            raise HTTPException(status_code=403, detail="Only authorized roles can trigger alerts")
        
        company = db.query(models.Company).filter(models.Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get health assessment
        health = get_financial_health(company_id, db, current_user)
        anomalies = health.get("anomalies", [])
        
        # Get notification contacts
        contacts = company.notification_contacts or {}
        generic_email_list = _extract_valid_emails(contacts.get("email", []))
        email_recipients = _extract_valid_emails(contacts.get("email_recipients", []))
        ceo_recipients = _extract_valid_emails(contacts.get("ceo"))
        finance_emails = _extract_valid_emails(contacts.get("finance", []))

        secondary_recipients = []
        for email in generic_email_list + email_recipients + finance_emails:
            if email not in secondary_recipients and email not in ceo_recipients:
                secondary_recipients.append(email)

        if not ceo_recipients and not secondary_recipients:
            return {
                "success": True,
                "message": "No recipients configured for alerts",
                "anomalies_detected": len(anomalies),
            }
        
        # Compose alert email
        if anomalies:
            subject = f"🚨 Financial Alert: {len(anomalies)} anomalies detected"
            
            anomaly_text = "\n\n".join([
                f"⚠️ {a.get('type', 'Unknown').upper()}\n"
                f"   Severity: {a.get('severity', 'unknown')}\n"
                f"   Message: {a.get('message', 'No details')}"
                for a in anomalies
            ])
            
            detailed_message = f"""
Financial Anomalies Detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMPANY
=======
{company.name}

EXECUTIVE SUMMARY
=================
Anomaly count: {len(anomalies)}
Critical issues: {health.get('critical_anomalies', 0)}
Overall risk score: {health.get('risk_score', 0)}/100
Health status: {health.get('health_status', 'unknown').upper()}
Runway: {health.get('runway_months', 0):.1f} months
Burn multiple: {health.get('burn_multiple', 0):.2f}x

DETAILED ANOMALIES
==================
{anomaly_text}

RECOMMENDED NEXT STEPS
======================
1. Review the detailed dashboard for category-level impact.
2. Prioritize the critical anomalies first.
3. Decide whether to freeze discretionary spend or escalate collections.

--
VIREON AI Financial Alert System
"""

            summary_message = f"""
Financial Anomalies Detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Anomalies detected: {len(anomalies)}
Critical issues: {health.get('critical_anomalies', 0)}
Overall risk score: {health.get('risk_score', 0)}/100
Runway: {health.get('runway_months', 0):.1f} months

Please review the detailed dashboard for the full anomaly breakdown.

--
VIREON AI Financial Alert System
"""

            # Send the CEO a detailed report first, then send the summary to everyone else.
            delivery_results = []
            sender_override = ceo_recipients[0] if ceo_recipients else None

            for recipient in ceo_recipients:
                try:
                    sent, error = alert_tasks.send_email(
                        recipient=recipient,
                        subject=subject,
                        body=detailed_message,
                        sender_override=sender_override,
                    )
                    delivery_results.append({"recipient": recipient, "sent": bool(sent), "error": error, "message_type": "detailed"})
                except Exception as e:
                    delivery_results.append({"recipient": recipient, "sent": False, "error": str(e), "message_type": "detailed"})

            for recipient in secondary_recipients:
                try:
                    sent, error = alert_tasks.send_email(
                        recipient=recipient,
                        subject=subject,
                        body=summary_message,
                        sender_override=sender_override,
                    )
                    delivery_results.append({"recipient": recipient, "sent": bool(sent), "error": error, "message_type": "summary"})
                except Exception as e:
                    delivery_results.append({"recipient": recipient, "sent": False, "error": str(e), "message_type": "summary"})
        else:
            delivery_results = []
        
        smtp_host = (os.getenv("SMTP_HOST") or "").strip().lower()
        local_mode = smtp_host in {"mailhog", "localhost", "127.0.0.1"}
        local_hint = " (local SMTP mode: view messages at http://localhost:8025)" if local_mode else ""

        success_count = len([r for r in delivery_results if r.get("sent")]) if delivery_results else 0
        failed = [r for r in delivery_results if not r.get("sent")]

        overall_success = (success_count > 0 and len(failed) == 0) or (not anomalies)
        if not anomalies:
            message_text = "No anomalies detected; no emails were sent."
        elif not delivery_results:
            message_text = f"Alerts processed for {len(ceo_recipients) + len(secondary_recipients)} recipients{local_hint}"
        elif overall_success:
            message_text = f"Alerts sent to {success_count} recipients{local_hint}"
        else:
            first_error = failed[0].get("error") if failed else "Unknown SMTP error"
            message_text = f"Delivery failed for {len(failed)} recipients: {first_error}"

        return {
            "success": overall_success,
            "message": message_text,
            "recipients": ceo_recipients + secondary_recipients,
            "ceo_recipients": ceo_recipients,
            "secondary_recipients": secondary_recipients,
            "sent_count": success_count,
            "failed_count": len(failed),
            "delivery_results": delivery_results,
            "anomalies_detected": len(anomalies),
            "critical_anomalies": health.get("critical_anomalies", 0),
            "health_assessment": health,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure-alerts/{company_id}")
def configure_alert_recipients(
    company_id: UUID,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_user_role: Optional[str] = Header(None),
):
    """Configure email recipients for financial alerts."""
    try:
        company = db.query(models.Company).filter(models.Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Initialize if needed
        if not company.notification_contacts:
            company.notification_contacts = {}
        
        # Cleanly extract and set fields
        ceo_candidates = _extract_valid_emails(payload.get("ceo") or "")
        ceo_email = ceo_candidates[0] if ceo_candidates else None
        finance_list = _extract_valid_emails(payload.get("finance") or [])
        email_list = _extract_valid_emails(payload.get("email_recipients") or [])

        # Clean and filter to valid values only.
        parsed_contacts = {
            "ceo": ceo_email,
            "finance": finance_list,
            "email_recipients": email_list,
        }
        
        # Keep existing email field if present (for backward compatibility)
        if "email" in company.notification_contacts:
            parsed_contacts["email"] = company.notification_contacts["email"]
        
        # Replace entire notification_contacts dict
        company.notification_contacts = parsed_contacts
        db.add(company)
        db.commit()
        db.refresh(company)
        
        return {
            "success": True,
            "message": "Alert recipients configured successfully",
            "recipients_count": len(set(([ceo_email] if ceo_email else []) + finance_list + email_list)),
            "notification_contacts": company.notification_contacts,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")


@router.post("/test-alert/{company_id}")
def send_test_alert(
    company_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Send a test financial alert to verify email configuration."""
    try:
        company = db.query(models.Company).filter(models.Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        contacts = company.notification_contacts or {}
        candidate_recipients: List[str] = []
        candidate_recipients.extend(_extract_valid_emails(contacts.get("email", [])))
        candidate_recipients.extend(_extract_valid_emails(contacts.get("email_recipients", [])))
        candidate_recipients.extend(_extract_valid_emails(contacts.get("ceo")))
        candidate_recipients.extend(_extract_valid_emails(contacts.get("finance", [])))
        if current_user.email:
            candidate_recipients.extend(_extract_valid_emails(current_user.email))

        seen = set()
        deduped = []
        for recipient in candidate_recipients:
            if recipient not in seen:
                seen.add(recipient)
                deduped.append(recipient)
        if not deduped:
            raise HTTPException(status_code=400, detail="No email recipient configured")
        
        test_message = f"""
Test Alert from VIREON AI Financial Alert System
Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test alert to verify your email configuration is working correctly.

If you received this message, your alerts are configured properly!

--
VIREON AI
"""
        
        delivery_results = []
        for recipient in deduped:
            success, error = alert_tasks.send_email(
                recipient=recipient,
                subject="✅ VIREON Test Alert",
                body=test_message,
            )
            delivery_results.append({"recipient": recipient, "sent": bool(success), "error": error})

        sent_count = len([r for r in delivery_results if r["sent"]])
        failed_count = len(delivery_results) - sent_count
        overall_success = failed_count == 0 and sent_count > 0
        
        return {
            "success": overall_success,
            "message": f"Test alert sent to {sent_count} recipients" if overall_success else f"Delivery failed for {failed_count} recipients",
            "recipient": deduped[0],
            "recipients": deduped,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "delivery_results": delivery_results,
            "error": delivery_results[0]["error"] if failed_count > 0 else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
