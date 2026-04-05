#!/usr/bin/env python3
"""
Finance Agent Monitoring Script
Monitors audit trails, consolidation accuracy, and agent performance
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys


class FinanceAgentMonitor:
    def __init__(self, db_path="./sqlalchemy.db"):
        self.db_path = db_path
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)
    
    def execute_query(self, query, params=None):
        """Execute database query"""
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def monitor_audit_events(self):
        """Monitor audit events"""
        print("\n📋 Audit Events Monitoring")
        print("-" * 60)
        
        # Total audit events
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM audit_events"
        )
        if result:
            total = result[0]['count']
            print(f"✅ Total Audit Events: {total}")
        
        # Events by type (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        result = self.execute_query(
            """SELECT event_type, COUNT(*) as count 
               FROM audit_events 
               WHERE timestamp > ? 
               GROUP BY event_type 
               ORDER BY count DESC""",
            (seven_days_ago.isoformat(),)
        )
        if result:
            print(f"\n📊 Event Types (Last 7 Days):")
            for row in result:
                print(f"  {row['event_type']}: {row['count']}")
        
        # Recent events
        result = self.execute_query(
            """SELECT entity_type, entity_id, event_type, timestamp 
               FROM audit_events 
               ORDER BY timestamp DESC 
               LIMIT 10"""
        )
        if result:
            print(f"\n⏰ Recent Audit Events:")
            for row in result:
                print(f"  {row['entity_type']} | {row['event_type']} | {row['timestamp']}")
        
        # Hash integrity check
        null_hash_count = self.execute_query(
            "SELECT COUNT(*) as count FROM audit_events WHERE immutable_hash IS NULL OR immutable_hash = ''"
        )
        if null_hash_count and null_hash_count[0]['count'] > 0:
            print(f"\n⚠️  WARNING: {null_hash_count[0]['count']} events with missing hash!")
        else:
            print(f"\n✅ All audit events have immutable hashes")
    
    def monitor_close_periods(self):
        """Monitor close periods"""
        print("\n\n📁 Close Periods Monitoring")
        print("-" * 60)
        
        # Total close periods
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM close_periods"
        )
        if result:
            print(f"✅ Total Close Periods: {result[0]['count']}")
        
        # By status
        result = self.execute_query(
            """SELECT status, COUNT(*) as count 
               FROM close_periods 
               GROUP BY status 
               ORDER BY count DESC"""
        )
        if result:
            print(f"\n📊 Close By Status:")
            for row in result:
                print(f"  {row['status']}: {row['count']}")
        
        # Readiness scores
        result = self.execute_query(
            """SELECT period, readiness_score, status 
               FROM close_periods 
               WHERE status != 'locked' 
               ORDER BY readiness_score DESC 
               LIMIT 5"""
        )
        if result:
            print(f"\n📈 Top Ready-to-Close Periods:")
            for row in result:
                print(f"  Period {row['period']}: {row['readiness_score']:.1f}% ({row['status']})")
        
        # Recently locked
        result = self.execute_query(
            """SELECT period, locked_by, locked_at 
               FROM close_periods 
               WHERE status = 'locked' 
               ORDER BY locked_at DESC 
               LIMIT 5"""
        )
        if result:
            print(f"\n🔒 Recently Locked Periods:")
            for row in result:
                print(f"  Period {row['period']} | Locked by {row['locked_by']} | {row['locked_at']}")
    
    def monitor_approval_requests(self):
        """Monitor approval workflows"""
        print("\n\n✅ Approval Requests Monitoring")
        print("-" * 60)
        
        # Total requests
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM approval_requests"
        )
        if result:
            print(f"✅ Total Approval Requests: {result[0]['count']}")
        
        # By status
        result = self.execute_query(
            """SELECT status, COUNT(*) as count 
               FROM approval_requests 
               GROUP BY status 
               ORDER BY count DESC"""
        )
        if result:
            print(f"\n📊 Requests By Status:")
            for row in result:
                print(f"  {row['status']}: {row['count']}")
        
        # Pending requests (should be processed)
        result = self.execute_query(
            """SELECT ar.id, ar.amount, ar.due_at, aw.name 
               FROM approval_requests ar
               JOIN approval_workflows aw ON ar.workflow_id = aw.id
               WHERE ar.status = 'pending' 
               ORDER BY ar.due_at ASC"""
        )
        if result:
            print(f"\n⏳ Pending Approvals:")
            for row in result:
                due_in = "OVERDUE" if row['due_at'] and row['due_at'] < datetime.utcnow().isoformat() else "Pending"
                print(f"  Amount: ${row['amount']:,.2f} | {row['name']} | Due: {row['due_at']} ({due_in})")
        else:
            print(f"\n✅ No pending approval requests")
        
        # Average approval time
        result = self.execute_query(
            """SELECT AVG(CAST(julianday(updated_at) - julianday(created_at) AS FLOAT)) as avg_days 
               FROM approval_requests 
               WHERE status IN ('approved', 'rejected')"""
        )
        if result and result[0]['avg_days']:
            print(f"\n⏱️  Average Approval Time: {result[0]['avg_days']:.2f} days")
    
    def monitor_consolidation(self):
        """Monitor consolidation snapshots"""
        print("\n\n🌍 Consolidation Monitoring")
        print("-" * 60)
        
        # Total snapshots
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM consolidation_snapshots"
        )
        if result:
            print(f"✅ Total Consolidation Snapshots: {result[0]['count']}")
        
        # By period
        result = self.execute_query(
            """SELECT period, COUNT(*) as count 
               FROM consolidation_snapshots 
               GROUP BY period 
               ORDER BY period DESC 
               LIMIT 10"""
        )
        if result:
            print(f"\n📊 Snapshots By Period:")
            for row in result:
                print(f"  {row['period']}: {row['count']} snapshots")
        
        # Intercompany transactions
        result = self.execute_query(
            """SELECT status, COUNT(*) as count, SUM(amount) as total_amount 
               FROM intercompany_transactions 
               GROUP BY status 
               ORDER BY count DESC"""
        )
        if result:
            print(f"\n📋 Intercompany Transactions:")
            for row in result:
                print(f"  {row['status']}: {row['count']} transactions | Total: ${row['total_amount']:,.2f}")
        
        # Entity hierarchy
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM entity_hierarchy"
        )
        if result:
            print(f"\n🏢 Entity Hierarchy:")
            print(f"  Total Relationships: {result[0]['count']}")
        
        result = self.execute_query(
            """SELECT COUNT(DISTINCT parent_company_id) as parents, 
                      COUNT(DISTINCT subsidiary_company_id) as subs 
               FROM entity_hierarchy"""
        )
        if result:
            row = result[0]
            print(f"  Parent Companies: {row['parents']}")
            print(f"  Subsidiary Companies: {row['subs']}")
    
    def monitor_database_health(self):
        """Monitor database health"""
        print("\n\n🏥 Database Health")
        print("-" * 60)
        
        # Table sizes
        tables = [
            'audit_events', 'close_periods', 'approval_requests',
            'consolidation_snapshots', 'intercompany_transactions'
        ]
        
        print("📊 Table Record Counts:")
        for table in tables:
            result = self.execute_query(
                f"SELECT COUNT(*) as count FROM {table}"
            )
            if result:
                count = result[0]['count']
                status = "✅" if count > 0 else "⚠️"
                print(f"  {status} {table.ljust(30)}: {count:>6} records")
        
        print("\n✅ Database is operational")
    
    def monitor_all(self):
        """Run all monitoring checks"""
        print("=" * 60)
        print("🚀 FINANCE AGENT MONITORING")
        print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
        print(f"Database: {self.db_path}")
        print("=" * 60)
        
        try:
            self.monitor_audit_events()
            self.monitor_close_periods()
            self.monitor_approval_requests()
            self.monitor_consolidation()
            self.monitor_database_health()
            
            print("\n" + "=" * 60)
            print("✅ Monitoring Complete")
            print("=" * 60)
            
            return True
        except Exception as e:
            print(f"\n❌ Monitoring failed: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()
    
    def export_metrics(self, output_file="finance_agent_metrics.json"):
        """Export metrics to JSON file"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "audit_events": {
                "total": self.execute_query("SELECT COUNT(*) as count FROM audit_events")[0]['count']
                if self.execute_query("SELECT COUNT(*) as count FROM audit_events") else 0
            },
            "close_periods": {
                "total": self.execute_query("SELECT COUNT(*) as count FROM close_periods")[0]['count']
                if self.execute_query("SELECT COUNT(*) as count FROM close_periods") else 0
            },
            "approval_requests": {
                "total": self.execute_query("SELECT COUNT(*) as count FROM approval_requests")[0]['count']
                if self.execute_query("SELECT COUNT(*) as count FROM approval_requests") else 0
            },
            "consolidation_snapshots": {
                "total": self.execute_query("SELECT COUNT(*) as count FROM consolidation_snapshots")[0]['count']
                if self.execute_query("SELECT COUNT(*) as count FROM consolidation_snapshots") else 0
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        print(f"✅ Metrics exported to {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Finance Agent Monitoring")
    parser.add_argument("--db", default="./sqlalchemy.db", help="Database path")
    parser.add_argument("--export", help="Export metrics to JSON file")
    
    args = parser.parse_args()
    
    monitor = FinanceAgentMonitor(args.db)
    
    if args.export:
        monitor.export_metrics(args.export)
    else:
        success = monitor.monitor_all()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
