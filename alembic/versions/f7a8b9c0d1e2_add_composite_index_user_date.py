"""Add composite index on transactions (user_id, transaction_date)

Revision ID: f7a8b9c0d1e2
Revises: 3f2c9a1b7e4a, c5f1e2b3d4e5
Create Date: 2026-03-31 21:30:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f7a8b9c0d1e2'
down_revision = ('3f2c9a1b7e4a', 'c5f1e2b3d4e5')
branch_labels = None
depends_on = None


def upgrade():
    # Composite index for the hot query path: daily balance + user transaction listing
    # This index covers WHERE user_id = ? AND transaction_date BETWEEN ? AND ?
    op.create_index(
        'ix_transactions_user_date',
        'transactions',
        ['user_id', 'transaction_date'],
        unique=False,
        if_not_exists=True,
    )


def downgrade():
    op.drop_index('ix_transactions_user_date', table_name='transactions')
