"""Add Series B+ extensions: department P&L, GL, customer cohorts

Revision ID: series_b_ext
    Revises: 7230fe6ad98b
Create Date: 2026-03-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "series_b_ext"
down_revision: Union[str, Sequence[str], None] = "7230fe6ad98b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add department field to existing transaction tables
    op.add_column(
        "financial_ledger_entries",
        sa.Column("department", sa.String(length=50), nullable=True)
    )
    op.create_index(
        "ix_financial_ledger_entries_department",
        "financial_ledger_entries",
        ["department"]
    )

    op.add_column(
        "expenses",
        sa.Column("department", sa.String(length=50), nullable=True)
    )
    op.create_index(
        "ix_expenses_department",
        "expenses",
        ["department"]
    )

    op.add_column(
        "payroll_entries",
        sa.Column("department", sa.String(length=50), nullable=True)
    )
    op.create_index(
        "ix_payroll_entries_department",
        "payroll_entries",
        ["department"]
    )

    # Create GL Account codes enum type
    gl_account_code_enum = sa.Enum(
        "1010", "1200", "1300", "1400", "1500", "1501",
        "2100", "2200", "2300", "2400",
        "3100", "3200",
        "4100", "4200", "4300",
        "5100", "5200", "5210", "5220", "5300", "5400", "5500",
        name="glaccountcode"
    )
    gl_account_code_enum.create(op.get_bind(), checkfirst=True)

    # Create Department enum type
    department_enum = sa.Enum(
        "engineering", "product", "marketing", "sales", "operations",
        "finance", "people", "design", "support",
        name="department"
    )
    department_enum.create(op.get_bind(), checkfirst=True)

    # Create general_ledger table
    op.create_table(
        "general_ledger",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("account_code", gl_account_code_enum, nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("debit_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("credit_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("department", department_enum, nullable=True),
        sa.Column(
            "product_tag",
            sa.Enum("orchard", "sprouts", "ai_lab", "shared", "unallocated", name="ledgerproducttag"),
            nullable=True
        ),
        sa.Column(
            "office_tag",
            sa.Enum("bengaluru", "gangavathi", "remote", "na", name="ledgerofficetag"),
            nullable=True
        ),
        sa.Column("source_ledger_id", sa.UUID(), nullable=True),
        sa.Column("source_type", sa.String(length=100), nullable=True),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_general_ledger_company_id", "general_ledger", ["company_id"])
    op.create_index("ix_general_ledger_account_code", "general_ledger", ["account_code"])
    op.create_index("ix_general_ledger_transaction_date", "general_ledger", ["transaction_date"])
    op.create_index("ix_general_ledger_department", "general_ledger", ["department"])

    # Create customer_cohorts table
    op.create_table(
        "customer_cohorts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("cohort_name", sa.String(length=255), nullable=False),
        sa.Column("cohort_type", sa.String(length=50), nullable=False),
        sa.Column("cohort_value", sa.String(length=255), nullable=False),
        sa.Column(
            "product_tag",
            sa.Enum("orchard", "sprouts", "ai_lab", "shared", "unallocated", name="ledgerproducttag"),
            nullable=True
        ),
        sa.Column("customer_acquired_date", sa.Date(), nullable=True),
        sa.Column("customer_count", sa.Integer(), server_default="0"),
        sa.Column("mrr_total", sa.Numeric(15, 2), server_default="0"),
        sa.Column("arr_total", sa.Numeric(15, 2), server_default="0"),
        sa.Column("churn_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("ltv_estimate", sa.Numeric(15, 2), nullable=True),
        sa.Column("cac_estimate", sa.Numeric(15, 2), nullable=True),
        sa.Column("nrr", sa.Numeric(5, 2), nullable=True),
        sa.Column("gross_margin_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("payback_months", sa.Numeric(5, 2), nullable=True),
        sa.Column("health_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_cohorts_company_id", "customer_cohorts", ["company_id"])
    op.create_index("ix_customer_cohorts_cohort_type", "customer_cohorts", ["cohort_type"])
    op.create_index("ix_customer_cohorts_product_tag", "customer_cohorts", ["product_tag"])


def downgrade() -> None:
    # Drop customer_cohorts table
    op.drop_index("ix_customer_cohorts_product_tag", table_name="customer_cohorts")
    op.drop_index("ix_customer_cohorts_cohort_type", table_name="customer_cohorts")
    op.drop_index("ix_customer_cohorts_company_id", table_name="customer_cohorts")
    op.drop_table("customer_cohorts")

    # Drop general_ledger table
    op.drop_index("ix_general_ledger_department", table_name="general_ledger")
    op.drop_index("ix_general_ledger_transaction_date", table_name="general_ledger")
    op.drop_index("ix_general_ledger_account_code", table_name="general_ledger")
    op.drop_index("ix_general_ledger_company_id", table_name="general_ledger")
    op.drop_table("general_ledger")

    # Drop enum types
    sa.Enum(name="department").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="glaccountcode").drop(op.get_bind(), checkfirst=True)

    # Remove department columns
    op.drop_index("ix_payroll_entries_department", table_name="payroll_entries")
    op.drop_column("payroll_entries", "department")

    op.drop_index("ix_expenses_department", table_name="expenses")
    op.drop_column("expenses", "department")

    op.drop_index("ix_financial_ledger_entries_department", table_name="financial_ledger_entries")
    op.drop_column("financial_ledger_entries", "department")
