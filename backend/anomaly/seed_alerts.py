"""
Seed Test Alerts
================
Insert test alerts for development and testing.
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL


# Test alerts matching Phase 1 hidden anomalies
SEED_ALERTS = [
    {
        "severity": "critical",
        "alert_type": "spike",
        "category": "aws",
        "amount": 18245.00,
        "baseline": 12100.00,
        "delta_pct": 50.6,
        "description": "AWS $18,245 vs expected $12,100 (+50.6%)",
        "runway_impact": -0.4,
        "suggested_owner": "CTO"
    },
    {
        "severity": "warning",
        "alert_type": "trend",
        "category": "payroll",
        "amount": 95000.00,
        "baseline": 85000.00,
        "delta_pct": 11.8,
        "description": "Payroll increasing 5%/month for 4 months",
        "runway_impact": -0.3,
        "suggested_owner": "CFO"
    },
    {
        "severity": "warning",
        "alert_type": "duplicate",
        "category": "saas",
        "amount": 1200.00,
        "baseline": 0,
        "delta_pct": 100,
        "description": "Potential duplicate: Stripe $1,200 appears twice in November",
        "runway_impact": -0.1,
        "suggested_owner": "CFO"
    },
    {
        "severity": "warning",
        "alert_type": "spike",
        "category": "contractors",
        "amount": 4500.00,
        "baseline": 0,
        "delta_pct": 100,
        "description": "New vendor: Acme Cloud Services $4,500 (first appearance)",
        "runway_impact": -0.1,
        "suggested_owner": "CTO"
    }
]


def seed_alerts():
    """
    Insert seed alerts into the database.
    """
    if not DATABASE_URL:
        print("DATABASE_URL not set. Alerts will not be seeded.")
        return
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        for alert in SEED_ALERTS:
            alert["period_start"] = datetime.now().date() - timedelta(days=30)
            alert["period_end"] = datetime.now().date()
            alert["created_at"] = datetime.now()
            
            conn.execute(text("""
                INSERT INTO alerts (severity, alert_type, category, amount, baseline,
                                   delta_pct, description, runway_impact, suggested_owner,
                                   period_start, period_end, created_at, status)
                VALUES (:severity, :alert_type, :category, :amount, :baseline,
                        :delta_pct, :description, :runway_impact, :suggested_owner,
                        :period_start, :period_end, :created_at, 'active')
            """), alert)
        
        conn.commit()
    
    print(f"✅ Seeded {len(SEED_ALERTS)} test alerts")


if __name__ == "__main__":
    seed_alerts()
