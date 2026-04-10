"""
Isolation Forest Anomaly Detection Service
==========================================
Uses Scikit-learn's Isolation Forest to detect anomalies in GL data.

Detects:
- Split invoices (same vendor, similar amounts, close dates)
- Seasonal/timing anomalies
- Unusual transaction patterns vs category baselines
- New high-value vendors
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------

def _prepare_gl_features(transactions: List[Dict]) -> pd.DataFrame:
    """
    Convert raw GL transaction list into a feature matrix.

    Features per row:
    - amount            : transaction value
    - day_of_month      : 1-31  (captures end-of-month gaming)
    - day_of_week       : 0-6   (Mon-Sun)
    - month             : 1-12  (seasonal pattern)
    - category_encoded  : integer label for expense category
    - vendor_frequency  : how many times this vendor appears in window
    - amount_zscore     : z-score of amount within same category
    """
    if not transactions:
        return pd.DataFrame()

    df = pd.DataFrame(transactions)

    # ── dates ────────────────────────────────────────────────────────────
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["day_of_month"] = df["date"].dt.day.fillna(15).astype(float)
        df["day_of_week"] = df["date"].dt.dayofweek.fillna(3).astype(float)
        df["month"] = df["date"].dt.month.fillna(6).astype(float)
    else:
        now = datetime.utcnow()
        df["day_of_month"] = float(now.day)
        df["day_of_week"] = float(now.weekday())
        df["month"] = float(now.month)

    # ── category encoding ────────────────────────────────────────────────
    if "category" in df.columns:
        categories = df["category"].unique()
        cat_map = {cat: float(i) for i, cat in enumerate(categories)}
        df["category_encoded"] = df["category"].map(cat_map).fillna(0.0)
    else:
        df["category_encoded"] = 0.0

    # ── vendor frequency ─────────────────────────────────────────────────
    if "vendor" in df.columns:
        freq = df["vendor"].value_counts()
        df["vendor_frequency"] = df["vendor"].map(freq).fillna(1.0).astype(float)
    else:
        df["vendor_frequency"] = 1.0

    # ── amount z-score per category ──────────────────────────────────────
    if "amount" in df.columns and "category" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df["amount_zscore"] = df.groupby("category")["amount"].transform(
            lambda x: (x - x.mean()) / (x.std(ddof=0) + 1e-8)
        )
    else:
        df["amount"] = df.get("amount", pd.Series(dtype=float)).fillna(0.0)
        df["amount_zscore"] = 0.0

    return df


# ---------------------------------------------------------------------------
# Core Isolation Forest Detector
# ---------------------------------------------------------------------------

def detect_with_isolation_forest(
    transactions: List[Dict],
    contamination: float = 0.05,
    n_estimators: int = 100,
    random_state: int = 42,
) -> List[Dict]:
    """
    Run Isolation Forest on GL transactions to surface anomalies.

    Args:
        transactions:  list of dicts with keys: amount, date, category, vendor, gl_account
        contamination: expected fraction of outliers (default 5 %)
        n_estimators:  number of trees
        random_state:  reproducibility seed

    Returns:
        List of anomaly dicts (severity, score, description, alert_type, …)
    """
    if len(transactions) < 10:
        logger.warning(
            "Isolation Forest skipped — need ≥ 10 transactions, got %d", len(transactions)
        )
        return []

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        logger.error("scikit-learn is not installed. Run: pip install scikit-learn")
        return []

    df = _prepare_gl_features(transactions)
    if df.empty:
        return []

    feature_cols = [
        "amount",
        "day_of_month",
        "day_of_week",
        "month",
        "category_encoded",
        "vendor_frequency",
        "amount_zscore",
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(0.0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    predictions = clf.fit_predict(X_scaled)  # -1 = anomaly, 1 = normal
    scores = clf.score_samples(X_scaled)     # more negative = more anomalous

    anomalies: List[Dict] = []
    for idx, (pred, score) in enumerate(zip(predictions, scores)):
        if pred != -1:
            continue

        row = df.iloc[idx]
        original = transactions[idx]
        severity = "critical" if score < -0.30 else "warning"

        anomalies.append(
            {
                "index": idx,
                "anomaly_score": float(score),
                "severity": severity,
                "amount": float(row.get("amount", 0)),
                "date": str(original.get("date", "")),
                "category": str(original.get("category", "unknown")),
                "vendor": str(original.get("vendor", "unknown")),
                "gl_account": str(original.get("gl_account", "")),
                "description": _describe_anomaly(row, original, score),
                "alert_type": _classify_type(row, original, df),
                "runway_impact": 0.0,
                "suggested_owner": "Finance",
                "detection_method": "isolation_forest",
            }
        )

    logger.info(
        "Isolation Forest: %d anomalies found from %d transactions",
        len(anomalies),
        len(transactions),
    )
    return anomalies


# ---------------------------------------------------------------------------
# Split Invoice Detector
# ---------------------------------------------------------------------------

def detect_split_invoices(
    transactions: List[Dict],
    similarity_threshold: float = 0.10,
    time_window_days: int = 30,
) -> List[Dict]:
    """
    Detect split-invoice fraud/errors.

    Pattern: same vendor has ≥2 transactions with similar amounts within a time
    window — a common technique to stay under approval thresholds.

    Args:
        transactions:          raw GL records
        similarity_threshold:  max relative difference to count as "similar" (10 %)
        time_window_days:      look-back window in calendar days

    Returns:
        List of split-invoice alert dicts
    """
    if not transactions:
        return []

    df = _prepare_gl_features(transactions)
    if df.empty or "vendor" not in df.columns or "amount" not in df.columns:
        return []

    df["_date"] = pd.to_datetime(df.get("date", pd.Series(dtype=str)), errors="coerce")

    alerts: List[Dict] = []
    seen_pairs: set = set()

    for vendor, grp in df.groupby("vendor"):
        if len(grp) < 2:
            continue

        rows = grp.reset_index(drop=True)
        amounts = rows["amount"].values
        dates = rows["_date"].values

        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a_i, a_j = float(amounts[i]), float(amounts[j])
                if a_i <= 0 or a_j <= 0:
                    continue

                rel_diff = abs(a_i - a_j) / max(a_i, a_j)
                if rel_diff > similarity_threshold:
                    continue

                # Date proximity
                d_i = pd.Timestamp(dates[i]) if not pd.isna(dates[i]) else None
                d_j = pd.Timestamp(dates[j]) if not pd.isna(dates[j]) else None
                days_apart = abs((d_i - d_j).days) if d_i and d_j else 0

                if days_apart > time_window_days:
                    continue

                pair_key = (str(vendor), round(min(a_i, a_j)), round(max(a_i, a_j)))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                combined = a_i + a_j
                alerts.append(
                    {
                        "alert_type": "split_invoice",
                        "severity": "critical" if combined > 10_000 else "warning",
                        "category": str(rows.iloc[i].get("category", "unknown")),
                        "vendor": str(vendor),
                        "amount": combined,
                        "baseline": combined / 2,
                        "delta_pct": 100.0,
                        "description": (
                            f"Possible split invoice: {vendor} has two similar charges "
                            f"${a_i:,.0f} and ${a_j:,.0f} within {days_apart} day(s). "
                            f"Combined: ${combined:,.0f}"
                        ),
                        "runway_impact": 0.0,
                        "suggested_owner": "Finance",
                        "individual_amounts": [a_i, a_j],
                        "days_apart": days_apart,
                        "detection_method": "split_invoice_heuristic",
                    }
                )

    return alerts


# ---------------------------------------------------------------------------
# Full Scan (convenience wrapper)
# ---------------------------------------------------------------------------

def run_isolation_forest_scan(
    transactions: List[Dict],
    contamination: float = 0.05,
) -> Dict[str, Any]:
    """
    Run the complete ML-based anomaly scan: Isolation Forest + split-invoice heuristic.

    Returns a summary dict with all anomalies found.
    """
    if_anomalies = detect_with_isolation_forest(
        transactions, contamination=contamination
    )
    split_alerts = detect_split_invoices(transactions)

    all_alerts = if_anomalies + split_alerts
    critical = [a for a in all_alerts if a["severity"] == "critical"]
    warnings = [a for a in all_alerts if a["severity"] == "warning"]

    return {
        "total": len(all_alerts),
        "critical": len(critical),
        "warnings": len(warnings),
        "anomalies": all_alerts,
        "split_invoices_found": len(split_alerts),
        "isolation_forest_flags": len(if_anomalies),
        "scan_method": "isolation_forest_v2",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _describe_anomaly(row: pd.Series, original: Dict, score: float) -> str:
    amount = float(row.get("amount", 0))
    vendor = str(original.get("vendor", "Unknown"))
    category = str(original.get("category", "unknown"))
    z = float(row.get("amount_zscore", 0))

    if abs(z) > 2.5:
        return (
            f"Statistically unusual: {vendor} charged ${amount:,.0f} "
            f"in {category} (z-score {z:.1f}σ)"
        )
    dom = int(row.get("day_of_month", 15))
    if dom >= 28 or dom <= 1:
        return (
            f"Suspicious timing: {vendor} ${amount:,.0f} in {category} "
            f"— unusual end/start-of-month pattern"
        )
    freq = int(row.get("vendor_frequency", 1))
    if freq <= 1:
        return (
            f"First-time vendor: {vendor} charged ${amount:,.0f} for {category}"
        )
    return (
        f"Isolation Forest flag: {vendor} ${amount:,.0f} in {category} "
        f"(anomaly score {score:.3f})"
    )


def _classify_type(row: pd.Series, original: Dict, df: pd.DataFrame) -> str:
    z = abs(float(row.get("amount_zscore", 0)))
    freq = int(row.get("vendor_frequency", 1))

    if z > 2.5:
        return "spike"
    if freq <= 1:
        return "new_vendor"

    vendor = str(original.get("vendor", ""))
    amount = float(row.get("amount", 0))
    if vendor and amount > 0 and "vendor" in df.columns:
        same = df[df["vendor"] == vendor]
        similar = same[
            (same["amount"] - amount).abs() / (amount + 1e-8) < 0.10
        ]
        if len(similar) > 1:
            return "split_invoice"

    return "anomaly"
