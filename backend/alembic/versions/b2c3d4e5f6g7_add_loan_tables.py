"""Add loan and loan payment tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add loan and loan payment tables."""
    
    # Create loans table
    op.create_table('loans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('loan_name', sa.String(length=255), nullable=False),
        sa.Column('principal_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('term_months', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('loan_type', sa.String(length=50), nullable=True),
        sa.Column('lender', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('remaining_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create loan_payments table
    op.create_table('loan_payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('loan_id', sa.UUID(), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('principal_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('interest_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('remaining_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop loan tables."""
    op.drop_table('loan_payments')
    op.drop_table('loans')