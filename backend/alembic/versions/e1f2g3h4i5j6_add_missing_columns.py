"""Add missing columns: companies sync timestamps, documents structured_data, monthly_metrics tax

Revision ID: e1f2g3h4i5j6
Revises: series_b_ext
Create Date: 2026-03-29 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e1f2g3h4i5j6"
down_revision: Union[str, Sequence[str], None] = "series_b_ext"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("last_sync_erpnext", sa.DateTime(), nullable=True))
    op.add_column("companies", sa.Column("last_sync_merge", sa.DateTime(), nullable=True))
    op.add_column("documents", sa.Column("structured_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("monthly_metrics", sa.Column("total_tax_liability", sa.Numeric(15, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("monthly_metrics", "total_tax_liability")
    op.drop_column("documents", "structured_data")
    op.drop_column("companies", "last_sync_merge")
    op.drop_column("companies", "last_sync_erpnext")
