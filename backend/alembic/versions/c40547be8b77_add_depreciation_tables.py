"""add_depreciation_tables

Revision ID: c40547be8b77
Revises: c3d4e5f6g7h8
Create Date: 2026-03-18 10:11:31.528961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c40547be8b77'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create fixed_assets table
    op.create_table('fixed_assets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('asset_name', sa.String(), nullable=False),
        sa.Column('asset_category', sa.String(), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('purchase_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('salvage_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('useful_life_years', sa.Integer(), nullable=False),
        sa.Column('depreciation_method', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('vendor', sa.String(), nullable=True),
        sa.Column('serial_number', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create depreciation_entries table
    op.create_table('depreciation_entries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('asset_id', sa.String(), nullable=False),
        sa.Column('depreciation_date', sa.Date(), nullable=False),
        sa.Column('depreciation_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('accumulated_depreciation', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('book_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['fixed_assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_fixed_assets_company_id'), 'fixed_assets', ['company_id'], unique=False)
    op.create_index(op.f('ix_fixed_assets_asset_category'), 'fixed_assets', ['asset_category'], unique=False)
    op.create_index(op.f('ix_depreciation_entries_asset_id'), 'depreciation_entries', ['asset_id'], unique=False)
    op.create_index(op.f('ix_depreciation_entries_depreciation_date'), 'depreciation_entries', ['depreciation_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_depreciation_entries_depreciation_date'), table_name='depreciation_entries')
    op.drop_index(op.f('ix_depreciation_entries_asset_id'), table_name='depreciation_entries')
    op.drop_index(op.f('ix_fixed_assets_asset_category'), table_name='fixed_assets')
    op.drop_index(op.f('ix_fixed_assets_company_id'), table_name='fixed_assets')
    
    # Drop tables
    op.drop_table('depreciation_entries')
    op.drop_table('fixed_assets')
