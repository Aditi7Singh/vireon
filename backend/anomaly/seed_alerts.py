#!/usr/bin/env python3
"""
Phase 4 - Seed Test Alerts for Development

Inserts 4 test anomalies matching Phase 1 hidden anomalies:
1. CRITICAL spike: AWS costs $18,245 vs baseline $12,100 (+50.6%)
2. WARNING trend: Payroll increasing 5%/month for 4 months
3. WARNING duplicate: Vendor "Stripe" $1,200 appears twice
4. WARNING new vendor: "Acme Cloud Services" $4,500 (first appearance)

Usage:
    python backend/anomaly/seed_alerts.py

Then verify:
    curl http://localhost:8000/alerts
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

def seed_alerts():
    """Insert test alerts into PostgreSQL"""
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("[SEED] ========== SEEDING TEST ALERTS ==========")
        
        # Test alerts matching Phase 1 hidden anomalies
        alerts = [
            {
                "severity": "CRITICAL",
                "alert_type": "spike",
                "category": "aws",
                "amount": 18245.00,
                "baseline": 12100.00,
                "delta_pct": 50.6,
                "description": "AWS $18,245 vs expected $12,100 (+50.6%) - Check EC2 instances and unattached volumes",
                "runway_impact": -0.4,
                "suggested_owner": "CTO",
                "period_start": (datetime.now() - timedelta(days=30)).date(),
                "period_end": datetime.now().date(),
            },
            {
                "severity": "WARNING",
                "alert_type": "trend",
                "category": "payroll",
                "amount": 107000.00,
                "baseline": 100000.00,
                "delta_pct": 7.0,
                "description": "Payroll expenses growing 5%/month for 4 consecutive months - trending from $100k to $107k",
                "runway_impact": -0.5,
                "suggested_owner": "CFO",
                "period_start": (datetime.now() - timedelta(days=120)).date(),
                "period_end": datetime.now().date(),
            },
            {
                "severity": "WARNING",
                "alert_type": "duplicate",
                "category": "payments",
                "amount": 1200.00,
                "baseline": 600.00,
                "delta_pct": 100.0,
                "description": "Duplicate payment detected: Stripe charged $1,200 twice in same month (possible billing error)",
                "runway_impact": -0.02,
                "suggested_owner": "CFO",
                "period_start": (datetime.now() - timedelta(days=30)).date(),
                "period_end": datetime.now().date(),
            },
            {
                "severity": "WARNING",
                "alert_type": "new_vendor",
                "category": "saas",
                "amount": 4500.00,
                "baseline": 0.00,
                "delta_pct": 0.0,
                "description": "New vendor alert: Acme Cloud Services charges $4,500 (first appearance) - verify this is authorized",
                "runway_impact": -0.1,
                "suggested_owner": "CTO",
                "period_start": (datetime.now() - timedelta(days=5)).date(),
                "period_end": datetime.now().date(),
            },
        ]
        
        # Insert alerts
        insert_query = """
            INSERT INTO alerts 
            (severity, alert_type, category, amount, baseline, delta_pct, 
             description, runway_impact, suggested_owner, period_start, period_end,
             status, created_at, updated_at)
            VALUES %s
        """
        
        records = []
        for alert in alerts:
            records.append((
                alert["severity"],
                alert["alert_type"],
                alert["category"],
                alert["amount"],
                alert["baseline"],
                alert["delta_pct"],
                alert["description"],
                alert["runway_impact"],
                alert["suggested_owner"],
                alert["period_start"],
                alert["period_end"],
                "active",
                datetime.now(),
                datetime.now(),
            ))
        
        execute_values(cursor, insert_query, records)
        conn.commit()
        
        print(f"[SEED] ✓ Inserted {len(alerts)} test alerts")
        
        # Show what was inserted
        cursor.execute("""
            SELECT id, severity, alert_type, category, description, created_at
            FROM alerts
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT 4
        """)
        
        print("\n[SEED] Created alerts:")
        print("-" * 100)
        for row in cursor.fetchall():
            alert_id, severity, alert_type, category, description, created_at = row
            print(f"  [{severity:8s}] {alert_type:10s} | {category:10s} | {description[:60]}...")
        print("-" * 100)
        
        # Show summary
        cursor.execute("""
            SELECT 
                severity,
                COUNT(*) as count
            FROM alerts
            WHERE status = 'active'
            GROUP BY severity
            ORDER BY CASE severity 
                WHEN 'CRITICAL' THEN 1
                WHEN 'WARNING' THEN 2
                ELSE 3
            END
        """)
        
        print("\n[SEED] Alert summary:")
        for severity, count in cursor.fetchall():
            print(f"  {severity}: {count}")
        
        cursor.close()
        conn.close()
        
        print("\n[SEED] ========== SEEDING COMPLETE ==========")
        print("\n[SEED] Verify with:")
        print("  curl http://localhost:8000/alerts")
        print("  curl http://localhost:8000/alerts?severity=critical")
        print("  curl http://localhost:8000/alerts?category=aws")
        
        return 0
    
    except psycopg2.Error as e:
        print(f"[SEED] ERROR: Database error: {e}")
        return 1
    except Exception as e:
        print(f"[SEED] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(seed_alerts())
