"""
Drop budgets table (cleanup)

Revision ID: 3f2c9a1b7e4a
Revises: 2b1a9c4d1f2b
Create Date: 2025-11-10 00:00:01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f2c9a1b7e4a'
down_revision = '2b1a9c4d1f2b'
branch_labels = None
depends_on = None

def upgrade():
    # Use raw SQL to avoid errors if the table doesn't exist in some envs
    op.execute('DROP TABLE IF EXISTS budgets CASCADE')


def downgrade():
    # Recreate a minimal budgets table compatible with older code, if needed
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('category_id', sa.Integer(), nullable=False, index=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('notify_threshold', sa.Float(), nullable=False, server_default=sa.text('0.8')),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'category_id', 'year', 'month', name='uq_budget_user_category_month'),
    )
