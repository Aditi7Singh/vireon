"""
Anomaly Detection Scanner
========================
Core anomaly detection engine with statistical analysis.
"""

import os
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config.settings import BACKEND_URL, DATABASE_URL
import anomaly_detection
import models


# Alert threshold rules
ALERT_RULES = {
    "warning": {"stddev": 1.5, "delta_pct": 15.0},
    "critical": {"stddev": 2.5, "delta_pct": 50.0}
}


def load_gl_transactions(days_back: int = 90) -> pd.DataFrame:
    """
    Load GL transactions from ERPNext API.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        DataFrame with columns: date, category, vendor, amount, gl_account
    """
    try:
        # Try to fetch from ERPNext
        response = httpx.get(
            f"{BACKEND_URL}/expenses",
            params={"months": min(days_back // 30, 12)},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            breakdown = data.get("breakdown", {})
            if isinstance(breakdown, dict) and breakdown:
                rows = [{"date": datetime.utcnow().date().isoformat(), "category": category, "vendor": category, "amount": amount, "gl_account": category} for category, amount in breakdown.items()]
                df = pd.DataFrame(rows)
                if not df.empty:
                    return df
    except Exception as e:
        print(f"Could not fetch from ERPNext: {e}")
    
    # Return empty DataFrame if no data
    return pd.DataFrame(columns=["date", "category", "vendor", "amount", "gl_account"])


def calculate_baselines(df: pd.DataFrame) -> Dict:
    """
    Calculate baseline statistics per expense category.
    
    Args:
        df: DataFrame of transactions
        
    Returns:
        Dictionary of category -> baseline statistics
    """
    if df.empty:
        return {}
    
    baselines = {}
    
    for category in df["category"].unique():
        cat_df = df[df["category"] == category]
        
        amounts = cat_df["amount"].values
        monthly_totals = cat_df.groupby("month")["amount"].sum() if "month" in cat_df.columns else amounts
        
        baselines[category] = {
            "avg": np.mean(amounts) if len(amounts) > 0 else 0,
            "stddev": np.std(amounts) if len(amounts) > 1 else 0,
            "monthly_values": list(monthly_totals) if len(monthly_totals) > 0 else [],
            "n_transactions": len(amounts)
        }
    
    return baselines


def detect_spike_alerts(
    df: pd.DataFrame, 
    baselines: Dict,
    thresholds: Dict = ALERT_RULES
) -> List[Dict]:
    """
    Detect spending spikes based on statistical thresholds.
    
    Args:
        df: DataFrame of transactions
        baselines: Calculated baseline statistics
        thresholds: Alert threshold rules
        
    Returns:
        List of alert dictionaries
    """
    alerts = []
    
    for category, baseline in baselines.items():
        if baseline["n_transactions"] < 2:
            continue
        
        avg = baseline["avg"]
        stddev = baseline["stddev"]
        
        # Check each transaction against thresholds
        cat_df = df[df["category"] == category]
        
        for _, row in cat_df.iterrows():
            amount = row.get("amount", 0)
            if avg > 0:
                delta_pct = ((amount - avg) / avg) * 100
                
                # Check critical threshold
                if delta_pct > thresholds["critical"]["delta_pct"] and amount > (avg + thresholds["critical"]["stddev"] * stddev):
                    alerts.append({
                        "severity": "critical",
                        "alert_type": "spike",
                        "category": category,
                        "amount": amount,
                        "baseline": avg,
                        "delta_pct": delta_pct,
                        "description": f"{category.title()} ${amount:,.0f} vs expected ${avg:,.0f} (+{delta_pct:.1f}%)",
                        "runway_impact": calculate_runway_impact(amount - avg)
                    })
                # Check warning threshold
                elif delta_pct > thresholds["warning"]["delta_pct"] and amount > (avg + thresholds["warning"]["stddev"] * stddev):
                    alerts.append({
                        "severity": "warning",
                        "alert_type": "spike",
                        "category": category,
                        "amount": amount,
                        "baseline": avg,
                        "delta_pct": delta_pct,
                        "description": f"{category.title()} ${amount:,.0f} vs expected ${avg:,.0f} (+{delta_pct:.1f}%)",
                        "runway_impact": calculate_runway_impact(amount - avg)
                    })
    
    return alerts


def detect_trend_alerts(baselines: Dict) -> List[Dict]:
    """
    Detect spending trends over multiple months.
    
    Args:
        baselines: Calculated baseline statistics
        
    Returns:
        List of trend alert dictionaries
    """
    alerts = []
    
    for category, baseline in baselines.items():
        monthly_values = baseline.get("monthly_values", [])
        
        if len(monthly_values) < 3:
            continue
        
        # Simple linear trend detection
        months = np.arange(len(monthly_values))
        if np.std(monthly_values) > 0:
            slope = np.polyfit(months, monthly_values, 1)[0]
            avg_monthly = np.mean(monthly_values)
            
            if avg_monthly > 0:
                monthly_growth_pct = (slope / avg_monthly) * 100
                
                # Alert if growing > 5% per month for 3+ months
                if monthly_growth_pct > 5:
                    alerts.append({
                        "severity": "warning",
                        "alert_type": "trend",
                        "category": category,
                        "amount": monthly_values[-1],
                        "baseline": avg_monthly,
                        "delta_pct": monthly_growth_pct * len(monthly_values),
                        "description": f"{category.title()} growing {monthly_growth_pct:.1f}%/month for {len(monthly_values)} months",
                        "runway_impact": calculate_runway_impact(monthly_values[-1] - avg_monthly)
                    })
    
    return alerts


def detect_duplicate_payments(df: pd.DataFrame, window_days: int = 30) -> List[Dict]:
    """
    Detect potential duplicate payments.
    
    Args:
        df: DataFrame of transactions
        window_days: Window for duplicate detection
        
    Returns:
        List of duplicate alert dictionaries
    """
    alerts = []
    
    if df.empty or "vendor" not in df.columns:
        return alerts
    
    # Group by vendor and amount
    for (vendor, amount), group in df.groupby(["vendor", "amount"]):
        if len(group) > 1 and amount > 0:
            # Check if within time window
            dates = pd.to_datetime(group.get("date", []))
            if len(dates) > 1:
                dates_sorted = sorted(dates)
                for i in range(1, len(dates_sorted)):
                    if (dates_sorted[i] - dates_sorted[i-1]).days <= window_days:
                        alerts.append({
                            "severity": "critical",
                            "alert_type": "duplicate",
                            "category": "general",
                            "amount": amount,
                            "baseline": 0,
                            "delta_pct": 100,
                            "description": f"Potential duplicate: {vendor} charged ${amount:,.0f} twice within {window_days} days",
                            "runway_impact": calculate_runway_impact(amount),
                            "vendor": vendor
                        })
    
    return alerts


def detect_duplicate_expenses(db) -> List[Dict]:
    """Detect duplicate expenses using company, vendor, amount, and transaction date."""
    alerts: List[Dict] = []
    try:
        rows = (
            db.query(models.Expense.company_id, models.Expense.contact_id, models.Expense.total_amount, models.Expense.transaction_date, models.Expense.category)
            .all()
        )
        seen = {}
        for company_id, contact_id, amount, transaction_date, category in rows:
            key = (str(company_id), str(contact_id), float(amount or 0), transaction_date)
            seen[key] = seen.get(key, 0) + 1
        for (company_id, contact_id, amount, transaction_date, category), count in seen.items():
            if count > 1 and amount > 0:
                alerts.append({
                    "severity": "critical",
                    "alert_type": "duplicate",
                    "category": category or "general",
                    "amount": amount,
                    "baseline": amount,
                    "delta_pct": 100.0,
                    "description": f"Duplicate expense detected for {category or 'general'} on {transaction_date}",
                    "runway_impact": 0.0,
                    "suggested_owner": "Finance",
                })
    except Exception as exc:
        print(f"[SCANNER] duplicate expense detector failed: {exc}")
    return alerts


def detect_unusual_payment_patterns(db) -> List[Dict]:
    """Detect unusually large or clustered vendor payments."""
    alerts: List[Dict] = []
    try:
        rows = db.query(models.Expense.contact_id, models.Expense.total_amount, models.Expense.transaction_date, models.Expense.category).all()
        grouped: Dict[str, List[float]] = {}
        for contact_id, amount, *_ in rows:
            key = str(contact_id)
            grouped.setdefault(key, []).append(float(amount or 0))
        for contact_id, amounts in grouped.items():
            if len(amounts) < 3:
                continue
            avg = float(np.mean(amounts))
            latest = amounts[-1]
            if avg > 0 and latest > avg * 1.75:
                alerts.append({
                    "severity": "warning",
                    "alert_type": "timing",
                    "category": "vendor",
                    "amount": latest,
                    "baseline": avg,
                    "delta_pct": round(((latest - avg) / avg) * 100, 1),
                    "description": f"Latest vendor payment is materially above history for contact {contact_id}",
                    "runway_impact": 0.0,
                    "suggested_owner": "Finance",
                })
    except Exception as exc:
        print(f"[SCANNER] payment pattern detector failed: {exc}")
    return alerts


def detect_vendor_pricing_anomalies(db) -> List[Dict]:
    """Detect vendor pricing drift using contact-level expense history."""
    alerts: List[Dict] = []
    try:
        rows = db.query(models.Expense.contact_id, models.Expense.total_amount, models.Expense.category).all()
        grouped: Dict[str, List[float]] = {}
        for contact_id, amount, _ in rows:
            grouped.setdefault(str(contact_id), []).append(float(amount or 0))
        for contact_id, amounts in grouped.items():
            if len(amounts) < 4:
                continue
            baseline = float(np.mean(amounts[:-1]))
            latest = amounts[-1]
            if baseline > 0:
                delta_pct = ((latest - baseline) / baseline) * 100
                if delta_pct >= 40:
                    alerts.append({
                        "severity": "warning" if delta_pct < 80 else "critical",
                        "alert_type": "vendor",
                        "category": "vendor_pricing",
                        "amount": latest,
                        "baseline": baseline,
                        "delta_pct": round(delta_pct, 1),
                        "description": f"Vendor pricing increased {delta_pct:.1f}% for contact {contact_id}",
                        "runway_impact": 0.0,
                        "suggested_owner": "Finance",
                    })
    except Exception as exc:
        print(f"[SCANNER] vendor pricing detector failed: {exc}")
    return alerts


def detect_payroll_anomalies(db) -> List[Dict]:
    """Detect overtime or payroll spikes from monthly payroll entries."""
    alerts: List[Dict] = []
    try:
        rows = db.query(models.PayrollEntry.pay_date, models.PayrollEntry.gross_pay, models.PayrollEntry.department).all()
        if not rows:
            return alerts
        monthly = {}
        for pay_date, gross_pay, department in rows:
            month_key = pay_date.strftime("%Y-%m") if pay_date else "unknown"
            monthly.setdefault(month_key, []).append(float(gross_pay or 0))
        series = [sum(values) for _, values in sorted(monthly.items())]
        if len(series) >= 3:
            baseline = float(np.mean(series[:-1]))
            latest = series[-1]
            if baseline > 0 and latest > baseline * 1.25:
                alerts.append({
                    "severity": "warning" if latest < baseline * 1.5 else "critical",
                    "alert_type": "spike",
                    "category": "payroll",
                    "amount": latest,
                    "baseline": baseline,
                    "delta_pct": round(((latest - baseline) / baseline) * 100, 1),
                    "description": "Payroll spike detected versus trailing average",
                    "runway_impact": 0.0,
                    "suggested_owner": "People",
                })
    except Exception as exc:
        print(f"[SCANNER] payroll detector failed: {exc}")
    return alerts


def detect_subscription_churn_alerts(db) -> List[Dict]:
    """Flag revenue drops that imply churn acceleration."""
    alerts: List[Dict] = []
    try:
        metrics = (
            db.query(models.MonthlyMetric)
            .order_by(models.MonthlyMetric.metric_month.asc())
            .all()
        )
        if len(metrics) < 3:
            return alerts
        revenues = [float(metric.total_revenue or 0) for metric in metrics]
        baseline = float(np.mean(revenues[:-1]))
        latest = revenues[-1]
        if baseline > 0 and latest < baseline * 0.9:
            alerts.append({
                "severity": "warning",
                "alert_type": "revenue_drop",
                "category": "subscription",
                "amount": latest,
                "baseline": baseline,
                "delta_pct": round(((latest - baseline) / baseline) * 100, 1),
                "description": "Subscription revenue is below trend, indicating potential churn acceleration",
                "runway_impact": 0.0,
                "suggested_owner": "Revenue",
            })
    except Exception as exc:
        print(f"[SCANNER] churn detector failed: {exc}")
    return alerts


def detect_customer_concentration_risk(db) -> List[Dict]:
    """Flag concentration when one customer dominates open receivables."""
    alerts: List[Dict] = []
    try:
        rows = db.query(models.Invoice.contact_id, models.Invoice.amount_due).filter(
            models.Invoice.type == "ACCOUNTS_RECEIVABLE",
            models.Invoice.amount_due > 0,
        ).all()
        if not rows:
            return alerts
        by_customer: Dict[str, float] = {}
        for contact_id, amount in rows:
            by_customer[str(contact_id)] = by_customer.get(str(contact_id), 0.0) + float(amount or 0)
        total = sum(by_customer.values())
        if total <= 0:
            return alerts
        top_customer, top_amount = max(by_customer.items(), key=lambda item: item[1])
        share = (top_amount / total) * 100
        if share >= 25:
            alerts.append({
                "severity": "warning" if share < 40 else "critical",
                "alert_type": "timing",
                "category": "customer_concentration",
                "amount": top_amount,
                "baseline": total,
                "delta_pct": round(share, 1),
                "description": f"Top customer {top_customer} represents {share:.1f}% of AR",
                "runway_impact": 0.0,
                "suggested_owner": "CEO",
            })
    except Exception as exc:
        print(f"[SCANNER] customer concentration detector failed: {exc}")
    return alerts


def detect_supply_chain_cost_anomalies(db) -> List[Dict]:
    """Detect cloud and supply-chain style spend spikes by category."""
    alerts: List[Dict] = []
    try:
        rows = db.query(models.Expense.category, models.Expense.total_amount).all()
        grouped: Dict[str, List[float]] = {}
        for category, amount in rows:
            grouped.setdefault((category or "misc").lower(), []).append(float(amount or 0))
        for category, amounts in grouped.items():
            if len(amounts) < 4:
                continue
            baseline = float(np.mean(amounts[:-1]))
            latest = amounts[-1]
            if baseline > 0 and latest > baseline * 1.4:
                alerts.append({
                    "severity": "warning" if latest < baseline * 2 else "critical",
                    "alert_type": "spike",
                    "category": category,
                    "amount": latest,
                    "baseline": baseline,
                    "delta_pct": round(((latest - baseline) / baseline) * 100, 1),
                    "description": f"Supply-chain style cost anomaly in {category}",
                    "runway_impact": 0.0,
                    "suggested_owner": "Operations",
                })
    except Exception as exc:
        print(f"[SCANNER] supply chain detector failed: {exc}")
    return alerts


def detect_new_vendor_anomalies(df: pd.DataFrame, threshold: float = 1000) -> List[Dict]:
    """
    Flag new vendors with significant charges.
    
    Args:
        df: DataFrame of transactions
        threshold: Minimum amount to flag
        
    Returns:
        List of new vendor alert dictionaries
    """
    alerts = []
    
    # This would require historical data to properly detect new vendors
    # For now, flag any significant charge without a clear pattern
    
    return alerts


def calculate_runway_impact(monthly_excess: float) -> float:
    """
    Calculate runway impact in months.
    
    Args:
        monthly_excess: Monthly amount over baseline
        
    Returns:
        Runway impact in months (negative = reduction)
    """
    try:
        # Get current burn from backend
        response = httpx.get(f"{BACKEND_URL}/burn-rate", timeout=10)
        if response.status_code == 200:
            data = response.json()
            monthly_burn = data.get("monthly_burn", 1)
            
            # Get current runway
            response = httpx.get(f"{BACKEND_URL}/runway", timeout=10)
            if response.status_code == 200:
                runway_data = response.json()
                current_runway = runway_data.get("runway_months", 1)
                
                return (monthly_excess / monthly_burn) * current_runway
    except Exception:
        pass
    
    return 0.0


def write_alerts_to_db(alerts: List[Dict]) -> int:
    """
    Write alerts to PostgreSQL database.
    
    Args:
        alerts: List of alert dictionaries
        
    Returns:
        Number of new alerts written
    """
    if not DATABASE_URL or not alerts:
        print(f"[SCANNER] No database configured or no alerts to write")
        return 0
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Insert alerts (simplified - would need full table schema)
            for alert in alerts:
                conn.execute(text("""
                    INSERT INTO alerts (severity, alert_type, category, amount, baseline, 
                                       delta_pct, description, runway_impact, status, created_at)
                    VALUES (:severity, :alert_type, :category, :amount, :baseline,
                           :delta_pct, :description, :runway_impact, 'active', NOW())
                """), alert)
            
            conn.commit()
            
        print(f"[SCANNER] Wrote {len(alerts)} new alerts to database")
        return len(alerts)
        
    except Exception as e:
        print(f"[SCANNER] Error writing to database: {e}")
        return 0


def run_full_scan() -> Dict:
    """
    Run the complete anomaly detection scan.
    
    Returns:
        Scan result summary dictionary
    """
    import time
    start_time = time.time()
    
    print("[SCANNER] Starting anomaly scan...")
    
    # Load data
    df = load_gl_transactions(days_back=90)
    print(f"[SCANNER] Loaded {len(df)} transactions")
    
    # Calculate baselines
    baselines = calculate_baselines(df)
    print(f"[SCANNER] Calculated baselines for {len(baselines)} categories")
    
    # Run detectors
    spike_alerts = detect_spike_alerts(df, baselines)
    trend_alerts = detect_trend_alerts(baselines)
    duplicate_alerts = detect_duplicate_payments(df)
    
    # Combine all alerts
    all_alerts = spike_alerts + trend_alerts + duplicate_alerts
    
    # Run additional detectors from anomaly_detection module
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # These functions add to the DB directly (anomaly table)
        anomaly_detection.detect_revenue_anomalies(db)
        anomaly_detection.detect_duplicate_invoices(db)

        duplicate_expense_alerts = detect_duplicate_expenses(db)
        vendor_pricing_alerts = detect_vendor_pricing_anomalies(db)
        payroll_alerts = detect_payroll_anomalies(db)
        churn_alerts = detect_subscription_churn_alerts(db)
        concentration_alerts = detect_customer_concentration_risk(db)
        supply_chain_alerts = detect_supply_chain_cost_anomalies(db)

        all_alerts.extend(
            duplicate_expense_alerts
            + vendor_pricing_alerts
            + payroll_alerts
            + churn_alerts
            + concentration_alerts
            + supply_chain_alerts
        )
        
        db.close()
        print("[SCANNER] Ran supplemental detectors (Revenue, Duplicates)")
    except Exception as e:
        print(f"[SCANNER] Supplemental detectors failed: {e}")
    
    # Count by severity
    critical_count = sum(1 for a in all_alerts if a["severity"] == "critical")
    warning_count = sum(1 for a in all_alerts if a["severity"] == "warning")
    
    # Write to database (spike, trend, duplicate_payment alerts)
    written = write_alerts_to_db(all_alerts)
    
    duration = time.time() - start_time
    
    result = {
        "alerts_found": len(all_alerts),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "written_to_db": written,
        "scan_duration_seconds": round(duration, 2)
    }
    
    print(f"[SCANNER] Scan complete: {result}")
    return result


if __name__ == "__main__":
    result = run_full_scan()
    print(f"Scan result: {result}")
