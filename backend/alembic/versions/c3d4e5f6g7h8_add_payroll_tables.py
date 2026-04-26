"""Add payroll tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-03-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add payroll tables."""
    
    # Create employees table
    op.create_table('employees',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('employee_id', sa.String(length=50), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('salary', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('pay_frequency', sa.String(length=50), nullable=True),
        sa.Column('job_title', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_employees_employee_id'), 'employees', ['employee_id'], unique=True)
    op.create_index(op.f('ix_employees_email'), 'employees', ['email'], unique=True)
    
    # Create payroll_entries table
    op.create_table('payroll_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('employee_id', sa.UUID(), nullable=True),
        sa.Column('pay_period_start', sa.Date(), nullable=False),
        sa.Column('pay_period_end', sa.Date(), nullable=False),
        sa.Column('gross_pay', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('federal_tax', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('state_tax', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('social_security', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('medicare', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('other_deductions', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('net_pay', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('pay_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop payroll tables."""
    op.drop_table('payroll_entries')
    op.drop_index(op.f('ix_employees_email'), table_name='employees')
    op.drop_index(op.f('ix_employees_employee_id'), table_name='employees')
    op.drop_table('employees')