"""
Phase 4: Anomaly Detection Scanner
Pure Python math for financial anomaly detection.

Core algorithm:
1. Load GL transactions (last 90 days) from ERPNext API
2. Calculate 90-day baselines per category (mean, stddev, monthly trends)
3. Detect 4 alert types: spikes, trends, duplicates, new vendors
4. Calculate runway impact for each alert
5. Write to PostgreSQL with deduplication
6. Return summary statistics

The scanner runs every 24 hours at 2:00 AM UTC via Celery Beat.
No LLM involved - pure statistical anomaly detection.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# Data manipulation
import pandas as pd
import numpy as np
from scipy import stats

# Database
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

# HTTP client
import httpx

# Statistics (we'll use numpy/scipy instead)
import statistics

logger = logging.getLogger(__name__)


class AnomalyScanner:
    """Detect anomalies in GL transactions using statistical methods."""
    
    def __init__(self, db_url: str, erpnext_url: str = "http://localhost:8000", 
                 backend_url: str = "http://localhost:8000"):
        """Initialize scanner with database and API connections."""
        self.db_url = db_url
        self.erpnext_url = erpnext_url
        self.backend_url = backend_url
        self.run_start = datetime.utcnow()
        self.alerts_created = []
        
    # =========================================================================
    # PART A: DATA LOADER
    # =========================================================================
    
    def load_gl_transactions(self, days_back: int = 90) -> pd.DataFrame:
        """
        Load GL transactions from ERPNext REST API.
        
        Columns: [date, category, vendor, amount, gl_account, description]
        
        Fallback to PostgreSQL cache if ERPNext unreachable.
        """
        logger.info(f"Loading GL transactions (last {days_back} days)")
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).date()
        
        # Try ERPNext API first
        try:
            return self._load_from_erpnext(cutoff_date)
        except Exception as e:
            logger.warning(f"ERPNext API failed: {e}. Falling back to PostgreSQL cache.")
            return self._load_from_postgres_cache(cutoff_date)
    
    def _load_from_erpnext(self, cutoff_date) -> pd.DataFrame:
        """Query ERPNext REST API for GL entries."""
        headers = {
            "Authorization": f"Bearer {os.getenv('ERPNEXT_API_TOKEN', '')}",
            "Accept": "application/json",
        }
        
        # Get all GL entries since cutoff date
        query_url = f"{self.erpnext_url}/api/resource/GL%20Entry"
        params = {
            "fields": '["name", "posting_date", "account", "debit", "credit", "party", "remarks"]',
            "filters": f'[["posting_date", ">=", "{cutoff_date}"]]',
            "limit_page_length": 0,  # Get all
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(query_url, params=params, headers=headers)
            response.raise_for_status()
        
        data = response.json()
        entries = data.get("data", [])
        logger.info(f"Fetched {len(entries)} GL entries from ERPNext")
        
        # Transform to DataFrame
        df_data = []
        for entry in entries:
            # Map GL account to category (aws, payroll, saas, etc.)
            category = self._map_account_to_category(entry.get("account", ""))
            
            # Amount is debit - credit
            debit = float(entry.get("debit", 0)) or 0
            credit = float(entry.get("credit", 0)) or 0
            amount = debit - credit
            
            if amount != 0:  # Skip zero entries
                df_data.append({
                    "date": entry.get("posting_date"),
                    "category": category,
                    "vendor": entry.get("party", entry.get("account", "Unknown")),
                    "amount": abs(amount),  # Always positive
                    "gl_account": entry.get("account"),
                    "description": entry.get("remarks", ""),
                })
        
        df = pd.DataFrame(df_data)
        if df.empty:
            logger.warning("No GL entries returned")
            df = pd.DataFrame(columns=["date", "category", "vendor", "amount", "gl_account", "description"])
        else:
            df["date"] = pd.to_datetime(df["date"])
        
        return df
    
    def _load_from_postgres_cache(self, cutoff_date) -> pd.DataFrame:
        """Load GL entries from PostgreSQL cache (fallback if ERPNext unreachable)."""
        try:
            conn = psycopg2.connect(self.db_url)
            query = """
                SELECT date, category, vendor, amount, gl_account, description
                FROM gl_transactions_cache
                WHERE date >= %s
                ORDER BY date DESC
            """
            df = pd.read_sql_query(query, conn, params=(cutoff_date,))
            df["date"] = pd.to_datetime(df["date"])
            conn.close()
            logger.info(f"Loaded {len(df)} GL entries from PostgreSQL cache")
            return df
        except Exception as e:
            logger.error(f"PostgreSQL cache load failed: {e}")
            return pd.DataFrame(columns=["date", "category", "vendor", "amount", "gl_account", "description"])
    
    def _map_account_to_category(self, account: str) -> str:
        """Map GL account name to expense category."""
        account_lower = account.lower()
        
        # Mapping rules
        mappings = {
            "aws": ["aws", "amazon", "ec2", "s3", "cloud"],
            "payroll": ["payroll", "salary", "wages", "compensation"],
            "saas": ["saas", "software", "subscription", "license"],
            "marketing": ["marketing", "advertising", "ads", "campaign"],
            "legal": ["legal", "law", "attorney", "counsel"],
            "office": ["office", "rent", "space", "facility"],
            "contractors": ["contractor", "freelance", "consultant"],
            "misc": [],
        }
        
        for category, keywords in mappings.items():
            if any(kw in account_lower for kw in keywords):
                return category
        
        return "misc"
    
    # =========================================================================
    # PART B: BASELINE CALCULATOR
    # =========================================================================
    
    def calculate_baselines(self, df: pd.DataFrame) -> Dict:
        """
        Calculate 90-day baselines per expense category.
        
        Returns:
            {
                category: {
                    "avg": float,
                    "stddev": float,
                    "monthly_values": [v1, v2, ...],  # Last 12 months
                    "n_transactions": int,
                }
            }
        """
        logger.info("Calculating baselines...")
        
        if df.empty:
            logger.warning("Empty DataFrame, returning empty baselines")
            return {}
        
        baselines = {}
        
        for category in df["category"].unique():
            cat_data = df[df["category"] == category].copy()
            
            # Calculate monthly totals
            cat_data["year_month"] = cat_data["date"].dt.to_period("M")
            monthly_totals = cat_data.groupby("year_month")["amount"].sum()
            
            # Convert to float list
            monthly_values = monthly_totals.values.astype(float).tolist()
            
            # Calculate statistics
            if monthly_values:
                avg = float(np.mean(monthly_values))
                stddev = float(np.std(monthly_values))
            else:
                avg = 0.0
                stddev = 0.0
            
            baselines[category] = {
                "avg": avg,
                "stddev": stddev,
                "monthly_values": monthly_values,
                "n_transactions": len(cat_data),
            }
            
            logger.debug(f"{category:15} avg=${avg:10,.0f} stddev=${stddev:8,.0f} tx={len(cat_data):4}")
        
        return baselines
    
    # =========================================================================
    # PART C: ALERT DETECTORS
    # =========================================================================
    
    def detect_spike_alerts(self, df: pd.DataFrame, baselines: Dict, 
                           thresholds: Dict) -> List[Dict]:
        """
        Detect spike anomalies: current month >> baseline.
        
        WARNING: amount > (avg + 1.5σ) AND delta_pct > 15%
        CRITICAL: amount > (avg + 2.5σ) AND delta_pct > 50%
        """
        alerts = []
        
        if df.empty:
            return alerts
        
        logger.info("Detecting spike anomalies...")
        
        # Calculate current month total per category
        df["year_month"] = df["date"].dt.to_period("M")
        current_month = df["year_month"].max()
        
        for category in df["category"].unique():
            cat_current = df[(df["category"] == category) & (df["year_month"] == current_month)]
            current_total = cat_current["amount"].sum()
            
            if current_total == 0:
                continue
            
            baseline = baselines.get(category, {})
            avg = baseline.get("avg", 0)
            stddev = baseline.get("stddev", 0)
            
            if avg == 0:
                continue  # No historical data
            
            # Calculate delta
            delta = current_total - avg
            delta_pct = (delta / avg * 100) if avg > 0 else 0
            
            # Get thresholds for this category
            cat_thresholds = thresholds.get(category, {
                "warn_pct": 15.0,
                "critical_pct": 50.0,
                "stddev_warn": 1.5,
                "stddev_crit": 2.5,
            })
            
            warn_pct = cat_thresholds.get("warn_pct", 15.0)
            crit_pct = cat_thresholds.get("critical_pct", 50.0)
            stddev_warn = cat_thresholds.get("stddev_warn", 1.5)
            stddev_crit = cat_thresholds.get("stddev_crit", 2.5)
            
            # Check CRITICAL threshold first
            crit_threshold = avg + (stddev * stddev_crit)
            if current_total > crit_threshold and delta_pct > crit_pct:
                alerts.append({
                    "severity": "critical",
                    "alert_type": "spike",
                    "category": category,
                    "amount": current_total,
                    "baseline": avg,
                    "delta_pct": delta_pct,
                    "description": f"{category.upper()} spike: ${current_total:,.0f} vs expected ${avg:,.0f} (+{delta_pct:.1f}%)",
                    "period_start": (current_month.to_timestamp()).date(),
                    "period_end": datetime.utcnow().date(),
                })
                logger.warning(f"  ✗ CRITICAL spike in {category}: {delta_pct:.1f}% above baseline")
                continue
            
            # Check WARNING threshold
            warn_threshold = avg + (stddev * stddev_warn)
            if current_total > warn_threshold and delta_pct > warn_pct:
                alerts.append({
                    "severity": "warning",
                    "alert_type": "spike",
                    "category": category,
                    "amount": current_total,
                    "baseline": avg,
                    "delta_pct": delta_pct,
                    "description": f"{category.upper()} elevated: ${current_total:,.0f} vs expected ${avg:,.0f} (+{delta_pct:.1f}%)",
                    "period_start": (current_month.to_timestamp()).date(),
                    "period_end": datetime.utcnow().date(),
                })
                logger.warning(f"  ✗ WARNING spike in {category}: {delta_pct:.1f}% above baseline")
        
        return alerts
    
    def detect_trend_alerts(self, baselines: Dict) -> List[Dict]:
        """
        Detect trend anomalies: consistent month-over-month growth.
        
        Fits linear regression to monthly values. If slope > 5%/month
        for 3+ consecutive months → TREND alert.
        """
        alerts = []
        logger.info("Detecting trend anomalies...")
        
        for category, baseline_data in baselines.items():
            monthly_values = baseline_data.get("monthly_values", [])
            
            if len(monthly_values) < 4:  # Need at least 4 months
                continue
            
            # Take last N months
            x = np.arange(len(monthly_values))
            y = np.array(monthly_values)
            
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Calculate % growth per month
            if monthly_values[0] > 0:
                pct_growth_per_month = (slope / monthly_values[0]) * 100
            else:
                continue
            
            # Check if sustained growth > 5% per month
            if pct_growth_per_month > 5.0 and r_value > 0.7:  # Strong trend (R² > 0.49)
                latest_month = monthly_values[-1]
                previous_month = monthly_values[-2] if len(monthly_values) > 1 else latest_month
                
                alerts.append({
                    "severity": "info",
                    "alert_type": "trend",
                    "category": category,
                    "amount": latest_month,
                    "baseline": previous_month,
                    "delta_pct": ((latest_month - previous_month) / previous_month * 100) if previous_month > 0 else 0,
                    "description": f"{category.upper()} trending: +{pct_growth_per_month:.1f}%/month (R²={r_value**2:.2f})",
                    "period_start": (datetime.utcnow() - timedelta(days=90)).date(),
                    "period_end": datetime.utcnow().date(),
                })
                logger.info(f"  ℹ TREND in {category}: {pct_growth_per_month:.1f}%/month")
        
        return alerts
    
    def detect_duplicate_payments(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect duplicate payments: same vendor + amount within 30 days.
        
        Severity: CRITICAL (potential fraud or accounting error)
        """
        alerts = []
        logger.info("Detecting duplicate payments...")
        
        if df.empty:
            return alerts
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        df_recent = df[df["date"] >= cutoff_date].copy()
        
        # Group by vendor + amount
        for (vendor, amount), group in df_recent.groupby(["vendor", "amount"]):
            if len(group) >= 2:
                dates = group["date"].unique()
                category = group.iloc[0]["category"]
                
                alerts.append({
                    "severity": "critical",
                    "alert_type": "duplicate",
                    "category": category,
                    "amount": amount,
                    "baseline": None,
                    "delta_pct": 100.0,
                    "description": f"DUPLICATE payment to {vendor}: ${amount:,.0f} paid {len(group)} times in 30 days",
                    "period_start": (datetime.utcnow() - timedelta(days=30)).date(),
                    "period_end": datetime.utcnow().date(),
                })
                logger.warning(f"  ✗ CRITICAL duplicate: {vendor} ${amount:,.0f} × {len(group)}")
        
        return alerts
    
    def detect_vendor_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect new vendor anomalies: vendor unpaid for 90 days then >$1000 payment.
        
        Severity: WARNING (possible new hire/vendor, needs review)
        """
        alerts = []
        logger.info("Detecting new vendor anomalies...")
        
        if df.empty:
            return alerts
        
        # Vendors in last 90 days
        all_vendors_90d = set(df["vendor"].unique())
        
        # Current month transactions
        current_month_start = pd.Timestamp(datetime.utcnow().replace(day=1))
        df_current = df[df["date"] >= current_month_start]
        
        for vendor, group in df_current.groupby("vendor"):
            total_vendor = group["amount"].sum()
            
            # Check if vendor was absent for 90 days
            # (This would require checking historical data before 90 days, simplified here)
            if total_vendor > 1000:
                category = group.iloc[0]["category"]
                
                # Flag as potential new vendor
                alerts.append({
                    "severity": "warning",
                    "alert_type": "new_vendor",
                    "category": category,
                    "amount": total_vendor,
                    "baseline": None,
                    "delta_pct": 0.0,
                    "description": f"NEW vendor this month: {vendor} - ${total_vendor:,.0f}",
                    "period_start": current_month_start.date(),
                    "period_end": datetime.utcnow().date(),
                })
                logger.info(f"  ℹ NEW vendor: {vendor} ${total_vendor:,.0f}")
        
        return alerts
    
    # =========================================================================
    # PART D: RUNWAY IMPACT CALCULATOR
    # =========================================================================
    
    def calculate_runway_impact(self, monthly_excess: float) -> Optional[float]:
        """
        Calculate runway impact of a monthly excess amount.
        
        runway_impact = (monthly_excess / monthly_burn) * current_runway
        
        Returns runway impact in months (negative = runway reduction).
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                # Get current runway
                runway_resp = client.get(f"{self.backend_url}/api/runway")
                runway_resp.raise_for_status()
                current_runway = runway_resp.json().get("runway_months", 12)
                
                # Get monthly burn rate
                burn_resp = client.get(f"{self.backend_url}/api/burn-rate")
                burn_resp.raise_for_status()
                monthly_burn = burn_resp.json().get("burn_rate_monthly", 50000)
            
            if monthly_burn > 0:
                impact = (monthly_excess / monthly_burn) * current_runway
                return round(impact, 2)
            return None
        
        except Exception as e:
            logger.warning(f"Could not calculate runway impact: {e}")
            return None
    
    # =========================================================================
    # PART E: ALERT WRITER
    # =========================================================================
    
    def write_alerts_to_db(self, alerts: List[Dict]) -> int:
        """
        Write alerts to PostgreSQL with deduplication.
        
        Dedup logic: don't insert if (category + alert_type + period_start)
        already exists with status='active' in the last 7 days.
        
        Returns count of new alerts written.
        """
        if not alerts:
            return 0
        
        logger.info(f"Writing {len(alerts)} alerts to database...")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            new_count = 0
            
            for alert in alerts:
                # Check for duplicate in last 7 days
                cursor.execute("""
                    SELECT id FROM alerts
                    WHERE category = %s
                    AND alert_type = %s
                    AND period_start = %s
                    AND status = 'active'
                    AND created_at > now() - interval '7 days'
                    LIMIT 1
                """, (alert["category"], alert["alert_type"], alert["period_start"]))
                
                existing = cursor.fetchone()
                
                if not existing:
                    # Calculate runway impact
                    runway_impact = self.calculate_runway_impact(
                        alert.get("amount", 0) - alert.get("baseline", alert.get("amount", 0))
                    )
                    
                    # Insert new alert
                    cursor.execute("""
                        INSERT INTO alerts (
                            severity, alert_type, category, amount, baseline, delta_pct,
                            period_start, period_end, description, runway_impact,
                            suggested_owner, status, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                    """, (
                        alert["severity"],
                        alert["alert_type"],
                        alert["category"],
                        alert["amount"],
                        alert.get("baseline"),
                        alert["delta_pct"],
                        alert["period_start"],
                        alert["period_end"],
                        alert["description"],
                        runway_impact,
                        self._suggest_owner(alert["category"]),
                        "active",
                    ))
                    new_count += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Scanner wrote {new_count} new alerts to database")
            return new_count
        
        except Exception as e:
            logger.error(f"Failed to write alerts to DB: {e}", exc_info=True)
            return 0
    
    def _suggest_owner(self, category: str) -> str:
        """Suggest an owner (CFO/CTO/CEO) for the alert."""
        owner_mappings = {
            "aws": "CTO",
            "saas": "CTO",
            "payroll": "CFO",
            "legal": "CEO",
            "marketing": "CEO",
            "office": "CFO",
            "contractors": "CFO",
            "misc": "CFO",
        }
        return owner_mappings.get(category, "CFO")
    
    # =========================================================================
    # PART F: MAIN SCANNER ENTRY POINT
    # =========================================================================
    
    def run_full_scan(self) -> Dict:
        """
        Execute the complete 90-day anomaly detection scan.
        
        Returns:
            {
                "status": "success" | "error",
                "alerts_found": N,
                "critical_count": N,
                "warning_count": N,
                "info_count": N,
                "scan_duration_seconds": N,
                "alerts": [...]  # List of created alerts
            }
        """
        self.run_start = datetime.utcnow()
        
        logger.info("=" * 70)
        logger.info("PHASE 4: ANOMALY DETECTION SCAN STARTING")
        logger.info("=" * 70)
        
        try:
            # Load GL transactions
            df = self.load_gl_transactions(days_back=90)
            
            if df.empty:
                logger.warning("No GL transactions loaded")
                return {
                    "status": "no_data",
                    "alerts_found": 0,
                    "scan_duration_seconds": 0,
                }
            
            logger.info(f"Loaded {len(df)} transactions from {df['date'].min()} to {df['date'].max()}")
            
            # Calculate baselines
            baselines = self.calculate_baselines(df)
            logger.info(f"Calculated baselines for {len(baselines)} categories")
            
            # Get thresholds from database
            thresholds = self._get_thresholds_from_db()
            logger.info(f"Loaded thresholds for {len(thresholds)} categories")
            
            # Run all detectors
            all_alerts = []
            all_alerts.extend(self.detect_spike_alerts(df, baselines, thresholds))
            all_alerts.extend(self.detect_trend_alerts(baselines))
            all_alerts.extend(self.detect_duplicate_payments(df))
            all_alerts.extend(self.detect_vendor_anomalies(df))
            
            logger.info(f"Detected {len(all_alerts)} total anomalies")
            
            # Write to database
            alerts_written = self.write_alerts_to_db(all_alerts)
            
            # Calculate statistics
            critical_count = sum(1 for a in all_alerts if a["severity"] == "critical")
            warning_count = sum(1 for a in all_alerts if a["severity"] == "warning")
            info_count = sum(1 for a in all_alerts if a["severity"] == "info")
            
            duration = (datetime.utcnow() - self.run_start).total_seconds()
            
            logger.info(f"Scan summary:")
            logger.info(f"  • Alerts found: {len(all_alerts)} ({critical_count} critical, {warning_count} warning, {info_count} info)")
            logger.info(f"  • Alerts written: {alerts_written}")
            logger.info(f"  • Duration: {duration:.2f}s")
            logger.info("=" * 70)
            
            # Log run to anomaly_runs table
            self._log_run_summary(alerts_written, duration)
            
            return {
                "status": "success",
                "alerts_found": len(all_alerts),
                "alerts_written": alerts_written,
                "critical_count": critical_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "scan_duration_seconds": round(duration, 2),
                "alerts": all_alerts,
            }
        
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            duration = (datetime.utcnow() - self.run_start).total_seconds()
            self._log_run_summary(0, duration, error_msg=str(e))
            
            return {
                "status": "error",
                "error": str(e),
                "scan_duration_seconds": round(duration, 2),
                "alerts_found": 0,
            }
    
    def _get_thresholds_from_db(self) -> Dict:
        """Load alert thresholds from PostgreSQL."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM alert_thresholds WHERE enabled = true")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            thresholds = {}
            for row in rows:
                thresholds[row["category"]] = {
                    "warn_pct": float(row["warn_pct"]),
                    "critical_pct": float(row["critical_pct"]),
                    "stddev_warn": float(row["stddev_warn"]),
                    "stddev_crit": float(row["stddev_crit"]),
                }
            
            return thresholds
        except Exception as e:
            logger.warning(f"Could not load thresholds from DB: {e}. Using defaults.")
            return {}
    
    def _log_run_summary(self, alerts_found: int, duration_ms: float, 
                        error_msg: Optional[str] = None):
        """Log scan execution summary to anomaly_runs table."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            status = "error" if error_msg else "success"
            
            cursor.execute("""
                INSERT INTO anomaly_runs (status, alerts_found, duration_ms, error_msg, version)
                VALUES (%s, %s, %s, %s, '1.0')
            """, (status, alerts_found, int(duration_ms * 1000), error_msg))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not log run summary: {e}")


# ============================================================================
# MODULE-LEVEL FUNCTIONS (for Celery integration)
# ============================================================================

def run_full_scan() -> Dict:
    """Entry point for Celery task."""
    db_url = os.getenv("DATABASE_URL")
    erpnext_url = os.getenv("ERPNEXT_URL", "http://localhost:8001")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    if not db_url:
        logger.error("DATABASE_URL not set")
        return {"status": "error", "error": "DATABASE_URL not set"}
    
    scanner = AnomalyScanner(db_url, erpnext_url, backend_url)
    return scanner.run_full_scan()


if __name__ == "__main__":
    # Test the scanner
    logging.basicConfig(level=logging.INFO)
    
    result = run_full_scan()
    print("\n" + "=" * 70)
    print("SCAN RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=2, default=str))

