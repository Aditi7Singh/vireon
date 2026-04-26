"""Add new models: Budget, BudgetLine, Forecast, Document

Revision ID: a1b2c3d4e5f6
Revises: 597a47bc7dc8
Create Date: 2026-03-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '597a47bc7dc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new tables for Budget, BudgetLine, Forecast, Document."""
    
    # Create budgets table
    op.create_table('budgets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create budget_lines table
    op.create_table('budget_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('budget_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('monthly_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['budget_id'], ['budgets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create forecasts table
    op.create_table('forecasts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('mrr_predicted', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('cash_predicted', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('confidence_lower', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('confidence_upper', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop new tables."""
    op.drop_table('documents')
    op.drop_table('forecasts')
    op.drop_table('budget_lines')
    op.drop_table('budgets')
