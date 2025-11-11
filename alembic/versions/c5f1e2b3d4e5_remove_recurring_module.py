"""Remove recurring module

Revision ID: c5f1e2b3d4e5
Revises: 961fd5c80514
Create Date: 2025-11-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c5f1e2b3d4e5'
down_revision: Union[str, None] = '961fd5c80514'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the recurring_id foreign key and column from transactions
    op.drop_constraint('transactions_recurring_id_fkey', 'transactions', type_='foreignkey')
    op.drop_index('ix_transactions_recurring_id', table_name='transactions')
    op.drop_column('transactions', 'recurring_id')
    
    # Drop the recurring_transactions table
    op.drop_table('recurring_transactions')
    
    # Drop the Frequency enum type
    op.execute("DROP TYPE IF EXISTS frequency")


def downgrade() -> None:
    # Recreate Frequency enum
    frequency_enum = postgresql.ENUM('DAILY', 'WEEKLY', 'MONTHLY', name='frequency', create_type=True)
    frequency_enum.create(op.get_bind())
    
    # Recreate recurring_transactions table
    op.create_table(
        'recurring_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('type', postgresql.ENUM('income', 'expense', name='transactiontype', create_type=False), nullable=False),
        sa.Column('frequency', postgresql.ENUM('DAILY', 'WEEKLY', 'MONTHLY', name='frequency', create_type=False), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('weekday', sa.Integer(), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('next_run_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recurring_transactions_id', 'recurring_transactions', ['id'], unique=False)
    op.create_index('ix_recurring_transactions_user_id', 'recurring_transactions', ['user_id'], unique=False)
    op.create_index('ix_recurring_transactions_category_id', 'recurring_transactions', ['category_id'], unique=False)
    
    # Add back recurring_id to transactions
    op.add_column('transactions', sa.Column('recurring_id', sa.Integer(), nullable=True))
    op.create_index('ix_transactions_recurring_id', 'transactions', ['recurring_id'], unique=False)
    op.create_foreign_key('transactions_recurring_id_fkey', 'transactions', 'recurring_transactions', ['recurring_id'], ['id'], ondelete='SET NULL')
