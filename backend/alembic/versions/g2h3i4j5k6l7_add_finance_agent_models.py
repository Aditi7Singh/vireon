"""Add finance agent models: close, approvals, audit, consolidation

Revision ID: g2h3i4j5k6l7
Revises: f1g2h3i4j5k6
Create Date: 2026-04-05 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, Sequence[str], None] = "f1g2h3i4j5k6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create close_periods table
    op.create_table(
        "close_periods",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("readiness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("locked_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_close_periods_company_id", "close_periods", ["company_id"])
    op.create_index("ix_close_periods_period", "close_periods", ["period"])

    # Create close_checklists table
    op.create_table(
        "close_checklists",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("close_period_id", sa.UUID(), nullable=False),
        sa.Column("item_key", sa.String(length=100), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["close_period_id"], ["close_periods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_close_checklists_close_period_id", "close_checklists", ["close_period_id"])

    # Create close_audit table
    op.create_table(
        "close_audit",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("close_period_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("audit_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["close_period_id"], ["close_periods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_close_audit_close_period_id", "close_audit", ["close_period_id"])
    op.create_index("ix_close_audit_action", "close_audit", ["action"])
    op.create_index("ix_close_audit_created_at", "close_audit", ["created_at"])

    # Create approval_workflows table
    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False, server_default="finance_operation"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_workflows_company_id", "approval_workflows", ["company_id"])

    # Create approval_steps table
    op.create_table(
        "approval_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approver_role", sa.String(length=100), nullable=False),
        sa.Column("min_amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("max_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("parallel_group", sa.String(length=100), nullable=True),
        sa.Column("escalation_hours", sa.Integer(), nullable=True),
        sa.Column("allow_delegation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_steps_workflow_id", "approval_steps", ["workflow_id"])

    # Create approval_requests table
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("reference_type", sa.String(length=100), nullable=False, server_default="finance_operation"),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("current_step_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("requested_by", sa.String(length=255), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_requests_company_id", "approval_requests", ["company_id"])
    op.create_index("ix_approval_requests_workflow_id", "approval_requests", ["workflow_id"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])

    # Create approval_actions table
    op.create_table(
        "approval_actions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=100), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("delegated_to", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["approval_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_actions_request_id", "approval_actions", ["request_id"])
    op.create_index("ix_approval_actions_created_at", "approval_actions", ["created_at"])

    # Create audit_events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("immutable_hash", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_company_id", "audit_events", ["company_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_immutable_hash", "audit_events", ["immutable_hash"])

    # Create entity_hierarchy table
    op.create_table(
        "entity_hierarchy",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parent_company_id", sa.UUID(), nullable=False),
        sa.Column("subsidiary_company_id", sa.UUID(), nullable=False),
        sa.Column("ownership_pct", sa.Numeric(precision=5, scale=2), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subsidiary_company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entity_hierarchy_parent_company_id", "entity_hierarchy", ["parent_company_id"])
    op.create_index("ix_entity_hierarchy_subsidiary_company_id", "entity_hierarchy", ["subsidiary_company_id"])

    # Create intercompany_transactions table
    op.create_table(
        "intercompany_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("from_company_id", sa.UUID(), nullable=False),
        sa.Column("to_company_id", sa.UUID(), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["from_company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intercompany_transactions_from_company_id", "intercompany_transactions", ["from_company_id"])
    op.create_index("ix_intercompany_transactions_to_company_id", "intercompany_transactions", ["to_company_id"])
    op.create_index("ix_intercompany_transactions_period", "intercompany_transactions", ["period"])

    # Create consolidation_snapshots table
    op.create_table(
        "consolidation_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("company_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("target_currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("balance_sheet", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pnl", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("minority_interest", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consolidation_snapshots_period", "consolidation_snapshots", ["period"])


def downgrade() -> None:
    # Drop all tables in reverse order of creation
    op.drop_table("consolidation_snapshots")
    op.drop_table("intercompany_transactions")
    op.drop_table("entity_hierarchy")
    op.drop_table("audit_events")
    op.drop_table("approval_actions")
    op.drop_table("approval_requests")
    op.drop_table("approval_steps")
    op.drop_table("approval_workflows")
    op.drop_table("close_audit")
    op.drop_table("close_checklists")
    op.drop_table("close_periods")
