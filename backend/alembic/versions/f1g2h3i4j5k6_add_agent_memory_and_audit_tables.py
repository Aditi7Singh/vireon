"""Add agent memory and audit tables

Revision ID: f1g2h3i4j5k6
Revises: e1f2g3h4i5j6
Create Date: 2026-04-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f1g2h3i4j5k6"
down_revision: Union[str, Sequence[str], None] = "e1f2g3h4i5j6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("query_count", sa.Integer(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_agent_conversations_session_id", "agent_conversations", ["session_id"])
    op.create_index("ix_agent_conversations_company_id", "agent_conversations", ["company_id"])
    op.create_index("ix_agent_conversations_user_id", "agent_conversations", ["user_id"])
    op.create_index("ix_agent_conversations_last_message_at", "agent_conversations", ["last_message_at"])

    op.create_table(
        "agent_conversation_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_conversation_messages_conversation_id", "agent_conversation_messages", ["conversation_id"])
    op.create_index("ix_agent_conversation_messages_created_at", "agent_conversation_messages", ["created_at"])

    op.create_table(
        "agent_tool_audit",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("tool_input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tool_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("chain_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ok"),
        sa.Column("data_timestamp", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_tool_audit_conversation_id", "agent_tool_audit", ["conversation_id"])
    op.create_index("ix_agent_tool_audit_company_id", "agent_tool_audit", ["company_id"])
    op.create_index("ix_agent_tool_audit_tool_name", "agent_tool_audit", ["tool_name"])
    op.create_index("ix_agent_tool_audit_chain_id", "agent_tool_audit", ["chain_id"])
    op.create_index("ix_agent_tool_audit_created_at", "agent_tool_audit", ["created_at"])

    op.create_table(
        "agent_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("preference_key", sa.String(length=100), nullable=False),
        sa.Column("preference_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_preferences_user_id", "agent_preferences", ["user_id"])
    op.create_index("ix_agent_preferences_company_id", "agent_preferences", ["company_id"])
    op.create_index("ix_agent_preferences_preference_key", "agent_preferences", ["preference_key"])


def downgrade() -> None:
    op.drop_index("ix_agent_preferences_preference_key", table_name="agent_preferences")
    op.drop_index("ix_agent_preferences_company_id", table_name="agent_preferences")
    op.drop_index("ix_agent_preferences_user_id", table_name="agent_preferences")
    op.drop_table("agent_preferences")

    op.drop_index("ix_agent_tool_audit_created_at", table_name="agent_tool_audit")
    op.drop_index("ix_agent_tool_audit_chain_id", table_name="agent_tool_audit")
    op.drop_index("ix_agent_tool_audit_tool_name", table_name="agent_tool_audit")
    op.drop_index("ix_agent_tool_audit_company_id", table_name="agent_tool_audit")
    op.drop_index("ix_agent_tool_audit_conversation_id", table_name="agent_tool_audit")
    op.drop_table("agent_tool_audit")

    op.drop_index("ix_agent_conversation_messages_created_at", table_name="agent_conversation_messages")
    op.drop_index("ix_agent_conversation_messages_conversation_id", table_name="agent_conversation_messages")
    op.drop_table("agent_conversation_messages")

    op.drop_index("ix_agent_conversations_last_message_at", table_name="agent_conversations")
    op.drop_index("ix_agent_conversations_user_id", table_name="agent_conversations")
    op.drop_index("ix_agent_conversations_company_id", table_name="agent_conversations")
    op.drop_index("ix_agent_conversations_session_id", table_name="agent_conversations")
    op.drop_table("agent_conversations")