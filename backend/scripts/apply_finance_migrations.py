"""
Database migration for all new finance features

Run with: alembic revision --autogenerate -m "Add finance enhancement tables"
Or apply directly with: python apply_finance_migrations.py
"""
from sqlalchemy import create_engine, MetaData
from database import Base, engine
import models

def create_all_tables():
    """Create all new tables for finance enhancements"""
    print("Creating new tables for finance enhancements...")
    
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    
    print("✓ All tables created successfully!")
    print("\nNew tables added:")
    print("- contracts")
    print("- contract_alerts")
    print("- bank_reconciliations")
    print("- bank_transaction_matches")
    print("- transaction_templates")
    print("- purchase_orders")
    print("- po_line_items")
    print("- customer_health_scores")
    print("- forecast_models")
    print("- forecast_accuracy")
    print("- narrative_reports")
    print("- board_reports")
    print("- scenario_comparisons")
    print("- finance_tasks")
    print("- transaction_comments")
    print("- inventory_items")
    print("- inventory_transactions")
    print("- revenue_recognition")
    print("- revenue_schedules")

if __name__ == "__main__":
    create_all_tables()
