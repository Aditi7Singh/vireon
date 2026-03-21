"""Add financial ledger and recommendation/alert tables.

Alembic-style migration script.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d4e5f6g7h8i9"
down_revision = "c40547be8b77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("notification_contacts", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "companies",
        sa.Column(
            "alert_thresholds",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{\"critical_months\": 3, \"warning_months\": 6}'::jsonb"),
        ),
    )

    op.create_table(
        "financial_ledger_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("amount_inr", sa.Numeric(15, 2), nullable=False),
        sa.Column("entry_type", sa.Enum("credit", "debit", name="ledgerentrytype"), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "revenue",
                "tech_cost",
                "non_tech_cost",
                "office_expense",
                "marketing",
                "payroll",
                "hiring",
                "loan_repayment",
                "misc",
                name="ledgercategory",
            ),
            nullable=False,
        ),
        sa.Column(
            "product_tag",
            sa.Enum("orchard", "sprouts", "ai_lab", "shared", "unallocated", name="ledgerproducttag"),
            nullable=False,
            server_default="unallocated",
        ),
        sa.Column(
            "office_tag",
            sa.Enum("bengaluru", "gangavathi", "remote", "na", name="ledgerofficetag"),
            nullable=False,
            server_default="na",
        ),
        sa.Column(
            "source",
            sa.Enum(
                "erpnext",
                "manual_cto",
                "manual_marketing",
                "manual_finance",
                "bank_feed",
                "aws_billing",
                "sandbox",
                name="ledgersource",
            ),
            nullable=False,
        ),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "entered_by_role",
            sa.Enum("ceo", "cto", "cso", "marketing", "finance", "system", name="ledgerenteredbyrole"),
            nullable=False,
            server_default="system",
        ),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_ledger_entries_company_id", "financial_ledger_entries", ["company_id"])
    op.create_index("ix_financial_ledger_entries_transaction_date", "financial_ledger_entries", ["transaction_date"])
    op.create_index("ix_financial_ledger_entries_entry_type", "financial_ledger_entries", ["entry_type"])
    op.create_index("ix_financial_ledger_entries_category", "financial_ledger_entries", ["category"])
    op.create_index("ix_financial_ledger_entries_product_tag", "financial_ledger_entries", ["product_tag"])

    op.create_table(
        "recommendation_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("runway_at_generation", sa.Numeric(8, 2), nullable=True),
        sa.Column("status", sa.Enum("active", "archived", name="recommendationstatus"), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "runway_alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("alert_level", sa.Enum("warning", "critical", name="runwayalertlevel"), nullable=False),
        sa.Column("runway_months", sa.Numeric(8, 2), nullable=False),
        sa.Column("runway_date", sa.Date(), nullable=False),
        sa.Column("alert_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("runway_alerts")
    op.drop_table("recommendation_reports")

    op.drop_index("ix_financial_ledger_entries_product_tag", table_name="financial_ledger_entries")
    op.drop_index("ix_financial_ledger_entries_category", table_name="financial_ledger_entries")
    op.drop_index("ix_financial_ledger_entries_entry_type", table_name="financial_ledger_entries")
    op.drop_index("ix_financial_ledger_entries_transaction_date", table_name="financial_ledger_entries")
    op.drop_index("ix_financial_ledger_entries_company_id", table_name="financial_ledger_entries")
    op.drop_table("financial_ledger_entries")

    op.drop_column("companies", "alert_thresholds")
    op.drop_column("companies", "notification_contacts")
