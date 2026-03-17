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
from config.settings import BACKEND_URL, DATABASE_URL


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
            # Transform to DataFrame
            expenses = data.get("breakdown", [])
            df = pd.DataFrame(expenses)
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
    
    # Count by severity
    critical_count = sum(1 for a in all_alerts if a["severity"] == "critical")
    warning_count = sum(1 for a in all_alerts if a["severity"] == "warning")
    
    # Write to database
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
